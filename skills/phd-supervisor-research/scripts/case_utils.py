#!/usr/bin/env python3
"""Shared helpers for supervisor-research case scripts."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DEFAULT_TOPIC_PROFILE = "lung_cancer"
TOPIC_PROFILES = {"lung_cancer", "cv_aligned_oncology"}
DEFAULT_TOPIC_BY_PROFILE = {
    "lung_cancer": "thoracic oncology, especially lung cancer",
    "cv_aligned_oncology": (
        "CV-aligned oncology: translational genetics/genomics, cancer multi-omics and molecular biology, "
        "tumour immunity and immunometabolism, precision oncology, clinical cancer biomarkers, "
        "and cancer genetic epidemiology"
    ),
}
# These patterns detect an oncology anchor, not candidate eligibility. Retain
# historical schema-1.2 semantics; apply candidate-exclusions.md manually before
# scoring a current candidate, including dominant disease-focus exclusions and
# core or parallel nuclear-medicine/imaging exclusions.
DIRECT_TOPIC_ANCHOR_PATTERNS = {
    "lung_cancer": re.compile(
        r"(?i)\b(?:lung|thoracic|nsclc|sclc|mesothelioma)\b|"
        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸膜间皮瘤|间皮瘤)"
    ),
    "cv_aligned_oncology": re.compile(
        r"(?i)\b(?:cancers?|tumou?rs?|oncolog(?:y|ical|ic)|neoplasms?|"
        r"malignan(?:t|cy|cies)|carcinomas?|melanomas?|leuk(?:a)?emias?|"
        r"lymphomas?|myelomas?|mesotheliomas?|sarcomas?|gliomas?|glioblastomas?|"
        r"neuroblastomas?|nsclc|sclc)\b|"
        r"(?:肿瘤|癌|白血病|淋巴瘤|骨髓瘤|肉瘤|间皮瘤)"
    ),
}
NEGATED_LUNG_ANCHOR_PATTERNS = [
    re.compile(
        r"(?i)\bnot(?:\s+(?:a|an|the))?\s*"
        r"(?:personal\s+)?(?:lung|thoracic|nsclc|sclc)"
        r"(?:[-\s]+(?:cancer|tumou?r|oncology|focus|line|topic))?\b"
    ),
    # "Non-lung tumour" positively describes a tumour at another site;
    # discard only the anatomical exclusion, retaining its tumour anchor.
    re.compile(r"(?i)\bnon[-\s]+(?:lung|thoracic|nsclc|sclc)\b"),
    re.compile(
        r"(?i)\b(?:lung|thoracic|nsclc|sclc)\b[^.;\n]{0,30}"
        r"\b(?:is|are)\s+not\b[^.;\n]{0,20}\b(?:focus|line|topic|research)\b"
    ),
    re.compile(
        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学|NSCLC|SCLC)"
        r"[^。；;\n]{0,20}(?:并非|不是|不属于)[^。；;\n]{0,16}(?:主线|方向|重点|课题|研究)"
    ),
    re.compile(
        r"(?:并非|不是|不属于)[^。；;\n]{0,12}"
        r"(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学|NSCLC|SCLC)"
    ),
    re.compile(r"非(?!小细胞)(?:肺癌|肺肿瘤|胸部肿瘤|胸部肿瘤学)"),
]


def resolve_topic_profile(case: dict) -> str:
    """Missing metadata retains legacy lung semantics; explicit invalid values fail."""
    profile = case.get("topicProfile", DEFAULT_TOPIC_PROFILE)
    if not isinstance(profile, str) or profile not in TOPIC_PROFILES:
        raise ValueError("case.json topicProfile must be lung_cancer or cv_aligned_oncology")
    return profile


def topic_has_direct_anchor(topic_profile: str, *values: object) -> bool:
    """Screen source text for a declared-topic anchor, without inferring scientific fit."""
    profile = resolve_topic_profile({"topicProfile": topic_profile})
    text = "\n".join(str(value or "") for value in values)
    if profile == "cv_aligned_oncology":
        # Excluding lung research does not exclude other oncology, but that
        # exclusion alone is not positive evidence of another cancer topic.
        for pattern in NEGATED_LUNG_ANCHOR_PATTERNS:
            text = pattern.sub("", text)
    return bool(DIRECT_TOPIC_ANCHOR_PATTERNS[profile].search(text))


SOURCE_TYPES = {
    "official_ranking",
    "official_research_profile",
    "official_role_contact",
    "official_school_structure",
    "publication",
    "grant_project",
    "clinical_trial",
    "doctoral_rule_supervision",
    "official_admissions_funding",
    "official_vacancy_portal",
    "vacancy",
    "chinese_secondary",
    "social_user_generated",
    "other_secondary",
    "discovery_lead",
}
SOURCE_AUTHORITY_CLASSES = {
    "official_ranking_publisher",
    "official_institution",
    "official_funder_registry",
    "official_trial_registry",
    "official_government_regulator",
    "primary_publication",
    "researcher_controlled",
    "professional_secondary",
    "social_user_generated",
    "other_secondary",
}
SOURCE_MEDIA = {
    "webpage",
    "pdf",
    "article",
    "database_record",
    "vacancy_posting",
    "social_post",
    "dataset",
    "other",
}
CLAIM_DOMAINS = {
    "ranking",
    "school_structure",
    "research",
    "current_role",
    "contact",
    "doctoral_rule",
    "doctoral_supervision",
    "admissions_funding",
    "recruitment",
    "conflict",
    "discovery",
}
DIRECT_RESEARCH_SOURCE_TYPES = {
    "official_research_profile",
    "publication",
    "grant_project",
    "clinical_trial",
}
OPPORTUNITY_STATUSES = {
    "open_current",
    "planned_official",
    "route_confirmed_no_vacancy",
    "direct_enquiry_recommended",
    "historical_only",
    "closed_expired",
    "no_public_evidence",
    "unverified",
}
OPPORTUNITY_SCOPES = {"person", "lab", "programme"}
DEADLINE_TYPES = {"fixed", "rolling", "until_filled", "not_stated", "not_applicable"}
DISCOVERY_PASS_TYPES = {"official_expansion", "literature_expansion", "saturation"}
COVERAGE_AREAS = {
    "medicine-clinical",
    "life-science-biomedicine",
    "cancer-hospital",
    "pathology-diagnostics",
    "public-health-data",
    "engineering-ai-imaging",
    "pharmacy-drug-discovery",
    "veterinary-comparative",
}
COVERAGE_AREA_ORDER = [
    "medicine-clinical",
    "life-science-biomedicine",
    "cancer-hospital",
    "pathology-diagnostics",
    "public-health-data",
    "engineering-ai-imaging",
    "pharmacy-drug-discovery",
    "veterinary-comparative",
]
CONFLICT_CATEGORIES = {
    "substantive_current_conflict",
    "announced_future_change",
    "stale_or_timepoint_difference",
    "translation_naming_difference",
    "low_confidence_unverifiable",
    "scope_or_role_difference",
}
CHECK_STATUSES = {
    "verified_source_found",
    "lead_only",
    "not_found_publicly",
    "public_access_blocked",
    "not_searched",
}
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "spm",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_url(url: str) -> str:
    parts = urlsplit(str(url).strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS and not key.lower().startswith("utm_")
    ]
    query.sort()
    return urlunsplit((scheme, host, path, urlencode(query, doseq=True), ""))


def evidence_work_key(source: dict) -> str:
    """Return a stable identity for one underlying paper/project/trial/posting."""
    explicit = str(source.get("workId", "")).strip().casefold()
    if explicit:
        return explicit
    identifiers = source.get("identifiers", {})
    if isinstance(identifiers, dict):
        for key in ["doi", "pmid", "pmcid", "grantId", "trialId", "postingId"]:
            value = str(identifiers.get(key, "")).strip().casefold()
            if value:
                return f"{key.casefold()}:{value}"
    url = str(source.get("url", "")).strip()
    parts = urlsplit(url)
    host = (parts.hostname or "").casefold()
    path = parts.path.rstrip("/")
    pubmed_match = re.search(r"/(\d+)$", path) if "pubmed.ncbi.nlm.nih.gov" in host else None
    if pubmed_match:
        return f"pmid:{pubmed_match.group(1)}"
    if host == "doi.org" and path:
        return f"doi:{path.lstrip('/').casefold()}"
    trial_match = re.search(r"/(NCT\d+)$", path, flags=re.I)
    if "clinicaltrials.gov" in host and trial_match:
        return f"trialid:{trial_match.group(1).casefold()}"
    return f"{source.get('type', 'source')}:{canonical_url(url)}"


def evidence_stats(sources: list[dict]) -> dict:
    urls = []
    for item in sources:
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        try:
            urls.append(canonical_url(url))
        except (TypeError, ValueError):
            urls.append(url)
    type_counts = Counter(str(item.get("type", "untyped")) for item in sources)
    return {
        "evidenceRecords": len(sources),
        "substantiveRecords": len(sources) - type_counts.get("discovery_lead", 0),
        "discoveryLeadRecords": type_counts.get("discovery_lead", 0),
        "uniqueUrls": len(set(urls)),
        "typeCounts": dict(sorted(type_counts.items())),
    }


def evidence_stats_line(sources: list[dict]) -> str:
    stats = evidence_stats(sources)
    by_type = "；".join(f"{key}={value}" for key, value in stats["typeCounts"].items())
    return (
        f"来源统计（由 data/sources.json 自动生成）：{stats['evidenceRecords']} 条来源记录，"
        f"其中 {stats['substantiveRecords']} 条可承担实质主张、"
        f"{stats['discoveryLeadRecords']} 条为隔离的发现线索；"
        f"{stats['uniqueUrls']} 个规范化去重链接；按互斥来源类型：{by_type}。"
    )


def visible_char_count(value: str) -> int:
    text = re.sub(r"\s+", "", str(value or ""))
    text = re.sub(r"[#*_`>\[\](){}|]", "", text)
    return len(text)


def md_cell(value: object) -> str:
    if isinstance(value, list):
        value = "<br>".join(str(item) for item in value if str(item).strip())
    text = str(value or "—").strip() or "—"
    return text.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def unique_ids(*groups: object) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for group in groups:
        values = group if isinstance(group, list) else []
        for value in values:
            item = str(value)
            if item and item not in seen:
                seen.add(item)
                result.append(item)
    return result


def source_links(source_ids: list[str], source_map: dict[str, dict]) -> str:
    links = []
    for source_id in source_ids:
        source = source_map.get(source_id)
        if not source:
            links.append(f"missing:{source_id}")
            continue
        title = str(source.get("title") or source_id).replace("[", "(").replace("]", ")")
        links.append(f"[{title}]({source.get('url', '')})")
    return "<br>".join(links) if links else "—"


def write_text(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    # Rendering often joins already punctuated source fragments with Chinese
    # semicolons. Normalize only unambiguous duplicate punctuation sequences;
    # the underlying evidence text remains unchanged in JSON.
    for duplicated, replacement in {
        "。；": "；",
        "；。": "。",
        "。。": "。",
        "；；": "；",
    }.items():
        text = text.replace(duplicated, replacement)
    path.write_text(text, encoding="utf-8")
