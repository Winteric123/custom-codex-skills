#!/usr/bin/env python3
"""Focused profile contracts; all filesystem fixtures are temporary cases."""

from __future__ import annotations

import copy
import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from case_utils import (
    DEFAULT_TOPIC_BY_PROFILE,
    resolve_topic_profile,
    topic_has_direct_anchor,
)
from render_outputs import common_header
from validate_case import Report, validate_case_metadata, validate_sources


SCRIPT_DIR = Path(__file__).resolve().parent
RUN_SCRIPT = (
    "import runpy,sys; from pathlib import Path; "
    "script=Path(sys.argv.pop(1)); sys.path.insert(0,str(script.parent)); "
    "runpy.run_path(str(script),run_name='__main__')"
)
AS_OF = dt.date.today()


def research_source(claim: str) -> dict:
    return {
        "id": "synthetic-research-source",
        "type": "official_research_profile",
        "authorityClass": "official_institution",
        "medium": "webpage",
        "title": "Ada Example: research profile",
        "url": "https://example.edu/research/ada-example",
        "publisher": "Example University",
        "accessedDate": AS_OF.isoformat(),
        "publishedDate": "",
        "status": "current",
        "claimDomains": ["research"],
        "subjectIds": ["ada-example"],
        "topicRelevance": "direct",
        "claim": claim,
        "personRoles": [{
            "subjectId": "ada-example",
            "roleType": "group_leader",
            "exactLabel": "Ada Example is the group leader.",
            "topicRelevance": "direct",
        }],
    }


def source_errors(source: dict, profile: str | None = None) -> list[str]:
    report = Report()
    args = ([copy.deepcopy(source)], AS_OF, True, report)
    if profile is None:
        validate_sources(*args)
    else:
        validate_sources(*args, topic_profile=profile)
    return report.errors


class TopicProfileContracts(unittest.TestCase):
    def test_missing_profile_retains_legacy(self) -> None:
        self.assertEqual(resolve_topic_profile({}), "lung_cancer")
        source = research_source("This is non-lung melanoma tumour immunometabolism research.")
        legacy = source_errors(source)
        explicit = source_errors(source, "lung_cancer")
        self.assertEqual(legacy, explicit)
        self.assertTrue(any("explicit non-lung/topic-negation" in error for error in legacy))

    def test_explicit_invalid_profiles_rejected(self) -> None:
        for value in ["", "generic", None, [], True]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "topicProfile"):
                    resolve_topic_profile({"topicProfile": value})
                report = Report()
                validate_case_metadata({"schemaVersion": "1.2", "topicProfile": value}, False, report)
                self.assertTrue(any("topicProfile" in error for error in report.errors))

    def test_non_lung_oncology_is_direct_in_cv_profile(self) -> None:
        for claim in [
            "This is non-lung melanoma tumour immunometabolism research.",
            "Non-lung tumour immunometabolism research.",
        ]:
            with self.subTest(claim=claim):
                source = research_source(claim)
                self.assertEqual(source_errors(source, "cv_aligned_oncology"), [])
                self.assertTrue(any("explicit non-lung/topic-negation" in error
                                    for error in source_errors(source, "lung_cancer")))

    def test_generic_methods_do_not_supply_oncology_anchor(self) -> None:
        for claim in [
            "Research in immunology and immunometabolism of healthy tissues.",
            "Research in multi-omics, machine learning, and data science.",
            "Research in precision medicine and clinical biomarkers of diabetes.",
        ]:
            with self.subTest(claim=claim):
                errors = source_errors(research_source(claim), "cv_aligned_oncology")
                self.assertTrue(any("source-specific cancer/oncology anchor" in error for error in errors))

    def test_negated_lung_claim_alone_does_not_supply_oncology_anchor(self) -> None:
        for claim in [
            "This is not lung cancer research.",
            "Lung cancer is not a research focus.",
            "肺癌并非该研究者的公开研究主线。",
        ]:
            with self.subTest(claim=claim):
                errors = source_errors(research_source(claim), "cv_aligned_oncology")
                self.assertTrue(any("source-specific cancer/oncology anchor" in error for error in errors))

    def test_non_oncology_statements_rejected(self) -> None:
        for claim in [
            "This is not cancer research; the study concerns healthy-tissue immunity.",
            "Non-oncology immunometabolism research.",
            "这不是肿瘤研究，研究项目关注健康组织免疫。",
        ]:
            with self.subTest(claim=claim):
                errors = source_errors(research_source(claim), "cv_aligned_oncology")
                self.assertTrue(any("explicit non-oncology/topic-negation" in error for error in errors))

    def test_anchor_uses_source_text_not_url_or_methods(self) -> None:
        source = research_source("Research in healthy-tissue immunity.")
        source["url"] = "https://example.edu/cancer/research"
        self.assertTrue(source_errors(source, "cv_aligned_oncology"))
        for field in ["title", "claim", "exactLabel"]:
            with self.subTest(field=field):
                anchored = copy.deepcopy(source)
                if field == "exactLabel":
                    anchored["personRoles"][0][field] += " Leads melanoma immunity research."
                else:
                    anchored[field] += " Melanoma immunity research."
                self.assertEqual(source_errors(anchored, "cv_aligned_oncology"), [])

    def test_programme_research_uses_selected_profile(self) -> None:
        source = research_source("Ada Example supervises thesis research in cancer immunometabolism.")
        source["type"] = "doctoral_rule_supervision"
        source["title"] = "Example doctoral programme"
        source["claimDomains"] = ["research", "doctoral_rule"]
        source["personRoles"][0]["roleType"] = "programme_host"
        source["personRoles"][0]["exactLabel"] = "Ada Example is a programme host."
        self.assertEqual(source_errors(source, "cv_aligned_oncology"), [])
        self.assertTrue(any("cannot carry direct/adjacent topic evidence" in error
                            for error in source_errors(source, "lung_cancer")))
        source["claim"] = "Ada Example supervises thesis research in healthy-tissue immunometabolism."
        errors = source_errors(source, "cv_aligned_oncology")
        self.assertTrue(any("cannot carry direct/adjacent topic evidence" in error for error in errors))
        source["claim"] = "Ada Example is listed on the cancer doctoral programme page."
        errors = source_errors(source, "cv_aligned_oncology")
        self.assertTrue(any("cannot carry direct/adjacent topic evidence" in error for error in errors))

    def test_profile_anchor_includes_disease_names(self) -> None:
        for text in ["melanoma", "leukaemia", "lymphoma", "NSCLC", "肿瘤免疫", "肺癌"]:
            with self.subTest(text=text):
                self.assertTrue(topic_has_direct_anchor("cv_aligned_oncology", text))
        self.assertFalse(topic_has_direct_anchor("cv_aligned_oncology", "immunometabolism multi-omics AI"))

    def test_render_preserves_legacy_header_and_displays_broad_profile(self) -> None:
        case = {"location": "Example", "topic": "lung cancer", "asOf": AS_OF.isoformat()}
        legacy = common_header("Report", case, [])
        explicit = common_header("Report", {**case, "topicProfile": "lung_cancer"}, [])
        self.assertEqual(legacy, explicit)
        self.assertFalse(any("主题证据范围" in line for line in legacy))
        broad = common_header("Report", {**case, "topicProfile": "cv_aligned_oncology"}, [])
        self.assertTrue(any("cv_aligned_oncology" in line for line in broad))


class InitProfileContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="supervisor-topic-profiles-")
        self.workspace = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def init(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-c", RUN_SCRIPT,
             str(SCRIPT_DIR / "init_case.py"), "--workspace", str(self.workspace),
             "--location", "Example", "--schools", "Example University", *args],
            check=False, capture_output=True, text=True, encoding="utf-8",
        )

    def created_case(self, *args: str) -> tuple[Path, dict]:
        result = self.init(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(json.loads(result.stdout)["caseDir"])
        return path, json.loads((path / "data" / "case.json").read_text(encoding="utf-8"))

    def test_defaults_and_profile_directories_do_not_collide(self) -> None:
        lung_path, lung = self.created_case()
        cv_path, cv = self.created_case("--topic-profile", "cv_aligned_oncology")
        self.assertEqual(lung["topicProfile"], "lung_cancer")
        self.assertEqual(lung["topic"], DEFAULT_TOPIC_BY_PROFILE["lung_cancer"])
        self.assertEqual(cv["topic"], DEFAULT_TOPIC_BY_PROFILE["cv_aligned_oncology"])
        self.assertIn("-lung-cancer-phd-supervisors-", lung_path.name)
        self.assertIn("-cv-oncology-", cv_path.name)
        self.assertNotEqual(lung_path, cv_path)
        custom_path, custom = self.created_case(
            "--topic-profile", "cv_aligned_oncology", "--topic", "Cancer genetic epidemiology"
        )
        self.assertEqual(custom["topic"], "Cancer genetic epidemiology")
        self.assertNotEqual(cv_path, custom_path)

    def test_legacy_resume_does_not_rewrite_metadata(self) -> None:
        path, case = self.created_case()
        case.pop("topicProfile")
        sentinel = path / "data" / "case.json"
        sentinel.write_text(json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        original = sentinel.read_bytes()
        result = self.init("--resume")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "existing")
        self.assertEqual(sentinel.read_bytes(), original)

    def test_resume_rejects_profile_change_without_rewriting(self) -> None:
        path, case = self.created_case()
        sentinel = path / "data" / "case.json"
        original = sentinel.read_bytes()
        result = self.init("--resume", "--output-dir", str(path),
                           "--topic-profile", "cv_aligned_oncology", "--topic", case["topic"])
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertIn("topicProfile", result.stderr)
        self.assertEqual(sentinel.read_bytes(), original)

    def test_cv_resume_and_invalid_inputs(self) -> None:
        path, _ = self.created_case("--topic-profile", "cv_aligned_oncology")
        original = (path / "data" / "case.json").read_bytes()
        result = self.init("--topic-profile", "cv_aligned_oncology", "--resume")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((path / "data" / "case.json").read_bytes(), original)
        self.assertEqual(self.init("--topic-profile", "unknown").returncode, 2)
        self.assertEqual(self.init("--topic", " ").returncode, 2)


if __name__ == "__main__":
    unittest.main()
