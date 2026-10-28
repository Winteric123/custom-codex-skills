#!/usr/bin/env python3
"""Synthetic application-material rendering contracts; no live applicant data."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from render_outputs import (
    render_application_readiness,
    render_document_requirements_matrix,
    warning_lines,
)


CASE = {
    "location": "Synthetic Region",
    "topic": "Cancer translational genomics",
    "topicProfile": "cv_aligned_oncology",
    "asOf": "2026-10-13",
}
SOURCE = {
    "id": "synthetic-admissions",
    "type": "official_programme",
    "title": "Example admissions requirements",
    "url": "https://example.edu/phd/application-materials",
}
SOURCE_MAP = {SOURCE["id"]: SOURCE}


def material_rule(route_id: str, **overrides: object) -> dict:
    rule = {
        "routeId": route_id,
        "materialType": "recommendation_letters",
        "requirementStatus": "required",
        "submissionStage": "initial_application",
        "summary": "Two independent academic references",
        "formatAndLength": "Official online reference form",
        "quantity": 2,
        "submitter": "referee",
        "submissionMethod": "Referee uploads directly through portal",
        "checkedAt": CASE["asOf"],
        "sourceIds": [SOURCE["id"]],
    }
    rule.update(overrides)
    return rule


def candidate(name: str, tier: str, *, route_status: str = "route_confirmed_no_vacancy") -> dict:
    candidate_id = name.lower().replace(" ", "-")
    route_id = candidate_id + "-route"
    return {
        "id": candidate_id,
        "name": name,
        "schoolId": "synthetic-school",
        "priorityTier": tier,
        "verifiedAt": CASE["asOf"],
        "doctoralRoute": "Legacy programme summary",
        "opportunities": [{
            "id": route_id,
            "routeName": name + " programme",
            "scope": "programme",
            "status": route_status,
            "deadlineType": "not_stated",
            "sourceIds": [SOURCE["id"]],
        }],
        "applicationReadiness": {
            "documentRequirements": [material_rule(route_id)],
            "requiredDocuments": "Legacy materials synopsis remains available",
            "researchAnchor": "Sourced cancer-genomics research anchor",
            "anchorSourceIds": [SOURCE["id"]],
            "researchGap": "Analyst-derived research gap",
            "proposedAim": "Analyst-derived bounded aim",
        },
    }


def matrix(records: list[dict]) -> str:
    lines: list[str] = []
    render_document_requirements_matrix(lines, CASE, records, SOURCE_MAP)
    return "\n".join(lines)


def materials_warnings(records: list[dict]) -> list[str]:
    return [
        warning for warning in warning_lines(CASE, [], records)
        if "材料" in warning
    ]


class ApplicationMaterialsRendererContracts(unittest.TestCase):
    def test_b_and_c_matrix_precedes_a_detail_and_preserves_a_fields(self) -> None:
        records = [candidate("C Candidate", "C"), candidate("A Candidate", "A"), candidate("B Candidate", "B")]
        with tempfile.TemporaryDirectory(prefix="synthetic-material-render-") as directory:
            case_dir = Path(directory)
            render_application_readiness(case_dir, CASE, records, SOURCE_MAP, [SOURCE])
            text = (case_dir / "06-APPLICATION-READINESS.md").read_text(encoding="utf-8")
        detail_start = text.index("## A 类导师申请准备详情")
        for name in ["B Candidate", "C Candidate"]:
            self.assertLess(text.index(name), detail_start)
        self.assertGreater(text.index("### 1. A Candidate"), detail_start)
        for retained_value in [
            "Legacy materials synopsis remains available",
            "Sourced cancer-genomics research anchor",
            "Analyst-derived research gap",
            "Analyst-derived bounded aim",
            "本文件不替申请人发言",
        ]:
            self.assertIn(retained_value, text)
        self.assertNotIn("### 2. B Candidate", text)

    def test_rule_fields_and_source_links_remain_in_the_same_row(self) -> None:
        record = candidate("B Candidate", "B")
        text = matrix([record])
        row = next(line for line in text.splitlines() if line.startswith("| B Candidate"))
        for expected in [
            "B Candidate programme (b-candidate-route)",
            "推荐信",
            "必需",
            "首次正式申请；2 份；推荐人",
            "Two independent academic references",
            "Official online reference form",
            "Referee uploads directly through portal",
            "2026-10-13",
            "[Example admissions requirements](https://example.edu/phd/application-materials)",
        ]:
            self.assertIn(expected, row)

    def test_missing_structured_materials_is_unverified_not_not_required(self) -> None:
        record = candidate("C Candidate", "C")
        del record["applicationReadiness"]["documentRequirements"]
        text = matrix([record])
        self.assertIn("C Candidate programme (c-candidate-route)", text)
        self.assertIn("未按新材料清单核验", text)
        self.assertIn("缺失不代表不要求", text)
        self.assertNotIn("官方明确不要求", text)
        self.assertTrue(materials_warnings([record]))

    def test_unknown_count_and_explicit_not_required_are_distinct(self) -> None:
        record = candidate("B Candidate", "B")
        record["applicationReadiness"]["documentRequirements"] = [material_rule(
            "b-candidate-route",
            materialType="motivation_letter",
            requirementStatus="not_public",
            quantity=None,
            submitter="not_stated",
            submissionStage="not_stated",
        ), material_rule(
            "b-candidate-route",
            materialType="supervisor_enquiry",
            requirementStatus="not_required",
            quantity=0,
            submissionStage="pre_contact",
            submitter="applicant",
            summary="Official programme expressly says advance PI contact is not required",
        )]
        text = matrix([record])
        self.assertIn("动机信 | 未公开说明 | 未说明阶段；数量未说明；未说明提交者", text)
        self.assertIn("导师联系/套磁 | 官方明确不要求 | 联系导师前/联系阶段；0 份；申请人", text)

    def test_archived_routes_do_not_create_current_audit_gaps(self) -> None:
        for archived_status in ["closed_expired", "historical_only"]:
            with self.subTest(archived_status=archived_status):
                record = candidate("B Candidate", "B", route_status=archived_status)
                record["applicationReadiness"]["documentRequirements"] = []
                text = matrix([record])
                self.assertNotIn("未按新材料清单核验", text)
                self.assertNotIn("B Candidate programme", text)
                self.assertEqual(materials_warnings([record]), [])
                record["opportunities"] = []
                record["opportunityStatus"] = archived_status
                self.assertNotIn("未按新材料清单核验", matrix([record]))
                self.assertEqual(materials_warnings([record]), [])

    def test_explicit_archived_materials_are_retained_with_route_status(self) -> None:
        for archived_status, label in [("closed_expired", "职位已关闭或过期"), ("historical_only", "仅发现历史机会")]:
            with self.subTest(archived_status=archived_status):
                record = candidate("C Candidate", "C", route_status=archived_status)
                record["applicationReadiness"]["documentRequirements"][0]["requirementStatus"] = "unverified"
                text = matrix([record])
                self.assertIn(f"路径状态：{label} ({archived_status})", text)
                self.assertIn("Two independent academic references", text)
                self.assertIn(SOURCE["url"], text)
                self.assertNotIn("未按新材料清单核验", text)
                self.assertEqual(materials_warnings([record]), [])

    def test_past_rules_do_not_fill_an_unaudited_current_route(self) -> None:
        record = candidate("B Candidate", "B", route_status="historical_only")
        record["opportunities"].append({
            "id": "current-route",
            "routeName": "Current programme",
            "scope": "programme",
            "status": "route_confirmed_no_vacancy",
        })
        text = matrix([record])
        self.assertIn("Current programme (current-route) | 材料清单未分项核验", text)
        self.assertIn("historical_only", text)
        self.assertTrue(any("至少一条当前申请路径" in warning for warning in materials_warnings([record])))
        # A separate completed current route removes that gap; archived rules remain historical.
        completed = copy.deepcopy(record)
        completed["applicationReadiness"]["documentRequirements"].append(material_rule("current-route"))
        self.assertEqual(materials_warnings([completed]), [])


if __name__ == "__main__":
    unittest.main()
