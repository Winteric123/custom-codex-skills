#!/usr/bin/env python3
"""Render the supervisor-research Markdown package from structured JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

from case_utils import (
    COVERAGE_AREA_ORDER,
    evidence_stats,
    evidence_stats_line,
    load_json,
    md_cell,
    resolve_topic_profile,
    source_links,
    unique_ids,
    visible_char_count,
    write_text,
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
OPTIONAL_CONTACT_OUTPUT = "08-CONTACT-AUDIT.md"

TIER_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
AREA_LABELS = {
    "medicine-clinical": "医学与临床",
    "life-science-biomedicine": "生命科学与生物医学",
    "cancer-hospital": "癌症中心与附属医院",
    "pathology-diagnostics": "病理与诊断",
    "public-health-data": "公共卫生、流行病学与数据科学",
    "engineering-ai-imaging": "工程、人工智能与影像",
    "pharmacy-drug-discovery": "药学与药物发现",
    "veterinary-comparative": "兽医与比较肿瘤学",
}
OPPORTUNITY_LABELS = {
    "open_current": "当前有官方开放博士职位/招生公告（call）",
    "planned_official": "官方已宣布未来机会",
    "route_confirmed_no_vacancy": "培养路径已确认，未见当前职位",
    "direct_enquiry_recommended": "建议直接询问，不能视为正在招生",
    "historical_only": "仅发现历史机会",
    "closed_expired": "职位已关闭或过期",
    "no_public_evidence": "未发现公开招生证据",
    "unverified": "尚未核验",
}

OPPORTUNITY_SCOPE_LABELS = {
    "person": "个人",
    "lab": "课题组",
    "programme": "项目/培养计划",
}

DEADLINE_TYPE_LABELS = {
    "fixed": "固定截止",
    "rolling": "滚动申请",
    "until_filled": "招满即止",
    "not_stated": "官方未说明",
    "not_applicable": "不适用",
}

DOCUMENT_TYPE_LABELS = {
    "motivation_letter": "动机信",
    "personal_statement": "个人陈述",
    "cover_letter": "申请附信（cover letter）",
    "supervisor_enquiry": "导师联系/套磁",
    "recommendation_letters": "推荐信",
    "research_proposal": "研究计划",
    "cv": "简历（CV）",
    "transcripts": "成绩单",
    "degree_certificates": "学位/毕业证明",
    "language_test": "语言成绩",
    "writing_sample": "写作样本",
    "other": "其他材料",
}
DOCUMENT_STATUS_LABELS = {
    "required": "必需",
    "optional": "可选",
    "not_required": "官方明确不要求",
    "conditional": "满足特定条件时要求",
    "not_public": "未公开说明",
    "unverified": "尚未核验",
}
DOCUMENT_STAGE_LABELS = {
    "pre_contact": "联系导师前/联系阶段",
    "initial_application": "首次正式申请",
    "after_shortlisting": "入围后",
    "after_offer": "录取后",
    "not_stated": "未说明阶段",
}
DOCUMENT_SUBMITTER_LABELS = {
    "applicant": "申请人",
    "referee": "推荐人",
    "not_stated": "未说明提交者",
}
ARCHIVED_OPPORTUNITY_STATUSES = {"closed_expired", "historical_only"}


def document_requirements(record: dict) -> list[dict]:
    """Return optional structured material rules without reinterpreting legacy text."""
    readiness = record.get("applicationReadiness", {})
    if not isinstance(readiness, dict):
        return []
    items = readiness.get("documentRequirements", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def document_route_map(record: dict) -> dict[str, dict]:
    opportunities = record.get("opportunities", [])
    if not isinstance(opportunities, list):
        return {}
    return {
        str(item.get("id")): item
        for item in opportunities
        if isinstance(item, dict) and item.get("id")
    }


def missing_current_document_audit(record: dict) -> bool:
    """Archived routes do not trigger a missing current-materials audit warning."""
    routes = document_route_map(record)
    requirements = document_requirements(record)
    if routes:
        current_route_ids = {
            route_id for route_id, route in routes.items()
            if route.get("status") not in ARCHIVED_OPPORTUNITY_STATUSES
        }
        audited_route_ids = {str(item.get("routeId") or "") for item in requirements}
        return bool(current_route_ids - audited_route_ids)
    return not requirements and record.get("opportunityStatus") not in ARCHIVED_OPPORTUNITY_STATUSES


def document_route_name(route_id: str, route: dict) -> str:
    name = str(route.get("routeName") or route_id or "未标明申请路径")
    if route_id and name != route_id:
        name = f"{name} ({route_id})"
    status = route.get("status")
    if status in ARCHIVED_OPPORTUNITY_STATUSES:
        name += f"；路径状态：{OPPORTUNITY_LABELS.get(status, status)} ({status})"
    return name


def record_verification_is_stale(record: dict, case: dict) -> bool:
    try:
        verified = dt.date.fromisoformat(str(record.get("verifiedAt", "")))
        as_of = dt.date.fromisoformat(str(case.get("asOf", "")))
    except ValueError:
        return False
    return (as_of - verified).days > 30


def dated_object_is_stale(value: object, case: dict) -> bool:
    if not isinstance(value, dict):
        return False
    try:
        checked = dt.date.fromisoformat(str(value.get("checkedAt", "")))
        as_of = dt.date.fromisoformat(str(case.get("asOf", "")))
    except ValueError:
        return False
    return 30 < (as_of - checked).days <= 90


def clean_sentence_fragment(value: object) -> str:
    """Trim terminal punctuation before the renderer supplies its own separators."""
    return str(value or "").strip().rstrip("。；;：:,.， ")


def comparable_text(value: object) -> str:
    """Return a punctuation-insensitive key used to avoid duplicate package text."""
    return "".join(
        ch.casefold()
        for ch in clean_sentence_fragment(value)
        if ch not in " \t\r\n。；;：:,.，、()（）[]【】"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a PhD-supervisor research case")
    parser.add_argument("--case-dir", required=True, help="Initialized case directory")
    return parser.parse_args()


def output_files(case_dir: Path) -> list[str]:
    files = list(OUTPUT_FILES)
    if (case_dir / "data" / "contact-audit.json").exists():
        files.append(OPTIONAL_CONTACT_OUTPUT)
    return files


def load_case(
    case_dir: Path,
) -> tuple[dict, list[dict], list[dict], list[dict], list[dict], dict | None]:
    data_dir = case_dir / "data"
    case = load_json(data_dir / "case.json")
    schools = load_json(data_dir / "schools.json")
    coverage = load_json(data_dir / "coverage.json")
    records = load_json(data_dir / "records.json")
    sources = load_json(data_dir / "sources.json")
    contact_audit_path = data_dir / "contact-audit.json"
    contact_audit = load_json(contact_audit_path) if contact_audit_path.exists() else None
    if not isinstance(case, dict):
        raise ValueError("case.json must contain an object")
    for name, value in [
        ("schools.json", schools),
        ("coverage.json", coverage),
        ("records.json", records),
        ("sources.json", sources),
    ]:
        if not isinstance(value, list):
            raise ValueError(f"{name} must contain an array")
    if contact_audit is not None and not isinstance(contact_audit, dict):
        raise ValueError("contact-audit.json must contain an object")
    return case, schools, coverage, records, sources, contact_audit


def nested_source_ids(value: object) -> list[str]:
    """Collect source references recursively so newly structured claims remain visible."""
    refs: list[str] = []

    def walk(item: object, key: str = "") -> None:
        if isinstance(item, dict):
            for child_key, child in item.items():
                if child_key.endswith("SourceIds") or child_key in {"sourceIds", "directEvidenceIds"}:
                    if isinstance(child, list):
                        refs.extend(str(source_id) for source_id in child if str(source_id).strip())
                    elif isinstance(child, dict):
                        walk(child, child_key)
                else:
                    walk(child, child_key)
        elif isinstance(item, list):
            for child in item:
                walk(child, key)

    walk(value)
    return unique_ids(refs)


def source_ids_from_record(record: dict) -> list[str]:
    return nested_source_ids(record)


def school_source_ids(school: dict) -> list[str]:
    return nested_source_ids(school)


def warning_lines(case: dict, coverage: list[dict], records: list[dict]) -> list[str]:
    warnings: list[str] = []
    warnings.extend(str(item) for item in case.get("limitations", []) if str(item).strip())
    blocked = [row for row in coverage if row.get("status") == "blocked_unverified"]
    if blocked:
        warnings.append(f"{len(blocked)} 个学院/机构检索分支因访问限制尚未完成核验。")
    unverified = [
        row
        for row in records
        if row.get("opportunityStatus") == "unverified"
        or any(
            isinstance(item, dict) and item.get("status") == "unverified"
            for item in (
                row.get("opportunities", [])
                if isinstance(row.get("opportunities", []), list)
                else []
            )
        )
    ]
    if unverified:
        warnings.append(f"{len(unverified)} 位候选人的招生状态仍为 unverified。")
    unresolved_conflicts = [
        (record, conflict)
        for record in records
        for conflict in record.get("conflicts", [])
        if isinstance(conflict, dict) and not str(conflict.get("decision", "")).strip()
    ]
    if unresolved_conflicts:
        warnings.append(f"{len(unresolved_conflicts)} 条冲突尚未给出证据裁决。")
    no_contact = [
        record
        for record in records
        if not record.get("contacts")
        or all(item.get("type") == "not_public" for item in record.get("contacts", []) if isinstance(item, dict))
    ]
    if no_contact:
        warnings.append(f"{len(no_contact)} 位候选人没有公开联系渠道。")
    stale_records = [record for record in records if record_verification_is_stale(record, case)]
    if stale_records:
        warnings.append(
            f"{len(stale_records)} 位候选人的逐记录核验日期距案例日期超过 30 天；使用前需复核："
            + "、".join(str(item.get("name") or item.get("id")) for item in stale_records)
            + "。"
        )
    stale_recruitment = [
        record for record in records if dated_object_is_stale(record.get("recruitmentAudit"), case)
    ]
    if stale_recruitment:
        warnings.append(
            f"{len(stale_recruitment)} 位候选人的招生核查距案例日期超过 30 天："
            + "、".join(str(item.get("name") or item.get("id")) for item in stale_recruitment)
            + "。"
        )
    stale_social = [
        record
        for record in records
        if any(
            dated_object_is_stale(record.get(check_name), case)
            for check_name in ["chineseCheck", "xiaohongshuCheck"]
        )
    ]
    if stale_social:
        warnings.append(
            f"{len(stale_social)} 位候选人的中文互联网或小红书核查距案例日期超过 30 天："
            + "、".join(str(item.get("name") or item.get("id")) for item in stale_social)
            + "。"
        )
    social_not_searched = [
        record
        for record in records
        if any(
            not isinstance(record.get(check_name), dict)
            or record.get(check_name, {}).get("status") == "not_searched"
            for check_name in ["chineseCheck", "xiaohongshuCheck"]
        )
    ]
    if social_not_searched:
        warnings.append(f"{len(social_not_searched)} 位候选人的中文互联网或小红书检查尚未完成。")
    evidence_exceptions = [
        record for record in records if str(record.get("directEvidenceException", "")).strip()
    ]
    if evidence_exceptions:
        warnings.append(
            f"A 类直接/近期证据例外 {len(evidence_exceptions)} 位："
            + "；".join(
                f"{record.get('name') or record.get('id')}：{record.get('directEvidenceException')}"
                for record in evidence_exceptions
            )
        )
    material_records = [record for record in records if record.get("priorityTier") in {"A", "B", "C"}]
    missing_material_checks = [record for record in material_records if missing_current_document_audit(record)]
    if missing_material_checks:
        warnings.append(
            f"{len(missing_material_checks)} 位 A/B/C 类候选人至少一条当前申请路径未按新材料清单核验；"
            "不得据此视为不需要动机信、导师联系、推荐信或其他申请材料。"
        )
    unresolved_material_checks = [
        (record, item)
        for record in material_records
        for item in document_requirements(record)
        if item.get("requirementStatus") in {"not_public", "unverified"}
        and document_route_map(record).get(str(item.get("routeId") or ""), {}).get("status")
        not in ARCHIVED_OPPORTUNITY_STATUSES
    ]
    if unresolved_material_checks:
        warnings.append(
            f"{len(unresolved_material_checks)} 项申请材料要求尚未公开说明或尚未核验；"
            "使用前需按对应申请路径确认。"
        )
    return warnings


def common_header(title: str, case: dict, sources: list[dict]) -> list[str]:
    lines = [
        f"# {title}",
        "",
        f"- 地区：{case.get('location', '—')}",
        f"- 研究主题：{case.get('topic', '—')}",
        f"- 核验日期：{case.get('asOf', '—')}",
    ]
    if resolve_topic_profile(case) == "cv_aligned_oncology":
        lines.append("- 主题证据范围：cv_aligned_oncology（T1–T4 按已声明的 CV 肿瘤学范围判定）")
    if case.get("intake"):
        lines.append(f"- 目标入学：{case['intake']}")
    lines.extend(["", evidence_stats_line(sources), ""])
    return lines


def join_values(value: object, empty: str = "—") -> str:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "；".join(items) if items else empty
    text = str(value or "").strip()
    return text or empty


def identifier_text(source: dict) -> str:
    values = []
    if str(source.get("workId", "")).strip():
        values.append(f"workId={source['workId']}")
    identifiers = source.get("identifiers", {})
    if isinstance(identifiers, dict):
        values.extend(
            f"{key}={value}"
            for key, value in sorted(identifiers.items())
            if str(value).strip()
        )
    return "；".join(values) if values else "—"


def person_roles_text(source: dict) -> str:
    roles = source.get("personRoles", [])
    if not isinstance(roles, list):
        return "—"
    values = []
    for item in roles:
        if isinstance(item, dict) and str(item.get("subjectId", "")).strip():
            values.append(
                f"{item.get('subjectId')}：{item.get('roleType') or '—'} / "
                f"{item.get('topicRelevance') or '—'} / {item.get('exactLabel') or '—'}"
            )
    return "；".join(values) if values else "—"


def affiliated_text(items: object) -> str:
    if not isinstance(items, list) or not items:
        return "—"
    values = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("officialName") or item.get("displayNameZh")
            relation = item.get("relationship") or "—"
            relation_type = item.get("relationshipType") or "unclassified"
            values.append(
                f"{name}（{relation_type}：{relation}）" if name else "—"
            )
        else:
            values.append(str(item))
    return "；".join(values)


def affiliation_text(
    record: dict, school_map: dict[str, dict], source_map: dict[str, dict]
) -> str:
    entries: list[str] = []
    for item in record.get("affiliations", []):
        if not isinstance(item, dict):
            continue
        school_id = str(item.get("schoolId", "")).strip()
        school = school_map.get(school_id, {})
        school_name = school.get("displayNameZh") or school.get("officialName") or school_id
        institution = (
            item.get("institution")
            or item.get("institutionName")
            or item.get("officialName")
            or ""
        )
        units = " / ".join(
            str(value).strip()
            for value in [item.get("faculty"), item.get("department")]
            if str(value or "").strip()
        )
        relationship = item.get("relationship") or ""
        role = item.get("role") or ""
        parts = [str(value).strip() for value in [school_name, institution, units] if str(value or "").strip()]
        entry = " · ".join(parts)
        labels = []
        if relationship:
            labels.append(f"关系：{relationship}")
        if role:
            labels.append(f"任职：{role}")
        if labels:
            entry += f"（{'；'.join(labels)}）"
        evidence = source_links(item.get("sourceIds", []), source_map)
        if evidence != "—":
            entry += f" {evidence}"
        if entry:
            entries.append(entry)

    if not entries:
        legacy = "；".join(
            value
            for value in [
                record.get("faculty", ""),
                record.get("department", ""),
                record.get("affiliatedInstitution", ""),
            ]
            if value
        )
        if legacy:
            entries.append(legacy)

    represented_school_ids = {
        str(item.get("schoolId", "")).strip()
        for item in record.get("affiliations", [])
        if isinstance(item, dict)
    }
    for school_id in record.get("additionalSchoolIds", []):
        if not str(school_id).strip() or str(school_id) in represented_school_ids:
            continue
        school = school_map.get(str(school_id), {})
        entries.append(
            f"补充高校：{school.get('displayNameZh') or school.get('officialName') or school_id}"
        )
    return "<br>".join(entries) if entries else "—"


def contact_text(record: dict, source_map: dict[str, dict]) -> str:
    type_labels = {
        "personal_email": "个人邮箱",
        "clinical_email": "临床邮箱",
        "group_email": "课题组邮箱",
        "unit_email": "单位邮箱",
        "department_mailbox": "科室邮箱",
        "secretariat_email": "秘书处邮箱",
        "assistant_contact": "助理／他人联系邮箱",
        "phone": "电话",
        "contact_form": "联系页面",
        "not_public": "未公开",
    }
    status_labels = {
        "published_current": "当前公开",
        "published_historical": "历史公开",
        "not_public": "未公开",
        "unclear": "状态未确认",
    }
    contacts = []
    for item in record.get("contacts", []):
        if not isinstance(item, dict):
            continue
        contact_type = item.get("type", "unknown")
        value = "未公开" if contact_type == "not_public" else (item.get("value") or "—")
        status = item.get("status", "")
        evidence = source_links(item.get("sourceIds", []), source_map)
        if contact_type == "not_public":
            rendered = "未公开"
        else:
            rendered = f"{type_labels.get(contact_type, contact_type)}：{value}"
            if status:
                rendered += f"（{status_labels.get(status, status)}）"
        if evidence != "—":
            rendered += f" {evidence}"
        contacts.append(rendered)
    return "<br>".join(contacts) if contacts else "—"


def opportunity_text(record: dict, source_map: dict[str, dict]) -> str:
    opportunities = record.get("opportunities", [])
    rendered: list[str] = []
    if isinstance(opportunities, list):
        for item in opportunities:
            if not isinstance(item, dict):
                continue
            scope = OPPORTUNITY_SCOPE_LABELS.get(item.get("scope"), item.get("scope") or "未标明层级")
            route = item.get("routeName") or item.get("id") or "未命名路径"
            status = item.get("status", "unverified")
            status_text = OPPORTUNITY_LABELS.get(status, status)
            deadline_type = item.get("deadlineType")
            deadline_text = DEADLINE_TYPE_LABELS.get(deadline_type, deadline_type or "未说明截止方式")
            if item.get("deadline"):
                deadline_text += f" {item['deadline']}"
            contact_policy = item.get("contactPolicy") or ""
            evidence = source_links(item.get("sourceIds", []), source_map)
            parts = [f"[{scope}] {route}: {status_text}（{status}）", deadline_text]
            if contact_policy:
                parts.append(f"联系规则：{contact_policy}")
            if evidence != "—":
                parts.append(evidence)
            rendered.append("；".join(parts))
    if rendered:
        return "<br>".join(rendered)

    status = record.get("opportunityStatus", "unverified")
    summary = f"{OPPORTUNITY_LABELS.get(status, status)}（{status}）"
    if record.get("opportunityDeadline"):
        summary += f"；截止：{record['opportunityDeadline']}"
    evidence = source_links(record.get("recruitmentSourceIds", []), source_map)
    if evidence != "—":
        summary += f" {evidence}"
    return summary


def recruitment_audit_text(record: dict, source_map: dict[str, dict]) -> str:
    audit = record.get("recruitmentAudit", {})
    if not isinstance(audit, dict) or not audit:
        return "—"
    parts = []
    if audit.get("checkedAt"):
        parts.append(f"检查日期：{audit['checkedAt']}")
    if audit.get("checkedScopes"):
        parts.append(f"检查层级：{join_values(audit['checkedScopes'])}")
    portal_values = []
    for portal in audit.get("portals", []):
        if not isinstance(portal, dict):
            continue
        label = str(portal.get("name") or "未命名入口")
        result = str(portal.get("result") or "")
        evidence = source_links(portal.get("sourceIds", []), source_map)
        portal_values.append(
            label + (f"：{result}" if result else "") + (f" {evidence}" if evidence != "—" else "")
        )
    if portal_values:
        parts.append("官方入口：" + "；".join(portal_values))
    if audit.get("queries"):
        parts.append(f"检查项：{join_values(audit['queries'])}")
    if audit.get("summary"):
        parts.append(str(audit["summary"]))
    evidence = source_links(audit.get("sourceIds", []), source_map)
    if evidence != "—":
        parts.append(f"证据：{evidence}")
    return "；".join(parts) if parts else "—"


def check_text(check: object, source_map: dict[str, dict]) -> str:
    if not isinstance(check, dict):
        return "—"
    parts = []
    if check.get("checkedAt"):
        parts.append(f"检查日期：{check['checkedAt']}")
    if check.get("queries"):
        parts.append(f"查询：{join_values(check['queries'])}")
    if check.get("summary"):
        parts.append(str(check["summary"]))
    if check.get("accessNote"):
        parts.append(f"访问说明：{check['accessNote']}")
    evidence = source_links(check.get("sourceIds", []), source_map)
    if evidence != "—":
        parts.append(evidence)
    return "；".join(parts) if parts else "—"


def render_index(
    case_dir: Path,
    case: dict,
    schools: list[dict],
    coverage: list[dict],
    records: list[dict],
    sources: list[dict],
    contact_audit: dict | None,
) -> None:
    tiers = Counter(str(item.get("priorityTier", "unclassified")) for item in records)
    warnings = warning_lines(case, coverage, records)
    scope_audit = case.get("scopeAudit", {}) if isinstance(case.get("scopeAudit"), dict) else {}
    excluded = scope_audit.get("excludedInstitutions", [])
    excluded_count = len(excluded) if isinstance(excluded, list) else 0
    lines = common_header("博士导师检索证据包", case, sources)
    lines.extend(
        [
            "## 范围与结果",
            "",
            f"- 范围模式：{case.get('scopeMode', '—')}",
            f"- 纳入学校数：{len(schools)}",
            f"- 范围审计排除机构数：{excluded_count}",
            f"- 候选人数：{len(records)}",
            "- 分级：" + "；".join(f"{tier}={tiers.get(tier, 0)}" for tier in ["A", "B", "C", "D"]),
            f"- 状态：{case.get('status', '—')}",
            "",
            "A 类表示研究匹配和培养路径证据较强，不等同于当前正在招生。",
            "",
            "## 范围审计摘要",
            "",
            f"- 排名体系：{scope_audit.get('rankingSystem') or '—'}",
            f"- 排名版本：{scope_audit.get('rankingEdition') or '—'}",
            f"- 排名发布日期：{scope_audit.get('rankingPublicationDate') or '—'}",
            f"- 覆盖法域：{join_values(scope_audit.get('jurisdictions'))}",
            f"- 官方筛选记录：{scope_audit.get('rankingQuery') or '—'}",
            f"- 阈值内机构计数：{scope_audit.get('eligibleInstitutionCount') if scope_audit.get('eligibleInstitutionCount') is not None else '—'}",
            f"- 纳入学校 ID：{join_values(scope_audit.get('includedSchoolIds'))}",
            "",
            "## 检索扩展与饱和记录",
            "",
        ]
    )
    passes = case.get("discoveryPasses", [])
    if isinstance(passes, list) and passes:
        for index, item in enumerate(passes, start=1):
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- 第 {index} 轮 `{item.get('passType', '—')}`（{item.get('performedAt', '—')}）："
                f"新增 {item.get('newCandidateCount', '—')} 人；范围/查询：{join_values(item.get('queriesOrUnits'))}。"
            )
    else:
        lines.append("- —")
    lines.extend(
        [
            "",
            "## 文件导航",
            "",
        ]
    )
    descriptions = {
        "01-SCHOOL-SCOPE.md": "学校、QS 与医学体系范围",
        "02-SUPERVISOR-TABLE.md": "导师总表",
        "03-COVERAGE-MATRIX.md": "跨学院检索覆盖矩阵",
        "04-EVIDENCE-CONFLICTS.md": "冲突、中文互联网与小红书核验",
        "05-A-TIER-DEEP-PROFILES.md": "A 类导师研究方向深描",
        "06-APPLICATION-READINESS.md": "A/B/C 类申请材料清单与 A 类申请准备信息（非材料撰写）",
        "07-SOURCE-LEDGER.md": "全部来源台账",
        "08-CONTACT-AUDIT.md": "联系方式归属、时效、官方优先检索顺序与首选渠道审计",
    }
    for filename in output_files(case_dir)[1:]:
        lines.append(f"- [{filename}]({filename})：{descriptions[filename]}")
    if contact_audit is not None:
        contact_records = contact_audit.get("records", [])
        contact_count = len(contact_records) if isinstance(contact_records, list) else 0
        lines.extend(
            [
                "",
                f"- 联系方式补充审计：{contact_count} 位候选人；详见 `08-CONTACT-AUDIT.md`。",
            ]
        )
    lines.extend(["", "## 未解决事项与限制", ""])
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- 未记录额外警告；仍应以实际申请时的最新官方页面为准。")
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "本证据包只做导师检索、证据核验、分级和研究型申请准备信息整理，不包含套磁信、动机信或完整研究计划的撰写。",
            "如后续进入独立写作流程，只交接已核验事实、带来源的 researchAnchor、明确标为分析者推导的 researchGap/proposedAim，以及待确认问题和风险提示；不得把这些内容直接改写成替申请人发言的邮件句子。",
        ]
    )
    write_text(case_dir / "00-INDEX.md", lines)


def render_school_scope(
    case_dir: Path, case: dict, schools: list[dict], source_map: dict[str, dict], sources: list[dict]
) -> None:
    lines = common_header("学校范围、QS 与医学体系", case, sources)
    scope_audit = case.get("scopeAudit", {}) if isinstance(case.get("scopeAudit"), dict) else {}
    lines.extend(
        [
            "## 排名范围审计",
            "",
            f"- 排名体系：{scope_audit.get('rankingSystem') or '—'}",
            f"- 排名版本：{scope_audit.get('rankingEdition') or '—'}",
            f"- 排名发布日期：{scope_audit.get('rankingPublicationDate') or '—'}",
            f"- 覆盖法域：{join_values(scope_audit.get('jurisdictions'))}",
            f"- 官方筛选记录：{scope_audit.get('rankingQuery') or '—'}",
            f"- 阈值内机构计数：{scope_audit.get('eligibleInstitutionCount') if scope_audit.get('eligibleInstitutionCount') is not None else '—'}",
            f"- 范围来源：{source_links(scope_audit.get('sourceIds', []), source_map)}",
            "",
            "## 纳入学校",
            "",
        ]
    )
    lines.extend(
        [
            "| ID | 国家/地区 | 学校 | 来源模式 | QS 版本/发布日期/名次/状态 | 医学体系 | 正式关联医院/中心/网络 | 纳入决定与理由 | 来源 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for school in schools:
        qs = school.get("qs", {})
        medical = school.get("medicalSystem", {})
        qs_text = " / ".join(
            str(value or "—")
            for value in [
                qs.get("edition"),
                qs.get("publicationDate"),
                qs.get("rank"),
                qs.get("status"),
            ]
        )
        origin = school.get("origin") or ("user_named" if school.get("namedByUser") else "ranking_screen")
        decision = school.get("inclusionDecision") or "included"
        reason = school.get("inclusionReason") or (
            "用户明确指定" if school.get("namedByUser") else "符合地区排名范围"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(school.get("id")),
                    md_cell(school.get("countryRegion")),
                    md_cell(
                        f"{school.get('displayNameZh') or school.get('officialName', '—')} / "
                        f"{school.get('officialName', '—')}"
                    ),
                    md_cell(origin),
                    md_cell(qs_text),
                    md_cell(f"{medical.get('status', '—')}：{medical.get('summary', '')}"),
                    md_cell(affiliated_text(school.get("affiliatedInstitutions"))),
                    md_cell(f"{decision}：{reason}"),
                    md_cell(source_links(school_source_ids(school), source_map)),
                ]
            )
            + " |"
        )
    excluded = scope_audit.get("excludedInstitutions", [])
    lines.extend(
        [
            "",
            "## 排除机构",
            "",
            "范围模式为地区 QS 筛选时，本表保留核验过但未纳入的机构，避免把未入选误写成漏检。",
            "",
            "| ID | 国家/地区 | 机构 | QS 版本/发布日期/名次/状态 | 排除决定与理由 | 来源 |",
            "|---|---|---|---|---|---|",
        ]
    )
    if isinstance(excluded, list) and excluded:
        for item in excluded:
            if not isinstance(item, dict):
                continue
            qs = item.get("qs", {}) if isinstance(item.get("qs"), dict) else {}
            qs_value = " / ".join(
                str(value or "—")
                for value in [
                    qs.get("edition"),
                    qs.get("publicationDate"),
                    qs.get("rank"),
                    qs.get("status"),
                ]
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(item.get("id")),
                        md_cell(item.get("countryRegion")),
                        md_cell(item.get("officialName") or item.get("name")),
                        md_cell(qs_value),
                        md_cell(
                            f"{item.get('inclusionDecision') or 'excluded'}："
                            f"{item.get('reason') or item.get('exclusionReason') or '—'}"
                        ),
                        md_cell(source_links(nested_source_ids(item), source_map)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| — | — | — | — | 未记录经核验的排除机构 | — |")
    write_text(case_dir / "01-SCHOOL-SCOPE.md", lines)


def render_supervisors(
    case_dir: Path,
    case: dict,
    schools: list[dict],
    records: list[dict],
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    lines = common_header("导师总表", case, sources)
    lines.extend(
        [
            "分级与招生状态是独立维度；A 类不代表当前有开放名额。",
            "",
        ]
    )
    school_map = {item["id"]: item for item in schools}
    ordered = sorted(
        records,
        key=lambda item: (
            school_map.get(item.get("schoolId"), {}).get("officialName", item.get("schoolId", "")),
            TIER_ORDER.get(item.get("priorityTier"), 9),
            item.get("name", ""),
        ),
    )
    current_group: tuple[str, str] | None = None
    table_header = [
        "| 姓名/课题组 | 高校、学院、科室与机构隶属 | 研究重点与概述 | 学术任职 | 行政/临床任职 | 公开联系方式及来源 | 主题/博导证据/分级 | 适合博士类型 | 培养与申请路径 | 分层机会状态 | 来源与注意事项 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for record in ordered:
        school = school_map.get(record.get("schoolId"), {})
        group = (record.get("schoolId", ""), record.get("priorityTier", "—"))
        if group != current_group:
            if current_group is not None:
                lines.append("")
            lines.extend(
                [
                    f"## {school.get('displayNameZh') or school.get('officialName') or record.get('schoolId')} · "
                    f"{record.get('priorityTier', '—')} 类",
                    "",
                    *table_header,
                ]
            )
            current_group = group
        institution = affiliation_text(record, school_map, source_map)
        # Some non-A records intentionally use the concise focus sentence as
        # their entire overview.  Show identical text once instead of joining
        # it to itself in the summary table.
        focus = join_values(list(dict.fromkeys(
            item for item in [record.get("focus"), record.get("directionOverviewZh")] if item
        )))
        classification = (
            f"{record.get('topicDirectness', '—')} / {record.get('supervisionEvidence', '—')} / "
            f"{record.get('priorityTier', '—')}"
        )
        basis = record.get("supervisionBasis", {})
        if isinstance(basis, dict) and basis.get("basisType"):
            classification += (
                f"；依据：{basis.get('basisType')}（指导活动：{basis.get('personSupervisionStatus', '—')}；"
                f"资格：{basis.get('eligibilityStatus', '—')}）"
            )
        opportunity = opportunity_text(record, source_map)
        cautions = []
        if record.get("verifiedAt"):
            cautions.append(f"逐记录核验日期：{record['verifiedAt']}")
        if record_verification_is_stale(record, case):
            cautions.append("核验已陈旧，使用前需复核")
        confidence = record.get("confidenceByClaim", {})
        if isinstance(confidence, dict) and confidence:
            cautions.append(
                "分字段置信度：" + "；".join(f"{key}={value}" for key, value in confidence.items())
            )
        if record.get("notes"):
            cautions.append(str(record["notes"]))
        if record.get("directEvidenceException"):
            cautions.append(f"直接/近期证据例外：{record['directEvidenceException']}")
        if record.get("conflicts"):
            cautions.append(f"{len(record['conflicts'])} 条冲突，见证据冲突表")
        audit = recruitment_audit_text(record, source_map)
        if audit != "—":
            cautions.append(f"招生核查：{audit}")
        cautions.append(source_links(source_ids_from_record(record), source_map))
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(
                        record.get("name", "—")
                        + (f"<br>{record.get('group')}" if record.get("group") else "")
                        + f"<br>ID: {record.get('id', '—')}"
                    ),
                    md_cell(institution),
                    md_cell(focus),
                    md_cell(record.get("academicRole")),
                    md_cell(record.get("adminClinicalRole")),
                    md_cell(contact_text(record, source_map)),
                    md_cell(classification),
                    md_cell(join_values(record.get("phdTypes"))),
                    md_cell(record.get("doctoralRoute")),
                    md_cell(opportunity),
                    md_cell("<br>".join(cautions)),
                ]
            )
            + " |"
        )
    if not records:
        lines.append("当前结构化数据中尚无候选导师。")
    write_text(case_dir / "02-SUPERVISOR-TABLE.md", lines)


def render_coverage(
    case_dir: Path,
    case: dict,
    schools: list[dict],
    coverage: list[dict],
    records: list[dict],
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    lines = common_header("跨学院检索覆盖矩阵", case, sources)
    lines.extend(
        [
            "| 学校 ID | 学校 | 检索分支 | 检查单位 | 状态 | 发现候选人 | 来源 | 备注/访问限制 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    school_map = {item["id"]: item for item in schools}
    record_map = {item["id"]: item for item in records}
    ordered = sorted(
        coverage,
        key=lambda row: (
            school_map.get(row.get("schoolId"), {}).get("officialName", row.get("schoolId", "")),
            COVERAGE_AREA_ORDER.index(row.get("area"))
            if row.get("area") in COVERAGE_AREA_ORDER
            else 99,
        ),
    )
    for row in ordered:
        school = school_map.get(row.get("schoolId"), {})
        candidate_names = [
            (
                f"{record_map.get(candidate_id, {}).get('name', candidate_id)} ({candidate_id})"
                if candidate_id in record_map
                else candidate_id
            )
            for candidate_id in row.get("candidateIds", [])
        ]
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.get("schoolId")),
                    md_cell(school.get("displayNameZh") or school.get("officialName") or row.get("schoolId")),
                    md_cell(AREA_LABELS.get(row.get("area"), row.get("area"))),
                    md_cell(join_values(row.get("units"))),
                    md_cell(row.get("status")),
                    md_cell(join_values(candidate_names)),
                    md_cell(source_links(row.get("sourceIds", []), source_map)),
                    md_cell(row.get("notes")),
                ]
            )
            + " |"
        )
    write_text(case_dir / "03-COVERAGE-MATRIX.md", lines)


def render_conflicts(
    case_dir: Path,
    case: dict,
    records: list[dict],
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    lines = common_header("证据冲突、中文互联网与社交平台核验", case, sources)
    lines.extend(
        [
            "## 裁决原则",
            "",
            "当前官方任职/项目/招生页面优先于原始论文、规范身份库、专业二手来源、中文二手来源和用户生成内容。"
            "低优先级来源可用于发现线索与暴露冲突，但不能单独推翻更新的官方证据。",
            "",
            "## 冲突记录",
            "",
            "| 导师 | 字段 | 类型 | 官方/主证据值 | 其他值 | 裁决 | 生效日期 | 来源 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    conflicts = [
        (record, conflict)
        for record in records
        for conflict in record.get("conflicts", [])
        if isinstance(conflict, dict)
    ]
    if conflicts:
        for record, conflict in conflicts:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(record.get("name")),
                        md_cell(conflict.get("field")),
                        md_cell(conflict.get("category")),
                        md_cell(conflict.get("officialValue")),
                        md_cell(conflict.get("otherValue")),
                        md_cell(conflict.get("decision")),
                        md_cell(conflict.get("effectiveDate")),
                        md_cell(source_links(conflict.get("sourceIds", []), source_map)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| — | — | — | 未记录实质冲突 | — | — | — | — |")
    lines.extend(
        [
            "",
            "## 中文互联网与小红书公开信息检查",
            "",
            "| 导师（ID） | 中文互联网状态 | 检查日期、查询、摘要、访问说明与来源 | 小红书状态 | 检查日期、查询、摘要、访问说明与来源 |",
            "|---|---|---|---|---|",
        ]
    )
    for record in records:
        chinese = record.get("chineseCheck", {}) if isinstance(record.get("chineseCheck"), dict) else {}
        xhs = (
            record.get("xiaohongshuCheck", {})
            if isinstance(record.get("xiaohongshuCheck"), dict)
            else {}
        )
        chinese_value = check_text(chinese, source_map)
        xhs_value = check_text(xhs, source_map)
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(f"{record.get('name')} ({record.get('id')})"),
                    md_cell(chinese.get("status")),
                    md_cell(chinese_value),
                    md_cell(xhs.get("status")),
                    md_cell(xhs_value),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "“not_found_publicly”仅表示在记录的公开检索范围内未找到；“public_access_blocked”表示平台登录或访问限制阻断核验，二者均不等于信息不存在。",
            "“not_searched”只允许出现在未完成草稿中；完整交付必须记录检查日期、实际查询和可访问性。",
        ]
    )
    write_text(case_dir / "04-EVIDENCE-CONFLICTS.md", lines)


def render_field(
    lines: list[str], heading: str, value: object, source_map: dict[str, dict] | None = None
) -> None:
    lines.extend([f"### {heading}", ""])
    if isinstance(value, list):
        if not value:
            lines.append("—")
        for item in value:
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or item.get("aim") or "未命名条目"
                summary = item.get("summary") or item.get("description") or item.get("text") or ""
                evidence = source_links(item.get("sourceIds", []), source_map or {})
                lines.append(
                    f"- {title}" + (f"：{summary}" if summary else "")
                    + (f" {evidence}" if evidence != "—" else "")
                )
            else:
                lines.append(f"- {item}")
    else:
        lines.append(str(value or "—"))
    lines.append("")


def render_deep_profiles(
    case_dir: Path,
    case: dict,
    records: list[dict],
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    lines = common_header("A 类导师研究方向深描", case, sources)
    a_records = sorted(
        [item for item in records if item.get("priorityTier") == "A"],
        key=lambda item: (item.get("schoolId", ""), item.get("name", "")),
    )
    lines.extend(
        [
            "方向概述要求 150–250 个可见字符；结构化研究画像要求超过 500 个可见字符。"
            "这两个指标分别统计，不能把后者长度写成前者长度。",
            "",
        ]
    )
    for index, record in enumerate(a_records, start=1):
        overview = str(record.get("directionOverviewZh", ""))
        structured = str(record.get("structuredProfileZh", ""))
        lines.extend(
            [
                f"## {index}. {record.get('name', '—')}",
                "",
                f"**记录 ID：** {record.get('id', '—')}",
                "",
                f"**逐记录核验日期：** {record.get('verifiedAt', '—')}",
                "",
                *(
                    ["**时效提示：** 核验已陈旧，使用前需复核。", ""]
                    if record_verification_is_stale(record, case)
                    else []
                ),
                f"**定位：** {record.get('focus') or '—'}",
                "",
                f"**研究方向概述（{visible_char_count(overview)} 字符）：** {overview or '—'}",
                "",
                f"**结构化研究画像（{visible_char_count(structured)} 字符）：**",
                "",
                structured or "—",
                "",
            ]
        )
        render_field(lines, "核心科学问题", record.get("scientificQuestions", []), source_map)
        render_field(lines, "研究主线", record.get("researchLines", []), source_map)
        render_field(lines, "样本、模型与数据", record.get("materialsModels", []), source_map)
        render_field(lines, "主要方法与分析链", record.get("methods", []), source_map)
        render_field(lines, "验证成熟度", record.get("validationMaturity", ""), source_map)
        render_field(lines, "本人角色与证据边界", record.get("roleBoundary", ""), source_map)
        basis = record.get("supervisionBasis", {})
        if isinstance(basis, dict):
            render_field(
                lines,
                "博士指导证据边界",
                (
                    f"{record.get('supervisionEvidence', '—')} / {basis.get('basisType', '—')} / "
                    f"{basis.get('status', '—')} / personSupervisionStatus={basis.get('personSupervisionStatus', '—')} / "
                    f"eligibilityStatus={basis.get('eligibilityStatus', '—')}。"
                    f"{basis.get('summary', '')} "
                    f"{source_links(unique_ids(basis.get('independenceSourceIds'), basis.get('traineeOrProgrammeSourceIds')), source_map)}"
                ),
                source_map,
            )
        if record.get("directEvidenceException"):
            render_field(lines, "A 类直接/近期证据例外", record.get("directEvidenceException"), source_map)
        lines.extend(["### 可拆分的博士工作包（均为分析者推导，不是完整研究计划）", ""])
        packages = record.get("doctoralWorkPackages", [])
        if not isinstance(packages, list) or not packages:
            lines.append("—")
        else:
            for package in packages:
                if isinstance(package, dict):
                    title = clean_sentence_fragment(package.get("title")) or "未命名工作包"
                    scope = clean_sentence_fragment(package.get("scope")) or "—"
                    assumptions = clean_sentence_fragment(package.get("assumptions")) or "—"
                    if comparable_text(title) == comparable_text(scope):
                        package_opening = title
                    else:
                        package_opening = f"{title}：{scope}"
                    lines.append(
                        f"- {package_opening}；"
                        f"前提/边界：{assumptions}；"
                        f"分析者推导：{'是' if package.get('analystDerived') is True else '未标明'}。"
                        f" {source_links(package.get('sourceIds', []), source_map)}"
                    )
                else:
                    lines.append(f"- {package}")
        lines.append("")
        claim_sources = record.get("claimSourceIds", {})
        if isinstance(claim_sources, dict):
            lines.extend(["### 字段级证据映射", ""])
            for field, source_ids in claim_sources.items():
                if source_ids:
                    lines.append(f"- {field}：{source_links(source_ids, source_map)}")
            lines.append("")
        lines.extend(
            [
                "### 关键证据",
                "",
                source_links(source_ids_from_record(record), source_map),
                "",
            ]
        )
    if not a_records:
        lines.append("当前数据中没有 A 类候选人。")
    write_text(case_dir / "05-A-TIER-DEEP-PROFILES.md", lines)


def render_document_requirements_matrix(
    lines: list[str],
    case: dict,
    records: list[dict],
    source_map: dict[str, dict],
) -> None:
    """Render route-bound material facts for all viable tiers before A-tier detail."""
    lines.extend(
        [
            "## A/B/C 类导师申请材料清单",
            "",
            "材料要求按对应申请路径记录；项目要求不自动等同于导师本人要求。"
            "动机信、个人陈述、申请附信、导师联系/套磁和推荐信分别核验。"
            "“未公开说明”“尚未核验”或缺少历史字段均不能解释为“不要求”。",
            "已关闭或仅历史路径不产生当前材料核验缺项；如保留其已记录材料，路径名称会标明历史/关闭状态。",
            "",
            "| 导师（ID）/分级 | 申请路径 | 材料类型 | 要求状态 | 提交阶段/数量/提交者 | 内容、格式与提交方式 | 核查日期 | 来源 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    viable_records = sorted(
        [record for record in records if record.get("priorityTier") in {"A", "B", "C"}],
        key=lambda record: (
            TIER_ORDER.get(record.get("priorityTier"), 9),
            record.get("schoolId", ""),
            record.get("name", ""),
        ),
    )
    for record in viable_records:
        route_map = document_route_map(record)
        requirements = document_requirements(record)
        identity = f"{record.get('name') or '—'} ({record.get('id') or '—'}) / {record.get('priorityTier')}"
        represented_routes: set[str] = set()
        for item in requirements:
            route_id = str(item.get("routeId") or "")
            route = route_map.get(route_id, {})
            route_name = document_route_name(route_id, route)
            if route_id:
                represented_routes.add(route_id)
            quantity = item.get("quantity")
            quantity_text = f"{quantity} 份" if isinstance(quantity, int) and not isinstance(quantity, bool) else "数量未说明"
            stage = DOCUMENT_STAGE_LABELS.get(item.get("submissionStage"), item.get("submissionStage") or "未说明阶段")
            submitter = DOCUMENT_SUBMITTER_LABELS.get(item.get("submitter"), item.get("submitter") or "未说明提交者")
            rules = [str(item.get("summary") or "未记录具体规则")]
            rules.append("格式/长度：" + str(item.get("formatAndLength") or "未公开说明"))
            rules.append("提交方式：" + str(item.get("submissionMethod") or "未公开说明"))
            checked_at = str(item.get("checkedAt") or "未记录核查日期")
            if dated_object_is_stale(item, case):
                checked_at += "；核验已陈旧，使用前需复核"
            lines.append(
                "| "
                + " | ".join(
                    md_cell(value)
                    for value in [
                        identity,
                        route_name,
                        DOCUMENT_TYPE_LABELS.get(item.get("materialType"), item.get("materialType") or "未标明材料类型"),
                        DOCUMENT_STATUS_LABELS.get(item.get("requirementStatus"), item.get("requirementStatus") or "尚未核验"),
                        f"{stage}；{quantity_text}；{submitter}",
                        "；".join(rules),
                        checked_at,
                        source_links(item.get("sourceIds", []), source_map),
                    ]
                )
                + " |"
            )
        unchecked_routes = [
            (route_id, route)
            for route_id, route in route_map.items()
            if route_id not in represented_routes
            and route.get("status") not in ARCHIVED_OPPORTUNITY_STATUSES
        ]
        if not requirements and not route_map and record.get("opportunityStatus") not in ARCHIVED_OPPORTUNITY_STATUSES:
            unchecked_routes = [("", {"routeName": record.get("doctoralRoute") or "未标明申请路径"})]
        for route_id, route in unchecked_routes:
            route_name = document_route_name(route_id, route)
            lines.append(
                "| "
                + " | ".join(
                    md_cell(value)
                    for value in [
                        identity,
                        route_name,
                        "材料清单未分项核验",
                        "未按新材料清单核验",
                        "未按新材料清单核验",
                        "历史概括文字不替代路径级材料核验；缺失不代表不要求。",
                        "—",
                        "—",
                    ]
                )
                + " |"
            )
    if not viable_records:
        lines.append("| — | — | — | 当前没有 A/B/C 类候选人 | — | — | — | — |")
    lines.append("")


def render_application_readiness(
    case_dir: Path,
    case: dict,
    records: list[dict],
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    lines = common_header("申请材料要求与 A 类导师申请准备信息", case, sources)
    lines.extend(
        [
            "本文件是研究型申请准备的边界化交接包。researchAnchor 是从可核验研究证据中选出的锚点；"
            "researchGap、proposedAim 和 generalApplicantFit 是分析者推导，分别不是导师声明、获批项目或申请人个人匹配结论。",
            "只允许向后续独立写作流程交接：可验证事实、researchAnchor、明确标注推导性质的 gap/aim、待确认问题与风险提示。"
            "本文件不替申请人发言，不包含主题行、称谓、套磁段落、个性化推销或完整研究计划。",
            "",
        ]
    )
    render_document_requirements_matrix(lines, case, records, source_map)
    lines.extend(["## A 类导师申请准备详情", ""])
    a_records = sorted(
        [item for item in records if item.get("priorityTier") == "A"],
        key=lambda item: (item.get("schoolId", ""), item.get("name", "")),
    )
    for index, record in enumerate(a_records, start=1):
        ready = record.get("applicationReadiness", {})
        if not isinstance(ready, dict):
            ready = {}
        application_claim_sources = ready.get("applicationClaimSourceIds", {})
        if not isinstance(application_claim_sources, dict):
            application_claim_sources = {}
        def readiness_claim(field: str) -> str:
            return (
                f"{ready.get(field) or '—'} "
                f"{source_links(application_claim_sources.get(field, []), source_map)}"
            ).strip()
        opportunity = opportunity_text(record, source_map)
        recruitment_audit = recruitment_audit_text(record, source_map)
        lines.extend(
            [
                f"### {index}. {record.get('name', '—')}",
                "",
                f"- 记录 ID：{record.get('id', '—')}",
                f"- 逐记录核验日期：{record.get('verifiedAt', '—')}",
                *(
                    ["- 时效提示：核验已陈旧，使用前需复核。"]
                    if record_verification_is_stale(record, case)
                    else []
                ),
                f"- 博士类型：{join_values(record.get('phdTypes'))}",
                f"- 培养/申请路径：{record.get('doctoralRoute') or '—'}",
                f"- 分层招生边界：{opportunity}",
                f"- 招生核查记录：{recruitment_audit}",
                f"- 官方联系规则：{readiness_claim('contactProtocol')}",
                f"- 申请窗口与截止：{readiness_claim('applicationWindow')}",
                f"- 资格与语言要求：{readiness_claim('eligibilityRequirements')}",
                f"- 必需材料：{readiness_claim('requiredDocuments')}",
                f"- 研究计划要求：{readiness_claim('proposalRequirement')}",
                f"- 经费、雇佣与学费模式：{readiness_claim('fundingModel')}",
                f"- 主导师/联合指导结构：{readiness_claim('supervisionSetup')}",
                f"- researchAnchor（证据锚点）：{clean_sentence_fragment(ready.get('researchAnchor')) or '—'}。 "
                f"{source_links(ready.get('anchorSourceIds', []), source_map)}",
                f"- researchGap（分析者推导，不是导师声明）：{ready.get('researchGap') or '—'} "
                f"{source_links(ready.get('gapSourceIds', []), source_map)}",
                f"- proposedAim（分析者推导，不是获批课题）：{ready.get('proposedAim') or '—'}",
                f"- 一般匹配背景（分析者推导，非申请人个人匹配结论）：{readiness_claim('generalApplicantFit')}",
                "",
                "#### 需要向项目或导师确认的问题",
                "",
            ]
        )
        questions = []
        for key in ["doctoralQuestions", "resourceQuestions", "fundingQuestions"]:
            value = ready.get(key, [])
            if isinstance(value, list):
                questions.extend(str(item) for item in value if str(item).strip())
            elif str(value or "").strip():
                questions.append(str(value))
        lines.extend(f"- {item}" for item in questions)
        if not questions:
            lines.append("- —")
        lines.extend(["", "#### 注意事项", ""])
        cautions = ready.get("cautions", [])
        if isinstance(cautions, list) and cautions:
            lines.extend(f"- {item}" for item in cautions)
        elif str(cautions or "").strip():
            lines.append(f"- {cautions}")
        else:
            lines.append("- —")
        lines.extend(
            [
                "",
                "#### 相关证据",
                "",
                source_links(
                    unique_ids(
                        record.get("researchSourceIds"),
                        record.get("doctoralSourceIds"),
                        record.get("recruitmentSourceIds"),
                        record.get("directEvidenceIds"),
                        ready.get("anchorSourceIds"),
                        ready.get("gapSourceIds"),
                        ready.get("applicationSourceIds"),
                        ready.get("proposalSourceIds"),
                        ready.get("fundingSourceIds"),
                        nested_source_ids(ready.get("documentRequirements", [])),
                        nested_source_ids(record.get("opportunities", [])),
                        nested_source_ids(record.get("recruitmentAudit", {})),
                    ),
                    source_map,
                ),
                "",
            ]
        )
    if not a_records:
        lines.append("当前数据中没有 A 类候选人。")
    write_text(case_dir / "06-APPLICATION-READINESS.md", lines)


def render_source_ledger(
    case_dir: Path, case: dict, sources: list[dict]
) -> None:
    lines = common_header("来源台账", case, sources)
    lines.extend(
        [
            "每条来源记录只在本台账出现一次，并以一个互斥 type 表示其主要证据功能；claimDomains 记录页面实际支持的全部主张域，同一页面支持多项主张时复用同一个 source ID。",
            "workId 与 DOI/PMID/PMCID/基金号/注册号/职位号等 identifiers 用于识别同一底层研究产出或机会，避免用不同落地页重复抬高证据数量。统计同时报告来源记录数与规范化去重链接数。",
            "",
            "| ID | 类型 | 主张域 | 明示主体 ID | 权威类别 | 载体 | workId/标识符 | 标题 | 发布者 | 发布/访问日期 | 支持主张 | 人物角色 | 主题相关性 | 状态 | URL |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for source in sorted(sources, key=lambda item: str(item.get("id", ""))):
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(source.get("id")),
                    md_cell(source.get("type")),
                    md_cell(join_values(source.get("claimDomains"))),
                    md_cell(join_values(source.get("subjectIds"))),
                    md_cell(source.get("authorityClass")),
                    md_cell(source.get("medium")),
                    md_cell(identifier_text(source)),
                    md_cell(source.get("title")),
                    md_cell(source.get("publisher")),
                    md_cell(
                        f"{source.get('publishedDate') or '—'} / {source.get('accessedDate') or '—'}"
                    ),
                    md_cell(source.get("claim")),
                    md_cell(person_roles_text(source)),
                    md_cell(source.get("topicRelevance")),
                    md_cell(source.get("status")),
                    md_cell(
                        f"[原始链接]({source.get('url')})" if source.get("url") else "—"
                    ),
                ]
            )
            + " |"
        )
    write_text(case_dir / "07-SOURCE-LEDGER.md", lines)


def render_contact_audit(
    case_dir: Path,
    case: dict,
    records: list[dict],
    contact_audit: dict | None,
    source_map: dict[str, dict],
    sources: list[dict],
) -> None:
    if contact_audit is None:
        return

    channel_type_labels = {
        "personal_email": "本人邮箱",
        "clinical_email": "本人临床邮箱",
        "publication_correspondence_email": "论文通讯邮箱（仅论文时点）",
        "group_email": "课题组邮箱",
        "unit_email": "研究单元邮箱",
        "department_mailbox": "院系／科室邮箱",
        "secretariat_email": "秘书处邮箱",
        "assistant_contact": "助理联系人",
        "phone": "电话",
        "contact_form": "联系表单",
        "not_public": "未发现公开渠道",
    }
    owner_labels = {
        "candidate": "导师本人",
        "assistant": "助理",
        "group": "课题组",
        "unit": "研究单元",
        "department": "院系／科室",
        "secretariat": "秘书处",
        "institution": "机构",
        "unclear": "归属未明确",
    }
    currentness_labels = {
        "current_official": "当前官方",
        "publication_time_only": "仅论文发表时点",
        "former_institution": "原机构",
        "currentness_unverified": "当前性未核实",
        "historical": "历史渠道",
        "not_public": "未公开",
    }
    stage_labels = {
        "current_official_primary": "当前官方主路径",
        "current_official_fallback": "当前官方备用路径",
        "publication": "论文通讯信息",
        "researcher_controlled": "研究者自管页面（线索）",
        "other": "其他核查",
    }
    policy_labels = {
        "explicitly_supported": "官方明确支持该联系路径",
        "explicitly_discouraged": "官方明确不建议主动联系",
        "restricted_to_route": "仅限指定联系路径",
        "not_stated": "官方未说明主动联系许可",
    }
    record_map = {str(item.get("id")): item for item in records if item.get("id")}
    lines = common_header("导师联系方式补充审计", case, sources)
    lines.extend(
        [
            f"- 补充审计版本：{contact_audit.get('schemaVersion') or '—'}",
            f"- 总体核查日期：{contact_audit.get('checkedAt') or '—'}",
            "",
            "本表区分联系人归属与当前性。公开联系方式不自动表示导师允许未经邀请的邮件；论文通讯邮箱也不自动等于当前官方邮箱。",
            "",
        ]
    )

    audit_records = contact_audit.get("records", [])
    if not isinstance(audit_records, list) or not audit_records:
        lines.append("当前补充审计没有候选人记录。")
        write_text(case_dir / OPTIONAL_CONTACT_OUTPUT, lines)
        return

    for index, audit_record in enumerate(audit_records, start=1):
        if not isinstance(audit_record, dict):
            continue
        candidate_id = str(audit_record.get("candidateId") or "")
        candidate = record_map.get(candidate_id, {})
        candidate_name = str(candidate.get("name") or candidate_id or "未标明候选人")
        lines.extend(
            [
                f"## {index}. {candidate_name}",
                "",
                f"- 候选人 ID：`{candidate_id or '—'}`",
                f"- 联系方式核查日期：{audit_record.get('checkedAt') or '—'}",
                f"- 当前机构：{audit_record.get('currentInstitutionZh') or '未核实'}",
                f"- 联系许可边界：{policy_labels.get(audit_record.get('contactPolicy'), audit_record.get('contactPolicy') or '未核实')}",
                f"- 风险提示：{audit_record.get('cautionZh') or '未记录额外提示'}",
                "",
                "### 官方优先检索顺序",
                "",
                "| 顺序 | 检索阶段 | 路径类型 | 结果 | 来源 |",
                "|---|---|---|---|---|",
            ]
        )
        search_audit = audit_record.get("searchAudit", {})
        steps = search_audit.get("steps", []) if isinstance(search_audit, dict) else []
        if isinstance(steps, list) and steps:
            for step_index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    continue
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            str(step_index),
                            md_cell(stage_labels.get(step.get("stage"), step.get("stage") or "—")),
                            md_cell(step.get("routeType") or "—"),
                            md_cell(step.get("resultZh") or "—"),
                            md_cell(source_links(step.get("sourceIds", []), source_map)),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("| — | — | — | 未记录检索步骤 | — |")
        exhausted = (
            search_audit.get("officialFallbacksExhaustedBeforePublication")
            if isinstance(search_audit, dict)
            else None
        )
        lines.extend(
            [
                "",
                "- 论文检索前已完成适用的官方备用路径检查："
                + ("是" if exhausted is True else "否或未核实"),
                "",
                "### 公开渠道",
                "",
                "| 渠道 ID | 类型 | 值 | 归属 | 当前性 | 本人绑定 | 来源 | 说明 |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        channels = audit_record.get("channels", [])
        if isinstance(channels, list) and channels:
            for channel in channels:
                if not isinstance(channel, dict):
                    continue
                channel_type = str(channel.get("type") or "")
                value = channel.get("value") or ("未发现公开渠道" if channel_type == "not_public" else "—")
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            md_cell(channel.get("channelId") or "—"),
                            md_cell(channel_type_labels.get(channel_type, channel_type or "—")),
                            md_cell(value),
                            md_cell(owner_labels.get(channel.get("owner"), channel.get("owner") or "—")),
                            md_cell(currentness_labels.get(channel.get("currentness"), channel.get("currentness") or "—")),
                            md_cell("是" if channel.get("candidateBound") is True else "否或未核实"),
                            md_cell(source_links(channel.get("sourceIds", []), source_map)),
                            md_cell(channel.get("notesZh") or "—"),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("| — | — | — | — | — | — | — | 未记录渠道 |")

        preferred = audit_record.get("preferredRoute")
        if isinstance(preferred, dict):
            lines.extend(
                [
                    "",
                    f"- 首选渠道 ID：`{preferred.get('preferredChannelId') or '—'}`",
                    f"- 选择理由：{preferred.get('reasonZh') or '—'}",
                    "- 发送前同日复核：" + ("需要" if preferred.get("sameDayRecheckRequired") is True else "不需要"),
                    "",
                ]
            )
        else:
            lines.extend(["", "- 首选渠道：无（仅 `not_public` 时允许）。", ""])

    write_text(case_dir / OPTIONAL_CONTACT_OUTPUT, lines)


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    case, schools, coverage, records, sources, contact_audit = load_case(case_dir)
    source_map = {str(item.get("id")): item for item in sources if item.get("id")}

    render_index(case_dir, case, schools, coverage, records, sources, contact_audit)
    render_school_scope(case_dir, case, schools, source_map, sources)
    render_supervisors(case_dir, case, schools, records, source_map, sources)
    render_coverage(case_dir, case, schools, coverage, records, source_map, sources)
    render_conflicts(case_dir, case, records, source_map, sources)
    render_deep_profiles(case_dir, case, records, source_map, sources)
    render_application_readiness(case_dir, case, records, source_map, sources)
    render_source_ledger(case_dir, case, sources)
    render_contact_audit(case_dir, case, records, contact_audit, source_map, sources)

    stats = evidence_stats(sources)
    tiers = Counter(str(item.get("priorityTier", "unclassified")) for item in records)
    print(
        json.dumps(
            {
                "status": "rendered",
                "caseDir": str(case_dir),
                "files": output_files(case_dir),
                "schools": len(schools),
                "candidates": len(records),
                "tierCounts": {tier: tiers.get(tier, 0) for tier in ["A", "B", "C", "D"]},
                **stats,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
