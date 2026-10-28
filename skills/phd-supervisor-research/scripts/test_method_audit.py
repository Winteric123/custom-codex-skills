#!/usr/bin/env python3
"""Contract tests for the supplemental method-audit validator and renderer."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate_method_audit.py"
RENDERER_PATH = SCRIPT_DIR / "render_method_audit.py"
SPEC = importlib.util.spec_from_file_location("validate_method_audit", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load validate_method_audit.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validation_payload = MODULE.validation_payload


def valid_fixture() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    records = [{"id": "candidate-one", "priorityTier": "A", "opportunityStatus": "no_public_evidence"}]
    case = {"asOf": "2026-10-25"}
    sources = []
    for index in range(1, 6):
        sources.append(
            {
                "id": f"paper-{index}",
                "type": "publication",
                "authorityClass": "primary_publication",
                "status": "current",
                "subjectIds": ["candidate-one"],
                "claimDomains": ["research"],
                "workId": f"doi:10.0000/example-{index}",
                "url": f"https://example.org/{index}",
            }
        )
    sources.append(
        {
            "id": "official-programme",
            "type": "official_research_profile",
            "subjectIds": ["candidate-one"],
            "authorityClass": "official_institution",
            "status": "current",
            "claimDomains": ["research"],
            "url": "https://example.edu/group",
        }
    )
    papers = [
        {
            "workId": "doi:10.0000/example-1",
            "title": "Integrated translational study one",
            "publicationDate": "2025-04-01",
            "inclusionDecision": "included",
            "exclusionReason": "",
            "identityEvidence": ["matching affiliation", "matching ORCID"],
            "authorRole": "O3C",
            "roleBasis": "explicit corresponding and senior author",
            "correspondingStatus": "CORRESPONDING",
            "seniorStatus": "EXPLICIT_SENIOR",
            "authorOrderStatus": "LAST",
            "authorshipEvidenceSourceIds": ["paper-1"],
            "authorshipEvidenceLocator": "correspondence and contribution statements",
            "methodCode": "RM-EB",
            "methodFamilyTags": ["EXPERIMENTAL", "OMICS"],
            "omicsModalities": ["TRANSCRIPTOMICS"],
            "translationCode": "TR3",
            "translationEvidence": {
                "hasClinicalAnchor": True,
                "hasMolecularOmicsOrMechanisticBridge": True,
                "hasIndependentOrOrthogonalValidation": True,
                "hasProspectiveOrInterventionalLink": True,
                "hasFunctionalValidation": True,
                "hasClinicalLevelValidation": True,
            },
            "clinicalOnlySubtype": None,
            "reviewDepth": "M3_FULL_TEXT_DESIGN",
            "reviewActor": "model_manual",
            "reviewedAt": "2026-10-25",
            "reviewLocator": "Methods pp. 3-8; author contributions p. 14",
            "scoreTrigger": True,
            "portfolioTrigger": False,
            "evidenceFeatures": {
                "clinicalAnchor": "trial-linked samples",
                "experimentalWork": "organoid perturbation",
                "omicsWork": "transcriptomic generation and analysis",
                "bioinformaticsWork": "transcriptomic analysis",
                "theoreticalMethodContribution": "none",
                "endpoint": "response biomarker and mechanism",
                "validation": "functional and clinical-level validation",
            },
            "sourceIds": ["paper-1"],
            "sourceUrls": ["https://example.org/1"],
            "conflicts": [],
        },
        {
            "workId": "doi:10.0000/example-2",
            "title": "Integrated translational study two",
            "publicationDate": "2024-06-15",
            "inclusionDecision": "included",
            "exclusionReason": "",
            "identityEvidence": ["matching affiliation", "stable co-author network"],
            "authorRole": "O2C",
            "roleBasis": "explicit co-corresponding author",
            "correspondingStatus": "CO_CORRESPONDING",
            "seniorStatus": "CO_SENIOR",
            "authorOrderStatus": "LAST",
            "authorshipEvidenceSourceIds": ["paper-2"],
            "authorshipEvidenceLocator": "correspondence and contribution statements",
            "methodCode": "RM-EB",
            "methodFamilyTags": ["EXPERIMENTAL", "OMICS"],
            "omicsModalities": ["SINGLE_CELL"],
            "translationCode": "TR2",
            "translationEvidence": {
                "hasClinicalAnchor": True,
                "hasMolecularOmicsOrMechanisticBridge": True,
                "hasIndependentOrOrthogonalValidation": True,
                "hasProspectiveOrInterventionalLink": False,
                "hasFunctionalValidation": True,
                "hasClinicalLevelValidation": False,
            },
            "clinicalOnlySubtype": None,
            "reviewDepth": "M3_FULL_TEXT_DESIGN",
            "reviewActor": "model_manual",
            "reviewedAt": "2026-10-25",
            "reviewLocator": "Results sections 2-5; correspondence record",
            "scoreTrigger": True,
            "portfolioTrigger": False,
            "evidenceFeatures": {
                "clinicalAnchor": "patient cohort",
                "experimentalWork": "functional cell assay",
                "omicsWork": "single-cell generation and analysis",
                "bioinformaticsWork": "single-cell analysis",
                "theoreticalMethodContribution": "none",
                "endpoint": "stratification biomarker",
                "validation": "independent cohort and orthogonal assay",
            },
            "sourceIds": ["paper-2"],
            "sourceUrls": ["https://example.org/2"],
            "conflicts": [],
        },
    ]
    for index, role, translation, publication_date in (
        (3, "O3C", "TR3", "2023-08-20"),
        (4, "O2C", "TR2", "2022-11-10"),
        (5, "O3C", "TR2", "2022-02-18"),
    ):
        paper = copy.deepcopy(papers[1])
        paper["workId"] = f"doi:10.0000/example-{index}"
        paper["title"] = f"Integrated translational study {index}"
        paper["publicationDate"] = publication_date
        paper["authorRole"] = role
        paper["roleBasis"] = "explicit corresponding/senior role"
        paper["correspondingStatus"] = "CORRESPONDING" if role == "O3C" else "CO_CORRESPONDING"
        paper["translationCode"] = translation
        if translation == "TR3":
            paper["translationEvidence"]["hasProspectiveOrInterventionalLink"] = True
            paper["translationEvidence"]["hasClinicalLevelValidation"] = True
        paper["sourceIds"] = [f"paper-{index}"]
        paper["sourceUrls"] = [f"https://example.org/{index}"]
        paper["authorshipEvidenceSourceIds"] = [f"paper-{index}"]
        papers.append(paper)
    audit = {
        "schemaVersion": "research-method-audit-1.1",
        "caseAsOf": "2026-10-25",
        "generatedAt": "2026-10-25",
        "searchScope": {
            "coverageClaim": "bounded_public_search",
            "defaultWindowYears": 5,
            "extendedWindowYears": 8,
        },
        "rosterReconciliation": {
            "retainedAbcCandidateIds": ["candidate-one"],
            "auditedCandidateIds": ["candidate-one"],
            "missingCandidateIds": [],
        },
        "candidates": [
            {
                "candidateId": "candidate-one",
                "name": "Example Professor",
                "priorityTier": "A",
                "departmentZh": "肿瘤转化研究中心",
                "currentRoleZh": "教授、课题组负责人",
                "researchDirectionZh": "成人实体瘤的实验、组学与临床转化研究",
                "scientificAuditStatus": "confirmed",
                "opportunityStatus": "no_public_evidence",
                "outreachControl": {"status": "active"},
                "searchDate": "2026-10-25",
                "windowYears": 5,
                "windowStart": "2021-10-25",
                "windowEnd": "2026-10-25",
                "extensionReason": None,
                "searchStatus": "bounded_complete",
                "searchPlan": [
                    {
                        "queryId": "pubmed-main",
                        "sourceKey": "pubmed",
                        "source": "PubMed",
                        "query": "Example Professor[Author] AND cancer",
                    }
                ],
                "searchLedger": [
                    {
                        "queryId": "pubmed-main",
                        "source": "PubMed",
                        "query": "Example Professor[Author] AND cancer",
                        "searchStage": "BASE_5Y",
                        "windowStart": "2021-10-25",
                        "windowEnd": "2026-10-25",
                        "searchedAt": "2026-10-25",
                        "pagesOrCursorsChecked": "all results",
                        "resultCount": 5,
                        "truncated": False,
                        "accessStatus": "complete",
                        "retryNotes": "",
                    }
                ],
                "searchReconciliation": {
                    "rawResults": 5,
                    "duplicateRecords": 0,
                    "uniqueWorks": 5,
                    "includedWorks": 5,
                    "excludedWorks": 0,
                },
                "papers": papers,
                "portfolioCounts": {"eligible": 5, "candidateLed": 5, "strongRole": 5},
                "portfolioCodes": ["RP-EB-INTRA", "RP-TRANS"],
                "dominance": {
                    "methodCode": "RM-EB",
                    "weightedNumerator": 4.7,
                    "weightedDenominator": 4.7,
                    "ratio": 1.0,
                },
                "scores": {
                    "methodIntegration": 30,
                    "clinicalTranslation": 30,
                    "researchOwnership": 20,
                    "recentContinuity": 10,
                    "evidenceCompleteness": 10,
                    "total": 100,
                },
                "scoreBasis": {
                    "methodIntegration": "two strong-role RM-EB papers",
                    "clinicalTranslation": "two M3 O3 TR3 papers plus further M3 TR2 evidence",
                    "researchOwnership": "five strong-role papers",
                    "recentContinuity": "five candidate-led papers in the rolling five-year window",
                    "evidenceCompleteness": "M3 papers, M4 cross-check and no unresolved conflicts",
                },
                "grade": "MTG1",
                "gradeAdjustment": {"applied": False, "from": "", "to": "", "reason": ""},
                "confidence": "high",
                "currentProgramCrossCheck": {
                    "status": "M4_CURRENT_PROGRAM_CROSSCHECK",
                    "result": "consistent",
                    "sourceIds": ["official-programme"],
                    "summary": "当前官方研究方向与论文组合一致。",
                },
                "conflicts": [],
            }
        ],
    }
    return records, case, sources, audit


def extended_fixture() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    fixture = valid_fixture()
    candidate = fixture[3]["candidates"][0]
    candidate["scientificAuditStatus"] = "provisional"
    candidate["papers"] = candidate["papers"][:2]
    candidate["windowYears"] = 8
    candidate["windowStart"] = "2018-10-25"
    candidate["extensionReason"] = "fewer_than_five_candidate_led_in_base_5y"
    candidate["searchLedger"][0]["resultCount"] = 2
    extended_entry = copy.deepcopy(candidate["searchLedger"][0])
    extended_entry["searchStage"] = "EXTENDED_8Y"
    extended_entry["windowStart"] = "2018-10-25"
    candidate["searchLedger"].append(extended_entry)
    candidate["searchReconciliation"] = {
        "rawResults": 2,
        "duplicateRecords": 0,
        "uniqueWorks": 2,
        "includedWorks": 2,
        "excludedWorks": 0,
    }
    candidate["portfolioCounts"] = {"eligible": 2, "candidateLed": 2, "strongRole": 2}
    candidate["dominance"] = {
        "methodCode": "RM-EB",
        "weightedNumerator": 1.85,
        "weightedDenominator": 1.85,
        "ratio": 1.0,
    }
    candidate["scores"] = {
        "methodIntegration": 30,
        "clinicalTranslation": 25,
        "researchOwnership": 12,
        "recentContinuity": 5,
        "evidenceCompleteness": 10,
        "total": 82,
    }
    candidate["grade"] = "pMTG1"
    candidate["confidence"] = "low"
    return fixture


def fixture_errors(
    fixture: tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]
) -> list[str]:
    with tempfile.TemporaryDirectory() as temp:
        case_dir = Path(temp)
        write_case(case_dir, fixture)
        return validation_payload(case_dir, strict=False)["errors"]


def write_case(root: Path, fixture: tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]) -> None:
    records, case, sources, audit = fixture
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    for name, value in (
        ("records.json", records),
        ("case.json", case),
        ("sources.json", sources),
        ("research-method-audit.json", audit),
    ):
        (data_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "00-INDEX.md").write_text("# 测试索引\n\n## 未解决事项与限制\n", encoding="utf-8")


class MethodAuditContractTests(unittest.TestCase):
    def test_valid_confirmed_fixture_renders_and_passes_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, valid_fixture())
            self.assertEqual(validation_payload(case_dir, strict=False)["status"], "valid")
            result = subprocess.run(
                [sys.executable, str(RENDERER_PATH), "--case-dir", str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report_path = case_dir / "08-RESEARCH-METHOD-TRANSLATION-AUDIT.md"
            self.assertTrue(report_path.is_file())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("生信 0；组学 5", report)
            self.assertIn("2021-10-25 至 2026-10-25", report)
            self.assertIn("通讯 CORRESPONDING", report)
            self.assertIn("omics: TRANSCRIPTOMICS", report)
            self.assertEqual(validation_payload(case_dir, strict=True)["status"], "valid")

    def test_missing_retained_candidate_fails(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"] = []
        fixture[3]["rosterReconciliation"]["auditedCandidateIds"] = []
        fixture[3]["rosterReconciliation"]["missingCandidateIds"] = ["candidate-one"]
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("missing from method audit" in item for item in result["errors"]))

    def test_mtg_u_cannot_hide_usable_machine_evidence(self) -> None:
        fixture = valid_fixture()
        candidate = fixture[3]["candidates"][0]
        candidate["scientificAuditStatus"] = "ungraded"
        candidate["grade"] = "MTG-U"
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("MTG-U is invalid" in item for item in result["errors"]))

    def test_mtg1_requires_verified_tr3_floor(self) -> None:
        fixture = valid_fixture()
        for paper in fixture[3]["candidates"][0]["papers"]:
            paper["translationCode"] = "TR2"
            paper["translationEvidence"]["hasProspectiveOrInterventionalLink"] = False
            paper["translationEvidence"]["hasClinicalLevelValidation"] = False
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("MTG1 requires" in item for item in result["errors"]))

    def test_score_above_80_can_be_explicitly_capped_at_mtg2(self) -> None:
        fixture = valid_fixture()
        candidate = fixture[3]["candidates"][0]
        for paper in candidate["papers"]:
            paper["translationCode"] = "TR2"
            paper["translationEvidence"]["hasProspectiveOrInterventionalLink"] = False
            paper["translationEvidence"]["hasClinicalLevelValidation"] = False
        candidate["scores"]["clinicalTranslation"] = 20
        candidate["scores"]["total"] = 90
        candidate["grade"] = "MTG2"
        candidate["gradeAdjustment"] = {
            "applied": True,
            "from": "MTG1",
            "to": "MTG2",
            "reason": "raw score exceeds 80 but the MTG1 TR3 floor is unmet",
        }
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            self.assertEqual(validation_payload(case_dir, strict=False)["status"], "valid")

    def test_publication_source_must_match_work_id(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["workId"] = "doi:10.0000/wrong"
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertTrue(any("same workId" in item for item in result["errors"]))

    def test_paper_outside_declared_window_fails(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["publicationDate"] = "2020-01-01"
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertTrue(any("outside the declared" in item for item in result["errors"]))

    def test_portfolio_code_threshold_is_derived(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["portfolioCodes"] = ["RP-EB-SPLIT"]
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertTrue(any("RP-EB-SPLIT requires" in item for item in result["errors"]))

    def test_hold_requires_reason_date_scope_and_recheck(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["outreachControl"] = {"status": "hold_user"}
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertTrue(any("held outreachControl" in item for item in result["errors"]))

    def test_blank_and_extra_candidate_ids_fail(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["candidateId"] = ""
        fixture[3]["rosterReconciliation"]["auditedCandidateIds"] = []
        fixture[3]["rosterReconciliation"]["missingCandidateIds"] = ["candidate-one"]
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertTrue(any("candidateId must be a non-empty string" in item for item in result["errors"]))

    def test_zero_abc_roster_renders_and_passes_strict(self) -> None:
        records, case, sources, audit = valid_fixture()
        records[0]["priorityTier"] = "D"
        audit["candidates"] = []
        audit["rosterReconciliation"] = {
            "retainedAbcCandidateIds": [],
            "auditedCandidateIds": [],
            "missingCandidateIds": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, (records, case, sources, audit))
            result = subprocess.run(
                [sys.executable, str(RENDERER_PATH), "--case-dir", str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(validation_payload(case_dir, strict=True)["status"], "valid")

    def test_stale_report_hash_fails_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, valid_fixture())
            result = subprocess.run(
                [sys.executable, str(RENDERER_PATH), "--case-dir", str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            audit_path = case_dir / "data" / "research-method-audit.json"
            audit_path.write_text(audit_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            strict_result = validation_payload(case_dir, strict=True)
            self.assertTrue(any("stale" in item for item in strict_result["errors"]))

    def test_vacancy_state_cannot_be_stored_as_outreach_control(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["outreachControl"]["status"] = "vacancy_unknown"
        with tempfile.TemporaryDirectory() as temp:
            case_dir = Path(temp)
            write_case(case_dir, fixture)
            result = validation_payload(case_dir, strict=False)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("outreachControl.status" in item for item in result["errors"]))

    def test_valid_extended_window_uses_active_stage_only(self) -> None:
        self.assertEqual(fixture_errors(extended_fixture()), [])

    def test_candidate_window_must_match_case_as_of(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["windowStart"] = "2021-10-24"
        self.assertTrue(any("candidate window must exactly match" in item for item in fixture_errors(fixture)))

    def test_each_planned_query_requires_base_stage(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["searchLedger"][0]["searchStage"] = "EXTENDED_8Y"
        self.assertTrue(any("requires exactly one BASE_5Y" in item for item in fixture_errors(fixture)))

    def test_extended_window_requires_every_extended_query(self) -> None:
        fixture = extended_fixture()
        fixture[3]["candidates"][0]["searchLedger"].pop()
        self.assertTrue(any("requires exactly one EXTENDED_8Y" in item for item in fixture_errors(fixture)))

    def test_reconciliation_uses_only_active_extended_results(self) -> None:
        fixture = extended_fixture()
        fixture[3]["candidates"][0]["searchReconciliation"]["rawResults"] = 4
        self.assertTrue(any("searchReconciliation.rawResults must equal 2" in item for item in fixture_errors(fixture)))

    def test_author_role_is_derived_from_structured_evidence(self) -> None:
        fixture = valid_fixture()
        paper = fixture[3]["candidates"][0]["papers"][0]
        paper["correspondingStatus"] = "NOT_CORRESPONDING"
        paper["seniorStatus"] = "NOT_SENIOR"
        paper["authorOrderStatus"] = "PENULTIMATE"
        self.assertTrue(any("authorRole must be derived as O0" in item for item in fixture_errors(fixture)))

    def test_method_tags_keep_bioinformatics_and_omics_separate(self) -> None:
        fixture = valid_fixture()
        paper = fixture[3]["candidates"][0]["papers"][0]
        paper["methodFamilyTags"] = ["EXPERIMENTAL", "BIOINFORMATICS"]
        self.assertTrue(any("OMICS tag and omicsModalities" in item for item in fixture_errors(fixture)))

    def test_method_code_rejects_incompatible_family_tags(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["methodFamilyTags"] = ["CLINICAL_OUTCOMES"]
        self.assertTrue(any("methodFamilyTags are incompatible with RM-EB" in item for item in fixture_errors(fixture)))

    def test_translation_code_requires_structured_evidence(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["translationEvidence"]["hasFunctionalValidation"] = False
        self.assertTrue(any("TR3 requires all six" in item for item in fixture_errors(fixture)))

    def test_rm_c_and_clin_only_are_biconditional(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["translationCode"] = "CLIN_ONLY"
        self.assertTrue(any("RM-C and CLIN_ONLY" in item for item in fixture_errors(fixture)))

    def test_lower_self_selected_score_is_rejected(self) -> None:
        fixture = valid_fixture()
        scores = fixture[3]["candidates"][0]["scores"]
        scores["methodIntegration"] = 26
        scores["total"] = 96
        self.assertTrue(any("uniquely derived value 30" in item for item in fixture_errors(fixture)))

    def test_score_trigger_is_recomputed(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["scoreTrigger"] = False
        self.assertTrue(any("scoreTrigger must equal derived value True" in item for item in fixture_errors(fixture)))

    def test_portfolio_trigger_is_recomputed(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["portfolioTrigger"] = True
        self.assertTrue(any("portfolioTrigger must equal derived value False" in item for item in fixture_errors(fixture)))

    def test_confirmed_derived_trigger_requires_m3(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["reviewDepth"] = "M2_HUMAN_ABSTRACT"
        self.assertTrue(any("score/portfolio trigger requires M3" in item for item in fixture_errors(fixture)))

    def test_portfolio_codes_must_equal_derived_set(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["portfolioCodes"] = ["RP-EB-INTRA"]
        self.assertTrue(any("portfolioCodes must equal derived codes" in item for item in fixture_errors(fixture)))

    def test_m4_result_must_be_consistent_for_confirmation(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["currentProgramCrossCheck"]["result"] = "mixed"
        self.assertTrue(any("result=consistent" in item for item in fixture_errors(fixture)))

    def test_conflict_requires_impact_and_blocks_confirmation(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["conflicts"] = [
            {"type": "identity", "summary": "unresolved identity", "material": True, "resolved": False}
        ]
        errors = fixture_errors(fixture)
        self.assertTrue(any("impact must be" in item for item in errors))

        fixture[3]["candidates"][0]["conflicts"][0]["impact"] = "BLOCKS_GRADE"
        self.assertTrue(any("forces scientificAuditStatus=incomplete" in item for item in fixture_errors(fixture)))

    def test_nonblocking_unresolved_conflict_forbids_confirmed(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["conflicts"] = [
            {
                "type": "current_direction",
                "summary": "minor unresolved wording difference",
                "material": False,
                "resolved": False,
                "impact": "NONBLOCKING_PROVISIONAL",
            }
        ]
        self.assertTrue(any("cannot coexist with confirmed" in item for item in fixture_errors(fixture)))

    def test_source_ids_reject_non_string_values(self) -> None:
        fixture = valid_fixture()
        fixture[3]["candidates"][0]["papers"][0]["sourceIds"] = [1]
        self.assertTrue(any("sourceIds must contain only non-empty strings" in item for item in fixture_errors(fixture)))

    def test_source_urls_reject_non_string_values(self) -> None:
        fixture = valid_fixture()
        fixture[2][0]["url"] = 123
        self.assertTrue(any("sources.json[0].url must be a non-empty string" in item for item in fixture_errors(fixture)))

    def test_method_and_translation_scores_use_strong_roles_only(self) -> None:
        papers = [
            {
                "authorRole": "O3C",
                "methodCode": "RM-E",
                "translationCode": "TR3",
                "reviewDepth": "M3_FULL_TEXT_DESIGN",
                "publicationDate": "2025-01-01",
            },
            {
                "authorRole": "O1F",
                "methodCode": "RM-B",
                "translationCode": "TR2",
                "reviewDepth": "M3_FULL_TEXT_DESIGN",
                "publicationDate": "2024-01-01",
            },
        ]
        scores = MODULE.derive_score_components(
            papers, MODULE.parse_date("2026-10-25"), False, False
        )
        self.assertEqual(scores["methodIntegration"], 6)
        self.assertEqual(scores["clinicalTranslation"], 14)

    def test_continuity_two_requires_years_six_to_eight_to_dominate(self) -> None:
        papers = [
            {
                "authorRole": "O1F",
                "methodCode": "RM-B",
                "translationCode": "TR0",
                "reviewDepth": "M2_HUMAN_ABSTRACT",
                "publicationDate": "2025-01-01",
            },
            {
                "authorRole": "O1F",
                "methodCode": "RM-B",
                "translationCode": "TR0",
                "reviewDepth": "M2_HUMAN_ABSTRACT",
                "publicationDate": "2019-12-01",
            },
            {
                "authorRole": "O1F",
                "methodCode": "RM-B",
                "translationCode": "TR0",
                "reviewDepth": "M2_HUMAN_ABSTRACT",
                "publicationDate": "2019-11-01",
            },
        ]
        scores = MODULE.derive_score_components(
            papers, MODULE.parse_date("2026-10-25"), False, False
        )
        self.assertEqual(scores["recentContinuity"], 2)

    def test_evidence_completeness_does_not_vacuously_score_ten_without_strong_role(self) -> None:
        papers = [
            {
                "authorRole": "O1F",
                "methodCode": "RM-B",
                "translationCode": "TR0",
                "reviewDepth": "M3_FULL_TEXT_DESIGN",
                "publicationDate": "2025-01-01",
            }
        ]
        scores = MODULE.derive_score_components(
            papers, MODULE.parse_date("2026-10-25"), True, False
        )
        self.assertEqual(scores["evidenceCompleteness"], 3)

    def test_authorship_evidence_must_be_bound_to_the_same_publication(self) -> None:
        fixture = valid_fixture()
        paper = fixture[3]["candidates"][0]["papers"][0]
        paper["authorshipEvidenceSourceIds"] = ["paper-2"]
        paper["sourceIds"] = ["paper-1", "paper-2"]
        errors = fixture_errors(fixture)
        self.assertTrue(any("authorship evidence requires a publication source with the same workId" in item for item in errors))

    def test_confirmed_requires_at_least_one_strong_role_paper(self) -> None:
        fixture = valid_fixture()
        for paper in fixture[3]["candidates"][0]["papers"]:
            paper["authorRole"] = "O1F"
            paper["correspondingStatus"] = "NOT_CORRESPONDING"
            paper["seniorStatus"] = "NOT_SENIOR"
            paper["authorOrderStatus"] = "FIRST"
        errors = fixture_errors(fixture)
        self.assertTrue(any("confirmed status requires at least one strong-role paper" in item for item in errors))
        self.assertTrue(any("derived evidenceCompleteness of at least 7" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
