#!/usr/bin/env python3
"""Application-material contracts using synthetic helper fixtures only."""

from __future__ import annotations

import copy
import datetime as dt
import unittest

from validate_case import (
    CORE_APPLICATION_MATERIAL_TYPES,
    Report,
    validate_application_materials,
    validate_case_metadata,
)


AS_OF = dt.date(2026, 10, 13)
PERSON_ID = "synthetic-person"
SCHOOL_ID = "synthetic-school"


def source(**changes) -> dict:
    return {
        "id": "synthetic-admissions",
        "authorityClass": "official_institution",
        "status": "current",
        "claimDomains": ["doctoral_rule", "admissions_funding"],
        "subjectIds": [SCHOOL_ID],
        "accessedDate": AS_OF.isoformat(),
        **changes,
    }


def row(material_type: str = "motivation_letter", **changes) -> dict:
    return {
        "routeId": "synthetic-route",
        "materialType": material_type,
        "requirementStatus": "required",
        "submissionStage": "initial_application",
        "summary": "Synthetic rule: one document is required.",
        "formatAndLength": "not_public: format and length not stated",
        "quantity": 1,
        "submitter": "applicant",
        "submissionMethod": "Application portal",
        "checkedAt": AS_OF.isoformat(),
        "sourceIds": ["synthetic-admissions"],
        **changes,
    }


def record(tier: str = "A", **changes) -> dict:
    return {
        "id": PERSON_ID,
        "schoolId": SCHOOL_ID,
        "priorityTier": tier,
        "opportunities": [{"id": "synthetic-route", "status": "route_confirmed_no_vacancy"}],
        "applicationReadiness": {
            "documentRequirements": [row(kind) for kind in sorted(CORE_APPLICATION_MATERIAL_TYPES)]
        },
        **changes,
    }


def errors(value: dict, *, flagged: bool = True, strict: bool = True, sources: dict | None = None) -> list[str]:
    report = Report()
    validate_application_materials(
        copy.deepcopy(value), PERSON_ID,
        sources if sources is not None else {"synthetic-admissions": source()},
        AS_OF, strict, report, audit_required=flagged,
    )
    return report.errors


class ApplicationMaterialContracts(unittest.TestCase):
    def test_valid_core_checks_for_all_target_tiers(self) -> None:
        for tier in ["A", "B", "C"]:
            with self.subTest(tier=tier):
                self.assertEqual(errors(record(tier)), [])

    def test_legacy_missing_array_is_not_migrated(self) -> None:
        value = record(applicationReadiness={})
        self.assertEqual(errors(value, flagged=False), [])
        value.pop("applicationReadiness")
        self.assertEqual(errors(value, flagged=False), [])

    def test_strict_new_cases_require_arrays_and_non_strict_does_not(self) -> None:
        for tier in ["A", "B", "C"]:
            value = record(tier, applicationReadiness={})
            self.assertTrue(any("is required" in error for error in errors(value)))
            self.assertEqual(errors(value, strict=False), [])
        self.assertEqual(errors(record("D", applicationReadiness={})), [])

    def test_legacy_explicit_arrays_are_still_checked(self) -> None:
        value = record(applicationReadiness={"documentRequirements": "not an array"})
        self.assertTrue(any("must be an array" in error for error in errors(value, flagged=False)))
        value["applicationReadiness"]["documentRequirements"] = [row(quantity=0)]
        self.assertTrue(any("quantity" in error for error in errors(value, flagged=False, strict=False)))

    def test_each_active_route_needs_its_own_core_checks(self) -> None:
        value = record()
        value["opportunities"].append({"id": "second-route", "status": "unverified"})
        self.assertTrue(any("active route second-route" in error for error in errors(value)))
        for kind in CORE_APPLICATION_MATERIAL_TYPES:
            value["applicationReadiness"]["documentRequirements"].append(row(kind, routeId="second-route"))
        self.assertEqual(errors(value), [])

    def test_historical_and_closed_routes_do_not_need_core_checks(self) -> None:
        value = record()
        for status in ["closed_expired", "historical_only"]:
            value["opportunities"].append({"id": status.replace("_", "-"), "status": status})
        self.assertEqual(errors(value), [])

    def test_duplicate_material_stage_rejected_but_separate_stage_allowed(self) -> None:
        value = record()
        value["applicationReadiness"]["documentRequirements"].append(row("motivation_letter"))
        self.assertTrue(any("duplicate route/material/stage" in error for error in errors(value)))
        value["applicationReadiness"]["documentRequirements"][-1]["submissionStage"] = "after_shortlisting"
        self.assertEqual(errors(value), [])

    def test_unknown_status_may_be_unsourced_but_asserted_status_may_not(self) -> None:
        for status in ["not_public", "unverified"]:
            value = record()
            value["applicationReadiness"]["documentRequirements"] = [
                row(kind, requirementStatus=status, sourceIds=[], quantity=None)
                for kind in CORE_APPLICATION_MATERIAL_TYPES
            ]
            self.assertEqual(errors(value), [])
        for status in ["required", "optional", "not_required", "conditional"]:
            value = record()
            value["applicationReadiness"]["documentRequirements"][0] = row(requirementStatus=status, sourceIds=[])
            self.assertTrue(any("sourceIds must contain" in error for error in errors(value)))

    def test_every_document_row_requires_existing_route(self) -> None:
        for route_id in ["unknown-route", "", None, []]:
            value = record()
            value["applicationReadiness"]["documentRequirements"][0]["routeId"] = route_id
            self.assertTrue(any("existing opportunities" in error for error in errors(value)))

    def test_fields_reject_empty_or_invalid_values_without_crashing(self) -> None:
        invalid = {
            "materialType": ["cv"], "requirementStatus": ["required"],
            "submissionStage": [], "summary": "", "formatAndLength": None,
            "quantity": True, "submitter": [], "submissionMethod": "",
            "checkedAt": "20261013", "sourceIds": [None],
        }
        for field, bad_value in invalid.items():
            with self.subTest(field=field):
                value = record()
                value["applicationReadiness"]["documentRequirements"][0][field] = bad_value
                self.assertTrue(any(field in error for error in errors(value)))

    def test_quantity_is_positive_integer_or_explicit_null(self) -> None:
        for quantity in [None, 1, 3]:
            value = record()
            value["applicationReadiness"]["documentRequirements"][0]["quantity"] = quantity
            self.assertEqual(errors(value), [])
        for quantity in [0, -1, 1.5, "2", True]:
            value = record()
            value["applicationReadiness"]["documentRequirements"][0]["quantity"] = quantity
            self.assertTrue(any("quantity" in error for error in errors(value)))
        value = record()
        del value["applicationReadiness"]["documentRequirements"][0]["quantity"]
        self.assertTrue(any("quantity" in error for error in errors(value)))

    def test_current_official_bound_sources_are_required(self) -> None:
        for change in [
            {"authorityClass": "primary_publication"}, {"status": "historical"},
            {"subjectIds": ["different-school"]}, {"claimDomains": ["research"]},
            {"accessedDate": ""},
        ]:
            with self.subTest(change=change):
                self.assertTrue(errors(record(), sources={"synthetic-admissions": source(**change)}))
        candidate_bound = source(subjectIds=[PERSON_ID])
        self.assertEqual(errors(record(), sources={"synthetic-admissions": candidate_bound}), [])
        joint = record(additionalSchoolIds=["joint-school"])
        self.assertEqual(errors(joint, sources={"synthetic-admissions": source(subjectIds=["joint-school"])}), [])

    def test_contact_only_source_cannot_prove_formal_application_documents(self) -> None:
        contact = source(claimDomains=["contact"])
        value = record(applicationReadiness={"documentRequirements": [row("supervisor_enquiry")]})
        self.assertEqual(errors(value, flagged=False, sources={"synthetic-admissions": contact}), [])
        value["applicationReadiness"]["documentRequirements"][0]["materialType"] = "recommendation_letters"
        self.assertTrue(any("claim domain" in error for error in errors(value, flagged=False, sources={"synthetic-admissions": contact})))

    def test_evidence_and_audit_dates_cannot_be_after_verification(self) -> None:
        value = record()
        value["applicationReadiness"]["documentRequirements"][0]["checkedAt"] = "2026-10-14"
        self.assertTrue(any("later than case asOf" in error for error in errors(value)))
        value["applicationReadiness"]["documentRequirements"][0]["checkedAt"] = "2026-10-12"
        self.assertTrue(any("accessed after checkedAt" in error for error in errors(value)))

    def test_unknown_sources_and_nested_outreach_prose_rejected(self) -> None:
        value = record()
        value["applicationReadiness"]["documentRequirements"][0]["sourceIds"] = ["missing-source"]
        self.assertTrue(any("unknown source" in error for error in errors(value)))
        for field in ["summary", "formatAndLength", "submissionMethod"]:
            value = record()
            value["applicationReadiness"]["documentRequirements"][0][field] = "I am writing to apply."
            self.assertTrue(any("contains correspondence prose" in error for error in errors(value)))

    def test_optional_case_flag_must_be_boolean(self) -> None:
        for flag in ["true", None, 1, [], {}]:
            report = Report()
            validate_case_metadata({"schemaVersion": "1.2", "applicationMaterialsAuditRequired": flag}, False, report)
            self.assertTrue(any("applicationMaterialsAuditRequired must be a boolean" in error for error in report.errors))
        for flag in [True, False]:
            report = Report()
            validate_case_metadata({"schemaVersion": "1.2", "applicationMaterialsAuditRequired": flag}, False, report)
            self.assertFalse(any("applicationMaterialsAuditRequired" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
