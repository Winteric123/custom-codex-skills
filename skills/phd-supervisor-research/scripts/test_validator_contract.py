#!/usr/bin/env python3
"""Mutation-based smoke tests for the strict supervisor-case validator.

The script copies one already-valid case into temporary directories, applies a
single invalid mutation, and confirms that strict validation rejects it. It
never edits the supplied case directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


JSON_FILES = ["case.json", "schools.json", "coverage.json", "records.json", "sources.json"]


def load_case(case_dir: Path) -> dict[str, object]:
    data_dir = case_dir / "data"
    return {
        name: json.loads((data_dir / name).read_text(encoding="utf-8"))
        for name in JSON_FILES
    }


def write_case(case_dir: Path, payloads: dict[str, object]) -> None:
    data_dir = case_dir / "data"
    for name, payload in payloads.items():
        (data_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def record(payloads: dict[str, object], candidate_id: str) -> dict:
    return next(item for item in payloads["records.json"] if item["id"] == candidate_id)


def source_map(payloads: dict[str, object]) -> dict[str, dict]:
    return {item["id"]: item for item in payloads["sources.json"]}


def missing_location_resolution(payloads: dict[str, object]) -> None:
    payloads["case.json"].pop("locationResolution", None)


def positive_rank_outside_threshold(payloads: dict[str, object]) -> None:
    payloads["schools.json"][0]["qs"]["rank"] = "301"


def person_role_not_in_subjects(payloads: dict[str, object]) -> None:
    source = next(item for item in payloads["sources.json"] if item.get("personRoles"))
    source["personRoles"][0]["subjectId"] = "ghost-person"


def generic_person_role_label(payloads: dict[str, object]) -> None:
    source = next(item for item in payloads["sources.json"] if item.get("personRoles"))
    source["personRoles"][0]["exactLabel"] = "named profile/group member"


def migrated_research_url_role_label(payloads: dict[str, object]) -> None:
    source = next(item for item in payloads["sources.json"] if item.get("personRoles"))
    source["personRoles"][0]["exactLabel"] = (
        "Candidate-associated official research URL; no person-specific research role is retained"
    )


def migrated_profile_contact_role_label(payloads: dict[str, object]) -> None:
    source = next(item for item in payloads["sources.json"] if item.get("personRoles"))
    source["personRoles"][0]["exactLabel"] = (
        "Candidate-bound official profile/contact URL; no source-specific role label is retained"
    )


def negated_principal_role_label(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    for source_id in candidate["researchSourceIds"]:
        source = sources[source_id]
        for role in source.get("personRoles", []):
            if role.get("subjectId") == candidate["id"] and role.get("topicRelevance") == "direct":
                role["roleType"] = "principal_investigator"
                role["exactLabel"] = "Michele De Palma is a co-applicant, not the principal investigator."
                return
    raise AssertionError("No direct Michele De Palma role source found")


def coauthor_upgraded_to_senior(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = sources[candidate["directEvidenceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "senior_or_corresponding_author"
    role["exactLabel"] = "Michele De Palma is a coauthor, not the corresponding author."


def first_author_mislabeled_coauthor(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["directEvidenceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "coauthor"
    role["exactLabel"] = (
        "Michele De Palma: De Palma is first author; Jane Smith is last and corresponding author."
    )


def first_author_mislabeled_senior_cross_person(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["directEvidenceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "senior_or_corresponding_author"
    role["exactLabel"] = "Michele De Palma: De Palma为第一作者，Jane Smith为末位及通讯作者。"


def coauthor_mislabeled_senior_cross_person(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["directEvidenceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "senior_or_corresponding_author"
    role["exactLabel"] = "Michele De Palma: De Palma为共同作者，Jane Smith为末位及通讯作者。"


def equal_contribution_co_senior_allowed(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["directEvidenceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "senior_or_corresponding_author"
    role["exactLabel"] = (
        "Michele De Palma: De Palma为倒数第二作者，并与末位作者标注共同贡献。"
    )


def direct_topic_negated_in_claim(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = next(
        sources[source_id]
        for source_id in candidate["researchSourceIds"]
        if any(
            role.get("subjectId") == candidate["id"] and role.get("topicRelevance") == "direct"
            for role in sources[source_id].get("personRoles", [])
        )
    )
    source["claim"] = "The page explicitly says this is not lung-cancer research."


def direct_topic_negated_in_label(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = next(
        sources[source_id]
        for source_id in candidate["researchSourceIds"]
        if any(
            role.get("subjectId") == candidate["id"] and role.get("topicRelevance") == "direct"
            for role in sources[source_id].get("personRoles", [])
        )
    )
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["exactLabel"] = "肺癌并非该研究者的公开研究主线。"


def source_topic_disagrees_with_person_roles(payloads: dict[str, object]) -> None:
    source = next(
        item
        for item in payloads["sources.json"]
        if "research" in item.get("claimDomains", [])
        and item.get("personRoles")
        and item.get("topicRelevance") == "direct"
    )
    source["topicRelevance"] = "background"


def migrated_summary_used_as_topic_evidence(payloads: dict[str, object]) -> None:
    source = next(
        item
        for item in payloads["sources.json"]
        if "research" in item.get("claimDomains", [])
        and any(
            role.get("topicRelevance") == "direct"
            for role in item.get("personRoles", [])
        )
    )
    person_name = source.get("title", "Candidate").split(":", 1)[0]
    source["claim"] = (
        f"Institutional research page retained for {person_name}'s documented focus: lung cancer"
    )


def generic_supporting_page_used_as_topic_evidence(payloads: dict[str, object]) -> None:
    source = next(
        item
        for item in payloads["sources.json"]
        if "research" in item.get("claimDomains", [])
        and any(role.get("topicRelevance") == "direct" for role in item.get("personRoles", []))
    )
    source["claim"] = "Official page supporting lung cancer."


def unsupported_s1_current_supervision(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    proof_id = candidate["supervisionBasis"]["traineeOrProgrammeSourceIds"][0]
    source = source_map(payloads)[proof_id]
    source["claimDomains"] = [x for x in source["claimDomains"] if x != "doctoral_supervision"]


def split_source_s1_person_eligibility(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    candidate["supervisionBasis"]["basisType"] = "person_eligibility_explicit"
    candidate["supervisionBasis"]["eligibilityStatus"] = "confirmed"
    # The existing page identifies current co-supervision, not prospective
    # eligibility. Merely adding a doctoral-rule domain must remain insufficient.
    proof_id = candidate["supervisionBasis"]["traineeOrProgrammeSourceIds"][0]
    source = source_map(payloads)[proof_id]
    source["type"] = "doctoral_rule_supervision"
    if "doctoral_rule" not in source["claimDomains"]:
        source["claimDomains"].append("doctoral_rule")


def t1_without_current_independent_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    for source_id in set(candidate["currentRoleSourceIds"] + candidate["researchSourceIds"]):
        source = sources[source_id]
        if (
            source.get("status") == "current"
            and source.get("authorityClass") == "official_institution"
            and candidate["id"] in source.get("subjectIds", [])
        ):
            for role in source.get("personRoles", []):
                if role.get("subjectId") == candidate["id"]:
                    role["roleType"] = "coauthor"


def t3_without_current_direct_project(payloads: dict[str, object]) -> None:
    candidate = next(item for item in payloads["records.json"] if item["topicDirectness"] == "T3")
    sources = source_map(payloads)
    changed = 0
    for source_id in candidate["researchSourceIds"]:
        source = sources[source_id]
        if source.get("status") != "current":
            continue
        for role in source.get("personRoles", []):
            if role.get("subjectId") == candidate["id"] and role.get("topicRelevance") == "direct":
                role["topicRelevance"] = "adjacent"
                changed += 1
    if not changed:
        raise AssertionError("No current direct T3 project source found")


def candidates_found_with_negative_unit(payloads: dict[str, object]) -> None:
    row = next(item for item in payloads["coverage.json"] if item["status"] == "candidates_found")
    row["units"] = ["No qualifying candidates found in this branch"]


def coverage_candidate_without_bound_source(payloads: dict[str, object]) -> None:
    row = next(item for item in payloads["coverage.json"] if item["status"] == "candidates_found")
    candidate_id = row["candidateIds"][0]
    sources = source_map(payloads)
    row["sourceIds"] = [
        source_id
        for source_id in row["sourceIds"]
        if candidate_id not in sources[source_id].get("subjectIds", [])
    ]


def audit_predates_portal(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    candidate["recruitmentAudit"]["checkedAt"] = "2026-09-06"


def verification_predates_role_source(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["verifiedAt"] = "2026-09-06"


def nonblank_not_public_contact(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["contacts"].append(
        {
            "type": "not_public",
            "value": "guessed@example.edu",
            "status": "not_public",
            "sourceIds": ["src-d4570b9bb30b"],
        }
    )


def split_source_personal_contact(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    contact = next(
        item for item in candidate["contacts"] if item["type"] in {"personal_email", "clinical_email"}
    )
    official_contact = sources[contact["sourceIds"][0]]
    official_contact["subjectIds"] = [candidate["schoolId"]]
    official_contact["personRoles"] = []
    candidate_only_noncontact = next(
        sources[source_id]
        for source_id in candidate["researchSourceIds"]
        if candidate["id"] in sources[source_id].get("subjectIds", [])
        and "contact" not in sources[source_id].get("claimDomains", [])
    )
    contact["sourceIds"] = [official_contact["id"], candidate_only_noncontact["id"]]


def other_person_email_mislabeled_personal(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    contact = next(item for item in candidate["contacts"] if item["type"] == "personal_email")
    contact["value"] = "person@example.edu"


def generic_mailbox_mislabeled_personal(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    contact = next(item for item in candidate["contacts"] if item["type"] == "personal_email")
    contact["value"] = "oncology-office@example.edu"


def doctoral_programme_used_as_person_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = sources[candidate["currentRoleSourceIds"][0]]
    source["type"] = "doctoral_rule_supervision"
    source["claimDomains"] = ["current_role", "doctoral_rule"]
    source["topicRelevance"] = "not_applicable"
    source["claim"] = "Official EDMS doctoral programme page."
    source["personRoles"] = [
        {
            "subjectId": candidate["id"],
            "roleType": "subject_profile",
            "exactLabel": "Michele De Palma: listed on the EDMS doctoral programme page",
            "topicRelevance": "background",
        }
    ]


def doctoral_programme_used_as_personal_contact(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    contact = next(item for item in candidate["contacts"] if item["type"] == "personal_email")
    source = sources[contact["sourceIds"][0]]
    source["type"] = "doctoral_rule_supervision"
    source["claimDomains"] = ["contact", "doctoral_rule"]
    source["topicRelevance"] = "not_applicable"
    source["claim"] = "Official EDMS doctoral programme page."
    source["personRoles"] = [
        {
            "subjectId": candidate["id"],
            "roleType": "programme_host",
            "exactLabel": "Michele De Palma: listed as a programme host",
            "topicRelevance": "background",
        }
    ]


def doctoral_programme_used_as_direct_research(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = sources[candidate["directEvidenceIds"][0]]
    source["type"] = "doctoral_rule_supervision"
    source["claimDomains"] = ["research", "doctoral_rule"]
    source["topicRelevance"] = "direct"
    source["claim"] = "Official EDMS doctoral programme page lists Michele De Palma."
    source["personRoles"] = [
        {
            "subjectId": candidate["id"],
            "roleType": "programme_host",
            "exactLabel": "Michele De Palma: listed as a programme host",
            "topicRelevance": "direct",
        }
    ]


def cross_person_research_claim_leak(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["directEvidenceIds"][0]]
    source["title"] = "Douglas Hanahan: official research evidence"
    source["claim"] = (
        "Institutional research page retained for Douglas Hanahan's documented focus: lung cancer"
    )
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["exactLabel"] = "Michele De Palma: named participant"


def cross_person_contact_claim_leak(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    contact = next(item for item in candidate["contacts"] if item["type"] == "personal_email")
    source = sources[contact["sourceIds"][0]]
    source["title"] = "Joerg Huelsken: contact source"
    source["claim"] = "Published contact used for Joerg Huelsken."
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["exactLabel"] = "Michele De Palma: laboratory head"


def discovery_lead_used_as_substantive_evidence(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["researchSourceIds"][0]]
    source["type"] = "discovery_lead"
    source["claimDomains"] = ["discovery"]
    source["topicRelevance"] = "not_applicable"
    source["personRoles"] = [
        {
            "subjectId": candidate["id"],
            "roleType": "mentioned_without_role",
            "exactLabel": "Discovery lead only; legacy association not used as role/topic evidence",
            "topicRelevance": "not_applicable",
        }
    ]


def pd_upgraded_to_independent_faculty(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["currentRoleSourceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "independent_faculty"
    role["exactLabel"] = "Michele De Palma: PD/Privatdozent and attending physician"


def attending_upgraded_to_unit_head(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source = source_map(payloads)[candidate["currentRoleSourceIds"][0]]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "unit_head"
    role["exactLabel"] = "Michele De Palma: attending physician"


def d_tier_direct_enquiry(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    candidate["opportunityStatus"] = "direct_enquiry_recommended"
    candidate["opportunities"][0]["status"] = "direct_enquiry_recommended"
    candidate["priorityTier"] = "D"


def direct_enquiry_with_unverified_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    candidate["opportunityStatus"] = "direct_enquiry_recommended"
    candidate["opportunities"][0]["status"] = "direct_enquiry_recommended"
    candidate["confidenceByClaim"]["currentRole"] = "unverified"


def complete_blocked_case_without_bounded_limitation(payloads: dict[str, object]) -> None:
    if not any(row.get("status") == "blocked_unverified" for row in payloads["coverage.json"]):
        row = payloads["coverage.json"][0]
        row.update(
            {
                "status": "blocked_unverified",
                "units": [],
                "candidateIds": [],
                "sourceIds": [],
                "notes": "Access blocked during recheck.",
            }
        )
    payloads["case.json"]["limitations"] = ["The report package was generated."]


def blocked_saturation_without_recheck(payloads: dict[str, object]) -> None:
    if not any(row.get("status") == "blocked_unverified" for row in payloads["coverage.json"]):
        row = payloads["coverage.json"][0]
        row.update(
            {
                "status": "blocked_unverified",
                "units": [],
                "candidateIds": [],
                "sourceIds": [],
                "notes": "Access blocked during recheck.",
            }
        )
    payloads["case.json"]["discoveryPasses"][-1]["queriesOrUnits"] = [
        "Final saturation result: zero additions"
    ]


def blocked_xhs_mislabeled_negative(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["xiaohongshuCheck"]["status"] = "not_found_publicly"


def future_direct_evidence(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source_map(payloads)[candidate["directEvidenceIds"][0]]["status"] = "future"


def legacy_opportunity_detail(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["opportunityDetail"] = "Currently recruiting"


def correspondence_in_research_handoff(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["applicationReadiness"]["researchGap"] = (
        "Subject: Prospective PhD application"
    )


def correspondence_in_nested_readiness(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["applicationReadiness"]["doctoralQuestions"][0] = (
        "Dear Professor De Palma, I would like to apply for your PhD position."
    )


def correspondence_in_work_package(payloads: dict[str, object]) -> None:
    record(payloads, "epfl-michele-de-palma")["doctoralWorkPackages"][0]["assumptions"] = (
        "I am writing to apply and please find my CV attached."
    )


def duplicate_formal_identifier_across_works(payloads: dict[str, object]) -> None:
    publications = [
        item
        for item in payloads["sources.json"]
        if item.get("type") == "publication" and item.get("identifiers", {}).get("pmid")
    ]
    first, second = publications[:2]
    second.setdefault("identifiers", {})["pmid"] = first["identifiers"]["pmid"]


def programme_host_used_as_academic_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    source = next(
        item
        for item in sources.values()
        if any(
            role.get("subjectId") == candidate["id"] and role.get("roleType") == "programme_host"
            for role in item.get("personRoles", [])
        )
    )
    candidate["claimSourceIds"]["academicRole"].append(source["id"])


def trial_role_used_as_admin_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "university-of-geneva-alfredo-addeo")
    sources = source_map(payloads)
    source = next(
        item
        for item in sources.values()
        if any(
            role.get("subjectId") == candidate["id"]
            and role.get("roleType") == "trial_responsible_investigator"
            for role in item.get("personRoles", [])
        )
    )
    source["claimDomains"] = sorted(set(source.get("claimDomains", [])) | {"current_role"})
    candidate["claimSourceIds"]["adminClinicalRole"].append(source["id"])


def programme_host_allowed_for_admin_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    sources = source_map(payloads)
    programme_source = next(
        item
        for item in sources.values()
        if any(
            role.get("subjectId") == candidate["id"] and role.get("roleType") == "programme_host"
            for role in item.get("personRoles", [])
        )
    )
    candidate["claimSourceIds"]["adminClinicalRole"] = [programme_source["id"]]


def non_specific_profile_used_as_academic_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source_id = candidate["claimSourceIds"]["academicRole"][0]
    source = source_map(payloads)[source_id]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "subject_profile"
    role["exactLabel"] = (
        "Official institutional staff profile for Michele De Palma; "
        "specific title not retained or inferred"
    )


def non_specific_profile_used_for_affiliation_role(payloads: dict[str, object]) -> None:
    candidate = record(payloads, "epfl-michele-de-palma")
    source_id = candidate["claimSourceIds"]["academicRole"][0]
    source = source_map(payloads)[source_id]
    role = next(item for item in source["personRoles"] if item["subjectId"] == candidate["id"])
    role["roleType"] = "subject_profile"
    role["exactLabel"] = (
        "Official institutional staff profile for Michele De Palma; "
        "specific title not retained or inferred"
    )
    candidate["academicRole"] = "unverified: exact current academic title not extracted"
    candidate["claimSourceIds"]["academicRole"] = []


def pubmed_host_mislabeled_as_institution(payloads: dict[str, object]) -> None:
    source = next(
        item
        for item in payloads["sources.json"]
        if item.get("type") == "publication"
        and "pubmed.ncbi.nlm.nih.gov" in str(item.get("url", "")).casefold()
    )
    # This pair previously bypassed the type/authority checks and could make a
    # PubMed record look like an institutional role/contact profile.
    source["type"] = "official_role_contact"
    source["authorityClass"] = "official_institution"
    source["claimDomains"] = sorted(
        set(source.get("claimDomains", [])) | {"current_role", "contact"}
    )


def cross_school_affiliation_without_school_binding(payloads: dict[str, object]) -> None:
    sources = source_map(payloads)
    for candidate in payloads["records.json"]:
        primary_school_id = candidate.get("schoolId")
        for affiliation in candidate.get("affiliations", []):
            additional_school_id = affiliation.get("schoolId")
            if not additional_school_id or additional_school_id == primary_school_id:
                continue
            matching_sources = [
                sources[source_id]
                for source_id in affiliation.get("sourceIds", [])
                if source_id in sources
                and sources[source_id].get("authorityClass") == "official_institution"
                and sources[source_id].get("status") == "current"
                and "current_role" in sources[source_id].get("claimDomains", [])
                and candidate["id"] in sources[source_id].get("subjectIds", [])
                and additional_school_id in sources[source_id].get("subjectIds", [])
            ]
            if not matching_sources:
                continue
            for source in matching_sources:
                source["subjectIds"] = [
                    subject_id
                    for subject_id in source.get("subjectIds", [])
                    if subject_id != additional_school_id
                ]
            return
    raise AssertionError("No cross-school affiliation with dual-bound official evidence found")


TESTS = [
    ("missing_location_resolution", missing_location_resolution, "locationResolution"),
    ("positive_rank_outside_threshold", positive_rank_outside_threshold, "exceeds top-300 scope"),
    ("person_role_not_in_subjects", person_role_not_in_subjects, "must also appear in source.subjectIds"),
    ("generic_person_role_label", generic_person_role_label, "contains placeholder text"),
    ("migrated_research_url_role_label", migrated_research_url_role_label, "contains placeholder text"),
    ("migrated_profile_contact_role_label", migrated_profile_contact_role_label, "contains placeholder text"),
    ("negated_principal_role_label", negated_principal_role_label, "contradicts roleType=principal_investigator"),
    ("coauthor_upgraded_to_senior", coauthor_upgraded_to_senior, "contradicts roleType=senior_or_corresponding_author"),
    ("first_author_mislabeled_coauthor", first_author_mislabeled_coauthor, "contradicts roleType=coauthor"),
    ("first_author_mislabeled_senior_cross_person", first_author_mislabeled_senior_cross_person, "stated only as first author"),
    ("coauthor_mislabeled_senior_cross_person", coauthor_mislabeled_senior_cross_person, "stated only as a coauthor"),
    ("direct_topic_negated_in_claim", direct_topic_negated_in_claim, "explicit non-lung/topic-negation"),
    ("direct_topic_negated_in_label", direct_topic_negated_in_label, "explicit non-lung/topic-negation"),
    ("source_topic_disagrees_with_person_roles", source_topic_disagrees_with_person_roles, "disagrees with personRoles aggregate"),
    ("migrated_summary_used_as_topic_evidence", migrated_summary_used_as_topic_evidence, "relies on a migrated candidate summary"),
    ("generic_supporting_page_used_as_topic_evidence", generic_supporting_page_used_as_topic_evidence, "relies on a migrated candidate summary"),
    ("doctoral_programme_used_as_person_role", doctoral_programme_used_as_person_role, "generic doctoral-programme listing"),
    ("doctoral_programme_used_as_personal_contact", doctoral_programme_used_as_personal_contact, "cannot support personal contact"),
    ("doctoral_programme_used_as_direct_research", doctoral_programme_used_as_direct_research, "cannot carry direct/adjacent topic evidence"),
    ("cross_person_research_claim_leak", cross_person_research_claim_leak, "claim/title names only"),
    ("cross_person_contact_claim_leak", cross_person_contact_claim_leak, "contact claim names only"),
    ("discovery_lead_used_as_substantive_evidence", discovery_lead_used_as_substantive_evidence, "used as substantive evidence"),
    ("pd_upgraded_to_independent_faculty", pd_upgraded_to_independent_faculty, "independent_faculty requires"),
    ("attending_upgraded_to_unit_head", attending_upgraded_to_unit_head, "unit_head requires"),
    ("unsupported_s1_current_supervision", unsupported_s1_current_supervision, "named_current_supervision"),
    ("split_source_s1_person_eligibility", split_source_s1_person_eligibility, "roleType=eligible_supervisor"),
    ("t1_without_current_independent_role", t1_without_current_independent_role, "requires paired candidate-bound current official evidence"),
    ("t3_without_current_direct_project", t3_without_current_direct_project, "T3 requires an explicit candidate-bound current official direct"),
    ("candidates_found_with_negative_unit", candidates_found_with_negative_unit, "candidates_found contradicts"),
    ("coverage_candidate_without_bound_source", coverage_candidate_without_bound_source, "lacks a candidate-bound current official"),
    ("audit_predates_portal", audit_predates_portal, "accessed after checkedAt"),
    ("verification_predates_role_source", verification_predates_role_source, "accessed after verifiedAt"),
    ("nonblank_not_public_contact", nonblank_not_public_contact, "not_public contact must have a blank value"),
    ("split_source_personal_contact", split_source_personal_contact, "one same candidate-bound official current contact source"),
    ("other_person_email_mislabeled_personal", other_person_email_mislabeled_personal, "may belong to another person"),
    ("generic_mailbox_mislabeled_personal", generic_mailbox_mislabeled_personal, "obvious unit/secretariat mailbox"),
    ("d_tier_direct_enquiry", d_tier_direct_enquiry, "direct_enquiry_recommended is not evidence-neutral"),
    ("direct_enquiry_with_unverified_role", direct_enquiry_with_unverified_role, "direct_enquiry_recommended is not evidence-neutral"),
    ("complete_blocked_case_without_bounded_limitation", complete_blocked_case_without_bounded_limitation, "status=complete with blocked coverage requires"),
    ("blocked_saturation_without_recheck", blocked_saturation_without_recheck, "must document an attempted/rechecked search"),
    ("blocked_xhs_mislabeled_negative", blocked_xhs_mislabeled_negative, "requires status=public_access_blocked"),
    ("future_direct_evidence", future_direct_evidence, "was not public by case asOf"),
    ("legacy_opportunity_detail", legacy_opportunity_detail, "opportunityDetail is unsupported"),
    ("correspondence_in_research_handoff", correspondence_in_research_handoff, "contains correspondence prose"),
    ("correspondence_in_nested_readiness", correspondence_in_nested_readiness, "contains correspondence prose"),
    ("correspondence_in_work_package", correspondence_in_work_package, "contains correspondence prose"),
    ("duplicate_formal_identifier_across_works", duplicate_formal_identifier_across_works, "assigned to multiple workIds"),
    ("programme_host_used_as_academic_role", programme_host_used_as_academic_role, "claimSourceIds.academicRole"),
    ("trial_role_used_as_admin_role", trial_role_used_as_admin_role, "roleType=trial_responsible_investigator"),
    ("non_specific_profile_used_as_academic_role", non_specific_profile_used_as_academic_role, "uses non-specific role evidence"),
    ("non_specific_profile_used_for_affiliation_role", non_specific_profile_used_for_affiliation_role, "affiliations[0].role is concrete"),
    ("pubmed_host_mislabeled_as_institution", pubmed_host_mislabeled_as_institution, "host pubmed.ncbi.nlm.nih.gov requires authorityClass=primary_publication"),
    ("cross_school_affiliation_without_school_binding", cross_school_affiliation_without_school_binding, "cross-school affiliation requires one current official institution source whose subjectIds include both candidate ID and additionalSchoolId"),
]

POSITIVE_TESTS = [
    ("equal_contribution_co_senior_allowed", equal_contribution_co_senior_allowed),
    ("programme_host_allowed_for_admin_role", programme_host_allowed_for_admin_role),
]


def run_validator(python: str, validator: Path, case_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [python, "-X", "utf8", str(validator), "--case-dir", str(case_dir), "--strict"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--validator", default=str(Path(__file__).with_name("validate_case.py")))
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    validator = Path(args.validator).resolve()
    baseline = run_validator(args.python, validator, case_dir)
    if baseline.returncode != 0:
        print(json.dumps({"status": "baseline_invalid", "output": baseline.stdout}, ensure_ascii=False, indent=2))
        return 2

    results = []
    with tempfile.TemporaryDirectory(prefix="supervisor-validator-contract-") as temp_root:
        for name, mutate, expected in TESTS:
            temp_case = Path(temp_root) / name
            shutil.copytree(case_dir, temp_case)
            payloads = load_case(temp_case)
            mutate(payloads)
            write_case(temp_case, payloads)
            completed = run_validator(args.python, validator, temp_case)
            caught = completed.returncode != 0 and expected in completed.stdout
            results.append(
                {
                    "test": name,
                    "caught": caught,
                    "expectedFragment": expected,
                    "returnCode": completed.returncode,
                }
            )
        for name, mutate in POSITIVE_TESTS:
            temp_case = Path(temp_root) / name
            shutil.copytree(case_dir, temp_case)
            payloads = load_case(temp_case)
            mutate(payloads)
            write_case(temp_case, payloads)
            completed = run_validator(args.python, validator, temp_case)
            results.append(
                {
                    "test": name,
                    "caught": completed.returncode == 0,
                    "expectedFragment": "<accepted positive control>",
                    "returnCode": completed.returncode,
                }
            )

    failed = [item for item in results if not item["caught"]]
    print(
        json.dumps(
            {
                "status": "passed" if not failed else "failed",
                "tests": len(results),
                "passed": len(results) - len(failed),
                "failed": failed,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
