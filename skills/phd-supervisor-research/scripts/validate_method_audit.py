#!/usr/bin/env python3
"""Validate the supplemental research-method/translation audit.

This validator intentionally leaves the base records.json schema untouched. It
reconciles the supplemental audit against every retained A/B/C record and
enforces the evidence-depth/status boundaries documented in
references/research-method-translation-audit.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "research-method-audit-1.1"
STATUSES = {"confirmed", "provisional", "ungraded", "incomplete"}
OUTREACH_STATES = {"active", "hold_no_capacity", "hold_user"}
AUTHOR_ROLES = {"O3C", "O2C", "O2S", "O1L", "O1F", "O0"}
STRONG_ROLES = {"O3C", "O2C", "O2S"}
CANDIDATE_LED_ROLES = STRONG_ROLES | {"O1L", "O1F"}
ROLE_WEIGHTS = {"O3C": 1.00, "O2C": 0.85, "O2S": 0.70, "O1L": 0.45, "O1F": 0.35, "O0": 0.15}
CORRESPONDING_STATUSES = {"CORRESPONDING", "CO_CORRESPONDING", "NOT_CORRESPONDING", "UNVERIFIED"}
SENIOR_STATUSES = {"EXPLICIT_SENIOR", "CO_SENIOR", "LAST_AUTHOR_ONLY", "NOT_SENIOR", "UNVERIFIED"}
AUTHOR_ORDER_STATUSES = {"FIRST", "CO_FIRST", "LAST", "PENULTIMATE", "MIDDLE", "CONSORTIUM", "OTHER"}
METHOD_CODES = {"RM-E", "RM-B", "RM-EB", "RM-M", "RM-C"}
METHOD_FAMILY_TAGS = {"EXPERIMENTAL", "BIOINFORMATICS", "OMICS", "THEORETICAL_METHOD", "CLINICAL_OUTCOMES"}
OMICS_MODALITIES = {
    "GENOMICS", "TRANSCRIPTOMICS", "EPIGENOMICS", "PROTEOMICS", "METABOLOMICS",
    "SINGLE_CELL", "SPATIAL", "MULTI_OMICS", "OTHER_OMICS",
}
TRANSLATION_CODES = {"TR0", "TR1", "TR2", "TR3", "CLIN_ONLY"}
CLINICAL_SUBTYPES = {"CO-RWE", "CO-TRIAL", "CO-OBS", "CO-EPID", "CO-PROC"}
REVIEW_DEPTHS = {"M0_MACHINE_ABSTRACT", "M2_HUMAN_ABSTRACT", "M3_FULL_TEXT_DESIGN"}
REVIEW_ACTORS = {"machine_rule", "model_manual", "human_manual"}
EVIDENCE_FEATURE_FIELDS = {
    "clinicalAnchor",
    "experimentalWork",
    "omicsWork",
    "bioinformaticsWork",
    "theoreticalMethodContribution",
    "endpoint",
    "validation",
}
TRANSLATION_EVIDENCE_FIELDS = {
    "hasClinicalAnchor",
    "hasMolecularOmicsOrMechanisticBridge",
    "hasIndependentOrOrthogonalValidation",
    "hasProspectiveOrInterventionalLink",
    "hasFunctionalValidation",
    "hasClinicalLevelValidation",
}
GRADES = {"MTG1", "MTG2", "MTG3", "MTG4"}
PROVISIONAL_GRADES = {f"p{grade}" for grade in GRADES}
PORTFOLIO_CODES = {
    "RP-E-PURE",
    "RP-B-PURE",
    "RP-EB-INTRA",
    "RP-EB-SPLIT",
    "RP-M-PURE",
    "RP-TRANS",
    "RP-C-PURE",
    "RP-C-DOMINANT",
}
SCORE_LIMITS = {
    "methodIntegration": (0, 30),
    "clinicalTranslation": (0, 30),
    "researchOwnership": (0, 20),
    "recentContinuity": (0, 10),
    "evidenceCompleteness": (0, 10),
}
SCORE_VALUES = {
    "methodIntegration": {0, 6, 10, 16, 22, 26, 30},
    "clinicalTranslation": {0, 6, 14, 20, 25, 30},
    "researchOwnership": {0, 6, 12, 16, 20},
    "recentContinuity": {0, 2, 5, 8, 10},
    "evidenceCompleteness": {0, 3, 7, 10},
}
GRADE_BANDS = {
    "MTG1": (80, 100),
    "MTG2": (65, 79),
    "MTG3": (45, 64),
    "MTG4": (0, 44),
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def contains_cjk(value: Any) -> bool:
    return nonempty(value) and bool(re.search(r"[\u3400-\u9fff]", value))


def parse_date(value: Any) -> date | None:
    if not nonempty(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def subtract_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def conflict_is_material_unresolved(item: Any) -> bool:
    return (
        isinstance(item, dict)
        and item.get("material") is True
        and item.get("resolved") is not True
    )


def string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    required: bool = False,
) -> list[str]:
    """Return a strictly typed, trimmed string list while recording errors."""
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label} must contain only non-empty strings")
    normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(normalized) != len(set(normalized)):
        errors.append(f"{label} must not contain duplicates")
    if required and not normalized:
        errors.append(f"{label} requires at least one entry")
    return normalized


def is_http_url(value: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s]+", value))


def derived_author_role(paper: dict[str, Any]) -> str | None:
    corresponding = paper.get("correspondingStatus")
    senior = paper.get("seniorStatus")
    order = paper.get("authorOrderStatus")
    if corresponding not in CORRESPONDING_STATUSES or senior not in SENIOR_STATUSES or order not in AUTHOR_ORDER_STATUSES:
        return None
    if corresponding == "CORRESPONDING":
        return "O3C"
    if corresponding == "CO_CORRESPONDING":
        return "O2C"
    if senior in {"EXPLICIT_SENIOR", "CO_SENIOR"}:
        return "O2S"
    if order == "LAST":
        return "O1L"
    if order in {"FIRST", "CO_FIRST"}:
        return "O1F"
    return "O0"


def effective_translation_code(paper: dict[str, Any]) -> str:
    code = str(paper.get("translationCode"))
    if code == "TR3" and paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN":
        return "TR2"
    return code


def derive_portfolio_codes(included: list[dict[str, Any]], status: Any) -> set[str]:
    if status not in {"confirmed", "provisional"}:
        return set()
    strong = [paper for paper in included if paper.get("authorRole") in STRONG_ROLES]
    methods = Counter(str(paper.get("methodCode")) for paper in strong)
    codes: set[str] = set()
    threshold = 2 if status == "confirmed" else 1
    if methods.get("RM-EB", 0) >= threshold:
        codes.add("RP-EB-INTRA")
    if methods.get("RM-E", 0) >= threshold and methods.get("RM-B", 0) >= threshold:
        codes.add("RP-EB-SPLIT")
    if sum(1 for paper in strong if paper.get("translationCode") in {"TR2", "TR3"}) >= threshold:
        codes.add("RP-TRANS")
    if len(strong) >= 5:
        method_set = {paper.get("methodCode") for paper in strong}
        pure_codes = {
            "RM-E": "RP-E-PURE",
            "RM-B": "RP-B-PURE",
            "RM-M": "RP-M-PURE",
            "RM-C": "RP-C-PURE",
        }
        if len(method_set) == 1:
            method = next(iter(method_set))
            code = pure_codes.get(str(method))
            if code and (
                code != "RP-C-PURE"
                or (
                    all(paper.get("translationCode") == "CLIN_ONLY" for paper in strong)
                    and not any(paper.get("translationCode") in {"TR2", "TR3"} for paper in included)
                )
            ):
                codes.add(code)
    denominator = sum(ROLE_WEIGHTS.get(str(paper.get("authorRole")), 0.0) for paper in included)
    clinical = sum(
        ROLE_WEIGHTS.get(str(paper.get("authorRole")), 0.0)
        for paper in included
        if paper.get("methodCode") == "RM-C"
    )
    ratio = clinical / denominator if denominator else 0.0
    if 0.70 <= ratio < 1.0:
        codes.add("RP-C-DOMINANT")
    return codes


def derive_score_components(
    included: list[dict[str, Any]],
    audit_as_of: date | None,
    m4_consistent: bool,
    material_unresolved: bool,
) -> dict[str, int]:
    strong = [paper for paper in included if paper.get("authorRole") in STRONG_ROLES]
    candidate_led = [paper for paper in included if paper.get("authorRole") in CANDIDATE_LED_ROLES]
    strong_methods = Counter(str(paper.get("methodCode")) for paper in strong)
    led_methods = Counter(str(paper.get("methodCode")) for paper in candidate_led)

    if strong_methods.get("RM-EB", 0) >= 2:
        method_score = 30
    elif (
        strong_methods.get("RM-EB", 0) >= 1
        and strong_methods.get("RM-E", 0) >= 2
        and strong_methods.get("RM-B", 0) >= 2
    ):
        method_score = 26
    elif strong_methods.get("RM-E", 0) >= 2 and strong_methods.get("RM-B", 0) >= 2:
        method_score = 22
    elif strong_methods.get("RM-EB", 0) >= 1 or (
        strong_methods.get("RM-E", 0) >= 1 and strong_methods.get("RM-B", 0) >= 1
    ):
        method_score = 16
    elif (
        strong_methods.get("RM-E", 0) >= 2 and led_methods.get("RM-B", 0) + led_methods.get("RM-EB", 0) >= 1
    ) or (
        strong_methods.get("RM-B", 0) >= 2 and led_methods.get("RM-E", 0) + led_methods.get("RM-EB", 0) >= 1
    ):
        method_score = 10
    elif strong and ({paper.get("methodCode") for paper in strong} <= {"RM-E"} or {paper.get("methodCode") for paper in strong} <= {"RM-B"}):
        method_score = 6
    else:
        method_score = 0

    strong_translation = [effective_translation_code(paper) for paper in strong]
    strong_tr3 = strong_translation.count("TR3")
    strong_tr2plus = strong_tr3 + strong_translation.count("TR2")
    if strong_tr3 >= 2:
        translation_score = 30
    elif strong_tr3 >= 1 and strong_translation.count("TR2") >= 1:
        translation_score = 25
    elif strong_tr2plus >= 2:
        translation_score = 20
    elif any(code in {"TR2", "TR3"} for code in strong_translation):
        translation_score = 14
    elif strong_translation.count("TR1") >= 2:
        translation_score = 6
    else:
        translation_score = 0

    strong_count = len(strong)
    ownership_score = 20 if strong_count >= 5 else 16 if strong_count >= 3 else 12 if strong_count == 2 else 6 if strong_count == 1 else 0
    five_year_led = 0
    if audit_as_of:
        five_year_start = subtract_years(audit_as_of, 5)
        five_year_led = sum(
            1
            for paper in candidate_led
            if (published := parse_date(paper.get("publicationDate"))) is not None and five_year_start <= published <= audit_as_of
        )
    if five_year_led >= 5:
        continuity_score = 10
    elif five_year_led >= 3:
        continuity_score = 8
    elif five_year_led >= 1 and m4_consistent:
        continuity_score = 5
    elif len(candidate_led) - five_year_led > five_year_led:
        continuity_score = 2
    else:
        continuity_score = 0

    all_strong_m3 = all(paper.get("reviewDepth") == "M3_FULL_TEXT_DESIGN" for paper in strong)
    all_strong_m2 = all(paper.get("reviewDepth") in {"M2_HUMAN_ABSTRACT", "M3_FULL_TEXT_DESIGN"} for paper in strong)
    if strong and m4_consistent and not material_unresolved and all_strong_m3:
        evidence_score = 10
    elif strong and not material_unresolved and all_strong_m2:
        evidence_score = 7
    else:
        evidence_score = 3
    return {
        "methodIntegration": method_score,
        "clinicalTranslation": translation_score,
        "researchOwnership": ownership_score,
        "recentContinuity": continuity_score,
        "evidenceCompleteness": evidence_score,
    }


def validation_payload(case_dir: Path, strict: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    records_path = case_dir / "data" / "records.json"
    case_path = case_dir / "data" / "case.json"
    sources_path = case_dir / "data" / "sources.json"
    audit_path = case_dir / "data" / "research-method-audit.json"
    report_path = case_dir / "08-RESEARCH-METHOD-TRANSLATION-AUDIT.md"

    for path in (records_path, case_path, sources_path, audit_path):
        if not path.is_file():
            errors.append(f"missing required file: {path}")
    if errors:
        return {
            "status": "invalid",
            "strict": strict,
            "caseDir": str(case_dir),
            "errors": errors,
            "warnings": warnings,
        }

    try:
        records = read_json(records_path)
        case = read_json(case_path)
        sources = read_json(sources_path)
        audit = read_json(audit_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"failed to read JSON: {exc}")
        return {
            "status": "invalid",
            "strict": strict,
            "caseDir": str(case_dir),
            "errors": errors,
            "warnings": warnings,
        }

    if not isinstance(records, list):
        errors.append("records.json must contain a list")
        records = []
    if not isinstance(case, dict):
        errors.append("case.json must contain an object")
        case = {}
    if not isinstance(sources, list):
        errors.append("sources.json must contain a list")
        sources = []
    if not isinstance(audit, dict):
        errors.append("research-method-audit.json must contain an object")
        audit = {}
    source_map: dict[str, dict[str, Any]] = {}
    for source_index, source in enumerate(sources):
        prefix = f"sources.json[{source_index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
            continue
        source_id = source_id.strip()
        if source_id in source_map:
            errors.append(f"sources.json contains duplicate source id {source_id}")
        if "url" in source:
            source_url = source.get("url")
            if not isinstance(source_url, str) or not source_url.strip():
                errors.append(f"{prefix}.url must be a non-empty string")
            elif not is_http_url(source_url.strip()):
                errors.append(f"{prefix}.url must be an absolute http(s) URL")
        source_map[source_id] = source
    source_ids_known = set(source_map)

    retained_ids: list[str] = []
    retained_records: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        if record.get("priorityTier") in {"A", "B", "C"}:
            candidate_id = str(record.get("id", "")).strip()
            if not candidate_id:
                errors.append(f"records.json[{index}] retained A/B/C record lacks id")
            else:
                retained_ids.append(candidate_id)
                retained_records[candidate_id] = record
    if len(retained_ids) != len(set(retained_ids)):
        errors.append("records.json contains duplicate retained A/B/C candidate ids")
    retained_set = set(retained_ids)

    if audit.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    case_as_of = parse_date(case.get("asOf"))
    audit_as_of = parse_date(audit.get("caseAsOf"))
    generated_at = parse_date(audit.get("generatedAt"))
    if audit_as_of is None:
        errors.append("caseAsOf must use YYYY-MM-DD")
    elif case_as_of and audit_as_of != case_as_of:
        errors.append("caseAsOf must equal data/case.json asOf")
    if generated_at is None:
        errors.append("generatedAt must use YYYY-MM-DD")
    search_scope = audit.get("searchScope")
    if not isinstance(search_scope, dict):
        errors.append("searchScope must be an object")
    else:
        if search_scope.get("coverageClaim") != "bounded_public_search":
            errors.append("searchScope.coverageClaim must be bounded_public_search")
        if search_scope.get("defaultWindowYears") != 5 or search_scope.get("extendedWindowYears") != 8:
            errors.append("searchScope must declare defaultWindowYears=5 and extendedWindowYears=8")

    candidates = audit.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        candidates = []
    candidate_ids: list[str] = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            continue
        raw_candidate_id = item.get("candidateId")
        if not isinstance(raw_candidate_id, str) or not raw_candidate_id.strip():
            errors.append(f"candidates[{index}].candidateId must be a non-empty string")
            candidate_ids.append("")
        else:
            candidate_ids.append(raw_candidate_id.strip())
    counts = Counter(candidate_ids)
    duplicate_ids = sorted(key for key, value in counts.items() if value > 1)
    if duplicate_ids:
        errors.append(f"duplicate audit candidate ids: {duplicate_ids}")
    audited_set = {item for item in candidate_ids if item}
    missing_ids = sorted(retained_set - audited_set)
    extra_ids = sorted(audited_set - retained_set)
    if missing_ids:
        errors.append(f"retained A/B/C candidates missing from method audit: {missing_ids}")
    if extra_ids:
        errors.append(f"method audit contains non-A/B/C candidate ids: {extra_ids}")

    reconciliation = audit.get("rosterReconciliation")
    if not isinstance(reconciliation, dict):
        errors.append("rosterReconciliation must be an object")
        reconciliation = {}
    declared_retained_list = as_list(reconciliation.get("retainedAbcCandidateIds"))
    declared_audited_list = as_list(reconciliation.get("auditedCandidateIds"))
    declared_missing_list = as_list(reconciliation.get("missingCandidateIds"))
    for field, values in (
        ("retainedAbcCandidateIds", declared_retained_list),
        ("auditedCandidateIds", declared_audited_list),
        ("missingCandidateIds", declared_missing_list),
    ):
        if any(not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"rosterReconciliation.{field} must contain only non-empty strings")
        normalized = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        if len(normalized) != len(set(normalized)):
            errors.append(f"rosterReconciliation.{field} must not contain duplicates")
    declared_retained = {value.strip() for value in declared_retained_list if isinstance(value, str) and value.strip()}
    declared_audited = {value.strip() for value in declared_audited_list if isinstance(value, str) and value.strip()}
    declared_missing = {value.strip() for value in declared_missing_list if isinstance(value, str) and value.strip()}
    if declared_retained != retained_set:
        errors.append("rosterReconciliation.retainedAbcCandidateIds does not match records.json A/B/C ids")
    if declared_audited != audited_set:
        errors.append("rosterReconciliation.auditedCandidateIds must match candidates[].candidateId exactly")
    if declared_missing != set(missing_ids):
        errors.append("rosterReconciliation.missingCandidateIds must equal retained ids absent from candidates[]")
    if declared_missing:
        errors.append("rosterReconciliation.missingCandidateIds must be empty for a complete full run")

    status_counts: Counter[str] = Counter()
    eligible_paper_count = 0
    depth_counts: Counter[str] = Counter()
    m4_count = 0

    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            errors.append(f"candidates[{index}] must be an object")
            continue
        candidate_id = str(candidate.get("candidateId", "")).strip() or f"index-{index}"
        label = f"candidate {candidate_id}"
        base_record = retained_records.get(candidate_id, {})
        if candidate.get("priorityTier") != base_record.get("priorityTier"):
            errors.append(f"{label}: priorityTier must match records.json")
        if candidate.get("opportunityStatus") != base_record.get("opportunityStatus"):
            errors.append(f"{label}: opportunityStatus must match records.json")
        for field in ("departmentZh", "currentRoleZh", "researchDirectionZh"):
            if not contains_cjk(candidate.get(field)):
                errors.append(f"{label}: {field} must contain substantive Chinese text")

        status = candidate.get("scientificAuditStatus")
        if status not in STATUSES:
            errors.append(f"{label}: invalid scientificAuditStatus {status!r}")
        else:
            status_counts[str(status)] += 1
        outreach = candidate.get("outreachControl")
        if not isinstance(outreach, dict) or outreach.get("status") not in OUTREACH_STATES:
            errors.append(f"{label}: outreachControl.status is missing or invalid")
        elif outreach.get("status") in {"hold_no_capacity", "hold_user"}:
            for field in ("reason", "scope", "recheckCondition"):
                if not nonempty(outreach.get(field)):
                    errors.append(f"{label}: held outreachControl requires {field}")
            recorded_at = parse_date(outreach.get("recordedAt"))
            if recorded_at is None:
                errors.append(f"{label}: held outreachControl.recordedAt must use YYYY-MM-DD")
            elif generated_at and recorded_at > generated_at:
                errors.append(f"{label}: outreachControl.recordedAt cannot be later than generatedAt")
        if candidate.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"{label}: confidence must be high, medium, or low")

        search_date = parse_date(candidate.get("searchDate"))
        if search_date is None:
            errors.append(f"{label}: searchDate must use YYYY-MM-DD")
        elif audit_as_of and search_date > audit_as_of:
            errors.append(f"{label}: searchDate cannot be later than caseAsOf")
        window_years = candidate.get("windowYears")
        if window_years not in {5, 8}:
            errors.append(f"{label}: windowYears must be 5 or 8")
        candidate_window_start = parse_date(candidate.get("windowStart"))
        candidate_window_end = parse_date(candidate.get("windowEnd"))
        expected_candidate_start = subtract_years(audit_as_of, window_years) if audit_as_of and window_years in {5, 8} else None
        if candidate_window_start is None or candidate_window_end is None:
            errors.append(f"{label}: windowStart/windowEnd must use YYYY-MM-DD")
        elif expected_candidate_start and audit_as_of and (
            candidate_window_start != expected_candidate_start or candidate_window_end != audit_as_of
        ):
            errors.append(f"{label}: candidate window must exactly match the active {window_years}-year interval ending on caseAsOf")
        extension_reason = candidate.get("extensionReason")
        search_status = candidate.get("searchStatus")
        if search_status not in {"bounded_complete", "search_incomplete"}:
            errors.append(f"{label}: searchStatus must be bounded_complete or search_incomplete")
        search_plan = candidate.get("searchPlan")
        if not isinstance(search_plan, list) or not search_plan:
            errors.append(f"{label}: searchPlan must be a non-empty list")
            search_plan = []
        plan_by_id: dict[str, dict[str, Any]] = {}
        for plan_index, plan_entry in enumerate(search_plan):
            prefix = f"{label} searchPlan[{plan_index}]"
            if not isinstance(plan_entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            query_id = plan_entry.get("queryId")
            if not isinstance(query_id, str) or not query_id.strip():
                errors.append(f"{prefix}: queryId must be a non-empty string")
                continue
            query_id = query_id.strip()
            if query_id in plan_by_id:
                errors.append(f"{label}: duplicate searchPlan queryId {query_id}")
            for field in ("sourceKey", "source", "query"):
                if not nonempty(plan_entry.get(field)):
                    errors.append(f"{prefix}: {field} is required")
            plan_by_id[query_id] = plan_entry
        ledger = candidate.get("searchLedger")
        if not isinstance(ledger, list) or not ledger:
            errors.append(f"{label}: searchLedger must be a non-empty list")
            ledger = []
        any_truncated = False
        retry_present = False
        ledger_by_query_stage: Counter[tuple[str, str]] = Counter()
        active_ledger: list[dict[str, Any]] = []
        base_start = subtract_years(audit_as_of, 5) if audit_as_of else None
        extended_start = subtract_years(audit_as_of, 8) if audit_as_of else None
        active_stage = "BASE_5Y" if window_years == 5 else "EXTENDED_8Y"
        for ledger_index, entry in enumerate(ledger):
            prefix = f"{label} searchLedger[{ledger_index}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            query_id = entry.get("queryId")
            if not isinstance(query_id, str) or not query_id.strip():
                errors.append(f"{prefix}: queryId must be a non-empty string")
                query_id = ""
            else:
                query_id = query_id.strip()
            search_stage = entry.get("searchStage")
            if search_stage not in {"BASE_5Y", "EXTENDED_8Y"}:
                errors.append(f"{prefix}: searchStage must be BASE_5Y or EXTENDED_8Y")
            if query_id and search_stage in {"BASE_5Y", "EXTENDED_8Y"}:
                ledger_by_query_stage[(query_id, str(search_stage))] += 1
            planned = plan_by_id.get(query_id)
            if query_id and planned is None:
                errors.append(f"{prefix}: queryId {query_id!r} is not declared in searchPlan")
            elif planned is not None:
                for field in ("source", "query"):
                    if entry.get(field) != planned.get(field):
                        errors.append(f"{prefix}: {field} must match searchPlan query {query_id}")
            for field in ("source", "query", "pagesOrCursorsChecked"):
                if not nonempty(entry.get(field)):
                    errors.append(f"{prefix}: {field} is required")
            entry_start = parse_date(entry.get("windowStart"))
            entry_end = parse_date(entry.get("windowEnd"))
            expected_start = base_start if search_stage == "BASE_5Y" else extended_start
            if entry_start is None or entry_end is None:
                errors.append(f"{prefix}: windowStart/windowEnd must use YYYY-MM-DD")
            elif expected_start and audit_as_of and (entry_start != expected_start or entry_end != audit_as_of):
                errors.append(f"{prefix}: structured window must exactly match {search_stage} ending on caseAsOf")
            ledger_searched_at = parse_date(entry.get("searchedAt"))
            if ledger_searched_at is None:
                errors.append(f"{prefix}: searchedAt must use YYYY-MM-DD")
            elif search_date and ledger_searched_at > search_date:
                errors.append(f"{prefix}: searchedAt cannot be later than candidate searchDate")
            elif generated_at and ledger_searched_at > generated_at:
                errors.append(f"{prefix}: searchedAt cannot be later than generatedAt")
            result_count = entry.get("resultCount")
            if not isinstance(result_count, int) or result_count < 0:
                errors.append(f"{prefix}: resultCount must be a non-negative integer")
            if not isinstance(entry.get("truncated"), bool):
                errors.append(f"{prefix}: truncated must be boolean")
            any_truncated = any_truncated or entry.get("truncated") is True
            if entry.get("accessStatus") not in {"complete", "partial", "blocked"}:
                errors.append(f"{prefix}: accessStatus must be complete, partial, or blocked")
            retry_present = retry_present or nonempty(entry.get("retryNotes"))
            if search_stage == active_stage:
                active_ledger.append(entry)
        required_stages = {"BASE_5Y"} | ({"EXTENDED_8Y"} if window_years == 8 else set())
        for query_id in plan_by_id:
            for stage in required_stages:
                count = ledger_by_query_stage[(query_id, stage)]
                if count != 1:
                    errors.append(f"{label}: query {query_id} requires exactly one {stage} ledger entry (found {count})")
            if window_years == 5 and ledger_by_query_stage[(query_id, "EXTENDED_8Y")]:
                errors.append(f"{label}: EXTENDED_8Y ledger entries are not allowed when the active window is five years")
        expected_search_status = "bounded_complete" if ledger and not any_truncated and all(
            isinstance(entry, dict) and entry.get("accessStatus") == "complete" for entry in ledger
        ) and all(ledger_by_query_stage[(query_id, stage)] == 1 for query_id in plan_by_id for stage in required_stages) else "search_incomplete"
        if search_status != expected_search_status:
            errors.append(f"{label}: searchStatus must reflect ledger truncation/access state ({expected_search_status})")

        papers = candidate.get("papers")
        if not isinstance(papers, list):
            errors.append(f"{label}: papers must be a list")
            papers = []
        seen_work_ids: set[str] = set()
        included: list[dict[str, Any]] = []
        five_year_candidate_led = 0
        paper_material_unresolved = False
        blocking_unresolved = False
        nonblocking_unresolved = False
        for paper_index, paper in enumerate(papers):
            prefix = f"{label} papers[{paper_index}]"
            if not isinstance(paper, dict):
                errors.append(f"{prefix} must be an object")
                continue
            work_id = str(paper.get("workId", "")).strip()
            if not work_id:
                errors.append(f"{prefix}: workId is required")
            elif work_id in seen_work_ids:
                errors.append(f"{prefix}: duplicate workId {work_id}")
            else:
                seen_work_ids.add(work_id)
            decision = paper.get("inclusionDecision")
            if decision not in {"included", "excluded"}:
                errors.append(f"{prefix}: inclusionDecision must be included or excluded")
                continue
            if decision == "excluded":
                if not nonempty(paper.get("exclusionReason")):
                    errors.append(f"{prefix}: excluded paper requires exclusionReason")
                continue

            included.append(paper)
            eligible_paper_count += 1
            publication_date = parse_date(paper.get("publicationDate"))
            if publication_date is None:
                errors.append(f"{prefix}: publicationDate must use YYYY-MM-DD")
            elif audit_as_of and publication_date > audit_as_of:
                errors.append(f"{prefix}: publicationDate cannot be later than caseAsOf")
            elif audit_as_of and window_years in {5, 8} and publication_date < subtract_years(audit_as_of, window_years):
                errors.append(f"{prefix}: publicationDate falls outside the declared {window_years}-year window")
            identity_evidence = paper.get("identityEvidence")
            if not isinstance(identity_evidence, list) or len([x for x in identity_evidence if nonempty(x)]) < 2:
                errors.append(f"{prefix}: identityEvidence requires at least two non-empty items")
            role = paper.get("authorRole")
            if role not in AUTHOR_ROLES:
                errors.append(f"{prefix}: invalid authorRole {role!r}")
            if not nonempty(paper.get("roleBasis")):
                errors.append(f"{prefix}: roleBasis is required")
            if paper.get("correspondingStatus") not in CORRESPONDING_STATUSES:
                errors.append(f"{prefix}: invalid correspondingStatus {paper.get('correspondingStatus')!r}")
            if paper.get("seniorStatus") not in SENIOR_STATUSES:
                errors.append(f"{prefix}: invalid seniorStatus {paper.get('seniorStatus')!r}")
            if paper.get("authorOrderStatus") not in AUTHOR_ORDER_STATUSES:
                errors.append(f"{prefix}: invalid authorOrderStatus {paper.get('authorOrderStatus')!r}")
            expected_role = derived_author_role(paper)
            if expected_role is not None and role != expected_role:
                errors.append(f"{prefix}: authorRole must be derived as {expected_role} from structured authorship statuses")
            authorship_source_ids = string_list(
                paper.get("authorshipEvidenceSourceIds"),
                f"{prefix}: authorshipEvidenceSourceIds",
                errors,
                required=True,
            )
            if not nonempty(paper.get("authorshipEvidenceLocator")):
                errors.append(f"{prefix}: authorshipEvidenceLocator is required")
            unknown_authorship_ids = sorted(set(authorship_source_ids) - source_ids_known)
            if unknown_authorship_ids:
                errors.append(f"{prefix}: unknown authorshipEvidenceSourceIds {unknown_authorship_ids}")
            for source_id in authorship_source_ids:
                source = source_map.get(source_id, {})
                if candidate_id not in as_list(source.get("subjectIds")):
                    errors.append(f"{prefix}: authorship evidence source {source_id} is not candidate-bound")
            if role in {"O3C", "O2C"} and paper.get("correspondingStatus") not in {"CORRESPONDING", "CO_CORRESPONDING"}:
                errors.append(f"{prefix}: {role} requires an explicit corresponding-status record")
            if role == "O2S" and paper.get("seniorStatus") not in {"EXPLICIT_SENIOR", "CO_SENIOR"}:
                errors.append(f"{prefix}: O2S requires an explicit senior/co-senior statement")
            method = paper.get("methodCode")
            translation = paper.get("translationCode")
            if method not in METHOD_CODES:
                errors.append(f"{prefix}: invalid methodCode {method!r}")
            if translation not in TRANSLATION_CODES:
                errors.append(f"{prefix}: invalid translationCode {translation!r}")
            method_tags = string_list(paper.get("methodFamilyTags"), f"{prefix}: methodFamilyTags", errors, required=True)
            modalities = string_list(paper.get("omicsModalities"), f"{prefix}: omicsModalities", errors)
            unknown_method_tags = sorted(set(method_tags) - METHOD_FAMILY_TAGS)
            unknown_modalities = sorted(set(modalities) - OMICS_MODALITIES)
            if unknown_method_tags:
                errors.append(f"{prefix}: unknown methodFamilyTags {unknown_method_tags}")
            if unknown_modalities:
                errors.append(f"{prefix}: unknown omicsModalities {unknown_modalities}")
            tag_set = set(method_tags)
            method_tag_rules = {
                "RM-E": tag_set == {"EXPERIMENTAL"},
                "RM-B": bool(tag_set & {"BIOINFORMATICS", "OMICS"}) and tag_set <= {"BIOINFORMATICS", "OMICS"},
                "RM-EB": "EXPERIMENTAL" in tag_set and bool(tag_set & {"BIOINFORMATICS", "OMICS"}) and tag_set <= {"EXPERIMENTAL", "BIOINFORMATICS", "OMICS"},
                "RM-M": "THEORETICAL_METHOD" in tag_set and tag_set <= {"THEORETICAL_METHOD", "BIOINFORMATICS", "OMICS"},
                "RM-C": tag_set == {"CLINICAL_OUTCOMES"},
            }
            if method in METHOD_CODES and not method_tag_rules.get(str(method), False):
                errors.append(f"{prefix}: methodFamilyTags are incompatible with {method}")
            if ("OMICS" in tag_set) != bool(modalities):
                errors.append(f"{prefix}: OMICS tag and omicsModalities must be present together")
            translation_evidence = paper.get("translationEvidence")
            if not isinstance(translation_evidence, dict):
                errors.append(f"{prefix}: translationEvidence must be an object")
                translation_evidence = {}
            missing_translation_evidence = sorted(TRANSLATION_EVIDENCE_FIELDS - set(translation_evidence))
            extra_translation_evidence = sorted(set(translation_evidence) - TRANSLATION_EVIDENCE_FIELDS)
            if missing_translation_evidence:
                errors.append(f"{prefix}: translationEvidence missing {missing_translation_evidence}")
            if extra_translation_evidence:
                errors.append(f"{prefix}: translationEvidence has unknown fields {extra_translation_evidence}")
            if any(not isinstance(translation_evidence.get(field), bool) for field in TRANSLATION_EVIDENCE_FIELDS):
                errors.append(f"{prefix}: every translationEvidence value must be boolean")
            te = translation_evidence
            clinical = te.get("hasClinicalAnchor") is True
            bridge = te.get("hasMolecularOmicsOrMechanisticBridge") is True
            independent = te.get("hasIndependentOrOrthogonalValidation") is True
            prospective = te.get("hasProspectiveOrInterventionalLink") is True
            functional = te.get("hasFunctionalValidation") is True
            clinical_level = te.get("hasClinicalLevelValidation") is True
            if translation == "TR0" and clinical:
                errors.append(f"{prefix}: TR0 requires hasClinicalAnchor=false")
            elif translation == "TR1" and (not clinical or not bridge or independent or prospective or functional or clinical_level):
                errors.append(f"{prefix}: TR1 requires a clinical bridge without independent, functional, prospective, or clinical-level validation")
            elif translation == "TR2" and (not clinical or not bridge or not independent or (prospective and functional and clinical_level)):
                errors.append(f"{prefix}: TR2 requires clinical bridge plus independent/orthogonal validation but not the complete TR3 loop")
            elif translation == "TR3" and not (clinical and bridge and independent and prospective and functional and clinical_level):
                errors.append(f"{prefix}: TR3 requires all six translationEvidence gates")
            elif translation == "CLIN_ONLY" and (not clinical or bridge or functional):
                errors.append(f"{prefix}: CLIN_ONLY requires a clinical anchor without molecular/mechanistic bridge or functional validation")
            if (method == "RM-C") != (translation == "CLIN_ONLY"):
                errors.append(f"{prefix}: RM-C and CLIN_ONLY must be assigned together")
            subtype = paper.get("clinicalOnlySubtype")
            if translation == "CLIN_ONLY" and subtype not in CLINICAL_SUBTYPES:
                errors.append(f"{prefix}: CLIN_ONLY requires a clinicalOnlySubtype")
            if translation != "CLIN_ONLY" and subtype not in {None, ""}:
                errors.append(f"{prefix}: clinicalOnlySubtype is allowed only with CLIN_ONLY")
            depth = paper.get("reviewDepth")
            actor = paper.get("reviewActor")
            if depth not in REVIEW_DEPTHS:
                errors.append(f"{prefix}: invalid reviewDepth {depth!r}")
            else:
                depth_counts[str(depth)] += 1
            if actor not in REVIEW_ACTORS:
                errors.append(f"{prefix}: invalid reviewActor {actor!r}")
            reviewed_at = parse_date(paper.get("reviewedAt"))
            if reviewed_at is None:
                errors.append(f"{prefix}: reviewedAt must use YYYY-MM-DD")
            elif generated_at and reviewed_at > generated_at:
                errors.append(f"{prefix}: reviewedAt cannot be later than generatedAt")
            if not nonempty(paper.get("reviewLocator")):
                errors.append(f"{prefix}: reviewLocator is required")
            if depth in {"M2_HUMAN_ABSTRACT", "M3_FULL_TEXT_DESIGN"} and actor == "machine_rule":
                errors.append(f"{prefix}: M2/M3 requires model_manual or human_manual actor")
            for field in ("scoreTrigger", "portfolioTrigger"):
                if not isinstance(paper.get(field), bool):
                    errors.append(f"{prefix}: {field} must be boolean")
            features = paper.get("evidenceFeatures")
            if not isinstance(features, dict) or not features:
                errors.append(f"{prefix}: evidenceFeatures must be a non-empty object")
            else:
                missing_features = sorted(EVIDENCE_FEATURE_FIELDS - set(features))
                if missing_features:
                    errors.append(f"{prefix}: evidenceFeatures missing {missing_features}")
                for field in EVIDENCE_FEATURE_FIELDS:
                    if field in features and not nonempty(features.get(field)):
                        errors.append(f"{prefix}: evidenceFeatures.{field} must be explicit, using 'none' when absent")
            paper_conflicts = paper.get("conflicts")
            if not isinstance(paper_conflicts, list):
                errors.append(f"{prefix}: conflicts must be a list")
            else:
                for conflict_index, conflict in enumerate(paper_conflicts):
                    conflict_prefix = f"{prefix} conflicts[{conflict_index}]"
                    if not isinstance(conflict, dict):
                        errors.append(f"{conflict_prefix} must be an object")
                        continue
                    if not nonempty(conflict.get("type")) or not nonempty(conflict.get("summary")):
                        errors.append(f"{conflict_prefix}: type and summary are required")
                    if not isinstance(conflict.get("material"), bool) or not isinstance(conflict.get("resolved"), bool):
                        errors.append(f"{conflict_prefix}: material and resolved must be boolean")
                    if conflict.get("impact") not in {"NONBLOCKING_PROVISIONAL", "BLOCKS_GRADE"}:
                        errors.append(f"{conflict_prefix}: impact must be NONBLOCKING_PROVISIONAL or BLOCKS_GRADE")
                    paper_material_unresolved = paper_material_unresolved or conflict_is_material_unresolved(conflict)
                    if conflict.get("resolved") is not True and conflict.get("impact") == "BLOCKS_GRADE":
                        blocking_unresolved = True
                    if conflict.get("resolved") is not True and conflict.get("impact") == "NONBLOCKING_PROVISIONAL":
                        nonblocking_unresolved = True
            source_ids = string_list(paper.get("sourceIds"), f"{prefix}: sourceIds", errors, required=True)
            source_urls = string_list(paper.get("sourceUrls"), f"{prefix}: sourceUrls", errors)
            if not set(authorship_source_ids).issubset(set(source_ids)):
                errors.append(f"{prefix}: authorshipEvidenceSourceIds must be included in sourceIds")
            if authorship_source_ids and not any(
                source_map.get(source_id, {}).get("type") == "publication"
                and source_map.get(source_id, {}).get("workId") == work_id
                for source_id in authorship_source_ids
            ):
                errors.append(
                    f"{prefix}: authorship evidence requires a publication source with the same workId"
                )
            for source_url in source_urls:
                if not is_http_url(source_url):
                    errors.append(f"{prefix}: sourceUrls entries must be absolute http(s) URLs")
            unknown_source_ids = sorted(set(source_ids) - source_ids_known)
            if unknown_source_ids:
                errors.append(f"{prefix}: unknown sourceIds {unknown_source_ids}")
            has_matching_publication_source = False
            for source_id in source_ids:
                source = source_map.get(source_id, {})
                if candidate_id not in as_list(source.get("subjectIds")):
                    errors.append(f"{prefix}: source {source_id} is not candidate-bound to {candidate_id}")
                if source.get("type") == "publication" and source.get("workId") == work_id:
                    has_matching_publication_source = True
            if source_ids and not has_matching_publication_source:
                errors.append(f"{prefix}: requires a publication source with the same workId")
            known_urls = {
                str(source_map.get(source_id, {}).get("url", "")).strip()
                for source_id in source_ids
                if str(source_map.get(source_id, {}).get("url", "")).strip()
            }
            if source_urls and not set(source_urls).issubset(known_urls):
                errors.append(f"{prefix}: sourceUrls must match the referenced sources.json records")
            if role in CANDIDATE_LED_ROLES and publication_date and audit_as_of:
                if publication_date >= subtract_years(audit_as_of, 5):
                    five_year_candidate_led += 1

        reconciliation_counts = candidate.get("searchReconciliation")
        if not isinstance(reconciliation_counts, dict):
            errors.append(f"{label}: searchReconciliation must be an object")
        else:
            raw_results = sum(
                int(entry.get("resultCount", 0))
                for entry in active_ledger
                if isinstance(entry, dict) and isinstance(entry.get("resultCount"), int)
            )
            included_count = len(included)
            excluded_count = sum(
                1 for paper in papers if isinstance(paper, dict) and paper.get("inclusionDecision") == "excluded"
            )
            unique_works = len([paper for paper in papers if isinstance(paper, dict)])
            expected_reconciliation = {
                "rawResults": raw_results,
                "uniqueWorks": unique_works,
                "includedWorks": included_count,
                "excludedWorks": excluded_count,
            }
            for field, expected in expected_reconciliation.items():
                if reconciliation_counts.get(field) != expected:
                    errors.append(f"{label}: searchReconciliation.{field} must equal {expected}")
            duplicate_records = reconciliation_counts.get("duplicateRecords")
            if not isinstance(duplicate_records, int) or duplicate_records < 0:
                errors.append(f"{label}: searchReconciliation.duplicateRecords must be a non-negative integer")
            elif raw_results - duplicate_records != unique_works:
                errors.append(
                    f"{label}: rawResults - duplicateRecords must equal uniqueWorks ({raw_results} - {duplicate_records} != {unique_works})"
                )
            if included_count + excluded_count != unique_works:
                errors.append(f"{label}: includedWorks + excludedWorks must equal uniqueWorks")

        if five_year_candidate_led < 5:
            if window_years != 8:
                errors.append(f"{label}: fewer than five five-year candidate-led papers requires an eight-year window")
            if extension_reason != "fewer_than_five_candidate_led_in_base_5y":
                errors.append(f"{label}: eight-year extension requires extensionReason=fewer_than_five_candidate_led_in_base_5y")
        else:
            if window_years != 5:
                errors.append(f"{label}: at least five five-year candidate-led papers requires the five-year active window")
            if extension_reason is not None:
                errors.append(f"{label}: five-year active window requires extensionReason=null")

        portfolio_counts = candidate.get("portfolioCounts")
        if not isinstance(portfolio_counts, dict):
            errors.append(f"{label}: portfolioCounts must be an object")
        else:
            expected_counts = {
                "eligible": len(included),
                "candidateLed": sum(1 for paper in included if paper.get("authorRole") in CANDIDATE_LED_ROLES),
                "strongRole": sum(1 for paper in included if paper.get("authorRole") in STRONG_ROLES),
            }
            for field, expected in expected_counts.items():
                if portfolio_counts.get(field) != expected:
                    errors.append(f"{label}: portfolioCounts.{field} must equal {expected}")

        conflicts = candidate.get("conflicts")
        if not isinstance(conflicts, list):
            errors.append(f"{label}: conflicts must be a list")
            conflicts = []
        for conflict_index, conflict in enumerate(conflicts):
            prefix = f"{label} conflicts[{conflict_index}]"
            if not isinstance(conflict, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if not nonempty(conflict.get("type")) or not nonempty(conflict.get("summary")):
                errors.append(f"{prefix}: type and summary are required")
            if not isinstance(conflict.get("material"), bool) or not isinstance(conflict.get("resolved"), bool):
                errors.append(f"{prefix}: material and resolved must be boolean")
            if conflict.get("impact") not in {"NONBLOCKING_PROVISIONAL", "BLOCKS_GRADE"}:
                errors.append(f"{prefix}: impact must be NONBLOCKING_PROVISIONAL or BLOCKS_GRADE")
            if conflict.get("resolved") is not True and conflict.get("impact") == "BLOCKS_GRADE":
                blocking_unresolved = True
            if conflict.get("resolved") is not True and conflict.get("impact") == "NONBLOCKING_PROVISIONAL":
                nonblocking_unresolved = True
        material_unresolved = paper_material_unresolved or any(conflict_is_material_unresolved(item) for item in conflicts)

        crosscheck = candidate.get("currentProgramCrossCheck")
        if not isinstance(crosscheck, dict):
            errors.append(f"{label}: currentProgramCrossCheck must be an object")
            crosscheck = {}
        crosscheck_status = crosscheck.get("status")
        if crosscheck_status not in {"M4_CURRENT_PROGRAM_CROSSCHECK", "not_completed"}:
            errors.append(f"{label}: invalid currentProgramCrossCheck.status")
        crosscheck_result = crosscheck.get("result")
        if crosscheck_result not in {"consistent", "mixed", "conflicting", "not_assessed"}:
            errors.append(f"{label}: invalid currentProgramCrossCheck.result")
        if crosscheck_status == "M4_CURRENT_PROGRAM_CROSSCHECK" and crosscheck_result == "not_assessed":
            errors.append(f"{label}: completed M4 cross-check requires an assessed result")
        if crosscheck_status == "not_completed" and crosscheck_result != "not_assessed":
            errors.append(f"{label}: not_completed cross-check requires result=not_assessed")
        if crosscheck_status == "M4_CURRENT_PROGRAM_CROSSCHECK":
            m4_count += 1
            crosscheck_source_ids = string_list(
                crosscheck.get("sourceIds"),
                f"{label}: currentProgramCrossCheck.sourceIds",
                errors,
                required=True,
            )
            unknown_crosscheck_ids = sorted(set(crosscheck_source_ids) - source_ids_known)
            if unknown_crosscheck_ids:
                errors.append(f"{label}: currentProgramCrossCheck has unknown sourceIds {unknown_crosscheck_ids}")
            for source_id in crosscheck_source_ids:
                source = source_map.get(source_id, {})
                if candidate_id not in as_list(source.get("subjectIds")):
                    errors.append(f"{label}: M4 source {source_id} is not candidate-bound")
                if source.get("authorityClass") != "official_institution" or source.get("status") != "current":
                    errors.append(f"{label}: M4 source {source_id} must be a current official-institution source")
                if "research" not in as_list(source.get("claimDomains")):
                    errors.append(f"{label}: M4 source {source_id} must support the research claim domain")
            if not nonempty(crosscheck.get("summary")):
                errors.append(f"{label}: completed M4 cross-check requires summary")
        else:
            pending_crosscheck_ids = string_list(
                crosscheck.get("sourceIds"),
                f"{label}: currentProgramCrossCheck.sourceIds",
                errors,
            )
            unknown_pending_ids = sorted(set(pending_crosscheck_ids) - source_ids_known)
            if unknown_pending_ids:
                errors.append(f"{label}: currentProgramCrossCheck has unknown sourceIds {unknown_pending_ids}")
        m4_consistent = crosscheck_status == "M4_CURRENT_PROGRAM_CROSSCHECK" and crosscheck_result == "consistent"
        expected_portfolio_codes = derive_portfolio_codes(included, status)
        baseline_trigger_scores = derive_score_components(included, audit_as_of, m4_consistent, material_unresolved)
        expected_score_triggers: list[bool] = []
        expected_portfolio_triggers: list[bool] = []
        for included_index in range(len(included)):
            reduced = included[:included_index] + included[included_index + 1 :]
            reduced_scores = derive_score_components(reduced, audit_as_of, m4_consistent, material_unresolved)
            expected_score_triggers.append(
                any(
                    baseline_trigger_scores[field] != reduced_scores[field]
                    for field in ("methodIntegration", "clinicalTranslation", "researchOwnership", "recentContinuity")
                )
            )
            expected_portfolio_triggers.append(
                derive_portfolio_codes(reduced, status) != expected_portfolio_codes
            )

        grade = candidate.get("grade")
        scores = candidate.get("scores")
        if status in {"confirmed", "provisional"}:
            if not included:
                errors.append(f"{label}: {status} status requires at least one usable included paper")
            if len(included) in {1, 2} and status != "provisional":
                errors.append(f"{label}: one or two usable papers permit only provisional status")
            if len(included) in {1, 2} and candidate.get("confidence") != "low":
                errors.append(f"{label}: one or two usable papers require low confidence")
            expected_grade_set = GRADES if status == "confirmed" else PROVISIONAL_GRADES
            if grade not in expected_grade_set:
                errors.append(f"{label}: {status} status has incompatible grade {grade!r}")
            if not isinstance(scores, dict):
                errors.append(f"{label}: {status} status requires scores")
                scores = {}
            component_total = 0
            for field, bounds in SCORE_LIMITS.items():
                value = scores.get(field)
                if not isinstance(value, int) or not bounds[0] <= value <= bounds[1]:
                    errors.append(f"{label}: scores.{field} must be an integer in {bounds}")
                elif value not in SCORE_VALUES[field]:
                    errors.append(f"{label}: scores.{field} must use a defined threshold value {sorted(SCORE_VALUES[field])}")
                else:
                    component_total += value
            if scores.get("total") != component_total:
                errors.append(f"{label}: scores.total must equal component sum {component_total}")
            normalized_grade = str(grade)[1:] if grade in PROVISIONAL_GRADES else grade
            grade_adjustment = candidate.get("gradeAdjustment")
            if not isinstance(grade_adjustment, dict):
                errors.append(f"{label}: confirmed/provisional status requires gradeAdjustment")
                grade_adjustment = {}
            total_value = scores.get("total")
            if isinstance(total_value, int):
                score_band = next(
                    (band for band, (low, high) in GRADE_BANDS.items() if low <= total_value <= high),
                    None,
                )
                method_score = scores.get("methodIntegration")
                m3_translation = [
                    paper
                    for paper in included
                    if paper.get("authorRole") in STRONG_ROLES
                    and paper.get("reviewDepth") == "M3_FULL_TEXT_DESIGN"
                    and paper.get("translationCode") in {"TR2", "TR3"}
                ]
                m3_tr3 = [paper for paper in m3_translation if paper.get("translationCode") == "TR3"]
                mtg1_floor_met = (
                    isinstance(method_score, int)
                    and method_score >= 22
                    and len(m3_tr3) >= 1
                    and len(m3_translation) >= 2
                )
                cap_required = score_band == "MTG1" and not mtg1_floor_met
                expected_grade = "MTG2" if cap_required else score_band
                if normalized_grade != expected_grade:
                    errors.append(
                        f"{label}: grade {grade} conflicts with score band/floor; expected "
                        f"{'p' if status == 'provisional' else ''}{expected_grade}"
                    )
                if cap_required:
                    if not (
                        grade_adjustment.get("applied") is True
                        and grade_adjustment.get("from") == "MTG1"
                        and grade_adjustment.get("to") == "MTG2"
                        and nonempty(grade_adjustment.get("reason"))
                    ):
                        errors.append(f"{label}: MTG1-floor cap requires a documented MTG1-to-MTG2 gradeAdjustment")
                elif grade_adjustment.get("applied") is not False:
                    errors.append(f"{label}: gradeAdjustment.applied must be false when no cap is required")
            score_basis = candidate.get("scoreBasis")
            if not isinstance(score_basis, dict):
                errors.append(f"{label}: confirmed/provisional status requires scoreBasis")
            else:
                for field in SCORE_LIMITS:
                    if not nonempty(score_basis.get(field)):
                        errors.append(f"{label}: scoreBasis.{field} is required")

            expected_components = derive_score_components(
                included, audit_as_of, m4_consistent, material_unresolved
            )
            for field, expected in expected_components.items():
                if scores.get(field) != expected:
                    errors.append(f"{label}: scores.{field} must equal uniquely derived value {expected}")
        elif status == "ungraded":
            if grade != "MTG-U":
                errors.append(f"{label}: ungraded status requires MTG-U")
            if scores is not None and scores != {}:
                errors.append(f"{label}: ungraded status must not carry scores")
            if candidate.get("confidence") != "low":
                errors.append(f"{label}: ungraded status requires low confidence")
            if included:
                errors.append(f"{label}: MTG-U is invalid when usable included papers exist")
            if window_years != 8:
                errors.append(f"{label}: MTG-U requires a completed eight-year window")
            if any_truncated:
                errors.append(f"{label}: MTG-U is invalid with a truncated search")
            if search_status != "bounded_complete":
                errors.append(f"{label}: MTG-U requires searchStatus=bounded_complete")
        elif status == "incomplete":
            if grade is not None:
                errors.append(f"{label}: incomplete status requires JSON null grade")
            if scores is not None and scores != {}:
                errors.append(f"{label}: incomplete status must not carry scores")
            if candidate.get("confidence") != "low":
                errors.append(f"{label}: incomplete status requires low confidence")
            if not blocking_unresolved:
                errors.append(f"{label}: incomplete status requires an unresolved BLOCKS_GRADE conflict")
            if not retry_present:
                errors.append(f"{label}: incomplete status requires documented retryNotes")

        if blocking_unresolved and status != "incomplete":
            errors.append(f"{label}: unresolved BLOCKS_GRADE conflict forces scientificAuditStatus=incomplete")
        if nonblocking_unresolved and status == "confirmed":
            errors.append(f"{label}: unresolved NONBLOCKING_PROVISIONAL conflict cannot coexist with confirmed status")

        if status == "confirmed":
            if not any(paper.get("authorRole") in STRONG_ROLES for paper in included):
                errors.append(f"{label}: confirmed status requires at least one strong-role paper")
            if baseline_trigger_scores.get("evidenceCompleteness", 0) < 7:
                errors.append(
                    f"{label}: confirmed status requires derived evidenceCompleteness of at least 7"
                )
            if search_status != "bounded_complete":
                errors.append(f"{label}: confirmed status requires searchStatus=bounded_complete")
            if not m4_consistent:
                errors.append(f"{label}: confirmed status requires M4 current-programme cross-check with result=consistent")
            if material_unresolved:
                errors.append(f"{label}: confirmed status is invalid with material unresolved conflicts")
            for paper_index, paper in enumerate(included):
                role = paper.get("authorRole")
                depth = paper.get("reviewDepth")
                if role in STRONG_ROLES and depth not in {"M2_HUMAN_ABSTRACT", "M3_FULL_TEXT_DESIGN"}:
                    errors.append(f"{label} papers[{paper_index}]: confirmed strong-role paper requires at least M2")
                if (expected_score_triggers[paper_index] or expected_portfolio_triggers[paper_index]) and depth != "M3_FULL_TEXT_DESIGN":
                    errors.append(f"{label} papers[{paper_index}]: score/portfolio trigger requires M3")
            if isinstance(scores, dict) and scores.get("methodIntegration", 0) >= 16:
                for paper in included:
                    if (
                        paper.get("authorRole") in STRONG_ROLES
                        and paper.get("methodCode") in {"RM-E", "RM-B", "RM-EB"}
                        and paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN"
                    ):
                        errors.append(f"{label}: confirmed integration score requires contributing strong-role papers at M3")
                        break
            if isinstance(scores, dict) and scores.get("clinicalTranslation", 0) >= 14:
                for paper in included:
                    if (
                        paper.get("authorRole") in STRONG_ROLES
                        and paper.get("translationCode") in {"TR2", "TR3"}
                        and paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN"
                    ):
                        errors.append(f"{label}: confirmed clinical-translation score requires contributing TR2/TR3 papers at M3")
                        break

        portfolio_codes = candidate.get("portfolioCodes")
        if not isinstance(portfolio_codes, list):
            errors.append(f"{label}: portfolioCodes must be a list")
            portfolio_codes = []
        unknown_codes = sorted(set(str(x) for x in portfolio_codes) - PORTFOLIO_CODES)
        if unknown_codes:
            errors.append(f"{label}: unknown portfolioCodes {unknown_codes}")
        if any(not isinstance(code, str) for code in portfolio_codes):
            errors.append(f"{label}: portfolioCodes must contain only strings")
        if len(portfolio_codes) != len(set(str(code) for code in portfolio_codes)):
            errors.append(f"{label}: portfolioCodes must not contain duplicates")
        declared_portfolio_codes = {code for code in portfolio_codes if isinstance(code, str)}
        if declared_portfolio_codes != expected_portfolio_codes:
            errors.append(
                f"{label}: portfolioCodes must equal derived codes {sorted(expected_portfolio_codes)}"
            )
        for paper_index, paper in enumerate(included):
            if paper.get("scoreTrigger") != expected_score_triggers[paper_index]:
                errors.append(
                    f"{label} included paper[{paper_index}]: scoreTrigger must equal derived value "
                    f"{expected_score_triggers[paper_index]}"
                )
            if paper.get("portfolioTrigger") != expected_portfolio_triggers[paper_index]:
                errors.append(
                    f"{label} included paper[{paper_index}]: portfolioTrigger must equal derived value "
                    f"{expected_portfolio_triggers[paper_index]}"
                )
        strong_papers = [paper for paper in included if paper.get("authorRole") in STRONG_ROLES]
        strong_rm_eb = [paper for paper in strong_papers if paper.get("methodCode") == "RM-EB"]
        strong_rm_e = [paper for paper in strong_papers if paper.get("methodCode") == "RM-E"]
        strong_rm_b = [paper for paper in strong_papers if paper.get("methodCode") == "RM-B"]
        strong_trans = [paper for paper in strong_papers if paper.get("translationCode") in {"TR2", "TR3"}]
        if "RP-EB-INTRA" in portfolio_codes:
            minimum = 2 if status == "confirmed" else 1
            if len(strong_rm_eb) < minimum:
                errors.append(f"{label}: RP-EB-INTRA requires at least {minimum} strong-role RM-EB paper(s)")
            if status == "confirmed" and any(paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN" for paper in strong_rm_eb):
                errors.append(f"{label}: confirmed RP-EB-INTRA requires its strong-role RM-EB papers at M3")
        if "RP-EB-SPLIT" in portfolio_codes:
            minimum = 2 if status == "confirmed" else 1
            if len(strong_rm_e) < minimum or len(strong_rm_b) < minimum:
                errors.append(f"{label}: RP-EB-SPLIT requires at least {minimum} strong-role RM-E and RM-B paper(s) each")
            if status == "confirmed" and any(
                paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN" for paper in strong_rm_e + strong_rm_b
            ):
                errors.append(f"{label}: confirmed RP-EB-SPLIT requires contributing papers at M3")
        if "RP-TRANS" in portfolio_codes:
            minimum = 2 if status == "confirmed" else 1
            if len(strong_trans) < minimum:
                errors.append(f"{label}: RP-TRANS requires at least {minimum} strong-role TR2/TR3 paper(s)")
            if status == "confirmed" and any(paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN" for paper in strong_trans):
                errors.append(f"{label}: confirmed RP-TRANS requires contributing papers at M3")
        pure_map = {
            "RP-E-PURE": "RM-E",
            "RP-B-PURE": "RM-B",
            "RP-M-PURE": "RM-M",
            "RP-C-PURE": "RM-C",
        }
        for code, method_code in pure_map.items():
            if code in portfolio_codes:
                if len(strong_papers) < 5 or any(paper.get("methodCode") != method_code for paper in strong_papers):
                    errors.append(f"{label}: {code} requires at least five strong-role papers all coded {method_code}")
                if code == "RP-C-PURE" and any(paper.get("translationCode") != "CLIN_ONLY" for paper in strong_papers):
                    errors.append(f"{label}: RP-C-PURE requires every strong-role paper to be CLIN_ONLY")
                if code == "RP-C-PURE" and any(
                    paper.get("translationCode") in {"TR2", "TR3"} for paper in included
                ):
                    errors.append(f"{label}: RP-C-PURE is invalid when any stable eligible TR2/TR3 line is present")
                if status == "confirmed" and any(
                    paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN" for paper in strong_papers
                ):
                    errors.append(f"{label}: confirmed {code} requires every strong-role paper at M3")

        dominance = candidate.get("dominance")
        if not isinstance(dominance, dict):
            errors.append(f"{label}: dominance must be an object")
        else:
            method_code = dominance.get("methodCode")
            if method_code is not None and method_code not in METHOD_CODES:
                errors.append(f"{label}: dominance.methodCode is invalid")
            expected_denominator = sum(ROLE_WEIGHTS.get(str(paper.get("authorRole")), 0) for paper in included)
            expected_numerator = sum(
                ROLE_WEIGHTS.get(str(paper.get("authorRole")), 0)
                for paper in included
                if paper.get("methodCode") == method_code
            )
            ratio = expected_numerator / expected_denominator if expected_denominator else 0.0
            for field, expected in (
                ("weightedNumerator", expected_numerator),
                ("weightedDenominator", expected_denominator),
                ("ratio", ratio),
            ):
                value = dominance.get(field)
                if not isinstance(value, (int, float)) or abs(float(value) - expected) > 0.011:
                    errors.append(f"{label}: dominance.{field} does not match role-weighted papers")
            if "RP-C-DOMINANT" in portfolio_codes and not (method_code == "RM-C" and 0.70 <= ratio < 1.0):
                errors.append(f"{label}: RP-C-DOMINANT requires RM-C ratio from 0.70 to below 1.0")
            if status == "confirmed" and "RP-C-DOMINANT" in portfolio_codes and any(
                paper.get("reviewDepth") != "M3_FULL_TEXT_DESIGN" for paper in included
            ):
                errors.append(f"{label}: confirmed RP-C-DOMINANT requires every denominator paper at M3")

        normalized_grade = str(grade)[1:] if grade in PROVISIONAL_GRADES else grade
        if normalized_grade == "MTG1":
            method_score = scores.get("methodIntegration") if isinstance(scores, dict) else None
            m3_tr = [
                paper
                for paper in included
                if paper.get("authorRole") in STRONG_ROLES
                and paper.get("reviewDepth") == "M3_FULL_TEXT_DESIGN"
                and paper.get("translationCode") in {"TR2", "TR3"}
            ]
            m3_tr3 = [paper for paper in m3_tr if paper.get("translationCode") == "TR3"]
            if not isinstance(method_score, int) or method_score < 22 or len(m3_tr3) < 1 or len(m3_tr) < 2:
                errors.append(
                    f"{label}: MTG1 requires methodIntegration>=22, one M3 strong-role TR3, and a second M3 strong-role TR2/TR3"
                )

    if strict:
        index_path = case_dir / "00-INDEX.md"
        if not report_path.is_file():
            errors.append(f"missing rendered audit report: {report_path}")
        else:
            report_text = report_path.read_text(encoding="utf-8-sig")
            audit_hash = hashlib.sha256(audit_path.read_bytes()).hexdigest()
            if audit_hash not in report_text:
                errors.append("rendered audit report is stale or lacks the current JSON SHA-256")
            if report_path.stat().st_mtime + 1e-6 < audit_path.stat().st_mtime:
                errors.append("rendered audit report is older than research-method-audit.json")
            for candidate_id in sorted(retained_set):
                if candidate_id not in report_text:
                    errors.append(f"rendered audit report omits candidate id {candidate_id}")
            required_report_fragments = [
                f"保留的 A/B/C 导师：{len(retained_set)} 人",
                f"纳入论文：{eligible_paper_count} 篇",
                "## 联系暂停控制",
            ]
            if retained_set:
                required_report_fragments.extend(["MTG 评分：", "评分依据：", "检索台账："])
            for fragment in required_report_fragments:
                if fragment not in report_text:
                    errors.append(f"rendered audit report lacks required fragment: {fragment}")
        if not index_path.is_file():
            errors.append(f"missing base index for method-audit navigation: {index_path}")
        else:
            index_text = index_path.read_text(encoding="utf-8-sig")
            if "[08-RESEARCH-METHOD-TRANSLATION-AUDIT.md](08-RESEARCH-METHOD-TRANSLATION-AUDIT.md)" not in index_text:
                errors.append("00-INDEX.md does not link the method/translation audit report")

    return {
        "status": "valid" if not errors else "invalid",
        "strict": strict,
        "caseDir": str(case_dir),
        "schemaVersion": audit.get("schemaVersion"),
        "retainedAbcCandidates": len(retained_set),
        "statusCounts": {key: status_counts.get(key, 0) for key in sorted(STATUSES)},
        "eligiblePapers": eligible_paper_count,
        "paperDepthCounts": {key: depth_counts.get(key, 0) for key in sorted(REVIEW_DEPTHS)},
        "m4Portfolios": m4_count,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    payload = validation_payload(args.case_dir.resolve(), args.strict)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
