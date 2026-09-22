#!/usr/bin/env python3
"""Validate a supervisor-research case before delivery."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from case_utils import (
    CHECK_STATUSES,
    CLAIM_DOMAINS,
    CONFLICT_CATEGORIES,
    COVERAGE_AREAS,
    DEADLINE_TYPES,
    DISCOVERY_PASS_TYPES,
    DIRECT_RESEARCH_SOURCE_TYPES,
    OPPORTUNITY_SCOPES,
    OPPORTUNITY_STATUSES,
    SOURCE_AUTHORITY_CLASSES,
    SOURCE_MEDIA,
    SOURCE_TYPES,
    canonical_url,
    evidence_work_key,
    evidence_stats,
    evidence_stats_line,
    load_json,
    visible_char_count,
)


OUTPUT_FILES = [
    "00-INDEX.md",
    "01-SCHOOL-SCOPE.md",
    "02-SUPERVISOR-TABLE.md",
    "03-COVERAGE-MATRIX.md",
    "04-EVIDENCE-CONFLICTS.md",
    "05-A-TIER-DEEP-PROFILES.md",
    "06-APPLICATION-READINESS.md",
    "07-SOURCE-LEDGER.md",
]
DATA_FILES = [
    "case.json",
    "schools.json",
    "coverage.json",
    "records.json",
    "sources.json",
]
QS_STATUSES = {
    "ranked",
    "rank_band",
    "specialist_not_in_overall",
    "not_ranked",
    "not_verified",
}
MEDICAL_STATUSES = {
    "medical_faculty_present",
    "medical_program_without_medical_faculty",
    "health_sciences_without_medical_degree",
    "specialist_medical_institution",
    "no_medical_faculty",
    "unclear",
}
COVERAGE_STATUSES = {
    "pending",
    "searched",
    "candidates_found",
    "not_present",
    "blocked_unverified",
}
CONTACT_TYPES = {
    "personal_email",
    "clinical_email",
    "group_email",
    "unit_email",
    "department_mailbox",
    "secretariat_email",
    "assistant_contact",
    "phone",
    "contact_form",
    "not_public",
}
CONTACT_STATUSES = {"published_current", "published_historical", "not_public", "unclear"}
TOPIC_CODES = {"T1", "T2", "T3", "T4"}
SUPERVISION_CODES = {"S1", "S2", "S3", "S4"}
SUPERVISION_BASIS_TYPES = {
    "person_eligibility_explicit",
    "current_doctoral_trainees",
    "programme_pi_or_host",
    "documented_thesis_supervision",
    "named_current_supervision",
    "named_supervisor_in_doctoral_posting",
    "co_supervision_only",
    "unverified",
}
PERSON_ROLE_TYPES = {
    "subject_profile",
    "group_leader",
    "independent_faculty",
    "unit_head",
    "principal_investigator",
    "co_principal_investigator",
    "co_investigator",
    "principal_applicant",
    "co_applicant",
    "grant_applicant",
    "grant_recipient",
    "trial_responsible_investigator",
    "sub_investigator",
    "collaborator",
    "team_member",
    "senior_or_corresponding_author",
    "first_author",
    "coauthor",
    "mentioned_without_role",
    "named_investigator",
    "programme_host",
    "eligible_supervisor",
    "doctoral_supervisor",
    "co_supervisor",
}
INDEPENDENT_RESEARCH_ROLE_TYPES = {
    "group_leader",
    "independent_faculty",
    "unit_head",
    "principal_investigator",
    "co_principal_investigator",
    "senior_or_corresponding_author",
}
CURRENT_INDEPENDENT_ROLE_TYPES = {
    "group_leader",
    "independent_faculty",
    "unit_head",
    "principal_investigator",
    "co_principal_investigator",
}
CURRENT_CONTACTABLE_ROLE_TYPES = CURRENT_INDEPENDENT_ROLE_TYPES | {
    "subject_profile",
    "eligible_supervisor",
    "doctoral_supervisor",
    "co_supervisor",
}
ROLE_LABEL_PLACEHOLDER_FRAGMENTS = {
    "role described on page or linked group member",
    "named profile/group member",
    "laboratory head or named investigator",
    "anchor attribution is described in the linked source",
    "contact record",
    "named subject on ",
    "candidate-associated official research url",
    "no person-specific research role is retained",
    "candidate-bound official profile/contact url",
    "no source-specific role label",
}
LOCATION_RELATIONSHIP_TYPES = {
    "country_exact",
    "subnational_within_country",
    "multi_jurisdiction_region",
}
TOPIC_EVIDENCE_SOURCE_TYPES = DIRECT_RESEARCH_SOURCE_TYPES | {
    "doctoral_rule_supervision",
    "official_role_contact",
}
CONFIDENCE_LEVELS = {"high", "medium", "low", "unverified", "not_applicable"}
CLAIM_CONFIDENCE_FIELDS = {"currentRole", "contact", "research", "supervision", "recruitment"}
MATERIAL_CLAIM_DOMAINS = {
    "group": {"current_role", "research"},
    "academicRole": {"current_role"},
    "adminClinicalRole": {"current_role"},
    "focus": {"research"},
    "phdTypes": {"doctoral_rule", "admissions_funding"},
    "doctoralRoute": {"doctoral_rule", "admissions_funding"},
    "directionOverviewZh": {"research"},
    "structuredProfileZh": {"research"},
    "scientificQuestions": {"research"},
    "materialsModels": {"research"},
    "methods": {"research"},
    "validationMaturity": {"research"},
    "roleBoundary": {"research", "current_role", "doctoral_supervision"},
}
MATERIAL_CLAIM_FIELDS = set(MATERIAL_CLAIM_DOMAINS)
ROLE_FIELD_ALLOWED_PERSON_ROLE_TYPES = {
    # These fields describe a current organisational or appointment role.  A
    # publication, grant, trial, collaboration or doctoral-supervision role is
    # not interchangeable with an academic title or unit/lab leadership role.
    "group": {
        "group_leader", "principal_investigator", "co_principal_investigator",
    },
    "academicRole": {
        "subject_profile", "named_investigator", "independent_faculty", "unit_head",
        "group_leader", "principal_investigator", "co_principal_investigator",
    },
    "adminClinicalRole": {
        "subject_profile", "named_investigator", "independent_faculty", "unit_head",
        "group_leader", "principal_investigator", "co_principal_investigator",
        "programme_host",
    },
}
ACADEMIC_ROLE_LABEL_RE = re.compile(
    r"\b(?:prof(?:essor)?|associate professor|assistant professor|full professor|ordinaria|"
    r"privatdozent|pd|lecturer|senior lecturer|ma[iî]tre|merc?|ph\.?d\.?|m\.?d\.?|dr\.?)\b",
    flags=re.I,
)
ADMIN_ROLE_LABEL_RE = re.compile(
    r"\b(?:head|co-head|director|co-director|chief|chair|vice|deputy|coordinator|"
    r"physician|attending|consultant|principal investigator|project leader|group leader|"
    r"leit(?:er|erin)|leitender arzt|fachbereichsleiter|chef de groupe|co-chef|m[ée]decin|"
    r"responsable)\b|负责人|主任|组长",
    flags=re.I,
)
NON_SPECIFIC_ROLE_EVIDENCE_FRAGMENTS = {
    "specific title not retained or inferred",
    "specific title is not retained or inferred",
    "no source-specific role label",
    "no person-specific role",
}
AFFILIATED_RELATIONSHIP_TYPES = {
    "owned_university_hospital",
    "affiliated_teaching_hospital",
    "formal_clinical_partner",
    "cross_institutional_research_network",
    "multi_institutional_cancer_centre",
}
TIERS = {"A", "B", "C", "D"}
SOURCE_TOPIC_RELEVANCE = {"direct", "adjacent", "background", "not_applicable"}
SOURCE_STATUSES = {"current", "future", "historical", "closed", "unclear"}
EXPLICIT_MISSING_MARKERS = {
    "not_public",
    "not_found_publicly",
    "not_applicable",
    "unverified",
    "未公开",
    "未找到公开信息",
    "未确认",
    "不适用",
}
OFFICIAL_SOURCE_AUTHORITIES = {
    "official_ranking_publisher",
    "official_institution",
    "official_funder_registry",
    "official_trial_registry",
    "official_government_regulator",
}

# These hosts identify the publisher/registry itself rather than a university,
# hospital, or research institute. Keep this list intentionally narrow: it is
# a guard against relabelling an obvious publication, registry, funder, or
# ranking page as an institutional profile in order to satisfy current-role or
# contact checks.
HOST_AUTHORITY_CLASS_RULES = {
    "pubmed.ncbi.nlm.nih.gov": "primary_publication",
    "pmc.ncbi.nlm.nih.gov": "primary_publication",
    "europepmc.org": "primary_publication",
    "doi.org": "primary_publication",
    "clinicaltrials.gov": "official_trial_registry",
    "snf.ch": "official_funder_registry",
    "topuniversities.com": "official_ranking_publisher",
    "qs.com": "official_ranking_publisher",
}

CORRESPONDENCE_PATTERNS = [
    re.compile(r"(?im)^\s*subject\s*[:：]"),
    re.compile(
        r"(?im)^\s*(?:dear\s+(?:professor|prof\.?|dr\.?|doctor)\b|"
        r"尊敬的[^\r\n，,:：]{0,30}(?:教授|老师|博士)\s*[,，:：]?)"
    ),
    re.compile(
        r"(?im)^\s*(?:sincerely|best regards|kind regards|yours sincerely|"
        r"yours faithfully|此致|敬礼)\s*[,，]?\s*$"
    ),
    re.compile(
        r"(?i)\b(?:i am writing to|i'm writing to|my name is|"
        r"please find (?:my )?(?:cv|resume) attached|"
        r"i would (?:like|wish) to apply|i am applying for)\b"
    ),
    re.compile(r"(?:我写信是为了|谨致函|本人(?:叫|是)|我叫|随信附上(?:我的)?(?:简历|CV)|申请加入您(?:的|所在)|希望加入您的?课题组)"),
]

DIRECT_TOPIC_NEGATION_PATTERNS = [
    re.compile(
        r"(?i)\b(?:not|non[-\s]+)(?:\s+(?:a|an|the))?\s*"
        r"(?:personal\s+)?(?:lung|thoracic|nsclc|sclc)"
        r"(?:[-\s]+(?:cancer|tumou?r|oncology|focus|line|topic))?\b"
    ),
    re.compile(
        r"(?i)\b(?:lung|thoracic|nsclc|sclc)\b[^.;]{0,30}"
        r"\b(?:is|are)\s+not\b[^.;]{0,20}\b(?:focus|line|topic|research)\b"
    ),
    re.compile(
        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学|NSCLC|SCLC)"
        r"[^。；;]{0,20}(?:并非|不是|不属于)[^。；;]{0,16}(?:主线|方向|重点|课题|研究)"
    ),
    re.compile(
        r"(?:并非|不是|不属于)[^。；;]{0,12}"
        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学|NSCLC|SCLC)"
    ),
    # Do not confuse 非小细胞肺癌 (NSCLC) with a negated lung-cancer claim.
    re.compile(r"非(?!小细胞)(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学)"),
]

CANDIDATES_FOUND_NEGATION_PATTERNS = [
    re.compile(r"(?i)\b(?:otherwise\s+)?no\s+qualifying\b"),
    re.compile(r"(?i)\bno\s+(?:eligible\s+|matching\s+)?candidates?\b"),
    re.compile(r"(?:无人|未发现候选|没有候选|无符合|没有符合)"),
]

MIGRATED_GENERIC_TOPIC_CLAIM_PATTERNS = [
    re.compile(r"(?i)^\s*institutional research page retained for\b"),
    re.compile(r"(?i)^\s*(?:official|institutional)\s+(?:research\s+)?page\s+supporting\b"),
    re.compile(r"(?i)^\s*current or time-stamped institutional role, unit and published contact for\b"),
    re.compile(r"^\s*(?:官网|机构)(?:研究)?页面(?:仅)?(?:支持|保留用于)"),
]

GENERIC_PERSONAL_MAILBOX_PATTERNS = [
    re.compile(
        r"(?i)(?:^|[._-])(?:info|contact|office|admin|admissions?|graduate|phd|"
        r"secretar(?:y|iat)|sekretariat|sekret|sekr|assistant|assistenz|department|dept|"
        r"service|clinic|centre|center|team|group|lab)(?:$|[._-])"
    ),
    re.compile(
        r"(?i)(?:oncology|onkologie|radioonkologie|thoraxchirurgie|patho[-_.]?medgen|"
        r"exhalomics|centrecancer|cancercentre|cancercenter)"
    ),
]

EXPLICIT_CURRENT_TITLE_PATTERNS = [
    re.compile(
        r"(?i)\b(?:full|associate|assistant|tenure[- ]track) professor\b|"
        r"\bprofesseur(?:e)?\s+(?:ordinaire|associ[ée]e?|assistant(?:e)?)\b|"
        r"\b(?:principal investigator|group leader|lab(?:oratory)? head)\b|"
        r"\b(?:head|chair|chief|director)\b[^.;，。；]{0,45}"
        r"\b(?:department|division|service|centre|center|institute|unit|laboratory|lab|programme|program)\b|"
        r"\b(?:attending|consultant|staff) (?:physician|surgeon|oncologist|pathologist)\b"
    ),
    re.compile(
        r"(?:正教授|副教授|助理教授|长聘轨助理教授|首席研究员|课题组负责人|实验室负责人|"
        r"科主任|系主任|部门负责人|中心主任|研究所所长|院长|主任医师|主治医师)"
    ),
]

EXPLICIT_RESEARCH_STATEMENT_PATTERNS = [
    re.compile(
        r"(?i)\b(?:research(?:es|ing)?|research (?:focus|line|programme|program|project)|"
        r"project|study|studies|thesis|dissertation|laboratory|lab|collaboration)\b"
    ),
    re.compile(r"(?:研究方向|研究重点|研究项目|课题|实验室|论文题目|博士论文|学位论文|项目名称)"),
]


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a PhD-supervisor research case")
    parser.add_argument("--case-dir", required=True, help="Initialized case directory")
    parser.add_argument("--strict", action="store_true", help="Require delivery-ready data and outputs")
    return parser.parse_args()


def load_inputs(case_dir: Path, report: Report) -> dict[str, object]:
    values: dict[str, object] = {}
    data_dir = case_dir / "data"
    for filename in DATA_FILES:
        path = data_dir / filename
        if not path.exists():
            report.error(f"Missing data file: data/{filename}")
            continue
        try:
            values[filename] = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            report.error(f"Cannot parse data/{filename}: {exc}")
    return values


def require_list(name: str, value: object, report: Report) -> list[dict]:
    if not isinstance(value, list):
        report.error(f"{name} must contain an array")
        return []
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            report.error(f"{name}[{index}] must be an object")
            continue
        result.append(item)
    return result


def check_unique_ids(label: str, items: list[dict], report: Report) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for index, item in enumerate(items):
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            report.error(f"{label}[{index}] has no id")
        elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item_id):
            report.error(f"{label} id must be a lowercase ASCII slug: {item_id}")
        elif item_id in result:
            report.error(f"Duplicate {label} id: {item_id}")
        else:
            result[item_id] = item
    return result


def parse_iso_date(value: object) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def parse_partial_date(value: object) -> tuple[dt.date | None, str]:
    text = str(value or "").strip()
    if not text:
        return None, ""
    for pattern, suffix, precision in [
        (r"\d{4}-\d{2}-\d{2}", "", "day"),
        (r"\d{4}-\d{2}", "-01", "month"),
        (r"\d{4}", "-01-01", "year"),
    ]:
        if re.fullmatch(pattern, text):
            try:
                return dt.date.fromisoformat(text + suffix), precision
            except ValueError:
                return None, precision
    return None, "invalid"


def rank_upper_bound(value: object) -> int | None:
    numbers = [int(item) for item in re.findall(r"\d+", str(value or ""))]
    return max(numbers) if numbers else None


def parse_rank_interval(value: object, status: object) -> tuple[int, int] | None:
    """Parse a positive exact QS rank or a positive rank band."""
    text = str(value or "").strip().replace("–", "-").replace("—", "-")
    if status == "ranked":
        match = re.fullmatch(r"[#=]?\s*(\d+)", text)
        if not match:
            return None
        rank = int(match.group(1))
        return (rank, rank) if rank > 0 else None
    if status == "rank_band":
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", text)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low, high) if 0 < low <= high else None
        match = re.fullmatch(r"(\d+)\s*\+", text)
        if match and int(match.group(1)) > 0:
            low = int(match.group(1))
            return low, low
    return None


def person_role_for(source: dict, subject_id: str) -> dict | None:
    for item in source.get("personRoles", []):
        if isinstance(item, dict) and item.get("subjectId") == subject_id:
            return item
    return None


def is_explicit_missing(value: object) -> bool:
    text = str(value or "").strip().casefold()
    return any(
        text == marker.casefold()
        or text.startswith(marker.casefold() + ":")
        or text.startswith(marker.casefold() + "：")
        for marker in EXPLICIT_MISSING_MARKERS
    )


def person_role_is_specific(source: dict, subject_id: str) -> bool:
    role = person_role_for(source, subject_id) or {}
    label = str(role.get("exactLabel", "")).strip().casefold()
    return bool(label) and not any(fragment in label for fragment in NON_SPECIFIC_ROLE_EVIDENCE_FRAGMENTS)


def normalized_search_text(value: object) -> str:
    """Case-fold text while preserving CJK and removing Latin diacritics."""
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def role_label_subject_segments(exact_label: str) -> tuple[list[str], str]:
    """Return clauses attributable to the person named before the first colon.

    The exact-label convention is ``Person Name: source-faithful role``.  We
    match authorship only inside a clause that repeats that person (or inside
    the first post-colon clause), so a last-author statement about a second
    named person cannot leak to the subject.
    """
    normalized = normalized_search_text(exact_label)
    match = re.match(r"^\s*([^:：]{2,100})\s*[:：]\s*(.*)$", normalized, flags=re.S)
    if not match:
        return [normalized], normalized
    subject_name, body = match.groups()
    latin_tokens = re.findall(r"[a-z][a-z'-]+", subject_name)
    cjk_tokens = re.findall(r"[\u3400-\u9fff]{2,}", subject_name)
    aliases = {subject_name.strip(), *[item for item in latin_tokens if len(item) >= 4], *cjk_tokens}
    raw_segments = [item.strip() for item in re.split(r"[,，;；.。\n]+", body) if item.strip()]
    subject_segments: list[str] = []
    for index, segment in enumerate(raw_segments):
        if index == 0 or any(
            re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", segment)
            for alias in aliases
            if alias
        ):
            subject_segments.append(segment)
    return subject_segments, body


def authorship_role_label_conflict(role_type: str, exact_label: str) -> str:
    """Detect source-faithful, person-specific authorship contradictions."""
    if role_type not in {"senior_or_corresponding_author", "first_author", "coauthor"}:
        return ""
    subject_segments, body = role_label_subject_segments(exact_label)
    subject_text = "\n".join(subject_segments)
    first = bool(
        re.search(
            r"(?i)\b(?:co[- ]?)?first author\b|(?:并列|共同)?第一作者|首位作者",
            subject_text,
        )
    )
    senior = bool(
        re.search(
            r"(?i)\b(?:co[- ]?)?(?:senior|last|corresponding) author\b|"
            r"(?:共同)?(?:末位|资深|通讯)作者|末位(?:及|和|或)?通讯作者",
            subject_text,
        )
    )
    subordinate = bool(
        re.search(
            r"(?i)\b(?:co[- ]?author|middle author|second author|collaborating author)\b|"
            r"(?:共同|合作|中间位)作者|第二作者|第\s*\d+\s*(?:位)?作者|倒数第二作者",
            subject_text,
        )
    )
    senior_negated = bool(
        re.search(
            r"(?i)\b(?:not|was not|is not)\b[^.;，。；]{0,24}"
            r"\b(?:senior|last|corresponding) author\b|"
            r"(?:非|并非|不是|不属于)[^,，;；.。]{0,16}(?:末位|资深|通讯)(?:作者|主导)?",
            subject_text + "\n" + body,
        )
    )
    equal_senior = bool(
        re.search(
            r"(?i)\b(?:co[- ]?senior|joint senior|equal(?:ly)? contribut(?:ed|ion))\b|"
            r"(?:共同资深|共同末位|共同通讯|标注共同贡献|同等贡献)",
            body,
        )
    )
    if role_type == "senior_or_corresponding_author":
        if senior and not senior_negated:
            return ""
        if equal_senior and (subordinate or first):
            return ""
        if senior_negated:
            return "the subject is explicitly not a senior/last/corresponding author"
        if first:
            return "the subject is stated only as first author, while senior/corresponding authorship is not stated"
        if subordinate:
            return "the subject is stated only as a coauthor/second/middle author"
    elif role_type == "first_author":
        if first:
            return ""
        if senior or subordinate:
            return "the subject is not stated as first author"
    elif role_type == "coauthor" and (first or (senior and not senior_negated)):
        return "a more specific first/senior/corresponding authorship role is explicitly stated"
    return ""


def explicit_independent_faculty_label(exact_label: str) -> bool:
    subject_segments, _ = role_label_subject_segments(exact_label)
    text = "\n".join(subject_segments)
    return bool(
        re.search(
            r"(?i)\b(?:full|associate) professor\b|"
            r"\btenure[- ]track assistant professor\b|"
            r"\bprofesseur(?:e)?\s+(?:ordinaire|associ[ée]e?)\b|"
            r"(?:正教授|副教授|长聘轨助理教授)",
            text,
        )
    )


def explicit_unit_head_label(exact_label: str) -> bool:
    subject_segments, _ = role_label_subject_segments(exact_label)
    text = "\n".join(subject_segments)
    return bool(
        re.search(
            r"(?i)\b(?:head|chair|chief|director)\b[^.;，。；]{0,45}"
            r"\b(?:department|division|service|centre|center|institute|unit)\b|"
            r"\b(?:department|division|service|centre|center|institute|unit)\b"
            r"[^.;，。；]{0,24}\b(?:head|chair|chief|director)\b|"
            r"(?:科主任|系主任|部门负责人|中心主任|研究所所长|服务主任|院长)",
            text,
        )
    )


def person_role_label_conflict(role_type: str, exact_label: str) -> str:
    """Return a narrow reason when a label contradicts an independent role."""
    authorship_conflict = authorship_role_label_conflict(role_type, exact_label)
    if authorship_conflict:
        return authorship_conflict
    if role_type not in INDEPENDENT_RESEARCH_ROLE_TYPES:
        return ""
    if role_type == "independent_faculty":
        if explicit_independent_faculty_label(exact_label):
            return ""
        return (
            "independent_faculty requires an explicit full/associate professor or "
            "tenure-track assistant-professor title; PD/Privatdozent/attending alone is insufficient"
        )
    if role_type == "unit_head":
        if explicit_unit_head_label(exact_label):
            return ""
        return "unit_head requires an explicit department/division/service/centre/institute leadership title"
    text = exact_label.casefold()
    subordinate = bool(
        re.search(
            r"\b(?:co[- ]?applicant|co[- ]?investigator|sub[- ]?investigator|"
            r"co[- ]?author|coauthor|team member|project partner)\b|"
            r"共同申请人|共同研究者|共同作者|团队成员|项目合作方",
            text,
        )
    )
    if role_type in {"principal_investigator", "co_principal_investigator"}:
        explicitly_negated = bool(
            re.search(
                r"\b(?:not|isn't|is not|was not)\b[^.;，。；]{0,24}"
                r"\b(?:principal investigator|pi)\b|"
                r"(?:并非|不是|不能算作|不等同于)[^。；;]{0,20}(?:个人)?\s*PI\b",
                text,
                flags=re.I,
            )
        )
        positive = bool(
            re.search(
                r"\b(?:principal investigator|co[- ]?pi|pi)\b|"
                r"(?:项目|课题|研究)(?:共同)?负责人|首席研究(?:员|者)|共同PI",
                exact_label,
                flags=re.I,
            )
        )
    elif role_type == "group_leader":
        explicitly_negated = bool(
            re.search(
                r"\b(?:not|isn't|is not|was not)\b[^.;，。；]{0,28}"
                r"\b(?:group leader|lab(?:oratory)? head)\b|"
                r"(?:并非|不是|不能算作|不等同于)[^。；;]{0,20}"
                r"(?:课题组长|实验室负责人|研究组负责人)",
                text,
                flags=re.I,
            )
        )
        positive = bool(
            re.search(
                r"\b(?:group leader|lab(?:oratory)? head|head of [^.;，。；]{0,32}"
                r"(?:group|lab(?:oratory)?))\b|课题组长|实验室负责人|研究组负责人",
                exact_label,
                flags=re.I,
            )
        )
    else:
        explicitly_negated = bool(
            re.search(
                r"\b(?:not|isn't|is not|was not)\b[^.;，。；]{0,24}"
                r"\b(?:senior|last|corresponding) author\b|"
                r"(?:非|并非|不是|不能算作|不等同于)\s*"
                r"(?:(?:主要|末位|资深|通讯|最后)\s*)?"
                r"(?:[/、或和]\s*(?:主要|末位|资深|通讯|最后)\s*)*作者",
                text,
                flags=re.I,
            )
        )
        positive = bool(
            re.search(
                r"\b(?:co[- ]?)?(?:senior|last|corresponding) author\b|"
                r"(?:共同)?(?:末位|资深|通讯)作者",
                exact_label,
                flags=re.I,
            )
        )
    if explicitly_negated:
        return "explicitly negates the assigned independent role"
    if subordinate and not positive:
        return "states only a co-applicant/co-investigator/coauthor role"
    return ""


def explicitly_negates_direct_topic(*values: object) -> bool:
    text = "\n".join(str(value or "") for value in values)
    return any(pattern.search(text) for pattern in DIRECT_TOPIC_NEGATION_PATTERNS)


def iter_string_values(value: object, path: str):
    """Yield (path, text) pairs from every nested string value."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_string_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_string_values(child, f"{path}[{index}]")


def validate_no_correspondence(value: object, path: str, report: Report) -> None:
    for string_path, text in iter_string_values(value, path):
        if any(pattern.search(text) for pattern in CORRESPONDENCE_PATTERNS):
            report.error(f"{string_path} contains correspondence prose")


def validate_string_list(
    value: object,
    path: str,
    report: Report,
    *,
    required: bool = False,
    unique: bool = True,
) -> list[str]:
    """Validate a JSON array whose members must be non-empty strings."""
    if not isinstance(value, list):
        report.error(f"{path} must be an array")
        return []
    cleaned: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            report.error(f"{path}[{index}] must be a non-empty string")
            continue
        cleaned.append(item.strip())
    if required and not cleaned:
        report.error(f"{path} must contain at least one non-empty string")
    if unique and len(cleaned) != len(set(cleaned)):
        report.error(f"{path} contains duplicate values")
    return cleaned


def validate_nonempty_items(
    value: object, path: str, report: Report, *, required: bool = False
) -> list[object]:
    """Reject empty scalar/object/list placeholders in a general-purpose array."""
    if not isinstance(value, list):
        report.error(f"{path} must be an array")
        return []
    valid: list[object] = []
    for index, item in enumerate(value):
        empty = (
            item is None
            or (isinstance(item, str) and not item.strip())
            or (isinstance(item, (dict, list)) and not item)
        )
        if empty:
            report.error(f"{path}[{index}] must not be empty")
        else:
            valid.append(item)
    if required and not valid:
        report.error(f"{path} must contain at least one non-empty item")
    return valid


def collect_source_refs(value: object, path: str = "") -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            lowered = key.lower()
            if lowered.endswith("sourceids") or lowered == "directevidenceids":
                if isinstance(child, list):
                    refs.extend((str(item), child_path) for item in child)
                elif not isinstance(child, dict):
                    refs.append(("", child_path))
            # Structured containers such as claimSourceIds hold nested lists;
            # recurse into them instead of treating the object itself as a ref.
            refs.extend(collect_source_refs(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            refs.extend(collect_source_refs(child, f"{path}[{index}]"))
    return refs


def validate_references(
    label: str, items: list[dict], source_map: dict[str, dict], report: Report
) -> None:
    for index, item in enumerate(items):
        identity = item.get("id") or item.get("name") or index
        refs_by_path: defaultdict[str, list[str]] = defaultdict(list)
        for source_id, field_path in collect_source_refs(item):
            refs_by_path[field_path].append(source_id)
        for field_path, source_ids in refs_by_path.items():
            if len(source_ids) != len(set(source_ids)):
                report.error(f"{label} {identity}: {field_path} contains duplicate source IDs")
            for source_id in dict.fromkeys(source_ids):
                if not source_id:
                    report.error(f"{label} {identity}: {field_path} contains an empty source ID")
                elif source_id not in source_map:
                    report.error(f"{label} {identity}: unknown source ID {source_id} at {field_path}")


def validate_case_metadata(case: dict, strict: bool, report: Report) -> dt.date | None:
    if case.get("schemaVersion") != "1.2":
        report.error("case.json schemaVersion must be 1.2")
    for field in ["location", "topic", "asOf", "scopeMode", "status"]:
        if not str(case.get(field, "")).strip():
            report.error(f"case.json missing {field}")
    if case.get("scopeMode") not in {"named_schools", "qs_top_300"}:
        report.error("case.json scopeMode must be named_schools or qs_top_300")
    if case.get("status") not in {"draft", "complete"}:
        report.error("case.json status must be draft or complete")
    if case.get("scopeMode") == "qs_top_300" and case.get("qsThreshold") != 300:
        report.error("Location-only scope must use qsThreshold=300 unless the skill specification changes")
    as_of = parse_iso_date(case.get("asOf"))
    if as_of is None:
        report.error("case.json asOf must use YYYY-MM-DD")
    elif as_of > dt.date.today():
        report.error("case.json asOf cannot be later than the current system date")
    requested_schools = validate_string_list(
        case.get("requestedSchools", []),
        "case.json requestedSchools",
        report,
        required=strict and case.get("scopeMode") == "named_schools",
    )
    if case.get("scopeMode") == "qs_top_300" and requested_schools:
        report.error("case.json requestedSchools must be empty for location-only QS scope")
    resolutions = case.get("requestedSchoolResolutions", [])
    if not isinstance(resolutions, list):
        report.error("case.json requestedSchoolResolutions must be an array")
    elif case.get("scopeMode") == "qs_top_300" and resolutions:
        report.error("case.json requestedSchoolResolutions must be empty for location-only QS scope")
    scope_audit = case.get("scopeAudit")
    if not isinstance(scope_audit, dict):
        report.error("case.json scopeAudit must be an object")
        scope_audit = {}
    if case.get("scopeMode") == "qs_top_300":
        for field in ["rankingSystem", "rankingEdition", "rankingPublicationDate"]:
            if strict and not str(scope_audit.get(field, "")).strip():
                report.error(f"case.json scopeAudit missing {field}")
        if strict and "qs" not in str(scope_audit.get("rankingSystem", "")).casefold():
            report.error("case.json scopeAudit.rankingSystem must identify QS for qs_top_300 mode")
        validate_string_list(
            scope_audit.get("jurisdictions", []),
            "case.json scopeAudit.jurisdictions",
            report,
            required=strict,
        )
        if strict and not str(scope_audit.get("rankingQuery", "")).strip():
            report.error("case.json scopeAudit.rankingQuery is required for qs_top_300 mode")
        eligible_count = scope_audit.get("eligibleInstitutionCount")
        if strict and (not isinstance(eligible_count, int) or eligible_count < 1):
            report.error(
                "case.json scopeAudit.eligibleInstitutionCount must be a positive integer"
            )
        ranking_date = parse_iso_date(scope_audit.get("rankingPublicationDate"))
        if strict and ranking_date is None:
            report.error("case.json scopeAudit.rankingPublicationDate must use YYYY-MM-DD")
        elif ranking_date and as_of and ranking_date > as_of:
            report.error("case.json scopeAudit.rankingPublicationDate is later than case asOf")
        validate_string_list(
            scope_audit.get("includedSchoolIds", []),
            "case.json scopeAudit.includedSchoolIds",
            report,
            required=strict,
        )
        validate_string_list(
            scope_audit.get("sourceIds", []),
            "case.json scopeAudit.sourceIds",
            report,
            required=strict,
        )
        location_resolution = case.get("locationResolution")
        if not isinstance(location_resolution, dict):
            report.error("case.json locationResolution must be an object for qs_top_300 mode")
            location_resolution = {}
        requested_location = str(location_resolution.get("requestedLocation", "")).strip()
        if requested_location != str(case.get("location", "")).strip():
            report.error("case.json locationResolution.requestedLocation must preserve case.location literally")
        resolved_jurisdictions = validate_string_list(
            location_resolution.get("resolvedJurisdictions", []),
            "case.json locationResolution.resolvedJurisdictions",
            report,
            required=strict,
        )
        scope_jurisdictions = [
            str(item).strip()
            for item in scope_audit.get("jurisdictions", [])
            if str(item).strip()
        ] if isinstance(scope_audit.get("jurisdictions"), list) else []
        if {item.casefold() for item in resolved_jurisdictions} != {
            item.casefold() for item in scope_jurisdictions
        }:
            report.error("case.json locationResolution must resolve exactly to scopeAudit.jurisdictions")
        relationship_type = location_resolution.get("relationshipType")
        if relationship_type not in LOCATION_RELATIONSHIP_TYPES:
            report.error("case.json locationResolution.relationshipType is invalid")
        if relationship_type == "country_exact" and requested_location.casefold() not in {
            item.casefold() for item in resolved_jurisdictions
        }:
            report.error("case.json country_exact location must equal one resolved jurisdiction")
        validate_string_list(
            location_resolution.get("sourceIds", []),
            "case.json locationResolution.sourceIds",
            report,
            required=strict,
        )
        excluded = scope_audit.get("excludedInstitutions", [])
        if strict and "excludedInstitutions" not in scope_audit:
            report.error("case.json scopeAudit must include excludedInstitutions, even when empty")
        if not isinstance(excluded, list):
            report.error("case.json scopeAudit.excludedInstitutions must be an array")
        else:
            excluded_names: set[str] = set()
            for index, item in enumerate(excluded):
                path = f"case.json scopeAudit.excludedInstitutions[{index}]"
                if not isinstance(item, dict):
                    report.error(f"{path} must be an object")
                    continue
                name = str(item.get("officialName", "")).strip()
                if not name:
                    report.error(f"{path} missing officialName")
                elif name.casefold() in excluded_names:
                    report.error(f"{path} duplicates excluded institution {name}")
                else:
                    excluded_names.add(name.casefold())
                if item.get("inclusionDecision") != "excluded":
                    report.error(f"{path}.inclusionDecision must be excluded")
                if not str(item.get("countryRegion", "")).strip():
                    report.error(f"{path} missing countryRegion")
                if not str(item.get("reason", "")).strip():
                    report.error(f"{path} missing reason")
                excluded_qs = item.get("qs")
                if not isinstance(excluded_qs, dict):
                    report.error(f"{path}.qs must be an object")
                    excluded_qs = {}
                if strict and excluded_qs.get("status") not in QS_STATUSES - {"not_verified"}:
                    report.error(f"{path}.qs.status must be resolved")
                if strict and excluded_qs.get("status") in {"ranked", "rank_band"}:
                    for field in ["edition", "publicationDate", "rank"]:
                        if not str(excluded_qs.get(field, "")).strip():
                            report.error(f"{path}.qs missing {field}")
                validate_string_list(
                    excluded_qs.get("sourceIds", []),
                    f"{path}.qs.sourceIds",
                    report,
                    required=strict,
                )
                validate_string_list(
                    item.get("sourceIds", []),
                    f"{path}.sourceIds",
                    report,
                    required=strict,
                )
    validate_string_list(case.get("limitations", []), "case.json limitations", report)
    passes = case.get("discoveryPasses", [])
    if not isinstance(passes, list):
        report.error("case.json discoveryPasses must be an array")
        passes = []
    performed_dates: list[dt.date] = []
    for index, discovery_pass in enumerate(passes):
        if not isinstance(discovery_pass, dict):
            report.error(f"case.json discoveryPasses[{index}] must be an object")
            continue
        new_count = discovery_pass.get("newCandidateCount")
        if not isinstance(new_count, int) or new_count < 0:
            report.error(
                f"case.json discoveryPasses[{index}].newCandidateCount must be a non-negative integer"
            )
        pass_type = discovery_pass.get("passType")
        if pass_type not in DISCOVERY_PASS_TYPES:
            report.error(f"case.json discoveryPasses[{index}].passType is invalid")
        performed = parse_iso_date(discovery_pass.get("performedAt"))
        if performed is None:
            report.error(f"case.json discoveryPasses[{index}].performedAt must use YYYY-MM-DD")
        elif as_of and performed > as_of:
            report.error(f"case.json discoveryPasses[{index}].performedAt is later than case asOf")
        elif performed:
            performed_dates.append(performed)
        validate_string_list(
            discovery_pass.get("queriesOrUnits", []),
            f"case.json discoveryPasses[{index}].queriesOrUnits",
            report,
            required=True,
        )
        validate_string_list(
            discovery_pass.get("sourceIds", []),
            f"case.json discoveryPasses[{index}].sourceIds",
            report,
            required=True,
        )
        candidate_ids = validate_string_list(
            discovery_pass.get("newCandidateIds", []),
            f"case.json discoveryPasses[{index}].newCandidateIds",
            report,
        )
        if isinstance(new_count, int) and new_count != len(candidate_ids):
            report.error(
                f"case.json discoveryPasses[{index}].newCandidateCount does not match unique newCandidateIds"
            )
    if strict:
        if case.get("status") != "complete":
            report.error("Strict mode requires case.json status=complete")
        if len(passes) < 3:
            report.error(
                "Strict mode requires two expansion passes plus a final saturation pass"
            )
        elif not isinstance(passes[-1], dict) or passes[-1].get("newCandidateCount") != 0:
            report.error("The final discovery pass must add zero qualified candidates")
        elif passes[-1].get("passType") != "saturation":
            report.error("The final discovery pass must use passType=saturation")
        if len(passes) >= 2:
            if not isinstance(passes[0], dict) or passes[0].get("passType") != "official_expansion":
                report.error("The first discovery pass must use passType=official_expansion")
            if not any(
                isinstance(item, dict) and item.get("passType") == "literature_expansion"
                for item in passes[1:-1]
            ):
                report.error("A literature_expansion pass is required before saturation")
        if len(performed_dates) == len(passes) and performed_dates != sorted(performed_dates):
            report.error("case.json discoveryPasses performedAt dates must be non-decreasing")
        if performed_dates and as_of and (as_of - performed_dates[-1]).days > 30:
            report.error("The final saturation pass is more than 30 days older than case asOf")
    return as_of


def validate_sources(
    sources: list[dict], as_of: dt.date | None, strict: bool, report: Report
) -> dict[str, dict]:
    source_map = check_unique_ids("source", sources, report)
    canonical_urls: defaultdict[str, list[str]] = defaultdict(list)
    identifier_works: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    identifiers_by_work: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for index, source in enumerate(sources):
        identity = source.get("id") or index
        source_type = source.get("type")
        if source_type not in SOURCE_TYPES:
            report.error(f"Source {identity}: invalid type {source_type}")
        if source.get("topicRelevance") not in SOURCE_TOPIC_RELEVANCE:
            report.error(f"Source {identity}: invalid topicRelevance")
        if source.get("status") not in SOURCE_STATUSES:
            report.error(f"Source {identity}: invalid status")
        authority = source.get("authorityClass")
        medium = source.get("medium")
        if authority not in SOURCE_AUTHORITY_CLASSES:
            report.error(f"Source {identity}: invalid authorityClass {authority}")
        if medium not in SOURCE_MEDIA:
            report.error(f"Source {identity}: invalid medium {medium}")
        claim_domains = validate_string_list(
            source.get("claimDomains", []),
            f"Source {identity}: claimDomains",
            report,
            required=strict,
        )
        invalid_domains = sorted(set(claim_domains) - CLAIM_DOMAINS)
        if invalid_domains:
            report.error(f"Source {identity}: invalid claimDomains {invalid_domains}")
        subject_ids = validate_string_list(
            source.get("subjectIds", []),
            f"Source {identity}: subjectIds",
            report,
        )
        person_roles = source.get("personRoles", [])
        if not isinstance(person_roles, list):
            report.error(f"Source {identity}: personRoles must be an array")
            person_roles = []
        seen_role_subjects: set[str] = set()
        for role_index, person_role in enumerate(person_roles):
            path = f"Source {identity}: personRoles[{role_index}]"
            if not isinstance(person_role, dict):
                report.error(f"{path} must be an object")
                continue
            subject_id = str(person_role.get("subjectId", "")).strip()
            role_type = str(person_role.get("roleType", "")).strip()
            exact_label = str(person_role.get("exactLabel", "")).strip()
            topic_relevance = person_role.get("topicRelevance")
            if not subject_id or not exact_label:
                report.error(f"{path} requires subjectId and exactLabel")
            if role_type not in PERSON_ROLE_TYPES:
                report.error(f"{path}.roleType is invalid")
            folded_label = exact_label.casefold()
            placeholder = next(
                (fragment for fragment in ROLE_LABEL_PLACEHOLDER_FRAGMENTS if fragment in folded_label),
                None,
            )
            if placeholder:
                report.error(
                    f"{path}.exactLabel contains placeholder text instead of a source-faithful role: {placeholder}"
                )
            if topic_relevance not in SOURCE_TOPIC_RELEVANCE:
                report.error(f"{path}.topicRelevance is invalid")
            role_conflict = person_role_label_conflict(role_type, exact_label)
            if role_conflict:
                report.error(f"{path}.exactLabel contradicts roleType={role_type}: {role_conflict}")
            if topic_relevance == "direct" and explicitly_negates_direct_topic(
                exact_label, source.get("claim", "")
            ):
                report.error(
                    f"{path}.topicRelevance=direct conflicts with an explicit non-lung/topic-negation statement"
                )
            if (
                strict
                and topic_relevance in {"direct", "adjacent"}
                and any(
                    pattern.search(str(source.get("claim", "")))
                    for pattern in MIGRATED_GENERIC_TOPIC_CLAIM_PATTERNS
                )
            ):
                report.error(
                    f"{path}.topicRelevance={topic_relevance} relies on a migrated candidate summary, "
                    "not a source-specific research claim"
                )
            if subject_id not in subject_ids:
                report.error(f"{path}.subjectId must also appear in source.subjectIds")
            if subject_id in seen_role_subjects:
                report.error(f"{path} duplicates a person role for {subject_id}")
            seen_role_subjects.add(subject_id)
        scalar_topic = source.get("topicRelevance")
        if "research" not in claim_domains:
            if scalar_topic != "not_applicable":
                report.error(
                    f"Source {identity}: non-research source must use topicRelevance=not_applicable"
                )
        elif person_roles:
            role_topics = {
                role.get("topicRelevance")
                for role in person_roles
                if isinstance(role, dict)
            }
            expected_topic = (
                "direct" if "direct" in role_topics
                else "adjacent" if "adjacent" in role_topics
                else "background"
            )
            if scalar_topic != expected_topic:
                report.error(
                    f"Source {identity}: source topicRelevance={scalar_topic} disagrees with "
                    f"personRoles aggregate={expected_topic}"
                )
        for field in ["title", "url", "publisher", "accessedDate", "claim"]:
            if not str(source.get(field, "")).strip():
                report.error(f"Source {identity}: missing {field}")
        url = str(source.get("url", "")).strip()
        try:
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.netloc:
                raise ValueError("not an absolute HTTP(S) URL")
            canon = canonical_url(url)
        except (ValueError, TypeError) as exc:
            report.error(f"Source {identity}: invalid URL ({exc})")
            canon = url
        canonical_urls[canon].append(str(identity))
        work_id = str(source.get("workId", "")).strip().casefold()
        identifiers = source.get("identifiers", {})
        if not isinstance(identifiers, dict):
            report.error(f"Source {identity}: identifiers must be an object")
            identifiers = {}
        allowed_identifier_keys = {"doi", "pmid", "pmcid", "grantId", "trialId", "postingId"}
        for key, raw_value in identifiers.items():
            if key not in allowed_identifier_keys:
                report.error(f"Source {identity}: unsupported identifier key {key}")
                continue
            value = str(raw_value).strip()
            if not value:
                report.error(f"Source {identity}: identifier {key} must not be empty")
                continue
            normalized = value.casefold()
            if key == "doi":
                normalized = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", normalized)
                if not re.fullmatch(r"10\.\d{4,9}/\S+", normalized):
                    report.error(f"Source {identity}: malformed DOI identifier {value}")
            elif key == "pmid" and not re.fullmatch(r"\d+", value):
                report.error(f"Source {identity}: malformed PMID identifier {value}")
            elif key == "pmcid" and not re.fullmatch(r"PMC\d+", value, flags=re.I):
                report.error(f"Source {identity}: malformed PMCID identifier {value}")
            elif key == "trialId" and not re.fullmatch(r"NCT\d+", value, flags=re.I):
                report.error(f"Source {identity}: malformed trial identifier {value}")
            if strict and source_type in {"publication", "grant_project", "clinical_trial", "vacancy"} and not work_id:
                report.error(f"Source {identity}: {source_type} with a formal identifier needs workId")
            if work_id:
                identifier_works[(key.casefold(), normalized)].add(work_id)
                identifiers_by_work[(work_id, key.casefold())].add(normalized)
        host = (urlsplit(url).hostname or "").casefold()
        path = urlsplit(url).path.rstrip("/")
        expected_host_authority = next(
            (
                expected
                for domain, expected in HOST_AUTHORITY_CLASS_RULES.items()
                if host == domain or host.endswith(f".{domain}")
            ),
            None,
        )
        if expected_host_authority and authority != expected_host_authority:
            report.error(
                f"Source {identity}: host {host} requires "
                f"authorityClass={expected_host_authority}, not {authority}"
            )
        if host == "doi.org" and path:
            doi_from_url = path.lstrip("/").casefold()
            doi_in_record = str(identifiers.get("doi", "")).strip().casefold()
            doi_in_record = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi_in_record)
            if doi_in_record != doi_from_url:
                report.error(f"Source {identity}: DOI URL and identifiers.doi disagree")
        if "pubmed.ncbi.nlm.nih.gov" in host:
            match = re.search(r"/(\d+)$", path)
            if match and str(identifiers.get("pmid", "")).strip() != match.group(1):
                report.error(f"Source {identity}: PubMed URL and identifiers.pmid disagree")
        if "clinicaltrials.gov" in host:
            match = re.search(r"/(NCT\d+)$", path, flags=re.I)
            if match and str(identifiers.get("trialId", "")).strip().casefold() != match.group(1).casefold():
                report.error(f"Source {identity}: ClinicalTrials.gov URL and identifiers.trialId disagree")
        accessed = parse_iso_date(source.get("accessedDate"))
        if accessed is None:
            report.error(f"Source {identity}: accessedDate must use YYYY-MM-DD")
        elif as_of and accessed > as_of:
            report.error(f"Source {identity}: accessedDate is later than case asOf")
        published, precision = parse_partial_date(source.get("publishedDate"))
        if precision == "invalid":
            report.error(f"Source {identity}: publishedDate must be YYYY, YYYY-MM, YYYY-MM-DD, or blank")
        elif published and as_of and published > as_of and source.get("status") != "future":
            report.error(f"Source {identity}: publishedDate is later than case asOf but status is not future")
        elif (
            published
            and accessed
            and published > accessed
            and source.get("status") not in {"future", "unclear"}
        ):
            report.error(f"Source {identity}: publishedDate is later than accessedDate")
        if source_type == "official_ranking" and authority != "official_ranking_publisher":
            report.error(f"Source {identity}: official_ranking needs official_ranking_publisher authority")
        if strict and source_type == "official_ranking" and "ranking" not in claim_domains:
            report.error(f"Source {identity}: official_ranking must claim domain ranking")
        if source_type in {
            "official_research_profile",
            "official_role_contact",
            "official_school_structure",
            "doctoral_rule_supervision",
            "official_vacancy_portal",
        } and authority != "official_institution":
            report.error(f"Source {identity}: {source_type} needs official_institution authority")
        if source_type in {"official_admissions_funding", "vacancy"} and authority not in {
            "official_institution",
            "official_funder_registry",
            "official_government_regulator",
        }:
            report.error(f"Source {identity}: {source_type} needs an official institution/funder/government authority")
        if source_type == "publication" and authority != "primary_publication":
            report.error(f"Source {identity}: publication needs primary_publication authority")
        if strict and source_type in DIRECT_RESEARCH_SOURCE_TYPES and "research" not in claim_domains:
            report.error(f"Source {identity}: {source_type} must claim domain research")
        if source_type == "grant_project" and authority not in {
            "official_funder_registry",
            "official_institution",
            "official_government_regulator",
        }:
            report.error(f"Source {identity}: grant_project needs official funder/institution/government authority")
        if source_type == "clinical_trial" and authority not in {
            "official_trial_registry",
            "official_government_regulator",
            "official_institution",
        }:
            report.error(f"Source {identity}: clinical_trial needs an official trial registry/government/institution authority")
        if source_type == "social_user_generated" and authority != "social_user_generated":
            report.error(f"Source {identity}: social_user_generated has incompatible authorityClass")
        if source_type == "discovery_lead":
            if claim_domains != ["discovery"]:
                report.error(
                    f"Source {identity}: discovery_lead must use only claimDomains=['discovery']"
                )
            if source.get("topicRelevance") != "not_applicable":
                report.error(f"Source {identity}: discovery_lead must use topicRelevance=not_applicable")
            for role_index, person_role in enumerate(person_roles):
                if not isinstance(person_role, dict):
                    continue
                if person_role.get("roleType") != "mentioned_without_role":
                    report.error(
                        f"Source {identity}: discovery_lead personRoles[{role_index}] must use "
                        "roleType=mentioned_without_role"
                    )
                if person_role.get("topicRelevance") != "not_applicable":
                    report.error(
                        f"Source {identity}: discovery_lead personRoles[{role_index}] must use "
                        "topicRelevance=not_applicable"
                    )
                if "discovery lead only; legacy association not used as role/topic evidence" not in str(
                    person_role.get("exactLabel", "")
                ).casefold():
                    report.error(
                        f"Source {identity}: discovery_lead personRoles[{role_index}] needs the fixed "
                        "transparent non-evidence label"
                    )
        required_domain_by_type = {
            "official_school_structure": "school_structure",
            "official_admissions_funding": "admissions_funding",
            "official_vacancy_portal": "recruitment",
            "vacancy": "recruitment",
        }
        required_domain = required_domain_by_type.get(str(source_type))
        if strict and required_domain and required_domain not in claim_domains:
            report.error(f"Source {identity}: {source_type} must claim domain {required_domain}")
        if (
            strict
            and source_type == "doctoral_rule_supervision"
            and not {"doctoral_rule", "doctoral_supervision"}.intersection(claim_domains)
        ):
            report.error(
                f"Source {identity}: doctoral_rule_supervision needs doctoral_rule and/or doctoral_supervision"
            )
        if strict and source_type == "doctoral_rule_supervision":
            source_text = "\n".join(
                [
                    str(source.get("title", "")),
                    str(source.get("claim", "")),
                    *[
                        str(role.get("exactLabel", ""))
                        for role in person_roles
                        if isinstance(role, dict)
                    ],
                ]
            )
            if "current_role" in claim_domains:
                for role_index, person_role in enumerate(person_roles):
                    if not isinstance(person_role, dict):
                        continue
                    exact_label = str(person_role.get("exactLabel", ""))
                    if not any(pattern.search(exact_label) for pattern in EXPLICIT_CURRENT_TITLE_PATTERNS):
                        report.error(
                            f"Source {identity}: personRoles[{role_index}] generic doctoral-programme "
                            "listing cannot substantiate a personal current role without an explicit title"
                        )
            if "contact" in claim_domains and person_roles:
                contact_is_explicit = bool(
                    re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", source_text)
                    or re.search(
                        r"(?i)\b(?:personal )?(?:e-?mail|contact (?:address|details?))\b|"
                        r"(?:个人邮箱|电子邮箱|联系邮箱|联系方式)",
                        source_text,
                    )
                )
                if not contact_is_explicit:
                    report.error(
                        f"Source {identity}: doctoral programme source cannot support personal contact "
                        "without an explicit person-specific contact statement"
                    )
            research_roles = [
                role
                for role in person_roles
                if isinstance(role, dict) and role.get("topicRelevance") in {"direct", "adjacent"}
            ]
            if "research" in claim_domains and research_roles:
                has_research_statement = any(
                    pattern.search(source_text) for pattern in EXPLICIT_RESEARCH_STATEMENT_PATTERNS
                )
                has_direct_topic = bool(
                    re.search(
                        r"(?i)\b(?:lung|thoracic|nsclc|sclc|mesothelioma)\b|"
                        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸膜间皮瘤|间皮瘤)",
                        source_text,
                    )
                )
                if not has_research_statement or (
                    any(role.get("topicRelevance") == "direct" for role in research_roles)
                    and not has_direct_topic
                ):
                    report.error(
                        f"Source {identity}: doctoral programme source cannot carry direct/adjacent topic "
                        "evidence without a source-specific research or thesis statement"
                    )
        if (
            strict
            and source_type == "official_role_contact"
            and not {"current_role", "contact"}.intersection(claim_domains)
        ):
            report.error(
                f"Source {identity}: official_role_contact needs current_role and/or contact claimDomain"
            )
    for canon, source_ids in canonical_urls.items():
        if len(source_ids) > 1:
            message = (
                f"Canonical URL is stored more than once ({canon}): {', '.join(source_ids)}; "
                "use one source record with multiple claimDomains"
            )
            if strict:
                report.error(message)
            else:
                report.warn(message)
    for (identifier_type, identifier), work_ids in identifier_works.items():
        if len(work_ids) > 1:
            report.error(
                f"Identifier {identifier_type}:{identifier} is assigned to multiple workIds: "
                + ", ".join(sorted(work_ids))
            )
    for (work_id, identifier_type), values in identifiers_by_work.items():
        if len(values) > 1:
            report.error(
                f"workId {work_id} has conflicting {identifier_type} values: "
                + ", ".join(sorted(values))
            )
    return source_map


def validate_schools(
    schools: list[dict], case: dict, source_map: dict[str, dict], strict: bool, report: Report
) -> dict[str, dict]:
    school_map = check_unique_ids("school", schools, report)
    if not schools:
        report.error("schools.json contains no schools")
    scope_mode = case.get("scopeMode")
    scope_audit = case.get("scopeAudit") if isinstance(case.get("scopeAudit"), dict) else {}
    ranking_edition = str(scope_audit.get("rankingEdition", "")).strip()
    ranking_publication_date = str(scope_audit.get("rankingPublicationDate", "")).strip()
    jurisdictions = {
        str(item).strip().casefold()
        for item in scope_audit.get("jurisdictions", [])
        if str(item).strip()
    } if isinstance(scope_audit.get("jurisdictions", []), list) else set()
    try:
        threshold = int(case.get("qsThreshold", 300))
    except (TypeError, ValueError):
        report.error("case.json qsThreshold must be an integer")
        threshold = 300
    normalized_school_names: set[str] = set()
    for index, school in enumerate(schools):
        identity = school.get("id") or index
        for field in ["officialName", "countryRegion"]:
            if not str(school.get(field, "")).strip():
                report.error(f"School {identity}: missing {field}")
        if (
            strict
            and scope_mode == "qs_top_300"
            and str(school.get("countryRegion", "")).strip().casefold() not in jurisdictions
        ):
            report.error(
                f"School {identity}: countryRegion is outside scopeAudit.jurisdictions"
            )
        normalized_school_name = re.sub(
            r"\s+", " ", str(school.get("officialName", "")).strip().casefold()
        )
        if normalized_school_name in normalized_school_names:
            report.error(f"School {identity}: duplicate normalized officialName")
        normalized_school_names.add(normalized_school_name)
        if school.get("origin") not in {"user_named", "ranking_screen"}:
            report.error(f"School {identity}: origin must be user_named or ranking_screen")
        elif scope_mode == "named_schools" and school.get("origin") != "user_named":
            report.error(f"School {identity}: named-school scope requires origin=user_named")
        elif scope_mode == "qs_top_300" and school.get("origin") != "ranking_screen":
            report.error(f"School {identity}: QS location scope requires origin=ranking_screen")
        if school.get("inclusionDecision") != "included":
            report.error(f"School {identity}: inclusionDecision must be included")
        if not str(school.get("inclusionReason", "")).strip():
            report.error(f"School {identity}: missing inclusionReason")
        qs = school.get("qs", {})
        medical = school.get("medicalSystem", {})
        if not isinstance(qs, dict):
            report.error(f"School {identity}: qs must be an object")
            qs = {}
        if not isinstance(medical, dict):
            report.error(f"School {identity}: medicalSystem must be an object")
            medical = {}
        if qs.get("status") not in QS_STATUSES:
            report.error(f"School {identity}: invalid QS status")
        if medical.get("status") not in MEDICAL_STATUSES:
            report.error(f"School {identity}: invalid medical-system status")
        if strict and qs.get("status") == "not_verified":
            report.error(f"School {identity}: QS status remains not_verified")
        if strict and qs.get("status") in {"ranked", "rank_band"}:
            if not str(qs.get("edition", "")).strip() or not str(qs.get("rank", "")).strip():
                report.error(f"School {identity}: ranked QS record needs edition and rank/band")
            qs_date = parse_iso_date(qs.get("publicationDate"))
            if qs_date is None:
                report.error(f"School {identity}: qs.publicationDate must use YYYY-MM-DD")
            if ranking_edition and str(qs.get("edition", "")).strip() != ranking_edition:
                report.error(f"School {identity}: QS edition differs from scopeAudit.rankingEdition")
            if ranking_publication_date and str(qs.get("publicationDate", "")).strip() != ranking_publication_date:
                report.error(
                    f"School {identity}: QS publicationDate differs from scopeAudit.rankingPublicationDate"
                )
            if parse_rank_interval(qs.get("rank"), qs.get("status")) is None:
                report.error(f"School {identity}: QS rank/band must be a positive exact rank or positive interval")
        qs_source_ids = validate_string_list(
            qs.get("sourceIds", []), f"School {identity}: qs.sourceIds", report, required=strict
        )
        if strict and not any(
            source_map.get(source_id, {}).get("type") == "official_ranking"
            and source_map.get(source_id, {}).get("authorityClass") == "official_ranking_publisher"
            and str(identity) in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in qs_source_ids
        ):
            report.error(f"School {identity}: QS claim lacks an official ranking-publisher source")
        if strict and medical.get("status") in {"", None, "unclear"}:
            report.error(f"School {identity}: medical-system status is unresolved")
        if strict and not str(medical.get("summary", "")).strip():
            report.error(f"School {identity}: medicalSystem.summary is required")
        medical_source_ids = validate_string_list(
            medical.get("sourceIds", []),
            f"School {identity}: medicalSystem.sourceIds",
            report,
            required=strict,
        )
        if strict and not any(
            source_map.get(source_id, {}).get("authorityClass") == "official_institution"
            and "school_structure" in source_map.get(source_id, {}).get("claimDomains", [])
            and str(identity) in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in medical_source_ids
        ):
            report.error(f"School {identity}: medical-system claim lacks an official structure source")
        validate_string_list(
            school.get("sourceIds", []), f"School {identity}: sourceIds", report
        )
        related_institutions = school.get("affiliatedInstitutions", [])
        if not isinstance(related_institutions, list):
            report.error(f"School {identity}: affiliatedInstitutions must be an array")
            related_institutions = []
        seen_related_ids: set[str] = set()
        for related_index, related in enumerate(related_institutions):
            path = f"School {identity}: affiliatedInstitutions[{related_index}]"
            if not isinstance(related, dict):
                report.error(f"{path} must be an object")
                continue
            related_id = str(related.get("id", "")).strip()
            if not related_id or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", related_id):
                report.error(f"{path}.id must be a lowercase ASCII slug")
            elif related_id in seen_related_ids:
                report.error(f"{path}.id duplicates another related institution")
            seen_related_ids.add(related_id)
            if not str(related.get("name", "")).strip() or not str(related.get("relationship", "")).strip():
                report.error(f"{path} requires name and relationship")
            if related.get("relationshipType") not in AFFILIATED_RELATIONSHIP_TYPES:
                report.error(f"{path} has invalid relationshipType")
            related_source_ids = validate_string_list(
                related.get("sourceIds", []), f"{path}.sourceIds", report, required=True
            )
            if strict and not any(
                source_map.get(source_id, {}).get("authorityClass") == "official_institution"
                and "school_structure" in source_map.get(source_id, {}).get("claimDomains", [])
                and str(identity) in source_map.get(source_id, {}).get("subjectIds", [])
                for source_id in related_source_ids
            ):
                report.error(f"{path} lacks school-bound official relationship evidence")
        if scope_mode == "named_schools" and not school.get("namedByUser"):
            message = f"School {identity}: named_schools scope but namedByUser is false"
            if strict:
                report.error(message)
            else:
                report.warn(message)
        # A user-named flag is provenance only; it never bypasses a location-wide
        # top-300 inclusion rule.
        if strict and scope_mode == "qs_top_300" and qs.get("status") not in {"ranked", "rank_band"}:
            report.error(f"School {identity}: location-only QS scope contains an unranked institution")
        if strict and scope_mode == "qs_top_300" and qs.get("status") in {"ranked", "rank_band"}:
            rank_interval = parse_rank_interval(qs.get("rank"), qs.get("status"))
            if rank_interval is None:
                report.error(f"School {identity}: QS rank/band is not machine-readable")
            elif rank_interval[1] > threshold:
                report.error(
                    f"School {identity}: QS rank/band {qs.get('rank')} exceeds top-{threshold} scope"
                )
    if scope_mode == "named_schools":
        resolutions = case.get("requestedSchoolResolutions", [])
        if not isinstance(resolutions, list):
            resolutions = []
        requested_names = [
            re.sub(r"\s+", " ", str(item).strip().casefold())
            for item in case.get("requestedSchools", [])
            if str(item).strip()
        ]
        resolved_names: list[str] = []
        resolved_school_ids: list[str] = []
        for index, resolution in enumerate(resolutions):
            path = f"case.json requestedSchoolResolutions[{index}]"
            if not isinstance(resolution, dict):
                report.error(f"{path} must be an object")
                continue
            requested_name = str(resolution.get("requestedName", "")).strip()
            school_id = str(resolution.get("schoolId", "")).strip()
            if not requested_name:
                report.error(f"{path} missing requestedName")
            else:
                resolved_names.append(re.sub(r"\s+", " ", requested_name.casefold()))
            if school_id not in school_map:
                report.error(f"{path} references unknown schoolId {school_id}")
            else:
                resolved_school_ids.append(school_id)
            if resolution.get("decision") not in {"resolved", "unresolved"}:
                report.error(f"{path}.decision must be resolved or unresolved")
            elif strict and resolution.get("decision") != "resolved":
                report.error(f"{path}.decision must be resolved before strict delivery")
            source_ids = validate_string_list(
                resolution.get("sourceIds", []), f"{path}.sourceIds", report, required=strict
            )
            if strict and not any(
                source_map.get(source_id, {}).get("authorityClass")
                in {"official_institution", "official_ranking_publisher"}
                for source_id in source_ids
            ):
                report.error(f"{path} lacks an official identity-resolution source")
        if sorted(requested_names) != sorted(resolved_names):
            report.error("requestedSchoolResolutions must preserve and resolve every requestedSchools literal")
        if sorted(resolved_school_ids) != sorted(school_map):
            report.error("requestedSchoolResolutions must map one-to-one onto included schools")
    if scope_mode == "qs_top_300":
        included_ids = scope_audit.get("includedSchoolIds", [])
        if isinstance(included_ids, list):
            included_set = {str(item).strip() for item in included_ids if str(item).strip()}
            school_ids = set(school_map)
            if included_set != school_ids:
                missing = sorted(school_ids - included_set)
                extra = sorted(included_set - school_ids)
                report.error(
                    "case.json scopeAudit.includedSchoolIds must exactly match schools.json "
                    f"(missing={missing}, extra={extra})"
                )
        eligible_count = scope_audit.get("eligibleInstitutionCount")
        if isinstance(eligible_count, int) and eligible_count != len(schools):
            report.error(
                "case.json scopeAudit.eligibleInstitutionCount must equal the number of included schools"
            )
        ranking_source_ids = scope_audit.get("sourceIds", [])
        if isinstance(ranking_source_ids, list) and strict and not any(
            source_map.get(str(source_id), {}).get("type") == "official_ranking"
            and source_map.get(str(source_id), {}).get("authorityClass")
            == "official_ranking_publisher"
            for source_id in ranking_source_ids
        ):
            report.error("case.json scopeAudit lacks an official ranking-publisher source")
        included_names = {
            str(school.get("officialName", "")).strip().casefold()
            for school in schools
            if str(school.get("officialName", "")).strip()
        }
        excluded = scope_audit.get("excludedInstitutions", [])
        if isinstance(excluded, list):
            for index, item in enumerate(excluded):
                if not isinstance(item, dict):
                    continue
                name = str(item.get("officialName", "")).strip()
                if name and name.casefold() in included_names:
                    report.error(
                        f"case.json scopeAudit.excludedInstitutions[{index}] is also included: {name}"
                    )
                path = f"case.json scopeAudit.excludedInstitutions[{index}]"
                country = str(item.get("countryRegion", "")).strip().casefold()
                if strict and country not in jurisdictions:
                    report.error(f"{path}.countryRegion is outside scopeAudit.jurisdictions")
                excluded_qs = item.get("qs") if isinstance(item.get("qs"), dict) else {}
                excluded_qs_ids = excluded_qs.get("sourceIds", [])
                if isinstance(excluded_qs_ids, list) and strict and not any(
                    source_map.get(str(source_id), {}).get("type") == "official_ranking"
                    and source_map.get(str(source_id), {}).get("authorityClass")
                    == "official_ranking_publisher"
                    for source_id in excluded_qs_ids
                ):
                    report.error(f"{path}.qs lacks an official ranking-publisher source")
                if excluded_qs.get("status") in {"ranked", "rank_band"}:
                    if ranking_edition and str(excluded_qs.get("edition", "")).strip() != ranking_edition:
                        report.error(f"{path}.qs edition differs from scopeAudit.rankingEdition")
                    if (
                        ranking_publication_date
                        and str(excluded_qs.get("publicationDate", "")).strip()
                        != ranking_publication_date
                    ):
                        report.error(
                            f"{path}.qs publicationDate differs from scopeAudit.rankingPublicationDate"
                        )
                    excluded_interval = parse_rank_interval(
                        excluded_qs.get("rank"), excluded_qs.get("status")
                    )
                    if excluded_interval is None:
                        report.error(f"{path}.qs rank/band is not machine-readable")
                    elif excluded_interval[1] <= threshold:
                        report.error(
                            f"{path} is within top-{threshold} and cannot be excluded"
                        )
    return school_map


def candidate_school_ids(record: dict) -> set[str]:
    result = {str(record.get("schoolId", "")).strip()}
    additional = record.get("additionalSchoolIds", [])
    if isinstance(additional, list):
        result.update(str(item).strip() for item in additional if str(item).strip())
    result.discard("")
    return result


def candidate_ids_named_in_text(text: object, record_map: dict[str, dict]) -> set[str]:
    """Find explicit full candidate names; do not guess from initials or common surnames."""
    normalized = re.sub(
        r"[^a-z0-9\u3400-\u9fff]+", " ", normalized_search_text(text)
    ).strip()
    padded = f" {normalized} "
    result: set[str] = set()
    for candidate_id, record in record_map.items():
        name = re.sub(
            r"[^a-z0-9\u3400-\u9fff]+",
            " ",
            normalized_search_text(record.get("name", "")),
        ).strip()
        if name and f" {name} " in padded:
            result.add(candidate_id)
    return result


def validate_source_entities_and_scope(
    case: dict,
    school_map: dict[str, dict],
    record_map: dict[str, dict],
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    known_entities = set(school_map) | set(record_map)
    for source_id, source in source_map.items():
        for subject_id in source.get("subjectIds", []):
            if subject_id not in known_entities:
                report.error(f"Source {source_id}: subjectIds contains unknown entity {subject_id}")
        for role in source.get("personRoles", []):
            if isinstance(role, dict) and role.get("subjectId") not in record_map:
                report.error(
                    f"Source {source_id}: personRoles subject must be a candidate ID, not {role.get('subjectId')}"
                )
        candidate_subjects = {
            str(subject_id)
            for subject_id in source.get("subjectIds", [])
            if str(subject_id) in record_map
        }
        explicitly_named = candidate_ids_named_in_text(
            f"{source.get('title', '')}\n{source.get('claim', '')}", record_map
        )
        if len(explicitly_named) == 1:
            named_owner = next(iter(explicitly_named))
            for candidate_id in candidate_subjects - {named_owner}:
                role = person_role_for(source, candidate_id)
                label = str((role or {}).get("exactLabel", ""))
                topic = (role or {}).get("topicRelevance")
                if (
                    "research" in source.get("claimDomains", [])
                    and topic in {"direct", "adjacent"}
                    and not any(pattern.search(label) for pattern in EXPLICIT_RESEARCH_STATEMENT_PATTERNS)
                ):
                    report.error(
                        f"Source {source_id}: claim/title names only {named_owner}, but direct/adjacent "
                        f"research evidence is bound to {candidate_id} without a person-specific research statement"
                    )
                contact_owner_wording = bool(
                    re.search(
                        r"(?i)(?:published\s+)?contact[^.;，。；]{0,30}(?:used\s+)?for|"
                        r"contact source for|(?:联系方式|邮箱)[^。；]{0,20}(?:用于|属于)",
                        str(source.get("claim", "")),
                    )
                )
                if "contact" in source.get("claimDomains", []) and contact_owner_wording and not re.search(
                    r"(?i)[^@\s]+@[^@\s]+\.[^@\s]+|\b(?:e-?mail|contact)\b|(?:邮箱|联系方式)",
                    label,
                ):
                    report.error(
                        f"Source {source_id}: contact claim names only {named_owner}, but is bound to "
                        f"{candidate_id} without a person-specific published contact statement"
                    )
    if case.get("scopeMode") == "qs_top_300":
        resolution = case.get("locationResolution", {})
        source_ids = resolution.get("sourceIds", []) if isinstance(resolution, dict) else []
        if strict and not any(
            source_map.get(source_id, {}).get("authorityClass")
            in {"official_ranking_publisher", "official_government_regulator"}
            and {"ranking", "school_structure"}.intersection(
                source_map.get(source_id, {}).get("claimDomains", [])
            )
            for source_id in source_ids
        ):
            report.error(
                "case.json locationResolution lacks an official ranking/government source for the jurisdiction mapping"
            )


def validate_discovery_candidates(
    case: dict,
    record_map: dict[str, dict],
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    passes = case.get("discoveryPasses", [])
    if not isinstance(passes, list):
        return
    seen: set[str] = set()
    for index, discovery_pass in enumerate(passes):
        if not isinstance(discovery_pass, dict):
            continue
        candidate_ids = discovery_pass.get("newCandidateIds", [])
        if not isinstance(candidate_ids, list):
            continue
        source_ids = discovery_pass.get("sourceIds", [])
        if not isinstance(source_ids, list):
            source_ids = []
        performed = parse_iso_date(discovery_pass.get("performedAt"))
        for source_id in source_ids:
            source = source_map.get(str(source_id), {})
            accessed = parse_iso_date(source.get("accessedDate"))
            if performed and accessed and accessed > performed:
                report.error(
                    f"case.json discoveryPasses[{index}] cites {source_id} accessed after performedAt"
                )
        pass_type = discovery_pass.get("passType")
        if strict and pass_type == "official_expansion" and not any(
            source_map.get(str(source_id), {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            for source_id in source_ids
        ):
            report.error(f"case.json discoveryPasses[{index}] official pass lacks official sources")
        if strict and pass_type == "literature_expansion" and not any(
            source_map.get(str(source_id), {}).get("type")
            in {"publication", "grant_project", "clinical_trial"}
            for source_id in source_ids
        ):
            report.error(
                f"case.json discoveryPasses[{index}] literature pass lacks a publication/grant/trial source"
            )
        for candidate_id in candidate_ids:
            candidate_id = str(candidate_id).strip()
            if not candidate_id:
                continue
            if candidate_id not in record_map:
                report.error(
                    f"case.json discoveryPasses[{index}] names unknown candidate ID {candidate_id}"
                )
            if candidate_id in seen:
                report.error(
                    f"case.json discoveryPasses[{index}] repeats previously discovered candidate {candidate_id}"
                )
            seen.add(candidate_id)
            if strict and not any(
                candidate_id in source_map.get(str(source_id), {}).get("subjectIds", [])
                for source_id in source_ids
            ):
                report.error(
                    f"case.json discoveryPasses[{index}] lacks candidate-bound source for {candidate_id}"
                )
    if strict and seen != set(record_map):
        report.error(
            "case.json discoveryPasses newCandidateIds must cover every candidate exactly once "
            f"(missing={sorted(set(record_map) - seen)}, extra={sorted(seen - set(record_map))})"
        )


def validate_coverage(
    coverage: list[dict],
    school_map: dict[str, dict],
    record_map: dict[str, dict],
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(coverage):
        identity = f"coverage[{index}]"
        school_id = row.get("schoolId")
        area = row.get("area")
        if school_id not in school_map:
            report.error(f"{identity}: unknown schoolId {school_id}")
        else:
            grouped[str(school_id)].append(row)
        if area not in COVERAGE_AREAS:
            report.error(f"{identity}: invalid area {area}")
        if row.get("status") not in COVERAGE_STATUSES:
            report.error(f"{identity}: invalid status {row.get('status')}")
        if strict and row.get("status") == "pending":
            report.error(f"{identity}: status remains pending")
        completed = row.get("status") in {"searched", "candidates_found", "not_present"}
        units = validate_string_list(
            row.get("units", []), f"{identity}.units", report, required=strict and completed
        )
        candidate_ids = validate_string_list(
            row.get("candidateIds", []), f"{identity}.candidateIds", report
        )
        for candidate_id in candidate_ids:
            if candidate_id not in record_map:
                report.error(f"{identity}: unknown candidateId {candidate_id}")
            elif str(school_id) not in candidate_school_ids(record_map[candidate_id]):
                report.error(
                    f"{identity}: candidate {candidate_id} is not affiliated with school {school_id}"
                )
        if row.get("status") == "candidates_found" and not candidate_ids:
            report.error(f"{identity}: candidates_found without candidateIds")
        if row.get("status") == "candidates_found":
            branch_text = "\n".join([*units, str(row.get("notes", ""))])
            if any(pattern.search(branch_text) for pattern in CANDIDATES_FOUND_NEGATION_PATTERNS):
                report.error(
                    f"{identity}: candidates_found contradicts a no-qualifying-candidate statement in units/notes"
                )
        if row.get("status") != "candidates_found" and candidate_ids:
            report.error(f"{identity}: candidateIds are allowed only when status=candidates_found")
        if row.get("status") in {"searched", "candidates_found", "not_present"} and strict and not row.get("sourceIds"):
            report.error(f"{identity}: completed search branch has no source evidence")
        coverage_source_ids = validate_string_list(
            row.get("sourceIds", []),
            f"{identity}.sourceIds",
            report,
            required=strict and row.get("status") in {"searched", "candidates_found", "not_present"},
        )
        if strict and completed and not any(
            source_map.get(source_id, {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and {"school_structure", "research", "current_role"}.intersection(
                source_map.get(source_id, {}).get("claimDomains", [])
            )
            and str(school_id) in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in coverage_source_ids
        ):
            report.error(f"{identity}: completed branch lacks school-bound official coverage evidence")
        if strict and row.get("status") == "candidates_found":
            for candidate_id in candidate_ids:
                if candidate_id not in record_map:
                    continue
                if not any(
                    source_map.get(source_id, {}).get("authorityClass")
                    == "official_institution"
                    and source_map.get(source_id, {}).get("status") == "current"
                    and {"research", "current_role"}.intersection(
                        source_map.get(source_id, {}).get("claimDomains", [])
                    )
                    and candidate_id in source_map.get(source_id, {}).get("subjectIds", [])
                    for source_id in coverage_source_ids
                ):
                    report.error(
                        f"{identity}: candidate {candidate_id} lacks a candidate-bound current official "
                        "research/current_role source in this coverage row"
                    )
        if row.get("status") == "blocked_unverified" and not str(row.get("notes", "")).strip():
            report.error(f"{identity}: blocked_unverified requires an explanatory note")
    for school_id in school_map:
        rows = grouped.get(school_id, [])
        area_counts = Counter(str(row.get("area")) for row in rows)
        missing = COVERAGE_AREAS - set(area_counts)
        duplicate = {area: count for area, count in area_counts.items() if count > 1}
        if missing:
            report.error(f"School {school_id}: missing coverage areas {sorted(missing)}")
        if duplicate:
            report.error(f"School {school_id}: duplicate coverage areas {duplicate}")
    represented_by_school: defaultdict[str, set[str]] = defaultdict(set)
    for row in coverage:
        school_id = str(row.get("schoolId", ""))
        candidate_ids = row.get("candidateIds", [])
        if isinstance(candidate_ids, list):
            represented_by_school[school_id].update(str(item) for item in candidate_ids)
    for candidate_id, record in record_map.items():
        # A D-tier discovery lead can be retained solely to document how a
        # name entered the pool.  Without any substantive current role or
        # research source it must not be presented as a found branch result.
        if (
            record.get("priorityTier") == "D"
            and not record.get("currentRoleSourceIds")
            and not record.get("researchSourceIds")
        ):
            continue
        for school_id in candidate_school_ids(record):
            if candidate_id not in represented_by_school.get(school_id, set()):
                message = (
                    f"Candidate {candidate_id} is not mapped to a coverage branch for school {school_id}"
                )
                if strict:
                    report.error(message)
                else:
                    report.warn(message)


def validate_completion_semantics(
    case: dict, coverage: list[dict], strict: bool, report: Report
) -> None:
    """Keep package completion separate from evidence of branch exhaustion."""
    if not strict or case.get("status") != "complete":
        return
    blocked = [row for row in coverage if row.get("status") == "blocked_unverified"]
    if not blocked:
        return
    limitations_text = "\n".join(
        str(item) for item in case.get("limitations", []) if str(item).strip()
    )
    if not re.search(
        r"(?i)\b(?:bounded|non[- ]?exhaustive|not exhaustive|access gap|access limit)\b|"
        r"(?:不表示|不能|并非|不是)[^。；;]{0,30}(?:穷尽|全覆盖|无遗漏)|"
        r"(?:访问限制|覆盖缺口|非穷尽)",
        limitations_text,
    ):
        report.error(
            "case.json status=complete with blocked coverage requires a limitation stating that "
            "completion means package generation, not exhaustive branch coverage"
        )
    passes = case.get("discoveryPasses", [])
    final_pass = passes[-1] if isinstance(passes, list) and passes else {}
    queries = final_pass.get("queriesOrUnits", []) if isinstance(final_pass, dict) else []
    saturation_text = "\n".join(str(item) for item in queries) if isinstance(queries, list) else ""
    if not re.search(
        r"(?i)\b(?:attempt(?:ed)?|recheck(?:ed)?|re-check(?:ed)?|retry|retried|repeat(?:ed)?)\b|"
        r"(?:再次尝试|重新尝试|重试|复核|复查|补查|重新核查)",
        saturation_text,
    ):
        report.error(
            "The final saturation pass must document an attempted/rechecked search of blocked "
            "branches; zero additions alone do not establish exhaustion"
        )


def personal_email_matches_candidate(value: str, candidate_name: str) -> bool:
    """Require a personal/clinical mailbox to visibly identify the candidate."""
    local = normalized_search_text(value.split("@", 1)[0])
    compact_local = re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", local)
    german_variant = (
        str(candidate_name).casefold()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    normalized_names = {normalized_search_text(candidate_name), normalized_search_text(german_variant)}
    name_tokens = {
        token
        for normalized_name in normalized_names
        for token in re.findall(r"[a-z0-9]+|[\u3400-\u9fff]{2,}", normalized_name)
        if len(token) >= 3
    }
    return any(
        token in local or re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", token) in compact_local
        for token in name_tokens
    )


def validate_contacts(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    contacts = record.get("contacts", [])
    if not isinstance(contacts, list):
        report.error(f"Candidate {identity}: contacts must be an array")
        return
    if not contacts:
        report.error(f"Candidate {identity}: add a published contact or explicit not_public entry")
    verified_at = parse_iso_date(record.get("verifiedAt"))
    for index, contact in enumerate(contacts):
        if not isinstance(contact, dict):
            report.error(f"Candidate {identity}: contact[{index}] must be an object")
            continue
        contact_type = contact.get("type")
        if contact_type not in CONTACT_TYPES:
            report.error(f"Candidate {identity}: invalid contact type {contact_type}")
        contact_status = contact.get("status")
        if contact_status not in CONTACT_STATUSES:
            report.error(f"Candidate {identity}: invalid contact status {contact_status}")
        elif contact_type == "not_public" and contact_status != "not_public":
            report.error(f"Candidate {identity}: not_public contact requires status=not_public")
        elif contact_type != "not_public" and strict and contact_status != "published_current":
            report.error(f"Candidate {identity}: deliverable contact must be published_current")
        source_ids = validate_string_list(
            contact.get("sourceIds", []),
            f"Candidate {identity}: contact[{index}].sourceIds",
            report,
            required=contact_type != "not_public",
        )
        if strict and contact_type != "not_public":
            allowed_subjects = (
                {identity}
                if contact_type in {"personal_email", "clinical_email"}
                else {identity, *candidate_school_ids(record)}
            )
            atomic_contact_sources = [
                source_map.get(source_id, {})
                for source_id in source_ids
                if source_map.get(source_id, {}).get("authorityClass")
                == "official_institution"
                and "contact" in source_map.get(source_id, {}).get("claimDomains", [])
                and source_map.get(source_id, {}).get("status") == "current"
                and allowed_subjects.intersection(
                    source_map.get(source_id, {}).get("subjectIds", [])
                )
            ]
            if not atomic_contact_sources:
                if contact_type in {"personal_email", "clinical_email"}:
                    report.error(
                        f"Candidate {identity}: contact[{index}] personal/clinical contact needs one same "
                        "candidate-bound official current contact source"
                    )
                else:
                    report.error(
                        f"Candidate {identity}: contact[{index}] lacks one same official current "
                        "contact-domain source bound to the candidate or affiliated school"
                    )
        value = str(contact.get("value", "")).strip()
        if strict and contact_type in {"personal_email", "clinical_email"} and value:
            local_part = normalized_search_text(value.split("@", 1)[0])
            if any(pattern.search(local_part) for pattern in GENERIC_PERSONAL_MAILBOX_PATTERNS):
                report.error(
                    f"Candidate {identity}: contact[{index}] is an obvious unit/secretariat mailbox; "
                    "use unit_email, department_mailbox, group_email, secretariat_email, or assistant_contact"
                )
            if not personal_email_matches_candidate(value, str(record.get("name", ""))):
                report.error(
                    f"Candidate {identity}: contact[{index}] personal/clinical email does not identify the "
                    "candidate and may belong to another person; use assistant_contact/unit_email as appropriate"
                )
        if strict and contact_type != "not_public" and verified_at and any(
            (parse_iso_date(source_map.get(source_id, {}).get("accessedDate")) or dt.date.min)
            > verified_at
            for source_id in source_ids
        ):
            report.error(
                f"Candidate {identity}: contact[{index}] cites a source accessed after verifiedAt"
            )
        if contact_type == "not_public":
            if str(contact.get("value", "")).strip():
                report.error(f"Candidate {identity}: not_public contact must have a blank value")
            if source_ids:
                report.error(f"Candidate {identity}: not_public contact must not cite a source as if it published a value")
        else:
            if not str(contact.get("value", "")).strip():
                report.error(f"Candidate {identity}: {contact_type} has no value")
        if contact_type in {
            "personal_email",
            "clinical_email",
            "group_email",
            "unit_email",
            "department_mailbox",
            "secretariat_email",
            "assistant_contact",
        }:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
                report.error(f"Candidate {identity}: malformed email address {value}")


def direct_recent_count(
    record: dict, source_map: dict[str, dict], as_of: dt.date | None
) -> tuple[int, int]:
    direct_work_dates: dict[str, str] = {}
    cutoff = None
    if as_of:
        try:
            cutoff = as_of.replace(year=as_of.year - 5)
        except ValueError:
            cutoff = as_of.replace(year=as_of.year - 5, day=28)
    for source_id in record.get("directEvidenceIds", []):
        source = source_map.get(source_id, {})
        role = person_role_for(source, str(record.get("id", ""))) or {}
        published, precision = parse_partial_date(source.get("publishedDate"))
        if (
            role.get("topicRelevance") != "direct"
            or source.get("type") not in DIRECT_RESEARCH_SOURCE_TYPES
            or source.get("status") == "future"
            or (as_of and published and published > as_of)
        ):
            continue
        published_raw = str(source.get("publishedDate", ""))
        work_key = evidence_work_key(source)
        current = direct_work_dates.get(work_key, "")
        if work_key not in direct_work_dates or published_raw > current:
            direct_work_dates[work_key] = published_raw
    recent = 0
    for published_raw in direct_work_dates.values():
        published, precision = parse_partial_date(published_raw)
        # Partial dates are interpreted conservatively at the first day of the
        # stated month/year.  A bare 2021 therefore cannot be treated as recent
        # on a September 2026 audit merely because the years match.
        if cutoff and published and precision != "invalid" and published >= cutoff:
            recent += 1
    return len(direct_work_dates), recent


def validate_recruitment_audit(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    as_of: dt.date | None,
    report: Report,
) -> set[str]:
    audit = record.get("recruitmentAudit")
    if not isinstance(audit, dict):
        report.error(
            f"Candidate {identity}: {record.get('opportunityStatus')} requires recruitmentAudit"
        )
        return set()
    checked_at = parse_iso_date(audit.get("checkedAt"))
    if checked_at is None:
        report.error(f"Candidate {identity}: recruitmentAudit.checkedAt must use YYYY-MM-DD")
    elif as_of and checked_at > as_of:
        report.error(f"Candidate {identity}: recruitmentAudit.checkedAt is later than case asOf")
    elif as_of:
        age_days = (as_of - checked_at).days
        if age_days > 90:
            report.error(
                f"Candidate {identity}: recruitment audit is {age_days} days old; recheck public routes"
            )
        elif age_days > 30:
            report.warn(f"Candidate {identity}: recruitment audit is {age_days} days old")
    portals = audit.get("portals", [])
    if not isinstance(portals, list) or not portals:
        report.error(f"Candidate {identity}: recruitmentAudit.portals must be a non-empty array")
        portals = []
    portal_source_ids: set[str] = set()
    for portal_index, portal in enumerate(portals):
        path = f"Candidate {identity}: recruitmentAudit.portals[{portal_index}]"
        if not isinstance(portal, dict):
            report.error(f"{path} must be an object")
            continue
        for field in ["name", "result"]:
            if not str(portal.get(field, "")).strip():
                report.error(f"{path} missing {field}")
        ids = validate_string_list(
            portal.get("sourceIds", []), f"{path}.sourceIds", report, required=True
        )
        portal_source_ids.update(ids)
        if not any(
            source_map.get(source_id, {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and {"recruitment", "contact", "doctoral_rule", "admissions_funding"}.intersection(
                source_map.get(source_id, {}).get("claimDomains", [])
            )
            and {identity, *candidate_school_ids(record)}.intersection(
                source_map.get(source_id, {}).get("subjectIds", [])
            )
            for source_id in ids
        ):
            report.error(f"{path} lacks an official source bound to the candidate or school")
    validate_string_list(
        audit.get("checkedScopes", []),
        f"Candidate {identity}: recruitmentAudit.checkedScopes",
        report,
        required=True,
    )
    validate_string_list(
        audit.get("queries", []),
        f"Candidate {identity}: recruitmentAudit.queries",
        report,
        required=True,
    )
    source_ids = validate_string_list(
        audit.get("sourceIds", []),
        f"Candidate {identity}: recruitmentAudit.sourceIds",
        report,
        required=True,
    )
    if not str(audit.get("summary", "")).strip():
        report.error(f"Candidate {identity}: recruitmentAudit.summary is required")
    if portal_source_ids - set(source_ids):
        report.error(f"Candidate {identity}: recruitmentAudit.sourceIds must include every portal source")
    if checked_at and any(
        (parse_iso_date(source_map.get(source_id, {}).get("accessedDate")) or dt.date.max) > checked_at
        for source_id in source_ids
    ):
        report.error(
            f"Candidate {identity}: recruitmentAudit cites a source accessed after checkedAt"
        )
    official_audit_sources = [
        source_map.get(source_id, {})
        for source_id in source_ids
        if source_map.get(source_id, {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
        and {"recruitment", "contact", "doctoral_rule", "admissions_funding"}.intersection(
            source_map.get(source_id, {}).get("claimDomains", [])
        )
    ]
    if not official_audit_sources:
        report.error(
            f"Candidate {identity}: recruitmentAudit needs an official vacancy-portal or contact-policy source"
        )
    elif not any(
        source.get("type") == "official_vacancy_portal"
        and source.get("status") == "current"
        and "recruitment" in source.get("claimDomains", [])
        and {identity, *candidate_school_ids(record)}.intersection(source.get("subjectIds", []))
        and parse_iso_date(source.get("accessedDate")) == checked_at
        for source in official_audit_sources
    ):
        report.error(
            f"Candidate {identity}: negative/route-only recruitment audit needs a current official vacancy portal bound to the candidate or school and accessed on checkedAt"
        )
    return set(source_ids)


def validate_opportunities(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    as_of: dt.date | None,
    strict: bool,
    report: Report,
) -> None:
    summary_status = record.get("opportunityStatus")
    recruitment_ids = validate_string_list(
        record.get("recruitmentSourceIds", []),
        f"Candidate {identity}: recruitmentSourceIds",
        report,
    )
    opportunities = record.get("opportunities", [])
    if not isinstance(opportunities, list):
        report.error(f"Candidate {identity}: opportunities must be an array")
        opportunities = []
    if strict and not opportunities:
        report.error(f"Candidate {identity}: strict schema 1.2 requires at least one opportunity route")

    opportunity_ids: set[str] = set()
    opportunity_statuses: set[str] = set()
    opportunity_scopes: set[str] = set()
    opportunity_source_ids: set[str] = set()
    fixed_deadlines_for_summary: set[str] = set()
    for index, opportunity in enumerate(opportunities):
        path = f"Candidate {identity}: opportunities[{index}]"
        if not isinstance(opportunity, dict):
            report.error(f"{path} must be an object")
            continue
        opportunity_id = str(opportunity.get("id", "")).strip()
        if not opportunity_id:
            report.error(f"{path} missing id")
        elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", opportunity_id):
            report.error(f"{path}.id must be a lowercase ASCII slug")
        elif opportunity_id in opportunity_ids:
            report.error(f"Candidate {identity}: duplicate opportunity id {opportunity_id}")
        opportunity_ids.add(opportunity_id)
        if opportunity.get("scope") not in OPPORTUNITY_SCOPES:
            report.error(f"{path}.scope is invalid")
        else:
            opportunity_scopes.add(str(opportunity.get("scope")))
        if str(opportunity.get("detail", "")).strip():
            report.error(f"{path}.detail is unsupported; use the validated contactPolicy field")
        for field in ["routeName", "contactPolicy"]:
            if not str(opportunity.get(field, "")).strip():
                report.error(f"{path} missing {field}")
        status = opportunity.get("status")
        if status not in OPPORTUNITY_STATUSES:
            report.error(f"{path}.status is invalid")
        else:
            opportunity_statuses.add(str(status))
        deadline_type = opportunity.get("deadlineType")
        if deadline_type not in DEADLINE_TYPES:
            report.error(f"{path}.deadlineType is invalid")
        deadline_text = str(opportunity.get("deadline", "")).strip()
        deadline = parse_iso_date(deadline_text) if deadline_text else None
        if deadline_type == "fixed" and deadline is None:
            report.error(f"{path}.deadline must use YYYY-MM-DD when deadlineType=fixed")
        elif deadline_text and deadline is None:
            report.error(f"{path}.deadline must use YYYY-MM-DD or be blank")
        if deadline_type != "fixed" and deadline_text:
            report.error(f"{path}.deadline must be blank unless deadlineType=fixed")
        if deadline and as_of and status in {"open_current", "planned_official"} and deadline <= as_of:
            report.error(f"{path}.deadline must be later than case asOf for {status}")
        if deadline and as_of and status == "closed_expired" and deadline > as_of:
            report.error(f"{path}.deadline is still in the future but status is closed_expired")
        if status in {"open_current", "planned_official"} and deadline_type == "not_applicable":
            report.error(f"{path}.deadlineType cannot be not_applicable for {status}")
        if status in {
            "route_confirmed_no_vacancy",
            "no_public_evidence",
            "direct_enquiry_recommended",
            "unverified",
        } and deadline_type == "fixed":
            report.error(f"{path}.deadlineType cannot be fixed for {status}")
        if status == summary_status and deadline_type == "fixed" and deadline_text:
            fixed_deadlines_for_summary.add(deadline_text)

        source_ids = validate_string_list(
            opportunity.get("sourceIds", []), f"{path}.sourceIds", report, required=True
        )
        opportunity_source_ids.update(source_ids)
        cited = [source_map.get(source_id, {}) for source_id in source_ids]
        official_vacancies = [
            source
            for source in cited
            if source.get("type") == "vacancy"
            and source.get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and "recruitment" in source.get("claimDomains", [])
        ]
        if status == "open_current":
            current_vacancies = [
                source for source in official_vacancies if source.get("status") == "current"
            ]
            if not current_vacancies:
                report.error(f"{path}: open_current requires a current official vacancy posting")
            elif opportunity.get("scope") == "person" and not any(
                identity in source.get("subjectIds", []) for source in current_vacancies
            ):
                report.error(
                    f"{path}: person-scoped vacancy source must list candidate ID in subjectIds"
                )
            elif opportunity.get("scope") == "lab" and not any(
                identity in source.get("subjectIds", [])
                for source in current_vacancies
            ):
                report.error(
                    f"{path}: lab-scoped vacancy source must bind the candidate until a validated lab registry exists"
                )
        if status == "planned_official" and not any(
            source.get("status") == "future" for source in official_vacancies
        ):
            report.error(f"{path}: planned_official requires a future official vacancy/call")
        if status == "closed_expired" and not any(
            source.get("status") == "closed" for source in official_vacancies
        ):
            report.error(f"{path}: closed_expired requires a closed official vacancy posting")
        if status == "historical_only" and not any(
            source.get("status") in {"historical", "closed"} for source in cited
        ):
            report.error(f"{path}: historical_only needs historical recruitment evidence")
        if status == "route_confirmed_no_vacancy" and not any(
            source.get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and "doctoral_rule" in source.get("claimDomains", [])
            and {identity, *candidate_school_ids(record)}.intersection(source.get("subjectIds", []))
            for source in cited
        ):
            report.error(f"{path}: route_confirmed_no_vacancy needs doctoral-route evidence")

    if opportunities and summary_status not in opportunity_statuses:
        report.error(
            f"Candidate {identity}: opportunityStatus is not represented in opportunities[]"
        )
    missing_from_summary = opportunity_source_ids - set(recruitment_ids)
    if strict and missing_from_summary:
        report.error(
            f"Candidate {identity}: recruitmentSourceIds omits opportunity sources {sorted(missing_from_summary)}"
        )
    summary_deadline = str(record.get("opportunityDeadline", "")).strip()
    if fixed_deadlines_for_summary and not summary_deadline:
        report.error(
            f"Candidate {identity}: opportunityDeadline must summarize its fixed-date route"
        )
    if summary_deadline:
        if parse_iso_date(summary_deadline) is None:
            report.error(f"Candidate {identity}: opportunityDeadline must use YYYY-MM-DD or be blank")
        elif fixed_deadlines_for_summary and summary_deadline not in fixed_deadlines_for_summary:
            report.error(
                f"Candidate {identity}: opportunityDeadline does not match its summarized fixed route"
            )
    if strict and str(record.get("opportunityDetail", "")).strip():
        report.error(
            f"Candidate {identity}: opportunityDetail is unsupported in strict schema 1.2; use opportunities[].contactPolicy"
        )

    audit_source_ids: set[str] = set()
    audited_statuses = {
        "route_confirmed_no_vacancy",
        "no_public_evidence",
        "direct_enquiry_recommended",
    }
    direct_enquiry_used = (
        summary_status == "direct_enquiry_recommended"
        or "direct_enquiry_recommended" in opportunity_statuses
    )
    if strict and direct_enquiry_used:
        role_confidence = str(record.get("confidenceByClaim", {}).get("currentRole", ""))
        current_role_sources = [
            source_map.get(str(source_id), {})
            for source_id in record.get("currentRoleSourceIds", [])
            if str(source_id)
        ]
        has_verified_current_role = any(
            source.get("authorityClass") == "official_institution"
            and source.get("status") == "current"
            and "current_role" in source.get("claimDomains", [])
            and identity in source.get("subjectIds", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            in CURRENT_CONTACTABLE_ROLE_TYPES
            for source in current_role_sources
        )
        has_published_contact = any(
            isinstance(contact, dict)
            and contact.get("type") != "not_public"
            and contact.get("status") == "published_current"
            and str(contact.get("value", "")).strip()
            for contact in record.get("contacts", [])
        ) if isinstance(record.get("contacts"), list) else False
        route_source_ids = {
            *[str(item) for item in record.get("doctoralSourceIds", []) if str(item)],
            *recruitment_ids,
            *opportunity_source_ids,
        }
        route_subjects = {identity, *candidate_school_ids(record)}
        has_official_route = any(
            source_map.get(source_id, {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and source_map.get(source_id, {}).get("status") == "current"
            and {"doctoral_rule", "recruitment"}.intersection(
                source_map.get(source_id, {}).get("claimDomains", [])
            )
            and route_subjects.intersection(source_map.get(source_id, {}).get("subjectIds", []))
            for source_id in route_source_ids
        )
        reasons: list[str] = []
        if record.get("priorityTier") == "D":
            reasons.append("D-tier record")
        if role_confidence not in {"high", "medium"} or not has_verified_current_role:
            reasons.append("current personal role is not verified")
        if not has_published_contact:
            reasons.append("no published contact channel")
        if not has_official_route:
            reasons.append("no current official doctoral/recruitment route")
        if reasons:
            report.error(
                f"Candidate {identity}: direct_enquiry_recommended is not evidence-neutral for "
                f"{', '.join(reasons)}; use no_public_evidence or unverified instead"
            )
    if summary_status in audited_statuses or opportunity_statuses.intersection(audited_statuses):
        audit_source_ids = validate_recruitment_audit(
            record, identity, source_map, as_of, report
        )
        checked_scopes = set(record.get("recruitmentAudit", {}).get("checkedScopes", []))
        audited_route_scopes = {
            str(item.get("scope"))
            for item in opportunities
            if isinstance(item, dict) and item.get("status") in audited_statuses
        }
        if not audited_route_scopes.issubset(checked_scopes):
            report.error(
                f"Candidate {identity}: recruitmentAudit.checkedScopes does not cover audited opportunity scopes {sorted(audited_route_scopes)}"
            )
    if strict and audit_source_ids - set(recruitment_ids):
        report.error(
            f"Candidate {identity}: recruitmentSourceIds omits recruitmentAudit sources "
            f"{sorted(audit_source_ids - set(recruitment_ids))}"
        )

    # Compatibility fallback for pre-1.2 draft data: still prevent unsupported
    # top-level recruitment claims even before opportunities[] is populated.
    if not opportunities:
        cited = [source_map.get(source_id, {}) for source_id in recruitment_ids]
        if summary_status == "open_current" and not any(
            source.get("type") == "vacancy"
            and source.get("authorityClass") == "official_institution"
            and "recruitment" in source.get("claimDomains", [])
            and source.get("status") == "current"
            for source in cited
        ):
            report.error(f"Candidate {identity}: open_current lacks a current official vacancy source")
        if summary_status == "planned_official" and not any(
            source.get("type") == "vacancy" and source.get("status") == "future"
            for source in cited
        ):
            report.error(f"Candidate {identity}: planned_official lacks a future official vacancy/call")
        if summary_status == "closed_expired" and not any(
            source.get("type") == "vacancy" and source.get("status") == "closed"
            for source in cited
        ):
            report.error(f"Candidate {identity}: closed_expired lacks a closed vacancy source")
        if summary_status == "historical_only" and not any(
            source.get("status") in {"historical", "closed"} for source in cited
        ):
            report.error(f"Candidate {identity}: historical_only lacks historical recruitment evidence")
        if summary_status == "route_confirmed_no_vacancy" and not record.get("doctoralSourceIds"):
            report.error(f"Candidate {identity}: route_confirmed_no_vacancy lacks doctoral-route evidence")


def validate_affiliations(
    record: dict,
    identity: str,
    school_map: dict[str, dict],
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> set[str]:
    primary_school_id = str(record.get("schoolId", "")).strip()
    if strict and "additionalSchoolIds" not in record:
        report.error(f"Candidate {identity}: strict schema 1.2 requires additionalSchoolIds[]")
    additional_ids = validate_string_list(
        record.get("additionalSchoolIds", []),
        f"Candidate {identity}: additionalSchoolIds",
        report,
    )
    if primary_school_id in additional_ids:
        report.error(f"Candidate {identity}: additionalSchoolIds repeats primary schoolId")
    declared_school_ids = {primary_school_id, *additional_ids}
    declared_school_ids.discard("")
    for school_id in declared_school_ids:
        if school_id not in school_map:
            report.error(f"Candidate {identity}: unknown affiliated schoolId {school_id}")

    affiliations = record.get("affiliations", [])
    if not isinstance(affiliations, list):
        report.error(f"Candidate {identity}: affiliations must be an array")
        affiliations = []
    if strict and not affiliations and record.get("priorityTier") != "D":
        report.error(f"Candidate {identity}: A/B/C records require affiliations[]")
    if strict and not affiliations and record.get("priorityTier") == "D":
        if record.get("currentRoleSourceIds"):
            report.error(
                f"Candidate {identity}: D-tier record with no affiliations must not retain "
                "currentRoleSourceIds"
            )
        if not is_explicit_missing(record.get("academicRole")):
            report.error(
                f"Candidate {identity}: D-tier record with no affiliations needs an explicit "
                "unverified academicRole marker"
            )
    represented_school_ids: set[str] = set()
    seen_affiliations: set[tuple[str, str, str, str, str, str]] = set()
    for index, affiliation in enumerate(affiliations):
        path = f"Candidate {identity}: affiliations[{index}]"
        if not isinstance(affiliation, dict):
            report.error(f"{path} must be an object")
            continue
        school_id = str(affiliation.get("schoolId", "")).strip()
        if not school_id:
            report.error(f"{path} missing schoolId")
        elif school_id not in school_map:
            report.error(f"{path} has unknown schoolId {school_id}")
        else:
            represented_school_ids.add(school_id)
        for field in ["institution", "faculty", "department", "relationship", "role"]:
            if not str(affiliation.get(field, "")).strip():
                report.error(f"{path} missing {field}; use an explicit not_applicable marker if needed")
        key = (
            school_id,
            str(affiliation.get("institution", "")).strip().casefold(),
            str(affiliation.get("faculty", "")).strip().casefold(),
            str(affiliation.get("department", "")).strip().casefold(),
            str(affiliation.get("relationship", "")).strip().casefold(),
            str(affiliation.get("role", "")).strip().casefold(),
        )
        if key in seen_affiliations:
            report.error(f"{path} duplicates another affiliation")
        seen_affiliations.add(key)
        source_ids = validate_string_list(
            affiliation.get("sourceIds", []), f"{path}.sourceIds", report, required=True
        )
        role_source_statuses = {"current"} if record.get("priorityTier") in {"A", "B", "C"} else {
            "current",
            "future",
            "historical",
        }
        if strict and not any(
            source_map.get(source_id, {}).get("authorityClass") == "official_institution"
            and source_map.get(source_id, {}).get("status") in role_source_statuses
            and "current_role" in source_map.get(source_id, {}).get("claimDomains", [])
            and identity in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in source_ids
        ):
            report.error(f"{path} lacks a current official affiliation source")
        if strict and school_id and school_id != primary_school_id and not any(
            source_map.get(source_id, {}).get("authorityClass") == "official_institution"
            and source_map.get(source_id, {}).get("status") == "current"
            and "current_role" in source_map.get(source_id, {}).get("claimDomains", [])
            and identity in source_map.get(source_id, {}).get("subjectIds", [])
            and school_id in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in source_ids
        ):
            report.error(
                f"{path} cross-school affiliation requires one current official institution "
                f"source whose subjectIds include both candidate ID and additionalSchoolId {school_id}"
            )
        if strict and not is_explicit_missing(affiliation.get("role")):
            allowed_affiliation_roles = set().union(*ROLE_FIELD_ALLOWED_PERSON_ROLE_TYPES.values())
            if not any(
                source_map.get(source_id, {}).get("authorityClass") == "official_institution"
                and source_map.get(source_id, {}).get("status") in role_source_statuses
                and (person_role_for(source_map.get(source_id, {}), identity) or {}).get("roleType")
                in allowed_affiliation_roles
                and person_role_is_specific(source_map.get(source_id, {}), identity)
                for source_id in source_ids
            ):
                report.error(
                    f"{path}.role is concrete but all cited person-role evidence is non-specific or incompatible"
                )
    if affiliations and represented_school_ids != declared_school_ids:
        report.error(
            f"Candidate {identity}: affiliations school set must match schoolId + additionalSchoolIds "
            f"(declared={sorted(declared_school_ids)}, represented={sorted(represented_school_ids)})"
        )
    return declared_school_ids


def validate_social_check(
    record: dict,
    identity: str,
    check_name: str,
    source_map: dict[str, dict],
    as_of: dt.date | None,
    strict: bool,
    report: Report,
) -> None:
    check = record.get(check_name)
    if not isinstance(check, dict):
        report.error(f"Candidate {identity}: {check_name} must be an object")
        return
    status = check.get("status")
    if status not in CHECK_STATUSES:
        report.error(f"Candidate {identity}: invalid {check_name} status")
    if strict and status == "not_searched":
        report.error(f"Candidate {identity}: {check_name} remains not_searched in strict mode")
    checked_at = parse_iso_date(check.get("checkedAt"))
    if strict and checked_at is None:
        report.error(f"Candidate {identity}: {check_name}.checkedAt must use YYYY-MM-DD")
    elif checked_at and as_of and checked_at > as_of:
        report.error(f"Candidate {identity}: {check_name}.checkedAt is later than case asOf")
    elif strict and checked_at and as_of:
        age_days = (as_of - checked_at).days
        if age_days > 90:
            report.error(
                f"Candidate {identity}: {check_name} is {age_days} days old; repeat the check"
            )
        elif age_days > 30:
            report.warn(f"Candidate {identity}: {check_name} is {age_days} days old")
    queries = validate_string_list(
        check.get("queries", []),
        f"Candidate {identity}: {check_name}.queries",
        report,
        required=strict,
    )
    minimum_queries = 2 if check_name == "xiaohongshuCheck" else 3
    if strict and len(queries) < minimum_queries:
        report.error(
            f"Candidate {identity}: {check_name} needs at least {minimum_queries} recorded query variants"
        )
    if strict and not str(check.get("summary", "")).strip():
        report.error(f"Candidate {identity}: {check_name}.summary is required")
    if strict and not str(check.get("accessNote", "")).strip():
        report.error(f"Candidate {identity}: {check_name}.accessNote is required")
    access_text = " ".join(
        [str(check.get("summary", "")), str(check.get("accessNote", ""))]
    ).casefold()
    blocked_markers = ["blocked", "inaccessible", "login", "logged-in", "private", "无法访问", "登录", "受限"]
    if (
        strict
        and check_name == "xiaohongshuCheck"
        and any(marker in access_text for marker in blocked_markers)
        and status != "public_access_blocked"
    ):
        report.error(
            f"Candidate {identity}: Xiaohongshu access limitation requires status=public_access_blocked"
        )
    source_ids = validate_string_list(
        check.get("sourceIds", []),
        f"Candidate {identity}: {check_name}.sourceIds",
        report,
        required=status in {"verified_source_found", "lead_only"},
    )
    if checked_at and any(
        (parse_iso_date(source_map.get(source_id, {}).get("accessedDate")) or dt.date.max) > checked_at
        for source_id in source_ids
    ):
        report.error(f"Candidate {identity}: {check_name} cites a source accessed after checkedAt")
    if strict and source_ids and checked_at and not any(
        parse_iso_date(source_map.get(source_id, {}).get("accessedDate")) == checked_at
        for source_id in source_ids
    ):
        report.error(f"Candidate {identity}: {check_name} needs at least one cited source accessed on checkedAt")
    if strict and check_name == "xiaohongshuCheck" and status == "verified_source_found":
        if not any(
            source_map.get(source_id, {}).get("type") == "social_user_generated"
            for source_id in source_ids
        ):
            report.error(
                f"Candidate {identity}: verified Xiaohongshu result needs a social_user_generated source"
            )
    if strict and status in {"verified_source_found", "lead_only"} and not any(
        identity in source_map.get(source_id, {}).get("subjectIds", []) for source_id in source_ids
    ):
        report.error(
            f"Candidate {identity}: {check_name} result lacks a person-bound source"
        )


def validate_conflicts(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    as_of: dt.date | None,
    report: Report,
) -> None:
    conflicts = record.get("conflicts", [])
    if not isinstance(conflicts, list):
        report.error(f"Candidate {identity}: conflicts must be an array")
        return
    for conflict_index, conflict in enumerate(conflicts):
        path = f"Candidate {identity}: conflict[{conflict_index}]"
        if not isinstance(conflict, dict):
            report.error(f"{path} must be an object")
            continue
        category = conflict.get("category")
        if category not in CONFLICT_CATEGORIES:
            report.error(f"{path} has invalid category {category}")
        for field in ["field", "officialValue", "otherValue", "decision"]:
            if not str(conflict.get(field, "")).strip():
                report.error(f"{path} missing {field}")
        effective_text = str(conflict.get("effectiveDate", "")).strip()
        effective_date = parse_iso_date(effective_text) if effective_text else None
        if category == "announced_future_change" and effective_date is None:
            report.error(f"{path}.effectiveDate must use YYYY-MM-DD for a future change")
        elif effective_text and effective_date is None:
            report.error(f"{path}.effectiveDate must use YYYY-MM-DD or be blank")
        elif category == "announced_future_change" and effective_date and as_of and effective_date <= as_of:
            report.error(f"{path}: effectiveDate has passed; reclassify and reverify the current role")
        refs = validate_string_list(
            conflict.get("sourceIds", []), f"{path}.sourceIds", report, required=True
        )
        required_refs = 1 if category == "low_confidence_unverifiable" else 2
        if len(refs) < required_refs:
            report.error(f"{path} needs {required_refs} unique source(s)")
        if category != "low_confidence_unverifiable":
            work_keys = [evidence_work_key(source_map[source_id]) for source_id in refs if source_id in source_map]
            if len(work_keys) != len(set(work_keys)):
                report.error(f"{path} cites duplicate underlying evidence rather than two sides")
        if category == "announced_future_change" and not any(
            source_map.get(source_id, {}).get("status") == "future" for source_id in refs
        ):
            report.error(f"{path} needs a source explicitly marked future")
        if category != "low_confidence_unverifiable" and refs and not any(
            source_map.get(source_id, {}).get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and "conflict" in source_map.get(source_id, {}).get("claimDomains", [])
            for source_id in refs
        ):
            report.error(f"{path} lacks an official conflict-domain source for officialValue")


def validate_application_readiness(
    record: dict, identity: str, source_map: dict[str, dict], report: Report
) -> None:
    ready = record.get("applicationReadiness")
    if not isinstance(ready, dict):
        report.error(f"Candidate {identity}: applicationReadiness must be an object")
        return
    validate_no_correspondence(
        ready,
        f"Candidate {identity}: applicationReadiness",
        report,
    )
    for field in [
        "contactProtocol",
        "applicationWindow",
        "eligibilityRequirements",
        "requiredDocuments",
        "proposalRequirement",
        "fundingModel",
        "supervisionSetup",
        "researchAnchor",
        "researchGap",
        "proposedAim",
        "generalApplicantFit",
    ]:
        if not str(ready.get(field, "")).strip():
            report.error(f"Candidate {identity}: applicationReadiness missing {field}")
    for field in ["researchGapAnalystDerived", "proposedAimAnalystDerived", "generalApplicantFitAnalystDerived"]:
        if ready.get(field) is not True:
            report.error(f"Candidate {identity}: applicationReadiness.{field} must be true")
    for field in ["researchGap", "proposedAim", "generalApplicantFit"]:
        text = str(ready.get(field, ""))
        if len(text) > 1200:
            report.error(f"Candidate {identity}: applicationReadiness.{field} exceeds the bounded handoff limit")
    for field in ["doctoralQuestions", "resourceQuestions", "fundingQuestions"]:
        validate_string_list(
            ready.get(field, []),
            f"Candidate {identity}: applicationReadiness.{field}",
            report,
            required=True,
        )
    anchor_ids = validate_string_list(
        ready.get("anchorSourceIds", []),
        f"Candidate {identity}: applicationReadiness.anchorSourceIds",
        report,
        required=True,
    )
    gap_ids = validate_string_list(
        ready.get("gapSourceIds", []),
        f"Candidate {identity}: applicationReadiness.gapSourceIds",
        report,
        required=True,
    )
    for field, source_ids in [("anchorSourceIds", anchor_ids), ("gapSourceIds", gap_ids)]:
        if not any(
            identity in source_map.get(source_id, {}).get("subjectIds", [])
            and "research" in source_map.get(source_id, {}).get("claimDomains", [])
            for source_id in source_ids
        ):
            report.error(
                f"Candidate {identity}: applicationReadiness.{field} needs candidate-bound research evidence"
            )
    application_ids = validate_string_list(
        ready.get("applicationSourceIds", []),
        f"Candidate {identity}: applicationReadiness.applicationSourceIds",
        report,
        required=True,
    )
    proposal_ids = validate_string_list(
        ready.get("proposalSourceIds", []),
        f"Candidate {identity}: applicationReadiness.proposalSourceIds",
        report,
        required=not is_explicit_missing(ready.get("proposalRequirement")),
    )
    funding_ids = validate_string_list(
        ready.get("fundingSourceIds", []),
        f"Candidate {identity}: applicationReadiness.fundingSourceIds",
        report,
        required=not is_explicit_missing(ready.get("fundingModel")),
    )
    source_requirements = [
        ("applicationSourceIds", application_ids, {"doctoral_rule", "admissions_funding", "recruitment", "contact"}),
        ("proposalSourceIds", proposal_ids, {"doctoral_rule", "admissions_funding"}),
        ("fundingSourceIds", funding_ids, {"admissions_funding", "recruitment"}),
    ]
    for field, source_ids, allowed_domains in source_requirements:
        for source_id in source_ids:
            source = source_map.get(source_id, {})
            if source.get("authorityClass") not in OFFICIAL_SOURCE_AUTHORITIES:
                report.error(
                    f"Candidate {identity}: applicationReadiness.{field} contains a non-official source {source_id}"
                )
            if not allowed_domains.intersection(source.get("claimDomains", [])):
                report.error(
                    f"Candidate {identity}: applicationReadiness.{field} source {source_id} lacks "
                    f"one of the required claim domains {sorted(allowed_domains)}"
                )
            if not {identity, *candidate_school_ids(record)}.intersection(source.get("subjectIds", [])):
                report.error(
                    f"Candidate {identity}: applicationReadiness.{field} source {source_id} is not bound to the candidate or school"
                )
    claim_sources = ready.get("applicationClaimSourceIds")
    application_claim_domains = {
        "contactProtocol": {"contact", "recruitment", "doctoral_rule"},
        "applicationWindow": {"doctoral_rule", "admissions_funding", "recruitment"},
        "eligibilityRequirements": {"doctoral_rule", "admissions_funding"},
        "requiredDocuments": {"doctoral_rule", "admissions_funding"},
        "proposalRequirement": {"doctoral_rule", "admissions_funding"},
        "fundingModel": {"admissions_funding", "recruitment"},
        "supervisionSetup": {"current_role", "doctoral_rule", "doctoral_supervision"},
        "generalApplicantFit": {"research"},
    }
    if not isinstance(claim_sources, dict):
        report.error(f"Candidate {identity}: applicationReadiness.applicationClaimSourceIds must be an object")
        claim_sources = {}
    unknown_claims = set(claim_sources) - set(application_claim_domains)
    if unknown_claims:
        report.error(
            f"Candidate {identity}: applicationClaimSourceIds has unknown fields {sorted(unknown_claims)}"
        )
    for field, allowed_domains in application_claim_domains.items():
        required = not is_explicit_missing(ready.get(field))
        ids = validate_string_list(
            claim_sources.get(field, []),
            f"Candidate {identity}: applicationReadiness.applicationClaimSourceIds.{field}",
            report,
            required=required,
        )
        for source_id in ids:
            source = source_map.get(source_id, {})
            if source.get("authorityClass") not in OFFICIAL_SOURCE_AUTHORITIES and field != "generalApplicantFit":
                report.error(
                    f"Candidate {identity}: application claim {field} uses non-official source {source_id}"
                )
            if not allowed_domains.intersection(source.get("claimDomains", [])):
                report.error(
                    f"Candidate {identity}: application claim {field} source {source_id} lacks a relevant domain"
                )
            if field != "generalApplicantFit" and not {
                identity, *candidate_school_ids(record)
            }.intersection(source.get("subjectIds", [])):
                report.error(
                    f"Candidate {identity}: application claim {field} source {source_id} is not bound to the candidate or school"
                )
        if field == "generalApplicantFit" and ids and not any(
            identity in source_map.get(source_id, {}).get("subjectIds", []) for source_id in ids
        ):
            report.error(f"Candidate {identity}: generalApplicantFit lacks candidate-bound research evidence")
    supervision_ids = claim_sources.get("supervisionSetup", [])
    if isinstance(supervision_ids, list) and not is_explicit_missing(ready.get("supervisionSetup")):
        if not any(
            identity in source_map.get(source_id, {}).get("subjectIds", [])
            and "current_role" in source_map.get(source_id, {}).get("claimDomains", [])
            for source_id in supervision_ids
        ):
            report.error(f"Candidate {identity}: supervisionSetup lacks candidate-bound current-role evidence")
    validate_string_list(
        ready.get("cautions", []),
        f"Candidate {identity}: applicationReadiness.cautions",
        report,
        required=True,
        unique=False,
    )


def validate_supervision_basis(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    code = record.get("supervisionEvidence")
    basis = record.get("supervisionBasis")
    if not isinstance(basis, dict):
        if strict:
            report.error(f"Candidate {identity}: strict schema 1.2 requires supervisionBasis")
        return
    if basis.get("basisType") not in SUPERVISION_BASIS_TYPES:
        report.error(f"Candidate {identity}: supervisionBasis has invalid basisType")
    if basis.get("status") not in {
        "person_level_supported", "limited_person_level", "route_only_unverified"
    }:
        report.error(f"Candidate {identity}: supervisionBasis has invalid status")
    if basis.get("personSupervisionStatus") not in {
        "confirmed", "activity_supported", "co_supervision_supported", "unverified"
    }:
        report.error(f"Candidate {identity}: supervisionBasis has invalid personSupervisionStatus")
    if basis.get("eligibilityStatus") not in {"confirmed", "not_confirmed"}:
        report.error(f"Candidate {identity}: supervisionBasis has invalid eligibilityStatus")
    if not str(basis.get("summary", "")).strip():
        report.error(f"Candidate {identity}: supervisionBasis.summary is required")
    independence_ids = validate_string_list(
        basis.get("independenceSourceIds", []),
        f"Candidate {identity}: supervisionBasis.independenceSourceIds",
        report,
        required=code in {"S1", "S2"},
    )
    trainee_ids = validate_string_list(
        basis.get("traineeOrProgrammeSourceIds", []),
        f"Candidate {identity}: supervisionBasis.traineeOrProgrammeSourceIds",
        report,
        required=code in {"S1", "S2"},
    )
    if code in {"S1", "S2"}:
        if basis.get("status") != "person_level_supported":
            report.error(f"Candidate {identity}: {code} requires person_level_supported supervisionBasis")
        if not any(
            source_map.get(source_id, {}).get("authorityClass") == "official_institution"
            and source_map.get(source_id, {}).get("status") == "current"
            and "current_role" in source_map.get(source_id, {}).get("claimDomains", [])
            and identity in source_map.get(source_id, {}).get("subjectIds", [])
            and (person_role_for(source_map.get(source_id, {}), identity) or {}).get("roleType")
            in CURRENT_INDEPENDENT_ROLE_TYPES
            for source_id in independence_ids
        ):
            report.error(
                f"Candidate {identity}: {code} lacks candidate-bound current official independent-role evidence"
            )
        if not any(
            source_map.get(source_id, {}).get("authorityClass") == "official_institution"
            and identity in source_map.get(source_id, {}).get("subjectIds", [])
            for source_id in trainee_ids
        ):
            report.error(
                f"Candidate {identity}: {code} lacks candidate-bound official trainee/programme/supervision evidence"
            )
    if code == "S1":
        if basis.get("basisType") not in {
            "person_eligibility_explicit",
            "documented_thesis_supervision",
            "named_current_supervision",
            "named_supervisor_in_doctoral_posting",
        }:
            report.error(
                f"Candidate {identity}: S1 requires explicit eligibility or documented person-level supervision"
            )
        if basis.get("personSupervisionStatus") != "confirmed":
            report.error(f"Candidate {identity}: S1 requires personSupervisionStatus=confirmed")
        expected_eligibility = (
            "confirmed" if basis.get("basisType") == "person_eligibility_explicit" else "not_confirmed"
        )
        if basis.get("eligibilityStatus") != expected_eligibility:
            report.error(
                f"Candidate {identity}: S1 {basis.get('basisType')} requires eligibilityStatus={expected_eligibility}"
            )
        basis_type = basis.get("basisType")
        matching = [source_map.get(source_id, {}) for source_id in trainee_ids]
        if basis_type == "person_eligibility_explicit" and not any(
            source.get("type") == "doctoral_rule_supervision"
            and source.get("authorityClass") == "official_institution"
            and source.get("status") == "current"
            and "doctoral_rule" in source.get("claimDomains", [])
            and identity in source.get("subjectIds", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            == "eligible_supervisor"
            for source in matching
        ):
            report.error(
                f"Candidate {identity}: person_eligibility_explicit needs one same current official, "
                "candidate-bound doctoral-rule source with roleType=eligible_supervisor"
            )
        if basis_type == "documented_thesis_supervision" and not any(
            source.get("type") in {"doctoral_rule_supervision", "official_research_profile"}
            and "doctoral_supervision" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            in {"doctoral_supervisor", "co_supervisor"}
            for source in matching
        ):
            report.error(f"Candidate {identity}: documented_thesis_supervision needs an official thesis/supervision record")
        if basis_type == "named_current_supervision" and not any(
            source.get("status") == "current"
            and "doctoral_supervision" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            in {"doctoral_supervisor", "co_supervisor"}
            for source in matching
        ):
            report.error(
                f"Candidate {identity}: named_current_supervision needs a current official person-bound supervision record"
            )
        if basis_type == "named_supervisor_in_doctoral_posting" and not any(
            source.get("type") == "vacancy"
            and "recruitment" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            in {"doctoral_supervisor", "co_supervisor", "principal_investigator", "co_principal_investigator"}
            for source in matching
        ):
            report.error(f"Candidate {identity}: named_supervisor_in_doctoral_posting needs a named official vacancy")
    elif code == "S2":
        if basis.get("basisType") not in {
            "current_doctoral_trainees",
            "programme_pi_or_host",
        }:
            report.error(f"Candidate {identity}: S2 requires a person-level doctoral activity basisType")
        if basis.get("personSupervisionStatus") != "activity_supported":
            report.error(f"Candidate {identity}: S2 requires personSupervisionStatus=activity_supported")
        if basis.get("eligibilityStatus") != "not_confirmed":
            report.error(f"Candidate {identity}: S2 must keep eligibilityStatus=not_confirmed")
        matching = [source_map.get(source_id, {}) for source_id in trainee_ids]
        if basis.get("basisType") == "current_doctoral_trainees" and not any(
            source.get("status") == "current"
            and "doctoral_supervision" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("roleType")
            in ({"doctoral_supervisor"} | CURRENT_INDEPENDENT_ROLE_TYPES)
            for source in matching
        ):
            report.error(f"Candidate {identity}: current_doctoral_trainees needs a current official trainee roster")
        if basis.get("basisType") == "programme_pi_or_host" and not any(
            source.get("type") == "doctoral_rule_supervision"
            and source.get("status") == "current"
            and "doctoral_supervision" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("roleType") == "programme_host"
            for source in matching
        ):
            report.error(f"Candidate {identity}: programme_pi_or_host needs a current official programme-host listing")
    elif code == "S3":
        if basis.get("status") != "route_only_unverified":
            report.error(f"Candidate {identity}: S3 requires status=route_only_unverified")
        if basis.get("personSupervisionStatus") != "unverified":
            report.error(f"Candidate {identity}: S3 requires personSupervisionStatus=unverified")
        if basis.get("eligibilityStatus") != "not_confirmed":
            report.error(f"Candidate {identity}: S3 must keep eligibilityStatus=not_confirmed")
        if basis.get("basisType") != "unverified":
            report.error(f"Candidate {identity}: S3 requires basisType=unverified")
    elif code == "S4":
        if basis.get("basisType") == "co_supervision_only":
            if basis.get("status") != "limited_person_level" or basis.get("personSupervisionStatus") != "co_supervision_supported":
                report.error(f"Candidate {identity}: co-supervision-only S4 requires limited_person_level/co_supervision_supported")
            if not any(
                source_map.get(source_id, {}).get("authorityClass") == "official_institution"
                and "doctoral_supervision" in source_map.get(source_id, {}).get("claimDomains", [])
                and identity in source_map.get(source_id, {}).get("subjectIds", [])
                and (person_role_for(source_map.get(source_id, {}), identity) or {}).get("roleType") == "co_supervisor"
                for source_id in trainee_ids
            ):
                report.error(f"Candidate {identity}: co-supervision-only S4 lacks official person-bound co-supervision evidence")
        elif basis.get("basisType") == "unverified":
            if basis.get("status") != "route_only_unverified" or basis.get("personSupervisionStatus") != "unverified":
                report.error(f"Candidate {identity}: unverified S4 requires route_only_unverified/unverified")
        else:
            report.error(f"Candidate {identity}: S4 requires basisType=co_supervision_only or unverified")
        if basis.get("eligibilityStatus") != "not_confirmed":
            report.error(f"Candidate {identity}: S4 must keep eligibilityStatus=not_confirmed")


def validate_claim_traceability(
    record: dict,
    identity: str,
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    confidence = record.get("confidenceByClaim")
    if not isinstance(confidence, dict):
        if strict:
            report.error(f"Candidate {identity}: strict schema 1.2 requires confidenceByClaim")
    else:
        missing_confidence = CLAIM_CONFIDENCE_FIELDS - set(confidence)
        if missing_confidence:
            report.error(
                f"Candidate {identity}: confidenceByClaim missing {sorted(missing_confidence)}"
            )
        for field, level in confidence.items():
            if field not in CLAIM_CONFIDENCE_FIELDS:
                report.error(f"Candidate {identity}: confidenceByClaim has unknown field {field}")
            elif level not in CONFIDENCE_LEVELS:
                report.error(
                    f"Candidate {identity}: confidenceByClaim.{field} has invalid level {level}"
                )

    claim_sources = record.get("claimSourceIds")
    if not isinstance(claim_sources, dict):
        if strict:
            report.error(f"Candidate {identity}: strict schema 1.2 requires claimSourceIds")
        return
    unknown_fields = set(claim_sources) - MATERIAL_CLAIM_FIELDS
    if unknown_fields:
        report.error(f"Candidate {identity}: claimSourceIds has unknown fields {sorted(unknown_fields)}")
    tier = record.get("priorityTier")
    required_fields = set()
    for field in MATERIAL_CLAIM_FIELDS:
        value = record.get(field)
        has_value = bool(value) if isinstance(value, (list, dict)) else bool(str(value or "").strip())
        if has_value and not is_explicit_missing(value):
            required_fields.add(field)
    for field in MATERIAL_CLAIM_FIELDS:
        ids = validate_string_list(
            claim_sources.get(field, []),
            f"Candidate {identity}: claimSourceIds.{field}",
            report,
            required=field in required_fields,
        )
        if not ids:
            continue
        allowed_domains = MATERIAL_CLAIM_DOMAINS[field]
        for source_id in ids:
            source = source_map.get(source_id, {})
            if not allowed_domains.intersection(source.get("claimDomains", [])):
                report.error(
                    f"Candidate {identity}: claimSourceIds.{field} source {source_id} lacks a relevant domain"
                )
            if field not in {"phdTypes", "doctoralRoute"} and identity not in source.get("subjectIds", []):
                report.error(
                    f"Candidate {identity}: claimSourceIds.{field} source {source_id} is not candidate-bound"
                )
            if field in ROLE_FIELD_ALLOWED_PERSON_ROLE_TYPES:
                person_role = person_role_for(source, identity) or {}
                role_type = person_role.get("roleType")
                if role_type not in ROLE_FIELD_ALLOWED_PERSON_ROLE_TYPES[field]:
                    report.error(
                        f"Candidate {identity}: claimSourceIds.{field} source {source_id} "
                        f"has incompatible roleType={role_type or '<missing>'}"
                    )
                if not person_role_is_specific(source, identity):
                    report.error(
                        f"Candidate {identity}: claimSourceIds.{field} source {source_id} "
                        "uses non-specific role evidence and cannot support a concrete role field"
                    )
                exact_label = str(person_role.get("exactLabel", ""))
                if field == "academicRole" and not ACADEMIC_ROLE_LABEL_RE.search(exact_label):
                    report.error(
                        f"Candidate {identity}: claimSourceIds.academicRole source {source_id} "
                        "does not retain an academic-title label"
                    )
                if field == "adminClinicalRole" and not ADMIN_ROLE_LABEL_RE.search(exact_label):
                    report.error(
                        f"Candidate {identity}: claimSourceIds.adminClinicalRole source {source_id} "
                        "does not retain an administrative/clinical leadership label"
                    )
                if source.get("authorityClass") != "official_institution" or source.get("status") != "current":
                    report.error(
                        f"Candidate {identity}: claimSourceIds.{field} source {source_id} must be a current official-institution role source"
                    )
            if field in {"phdTypes", "doctoralRoute"}:
                allowed_subjects = {identity, *candidate_school_ids(record)}
                if source.get("authorityClass") not in OFFICIAL_SOURCE_AUTHORITIES:
                    report.error(
                        f"Candidate {identity}: claimSourceIds.phdTypes source {source_id} is not official"
                    )
                if not allowed_subjects.intersection(source.get("subjectIds", [])):
                    report.error(
                        f"Candidate {identity}: claimSourceIds.phdTypes source {source_id} is not bound to the candidate or an affiliated school"
                    )


def validate_records(
    records: list[dict],
    school_map: dict[str, dict],
    source_map: dict[str, dict],
    as_of: dt.date | None,
    strict: bool,
    report: Report,
) -> dict[str, dict]:
    record_map = check_unique_ids("candidate", records, report)
    name_pairs: set[tuple[str, str]] = set()
    records_by_name: defaultdict[str, list[dict]] = defaultdict(list)
    for index, record in enumerate(records):
        identity = str(record.get("id") or record.get("name") or index)
        for field in ["name", "schoolId", "academicRole", "focus", "primaryCategory"]:
            if not str(record.get(field, "")).strip():
                report.error(f"Candidate {identity}: missing {field}")
        school_id = str(record.get("schoolId", "")).strip()
        if school_id not in school_map:
            report.error(f"Candidate {identity}: unknown schoolId {school_id}")
        associated_school_ids = validate_affiliations(
            record, identity, school_map, source_map, strict, report
        )
        normalized_name = re.sub(r"\s+", " ", str(record.get("name", "")).casefold()).strip()
        for associated_school_id in associated_school_ids or {school_id}:
            pair = (associated_school_id, normalized_name)
            if pair in name_pairs:
                report.error(
                    f"Duplicate candidate name within school: {record.get('name')} / {associated_school_id}"
                )
            name_pairs.add(pair)
        for previous in records_by_name[normalized_name]:
            prior_orcid = str(previous.get("orcid", "")).strip()
            this_orcid = str(record.get("orcid", "")).strip()
            explicit_distinction = (
                prior_orcid
                and this_orcid
                and prior_orcid != this_orcid
            ) or (
                str(previous.get("sameNameException", "")).strip()
                and str(record.get("sameNameException", "")).strip()
            )
            if not explicit_distinction:
                message = (
                    f"Candidate name {record.get('name')} appears in multiple records; merge joint appointments "
                    "into one record with additionalSchoolIds, or document distinct ORCIDs/sameNameException"
                )
                if strict:
                    report.error(message)
                else:
                    report.warn(message)
        records_by_name[normalized_name].append(record)
        orcid = str(record.get("orcid", "")).strip()
        if orcid and not re.fullmatch(r"(?:https?://orcid\.org/)?\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid):
            report.error(f"Candidate {identity}: malformed ORCID {orcid}")
        if record.get("topicDirectness") not in TOPIC_CODES:
            report.error(f"Candidate {identity}: invalid topicDirectness")
        if record.get("supervisionEvidence") not in SUPERVISION_CODES:
            report.error(f"Candidate {identity}: invalid supervisionEvidence")
        validate_supervision_basis(record, identity, source_map, strict, report)
        tier = record.get("priorityTier")
        if tier not in TIERS:
            report.error(f"Candidate {identity}: invalid priorityTier")
        status = record.get("opportunityStatus")
        if status not in OPPORTUNITY_STATUSES:
            report.error(f"Candidate {identity}: invalid opportunityStatus")
        verified_at = parse_iso_date(record.get("verifiedAt"))
        if verified_at is None:
            report.error(f"Candidate {identity}: verifiedAt must use YYYY-MM-DD")
        elif as_of and verified_at > as_of:
            report.error(f"Candidate {identity}: verifiedAt is later than case asOf")
        elif strict and as_of:
            age_days = (as_of - verified_at).days
            if age_days > 90:
                report.error(
                    f"Candidate {identity}: verification is {age_days} days old; reverify before delivery"
                )
            elif age_days > 30:
                report.warn(f"Candidate {identity}: verification is {age_days} days old")
        validate_contacts(record, identity, source_map, strict, report)
        for check_name in ["chineseCheck", "xiaohongshuCheck"]:
            validate_social_check(
                record, identity, check_name, source_map, as_of, strict, report
            )
        validate_conflicts(record, identity, source_map, as_of, report)
        validate_claim_traceability(record, identity, source_map, strict, report)

        current_role_ids = validate_string_list(
            record.get("currentRoleSourceIds", []),
            f"Candidate {identity}: currentRoleSourceIds",
            report,
        )
        research_source_ids = validate_string_list(
            record.get("researchSourceIds", []),
            f"Candidate {identity}: researchSourceIds",
            report,
        )
        doctoral_source_ids = validate_string_list(
            record.get("doctoralSourceIds", []),
            f"Candidate {identity}: doctoralSourceIds",
            report,
        )
        direct_evidence_ids = validate_string_list(
            record.get("directEvidenceIds", []),
            f"Candidate {identity}: directEvidenceIds",
            report,
        )
        official_current = [
            source_map[source_id]
            for source_id in current_role_ids
            if source_id in source_map
            and source_map[source_id].get("authorityClass") == "official_institution"
            and source_map[source_id].get("status") == "current"
            and "current_role" in source_map[source_id].get("claimDomains", [])
            and identity in source_map[source_id].get("subjectIds", [])
        ]
        if tier in {"A", "B", "C"} and not official_current:
            report.error(f"Candidate {identity}: {tier}-tier lacks a current official role source")
        role_access_dates = [
            parse_iso_date(source_map.get(source_id, {}).get("accessedDate"))
            for source_id in current_role_ids
            if source_id in source_map
        ]
        if verified_at and any(date and date > verified_at for date in role_access_dates):
            report.error(f"Candidate {identity}: currentRoleSourceIds include evidence accessed after verifiedAt")
        if strict and verified_at and official_current and not any(
            parse_iso_date(source.get("accessedDate")) == verified_at for source in official_current
        ):
            report.error(
                f"Candidate {identity}: verifiedAt needs at least one current official role source accessed on that date"
            )
        topic_sources = [
            source_map[source_id]
            for source_id in research_source_ids
            if source_id in source_map
            and source_map[source_id].get("type") in TOPIC_EVIDENCE_SOURCE_TYPES
            and (person_role_for(source_map[source_id], identity) or {}).get("topicRelevance")
            in {"direct", "adjacent"}
            and "research" in source_map[source_id].get("claimDomains", [])
            and identity in source_map[source_id].get("subjectIds", [])
            and source_map[source_id].get("status") != "future"
        ]
        if tier in {"A", "B", "C"} and not topic_sources:
            report.error(f"Candidate {identity}: {tier}-tier lacks a relevant topic-evidence source")
        if strict and set(direct_evidence_ids) - set(research_source_ids):
            report.error(
                f"Candidate {identity}: directEvidenceIds must be a subset of researchSourceIds"
            )
        direct_work_keys: list[str] = []
        for source_id in direct_evidence_ids:
            source = source_map.get(source_id, {})
            if source.get("type") not in DIRECT_RESEARCH_SOURCE_TYPES:
                report.error(f"Candidate {identity}: direct evidence {source_id} has an ineligible source type")
                continue
            role = person_role_for(source, identity) or {}
            if role.get("topicRelevance") != "direct" or "research" not in source.get("claimDomains", []):
                report.error(f"Candidate {identity}: direct evidence {source_id} is not direct research evidence")
                continue
            published, _ = parse_partial_date(source.get("publishedDate"))
            if source.get("status") == "future" or (as_of and published and published > as_of):
                report.error(f"Candidate {identity}: direct evidence {source_id} was not public by case asOf")
                continue
            if identity not in source.get("subjectIds", []):
                report.error(
                    f"Candidate {identity}: direct evidence {source_id} does not identify the candidate"
                )
            direct_work_keys.append(evidence_work_key(source))
            if (
                strict
                and source.get("type") in {"publication", "grant_project", "clinical_trial"}
                and not str(source.get("workId", "")).strip()
            ):
                report.error(
                    f"Candidate {identity}: direct evidence {source_id} needs a shared workId "
                    "to reconcile DOI, PubMed, and registry landing pages"
                )
            if role.get("roleType") not in PERSON_ROLE_TYPES:
                report.error(
                    f"Candidate {identity}: direct evidence {source_id} lacks candidate role attribution"
                )
        if len(direct_work_keys) != len(set(direct_work_keys)):
            report.error(
                f"Candidate {identity}: directEvidenceIds contain duplicate underlying works"
            )

        topic_code = record.get("topicDirectness")
        if strict and topic_code in {"T1", "T2"}:
            current_independent_role = any(
                source.get("authorityClass") == "official_institution"
                and source.get("status") == "current"
                and source.get("type") in {"official_research_profile", "official_role_contact"}
                and "current_role" in source.get("claimDomains", [])
                and identity in source.get("subjectIds", [])
                and (person_role_for(source, identity) or {}).get("roleType")
                in CURRENT_INDEPENDENT_ROLE_TYPES
                for source in official_current
            )
            current_direct_topic = any(
                source.get("authorityClass") == "official_institution"
                and source.get("status") == "current"
                and source.get("type") in {"official_research_profile", "official_role_contact"}
                and "research" in source.get("claimDomains", [])
                and identity in source.get("subjectIds", [])
                and (person_role_for(source, identity) or {}).get("topicRelevance") == "direct"
                for source in topic_sources
            )
            if not (current_independent_role and current_direct_topic):
                report.error(
                    f"Candidate {identity}: {topic_code} requires paired candidate-bound current official evidence for both a direct topic and an independent role"
                )
        if strict and topic_code == "T3" and not any(
            source.get("authorityClass") in OFFICIAL_SOURCE_AUTHORITIES
            and source.get("status") == "current"
            and source.get("type")
            in {"official_research_profile", "official_role_contact", "grant_project", "clinical_trial"}
            and identity in source.get("subjectIds", [])
            and "research" in source.get("claimDomains", [])
            and (person_role_for(source, identity) or {}).get("topicRelevance") == "direct"
            for source in topic_sources
        ):
            report.error(
                f"Candidate {identity}: T3 requires an explicit candidate-bound current official "
                "direct lung-cancer application/project"
            )

        validate_opportunities(record, identity, source_map, as_of, strict, report)
        validate_string_list(
            record.get("secondaryCategories", []),
            f"Candidate {identity}: secondaryCategories",
            report,
        )
        validate_string_list(
            record.get("phdTypes", []),
            f"Candidate {identity}: phdTypes",
            report,
            required=tier == "A",
        )
        if tier == "A":
            if record.get("topicDirectness") == "T4":
                report.error(f"Candidate {identity}: A-tier cannot have T4 topic directness")
            overview_count = visible_char_count(str(record.get("directionOverviewZh", "")))
            structured_count = visible_char_count(str(record.get("structuredProfileZh", "")))
            if not 150 <= overview_count <= 250:
                report.error(
                    f"Candidate {identity}: directionOverviewZh has {overview_count} characters; expected 150-250"
                )
            if structured_count <= 500:
                report.error(
                    f"Candidate {identity}: structuredProfileZh has {structured_count} characters; expected >500"
                )
            direct_count, recent_count = direct_recent_count(record, source_map, as_of)
            exception = str(record.get("directEvidenceException", "")).strip()
            if record.get("supervisionEvidence") not in {"S1", "S2"}:
                report.error(f"Candidate {identity}: A-tier requires S1 or S2 supervision evidence")
            if not str(record.get("doctoralRoute", "")).strip() or not record.get("doctoralSourceIds"):
                report.error(f"Candidate {identity}: A-tier needs a sourced doctoral route")
            elif not any(
                source_map.get(source_id, {}).get("authorityClass") == "official_institution"
                and {"doctoral_rule", "admissions_funding"}.intersection(
                    source_map.get(source_id, {}).get("claimDomains", [])
                )
                for source_id in doctoral_source_ids
            ):
                report.error(
                    f"Candidate {identity}: A-tier doctoral route lacks an official doctoral/admissions-domain source"
                )
            if not research_source_ids:
                report.error(f"Candidate {identity}: A-tier needs researchSourceIds")
            if direct_count == 0:
                report.error(
                    f"Candidate {identity}: A-tier requires at least one candidate-bound direct topic work; "
                    "directEvidenceException cannot replace all direct evidence"
                )
            elif direct_count < 2 and not exception:
                report.error(
                    f"Candidate {identity}: A-tier needs two direct evidence records or an explicit exception"
                )
            elif direct_count < 2:
                report.warn(f"Candidate {identity}: direct-evidence exception: {exception}")
            if direct_count >= 2 and recent_count < 2 and not exception:
                report.error(
                    f"Candidate {identity}: fewer than two direct evidence records fall within five years; "
                    "add directEvidenceException or lower the tier"
                )
            elif direct_count >= 2 and recent_count < 2:
                report.warn(f"Candidate {identity}: recent-evidence exception: {exception}")
            validate_application_readiness(record, identity, source_map, report)
            for field in ["scientificQuestions", "materialsModels", "methods"]:
                validate_string_list(
                    record.get(field, []),
                    f"Candidate {identity}: {field}",
                    report,
                    required=True,
                    unique=False,
                )
            for field in ["validationMaturity", "roleBoundary"]:
                if not str(record.get(field, "")).strip():
                    report.error(f"Candidate {identity}: A-tier profile missing {field}")
            research_lines = record.get("researchLines", [])
            if not isinstance(research_lines, list) or not research_lines:
                report.error(f"Candidate {identity}: researchLines must be a non-empty array")
            else:
                for line_index, line in enumerate(research_lines):
                    path = f"Candidate {identity}: researchLines[{line_index}]"
                    if not isinstance(line, dict):
                        report.error(f"{path} must be an object")
                        continue
                    for field in ["title", "summary"]:
                        if not str(line.get(field, "")).strip():
                            report.error(f"{path} missing {field}")
                    validate_string_list(
                        line.get("sourceIds", []), f"{path}.sourceIds", report, required=True
                    )
                    if not any(
                        identity in source_map.get(source_id, {}).get("subjectIds", [])
                        and "research" in source_map.get(source_id, {}).get("claimDomains", [])
                        for source_id in line.get("sourceIds", [])
                    ):
                        report.error(f"{path} lacks candidate-bound research evidence")
            work_packages = validate_nonempty_items(
                record.get("doctoralWorkPackages", []),
                f"Candidate {identity}: doctoralWorkPackages",
                report,
                required=True,
            )
            if not 2 <= len(work_packages) <= 3:
                report.error(f"Candidate {identity}: doctoralWorkPackages must contain 2-3 items")
            for package_index, package in enumerate(work_packages):
                path = f"Candidate {identity}: doctoralWorkPackages[{package_index}]"
                if not isinstance(package, dict):
                    report.error(f"{path} must be an object, not free-form proposal prose")
                    continue
                validate_no_correspondence(package, path, report)
                for field in ["title", "scope", "assumptions"]:
                    if not str(package.get(field, "")).strip():
                        report.error(f"{path} missing {field}")
                if package.get("analystDerived") is not True:
                    report.error(f"{path}.analystDerived must be true")
                package_ids = validate_string_list(
                    package.get("sourceIds", []), f"{path}.sourceIds", report, required=True
                )
                if not any(
                    identity in source_map.get(source_id, {}).get("subjectIds", [])
                    and "research" in source_map.get(source_id, {}).get("claimDomains", [])
                    for source_id in package_ids
                ):
                    report.error(f"{path} lacks candidate-bound research evidence")
    return record_map


def validate_outputs(
    case_dir: Path,
    case: dict,
    schools: list[dict],
    coverage: list[dict],
    records: list[dict],
    sources: list[dict],
    strict: bool,
    report: Report,
) -> None:
    if not strict:
        return
    stats_line = evidence_stats_line(sources)
    texts: dict[str, str] = {}
    for filename in OUTPUT_FILES:
        path = case_dir / filename
        if not path.exists():
            report.error(f"Missing rendered output: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[filename] = text
        if stats_line not in text:
            report.error(f"{filename}: computed evidence statistics line is missing or inconsistent")
        if strict:
            duplicated_punctuation = next(
                (token for token in ("。；", "；。", "。。", "；；") if token in text),
                None,
            )
            if duplicated_punctuation:
                report.error(
                    f"{filename}: contains duplicated Chinese punctuation {duplicated_punctuation}"
                )
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"^(?:https?://|mailto:|#)", link):
                continue
            target = link.split("#", 1)[0]
            if target and not (path.parent / target).resolve().exists():
                report.error(f"{filename}: broken local link {link}")
    index_text = texts.get("00-INDEX.md", "")
    for limitation in case.get("limitations", []):
        if str(limitation).strip() and str(limitation) not in index_text:
            report.error(f"00-INDEX.md does not surface case limitation: {limitation}")
    if any(row.get("status") == "blocked_unverified" for row in coverage):
        if "访问限制" not in index_text:
            report.error("00-INDEX.md does not surface blocked coverage branches")
    if any(row.get("opportunityStatus") == "unverified" for row in records):
        if "招生状态仍为 unverified" not in index_text:
            report.error("00-INDEX.md does not surface unverified opportunity status")
    for record in records:
        candidate_id = str(record.get("id", ""))
        name = str(record.get("name") or candidate_id)
        exception = str(record.get("directEvidenceException", "")).strip()
        if exception and (name not in index_text or exception not in index_text):
            report.error(
                f"00-INDEX.md does not surface direct-evidence exception for {candidate_id}"
            )
        recruitment = record.get("recruitmentAudit")
        if isinstance(recruitment, dict):
            checked = parse_iso_date(recruitment.get("checkedAt"))
            case_date = parse_iso_date(case.get("asOf"))
            if checked and case_date and 30 < (case_date - checked).days <= 90:
                if name not in index_text or "招生核查距案例日期超过 30 天" not in index_text:
                    report.error(f"00-INDEX.md does not surface stale recruitment audit for {candidate_id}")
        stale_social = False
        for check_name in ["chineseCheck", "xiaohongshuCheck"]:
            check = record.get(check_name)
            if not isinstance(check, dict):
                continue
            checked = parse_iso_date(check.get("checkedAt"))
            case_date = parse_iso_date(case.get("asOf"))
            if checked and case_date and 30 < (case_date - checked).days <= 90:
                stale_social = True
        if stale_social and (name not in index_text or "中文互联网或小红书核查距案例日期超过 30 天" not in index_text):
            report.error(f"00-INDEX.md does not surface stale social check for {candidate_id}")
    school_scope_text = texts.get("01-SCHOOL-SCOPE.md", "")
    coverage_text = texts.get("03-COVERAGE-MATRIX.md", "")
    for school in schools:
        school_id = str(school.get("id", ""))
        if not re.search(rf"^\|\s*{re.escape(school_id)}\s*\|", school_scope_text, flags=re.MULTILINE):
            report.error(f"01-SCHOOL-SCOPE.md does not contain school {school_id}")
        if not re.search(rf"^\|\s*{re.escape(school_id)}\s*\|", coverage_text, flags=re.MULTILINE):
            report.error(f"03-COVERAGE-MATRIX.md does not contain school {school_id}")
    supervisor_text = texts.get("02-SUPERVISOR-TABLE.md", "")
    profiles_text = texts.get("05-A-TIER-DEEP-PROFILES.md", "")
    readiness_text = texts.get("06-APPLICATION-READINESS.md", "")
    for record in records:
        candidate_id = str(record.get("id", ""))
        if supervisor_text.count(f"ID: {candidate_id}") != 1:
            report.error(f"02-SUPERVISOR-TABLE.md does not contain candidate {candidate_id}")
        if record.get("priorityTier") == "A":
            if profiles_text.count(f"**记录 ID：** {candidate_id}") != 1:
                report.error(f"05-A-TIER-DEEP-PROFILES.md does not contain A-tier candidate {candidate_id}")
            if readiness_text.count(f"- 记录 ID：{candidate_id}") != 1:
                report.error(f"06-APPLICATION-READINESS.md does not contain A-tier candidate {candidate_id}")
    ledger = texts.get("07-SOURCE-LEDGER.md", "")
    for source in sources:
        source_id = str(source.get("id", ""))
        count = len(re.findall(rf"^\|\s*{re.escape(source_id)}\s*\|", ledger, flags=re.MULTILINE))
        if count != 1:
            report.error(f"07-SOURCE-LEDGER.md lists source {source_id} {count} times; expected once")


def validate_source_usage(
    case: dict,
    schools: list[dict],
    coverage: list[dict],
    records: list[dict],
    source_map: dict[str, dict],
    strict: bool,
    report: Report,
) -> None:
    referenced_ids = {
        source_id
        for value in [case, schools, coverage, records]
        for source_id, _ in collect_source_refs(value)
        if source_id
    }
    orphan_ids = sorted(set(source_map) - referenced_ids)
    if orphan_ids:
        message = f"Unreferenced source records inflate the evidence ledger: {orphan_ids}"
        if strict:
            report.error(message)
        else:
            report.warn(message)


def validate_discovery_lead_usage(
    case: dict,
    schools: list[dict],
    coverage: list[dict],
    records: list[dict],
    source_map: dict[str, dict],
    report: Report,
) -> None:
    """Discovery-only associations may appear only in non-material case provenance."""
    containers = [
        ("case", case),
        ("schools", schools),
        ("coverage", coverage),
        ("records", records),
    ]
    for container_name, value in containers:
        for source_id, field_path in collect_source_refs(value):
            if source_map.get(source_id, {}).get("type") != "discovery_lead":
                continue
            if container_name == "case":
                if field_path == "supportingSourceIds":
                    continue
                if re.fullmatch(r"discoveryPasses\[\d+\]\.sourceIds", field_path):
                    continue
            report.error(
                f"Discovery lead {source_id} is used as substantive evidence at "
                f"{container_name}.{field_path}; it is allowed only in case.supportingSourceIds "
                "or case.discoveryPasses[].sourceIds"
            )


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    report = Report()
    values = load_inputs(case_dir, report)
    if report.errors:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "caseDir": str(case_dir),
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    case_value = values.get("case.json")
    if not isinstance(case_value, dict):
        report.error("case.json must contain an object")
        case: dict = {}
    else:
        case = case_value
    schools = require_list("schools.json", values.get("schools.json"), report)
    coverage = require_list("coverage.json", values.get("coverage.json"), report)
    records = require_list("records.json", values.get("records.json"), report)
    sources = require_list("sources.json", values.get("sources.json"), report)

    as_of = validate_case_metadata(case, args.strict, report)
    source_map = validate_sources(sources, as_of, args.strict, report)
    school_map = validate_schools(schools, case, source_map, args.strict, report)
    record_map = validate_records(
        records, school_map, source_map, as_of, args.strict, report
    )
    validate_source_entities_and_scope(
        case, school_map, record_map, source_map, args.strict, report
    )
    validate_discovery_candidates(case, record_map, source_map, args.strict, report)
    validate_references("case", [case], source_map, report)
    validate_references("school", schools, source_map, report)
    validate_references("coverage", coverage, source_map, report)
    validate_references("candidate", records, source_map, report)
    validate_coverage(coverage, school_map, record_map, source_map, args.strict, report)
    validate_completion_semantics(case, coverage, args.strict, report)
    validate_source_usage(
        case, schools, coverage, records, source_map, args.strict, report
    )
    validate_discovery_lead_usage(case, schools, coverage, records, source_map, report)
    validate_outputs(
        case_dir, case, schools, coverage, records, sources, args.strict, report
    )

    stats = evidence_stats(sources)
    tiers = Counter(str(item.get("priorityTier", "unclassified")) for item in records)
    scope_audit = case.get("scopeAudit") if isinstance(case.get("scopeAudit"), dict) else {}
    excluded = scope_audit.get("excludedInstitutions", [])
    payload = {
        "status": "valid" if not report.errors else "invalid",
        "strict": args.strict,
        "caseDir": str(case_dir),
        "asOf": case.get("asOf", ""),
        "scopeMode": case.get("scopeMode", ""),
        "schools": len(schools),
        "checkedExclusions": len(excluded) if isinstance(excluded, list) else 0,
        "candidates": len(records),
        "tierCounts": {tier: tiers.get(tier, 0) for tier in ["A", "B", "C", "D"]},
        **stats,
        "errorCount": len(report.errors),
        "warningCount": len(report.warnings),
        "errors": report.errors,
        "warnings": report.warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
