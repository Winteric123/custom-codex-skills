#!/usr/bin/env python3
"""Focused tests for the optional contact-audit contract."""

from __future__ import annotations

import datetime as dt
import unittest

from validate_case import Report, validate_contact_audit, validate_contacts


class ContactAuditContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record_map = {
            "example-university-person": {
                "id": "example-university-person",
                "contacts": [
                    {
                        "type": "contact_form",
                        "value": "https://example.edu/person/contact",
                    }
                ],
            }
        }
        self.source_map = {
            "src-profile": {
                "id": "src-profile",
                "authorityClass": "official_institution",
                "status": "current",
                "claimDomains": ["current_role", "contact"],
                "subjectIds": ["example-university-person"],
            },
            "src-form": {
                "id": "src-form",
                "authorityClass": "official_institution",
                "status": "current",
                "claimDomains": ["contact"],
                "subjectIds": ["example-university-person"],
            },
            "src-paper": {
                "id": "src-paper",
                "authorityClass": "primary_publication",
                "claimDomains": ["contact"],
                "subjectIds": ["example-university-person"],
            },
        }

    def valid_audit(self) -> dict:
        return {
            "schemaVersion": "1.0",
            "checkedAt": "2026-10-25",
            "records": [
                {
                    "candidateId": "example-university-person",
                    "checkedAt": "2026-10-25",
                    "currentInstitutionZh": "示例大学医学中心",
                    "searchAudit": {
                        "officialFallbacksExhaustedBeforePublication": True,
                        "steps": [
                            {
                                "stage": "current_official_primary",
                                "routeType": "personal_profile",
                                "resultZh": "已检查本人官网页面。",
                                "sourceIds": ["src-profile"],
                            },
                            {
                                "stage": "current_official_fallback",
                                "routeType": "person_directed_form",
                                "resultZh": "找到本人定向联系表单。",
                                "sourceIds": ["src-form"],
                            },
                        ],
                    },
                    "channels": [
                        {
                            "channelId": "official-person-form",
                            "type": "contact_form",
                            "value": "https://example.edu/person/contact",
                            "owner": "candidate",
                            "currentness": "current_official",
                            "sourceIds": ["src-form"],
                            "candidateBound": True,
                        }
                    ],
                    "preferredRoute": {
                        "preferredChannelId": "official-person-form",
                        "reasonZh": "当前官方且本人定向。",
                        "sameDayRecheckRequired": False,
                    },
                    "contactPolicy": "not_stated",
                }
            ],
        }

    def test_valid_contact_audit(self) -> None:
        report = Report()
        validate_contact_audit(
            self.valid_audit(),
            self.record_map,
            self.source_map,
            dt.date(2026, 10, 25),
            report,
        )
        self.assertEqual([], report.errors)

    def test_rejects_missing_ownership_sources_invalid_preference_and_mixed_not_public(self) -> None:
        audit = self.valid_audit()
        channels = audit["records"][0]["channels"]
        channels[0].pop("owner")
        channels[0].pop("sourceIds")
        channels.extend(
            [
                {
                    "channelId": "official-person-form",
                    "type": "not_public",
                    "value": "",
                    "owner": "unclear",
                    "currentness": "not_public",
                    "sourceIds": [],
                    "candidateBound": False,
                }
            ]
        )
        audit["records"][0]["preferredRoute"]["preferredChannelId"] = "missing-channel"
        report = Report()
        validate_contact_audit(
            audit,
            self.record_map,
            self.source_map,
            dt.date(2026, 10, 25),
            report,
        )
        joined = "\n".join(report.errors)
        self.assertIn("owner has invalid or missing value", joined)
        self.assertIn("sourceIds is required", joined)
        self.assertIn("duplicate channelId", joined)
        self.assertIn("not_public cannot coexist", joined)
        self.assertIn("preferredChannelId does not resolve", joined)

    def test_requires_official_primary_and_fallback_before_publication(self) -> None:
        audit = self.valid_audit()
        record = audit["records"][0]
        record["searchAudit"] = {
            "officialFallbacksExhaustedBeforePublication": False,
            "steps": [
                {
                    "stage": "publication",
                    "routeType": "primary_publication",
                    "resultZh": "先检索了论文。",
                    "sourceIds": ["src-paper"],
                },
                {
                    "stage": "current_official_fallback",
                    "routeType": "person_directed_form",
                    "resultZh": "随后才检查官方表单。",
                    "sourceIds": ["src-form"],
                },
            ],
        }
        record["channels"] = [
            {
                "channelId": "paper-email-2025",
                "type": "publication_correspondence_email",
                "value": "person@example.edu",
                "owner": "candidate",
                "currentness": "publication_time_only",
                "sourceIds": ["src-paper"],
                "candidateBound": True,
            }
        ]
        record["preferredRoute"] = {
            "preferredChannelId": "paper-email-2025",
            "reasonZh": "没有其他可用渠道。",
            "sameDayRecheckRequired": True,
        }
        report = Report()
        validate_contact_audit(
            audit,
            self.record_map,
            self.source_map,
            dt.date(2026, 10, 25),
            report,
        )
        joined = "\n".join(report.errors)
        self.assertIn("official fallbacks were exhausted first", joined)
        self.assertIn("preceding official-primary step", joined)
        self.assertIn("records an official search after publication", joined)

    def test_strict_contacts_reject_unknown_keys_and_mixed_not_public(self) -> None:
        record = {
            "id": "example-university-person",
            "name": "Example Person",
            "verifiedAt": "2026-10-25",
            "schoolId": "example-university",
            "contacts": [
                {
                    "type": "contact_form",
                    "value": "https://example.edu/person/contact",
                    "status": "published_current",
                    "sourceIds": ["src-form"],
                    "owner": "candidate",
                },
                {
                    "type": "not_public",
                    "value": "",
                    "status": "not_public",
                    "sourceIds": [],
                },
            ],
        }
        report = Report()
        validate_contacts(record, record["id"], self.source_map, True, report)
        joined = "\n".join(report.errors)
        self.assertIn("unsupported strict-schema keys", joined)
        self.assertIn("not_public cannot coexist", joined)

    def test_supplement_requires_atomic_sources_and_current_official_preference(self) -> None:
        audit = self.valid_audit()
        record = audit["records"][0]
        record["channels"].append(
            {
                "channelId": "paper-email-2025",
                "type": "publication_correspondence_email",
                "value": "person@example.edu",
                "owner": "candidate",
                "currentness": "publication_time_only",
                "sourceIds": ["src-paper"],
                "candidateBound": True,
            }
        )
        record["searchAudit"]["steps"].append(
            {
                "stage": "publication",
                "routeType": "primary_publication",
                "resultZh": "找到论文通讯邮箱。",
                "sourceIds": ["src-paper"],
            }
        )
        record["preferredRoute"] = {
            "preferredChannelId": "paper-email-2025",
            "reasonZh": "错误地优先选择论文邮箱。",
            "sameDayRecheckRequired": True,
        }
        broken_sources = {
            key: dict(value) for key, value in self.source_map.items()
        }
        broken_sources["src-form"] = {
            **broken_sources["src-form"],
            "status": "historical",
            "claimDomains": ["current_role"],
            "subjectIds": [],
        }
        broken_sources["src-paper"] = {
            **broken_sources["src-paper"],
            "claimDomains": ["research"],
            "subjectIds": [],
        }
        report = Report()
        validate_contact_audit(
            audit,
            self.record_map,
            broken_sources,
            dt.date(2026, 10, 25),
            report,
        )
        joined = "\n".join(report.errors)
        self.assertIn("current, contact-domain official-institution source", joined)
        self.assertIn("candidate-bound, contact-domain primary-publication source", joined)
        self.assertIn("must select a current_official channel", joined)

    def test_rejects_cross_file_not_public_conflict_in_both_directions(self) -> None:
        audit = self.valid_audit()
        record_map = {
            "example-university-person": {
                **self.record_map["example-university-person"],
                "contacts": [
                    {"type": "not_public", "value": "", "status": "not_public", "sourceIds": []}
                ],
            }
        }
        report = Report()
        validate_contact_audit(
            audit,
            record_map,
            self.source_map,
            dt.date(2026, 10, 25),
            report,
        )
        self.assertIn("valued supplemental channels conflict", "\n".join(report.errors))


if __name__ == "__main__":
    unittest.main()
