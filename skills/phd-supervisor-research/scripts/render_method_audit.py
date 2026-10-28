#!/usr/bin/env python3
"""Render 08-RESEARCH-METHOD-TRANSLATION-AUDIT.md from the supplemental JSON."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


_VALIDATOR_PATH = Path(__file__).with_name("validate_method_audit.py")
_VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_method_audit", _VALIDATOR_PATH)
if _VALIDATOR_SPEC is None or _VALIDATOR_SPEC.loader is None:
    raise RuntimeError(f"Cannot load validator module from {_VALIDATOR_PATH}")
_VALIDATOR_MODULE = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR_MODULE)
validation_payload = _VALIDATOR_MODULE.validation_payload

ROLE_SORT_ORDER = {"O3C": 0, "O2C": 1, "O2S": 2, "O1L": 3, "O1F": 4, "O0": 5}

TRANSLATION_EVIDENCE_LABELS = {
    "hasClinicalAnchor": "临床锚点",
    "hasMolecularOmicsOrMechanisticBridge": "分子／组学／机制桥接",
    "hasIndependentOrOrthogonalValidation": "独立／正交验证",
    "hasProspectiveOrInterventionalLink": "前瞻／干预关联",
    "hasFunctionalValidation": "功能验证",
    "hasClinicalLevelValidation": "临床层面验证",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def escape_cell(value: Any) -> str:
    rendered = "未公开／未核实" if value is None or value == "" else str(value)
    return rendered.replace("|", "\\|").replace("\n", "<br>")


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def format_conflict(item: Any) -> str:
    if not isinstance(item, dict):
        return "未结构化冲突"
    conflict_type = item.get("type") or "未分类"
    impact = item.get("impact") or "impact 未记录"
    resolution = "已解决" if item.get("resolved") is True else "未解决"
    summary = item.get("summary") or "未说明冲突"
    return f"{conflict_type}｜{impact}｜{resolution}｜{summary}"


def unresolved_conflicts(candidate: dict[str, Any]) -> list[str]:
    output: list[str] = []
    for item in candidate.get("conflicts", []):
        if isinstance(item, dict) and item.get("resolved") is not True:
            output.append(format_conflict(item))
    for paper in candidate.get("papers", []):
        if not isinstance(paper, dict):
            continue
        for item in paper.get("conflicts", []):
            if isinstance(item, dict) and item.get("resolved") is not True:
                output.append(
                    f"{paper.get('workId', '未标识论文')}：{format_conflict(item)}"
                )
    return output


def join_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "未记录"
    return "；".join(f"{key}={item}" for key, item in value.items())


def format_translation_evidence(value: Any) -> str:
    if not isinstance(value, dict):
        return "未记录"
    return "；".join(
        f"{label}={'是' if value.get(field) is True else '否'}"
        for field, label in TRANSLATION_EVIDENCE_LABELS.items()
    )


def paper_sort_key(paper: dict[str, Any]) -> tuple[int, int, str]:
    raw_date = paper.get("publicationDate")
    try:
        date_rank = -date.fromisoformat(str(raw_date)).toordinal()
    except ValueError:
        date_rank = 0
    return (
        ROLE_SORT_ORDER.get(str(paper.get("authorRole")), len(ROLE_SORT_ORDER)),
        date_rank,
        str(paper.get("workId") or ""),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", required=True, type=Path)
    args = parser.parse_args()
    case_dir = args.case_dir.resolve()
    check = validation_payload(case_dir, strict=False)
    if check["status"] != "valid":
        print(json.dumps(check, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    audit_path = case_dir / "data" / "research-method-audit.json"
    audit = read_json(audit_path)
    audit_sha256 = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    candidates = audit.get("candidates", [])
    status_counts = Counter(item.get("scientificAuditStatus") for item in candidates)
    depth_counts: Counter[str] = Counter()
    method_family_counts: Counter[str] = Counter()
    eligible_count = 0
    m4_count = 0
    all_conflicts: list[tuple[str, str]] = []
    for candidate in candidates:
        if candidate.get("currentProgramCrossCheck", {}).get("status") == "M4_CURRENT_PROGRAM_CROSSCHECK":
            m4_count += 1
        for paper in candidate.get("papers", []):
            if paper.get("inclusionDecision") == "included":
                eligible_count += 1
                depth_counts[str(paper.get("reviewDepth"))] += 1
                method_family_counts.update(set(string_list(paper.get("methodFamilyTags"))))
        for conflict in unresolved_conflicts(candidate):
            all_conflicts.append((str(candidate.get("name") or candidate.get("candidateId")), conflict))

    lines = [
        "# 研究方法与临床转化审计",
        "",
        f"- 案例核验日期：{audit.get('caseAsOf', '未核实')}",
        f"- 审计生成日期：{audit.get('generatedAt', '未核实')}",
        f"- 审计 JSON SHA-256：`{audit_sha256}`",
        f"- 保留的 A/B/C 导师：{len(candidates)} 人",
        (
            "- 科学审计状态："
            f"confirmed {status_counts.get('confirmed', 0)}；"
            f"provisional {status_counts.get('provisional', 0)}；"
            f"ungraded {status_counts.get('ungraded', 0)}；"
            f"incomplete {status_counts.get('incomplete', 0)}"
        ),
        f"- 纳入论文：{eligible_count} 篇",
        (
            "- 方法家族论文数（多标签分别计数）："
            f"实验 {method_family_counts.get('EXPERIMENTAL', 0)}；"
            f"生信 {method_family_counts.get('BIOINFORMATICS', 0)}；"
            f"组学 {method_family_counts.get('OMICS', 0)}；"
            f"理论方法 {method_family_counts.get('THEORETICAL_METHOD', 0)}；"
            f"纯临床结局 {method_family_counts.get('CLINICAL_OUTCOMES', 0)}"
        ),
        (
            "- 论文证据深度："
            f"M0 {depth_counts.get('M0_MACHINE_ABSTRACT', 0)}；"
            f"M2 {depth_counts.get('M2_HUMAN_ABSTRACT', 0)}；"
            f"M3 {depth_counts.get('M3_FULL_TEXT_DESIGN', 0)}；"
            f"完成 M4 当前研究方向交叉核对 {m4_count} 位导师"
        ),
        "",
        "> MTG 与 A/B/C 衡量不同维度。MTG 仅用于同一 A/B/C 档内的次级排序或并列决策，不自动改变导师档级。M2 的历史代码名含 HUMAN，但只有 `reviewActor=human_manual` 才表示真实人工审核；其余情况按实际 actor 展示。",
        "",
        "## 中文代码图例",
        "",
        "- 作者角色：`O3C` 明确通讯／末位通讯；`O2C` 明确共同通讯；`O2S` 明确资深／共同资深但非通讯；`O1L` 仅末位；`O1F` 第一／共同第一；`O0` 普通中间、联盟成员或无明确声明的倒数第二作者。",
        "- 主方法码：`RM-E` 基础／机制实验；`RM-B` 应用生信或组学；`RM-EB` 同篇实验—计算整合；`RM-M` 理论／算法／软件方法；`RM-C` 纯临床结局研究。",
        "- 方法家族标签：`EXPERIMENTAL` 实验；`BIOINFORMATICS` 生物信息分析；`OMICS` 组学；`THEORETICAL_METHOD` 理论方法；`CLINICAL_OUTCOMES` 纯临床结局。生信与组学独立计数，可在同一论文共存。",
        "- 转化码：`TR0` 无真实临床锚点；`TR1` 临床锚点加分子／组学／机制桥接；`TR2` 再加独立或正交验证；`TR3` 前瞻／干预关联、功能验证和临床层面验证闭环；`CLIN_ONLY` 无分子／组学／功能桥接的纯临床研究。",
        "- 检索阶段：`BASE_5Y` 滚动五年基线；`EXTENDED_8Y` 因五年 candidate-led 论文不足五篇而扩展至滚动八年。",
        "- 冲突影响：`NONBLOCKING_PROVISIONAL` 允许保留临时等级但不能 confirmed；`BLOCKS_GRADE` 阻断等级并要求 incomplete。",
        "",
        "## 导师总表",
        "",
        "| 稳定ID | 导师 | 中文院系／课题组 | 中文当前任职 | 中文研究方向 | A/B/C | 科学审计状态 | MTG | 置信度 | 组合类型 | 机会状态 | 联系控制 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for candidate in candidates:
        lines.append(
            "| "
            + " | ".join(
                escape_cell(value)
                for value in (
                    candidate.get("candidateId"),
                    candidate.get("name") or candidate.get("candidateId"),
                    candidate.get("departmentZh"),
                    candidate.get("currentRoleZh"),
                    candidate.get("researchDirectionZh"),
                    candidate.get("priorityTier"),
                    candidate.get("scientificAuditStatus"),
                    candidate.get("grade"),
                    candidate.get("confidence"),
                    ", ".join(candidate.get("portfolioCodes", [])) or "未形成组合代码",
                    candidate.get("opportunityStatus"),
                    candidate.get("outreachControl", {}).get("status"),
                )
            )
            + " |"
        )

    lines.extend(["", "## 逐位论文组合", ""])
    for candidate in candidates:
        name = candidate.get("name") or candidate.get("candidateId")
        outreach = candidate.get("outreachControl", {})
        crosscheck = candidate.get("currentProgramCrossCheck", {})
        lines.extend(
            [
                f"### {name}（{candidate.get('candidateId', '未核实')}）",
                "",
                f"- 分类与分级：{candidate.get('priorityTier', '未核实')}；{candidate.get('scientificAuditStatus', '未核实')}；{candidate.get('grade') or '未分级'}",
                f"- 置信度：{candidate.get('confidence', '未核实')}；等级调整：{join_mapping(candidate.get('gradeAdjustment'))}",
                f"- 院系／课题组：{candidate.get('departmentZh', '未核实')}",
                f"- 当前任职：{candidate.get('currentRoleZh', '未核实')}",
                f"- 研究方向：{candidate.get('researchDirectionZh', '未核实')}",
                f"- 审计窗口：{candidate.get('windowYears', '未核实')} 年（{candidate.get('windowStart', '未核实')} 至 {candidate.get('windowEnd', '未核实')}）；扩展原因 {candidate.get('extensionReason') or '不适用'}；检索日 {candidate.get('searchDate', '未核实')}；检索状态 {candidate.get('searchStatus', '未核实')}",
                f"- 检索对账：{join_mapping(candidate.get('searchReconciliation'))}",
                f"- 组合代码：{', '.join(candidate.get('portfolioCodes', [])) or '未形成组合代码'}",
                f"- 组合计数：{join_mapping(candidate.get('portfolioCounts'))}；主导方法：{join_mapping(candidate.get('dominance'))}",
                f"- MTG 评分：{join_mapping(candidate.get('scores'))}",
                f"- 评分依据：{join_mapping(candidate.get('scoreBasis'))}",
                f"- M4 当前方向核对：{crosscheck.get('status', '未完成')}；结果 {crosscheck.get('result', 'not_assessed')}；来源 {', '.join(string_list(crosscheck.get('sourceIds'))) or '未核实'}；{crosscheck.get('summary', '')}",
                f"- 机会状态：{candidate.get('opportunityStatus', '未核实')}；联系控制：{outreach.get('status', '未核实')}；原因 {outreach.get('reason') or '无'}；日期 {outreach.get('recordedAt') or '无'}；范围 {outreach.get('scope') or '无'}；复核条件 {outreach.get('recheckCondition') or '无'}",
                "",
                "检索计划：",
                "",
                "| queryId | sourceKey | 来源 | 精确查询 |",
                "|---|---|---|---|",
            ]
        )
        search_plan = [entry for entry in candidate.get("searchPlan", []) if isinstance(entry, dict)]
        if search_plan:
            for entry in search_plan:
                lines.append(
                    "| "
                    + " | ".join(
                        escape_cell(value)
                        for value in (
                            entry.get("queryId"),
                            entry.get("sourceKey"),
                            entry.get("source"),
                            entry.get("query"),
                        )
                    )
                    + " |"
                )
        else:
            lines.append("| 未记录 | 未记录 | 未记录 | 未记录 |")
        lines.extend(
            [
                "",
                "检索台账：",
                "",
                "| queryId | 来源 | 阶段 | 结构化窗口 | 检索日 | 分页／游标 | 结果数 | 访问／截断 | 重试说明 |",
                "|---|---|---|---|---|---|---:|---|---|",
            ]
        )
        search_ledger = [entry for entry in candidate.get("searchLedger", []) if isinstance(entry, dict)]
        if search_ledger:
            for entry in search_ledger:
                lines.append(
                    "| "
                    + " | ".join(
                        escape_cell(value)
                        for value in (
                            entry.get("queryId"),
                            entry.get("source"),
                            entry.get("searchStage"),
                            f"{entry.get('windowStart', '未核实')} 至 {entry.get('windowEnd', '未核实')}",
                            entry.get("searchedAt"),
                            entry.get("pagesOrCursorsChecked"),
                            entry.get("resultCount"),
                            f"{entry.get('accessStatus', '未核实')} / truncated={entry.get('truncated', '未核实')}",
                            entry.get("retryNotes") or "无",
                        )
                    )
                    + " |"
                )
        else:
            lines.append("| 未记录 | 未记录 | 未记录 | 未记录 | 未记录 | 未记录 | 0 | 未记录 | 未记录 |")
        candidate_level_conflicts = [
            format_conflict(item) for item in candidate.get("conflicts", []) if isinstance(item, dict)
        ]
        lines.extend(
            [
                "",
                "候选人级冲突（含 impact）："
                + ("；".join(candidate_level_conflicts) if candidate_level_conflicts else "无。"),
                "",
                "| workId／论文 | 日期 | 通讯／资深／作者顺序 | 方法主码／家族／组学 | 转化码／结构化证据 | 证据特征 | 审阅深度／主体／日期／定位 | 来源 | 是否触发评分／组合 | 冲突及 impact |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        included = sorted(
            [
                paper
                for paper in candidate.get("papers", [])
                if isinstance(paper, dict) and paper.get("inclusionDecision") == "included"
            ],
            key=paper_sort_key,
        )
        if not included:
            lines.append("| 无可用纳入论文 | — | — | — | — | — | — | — | — | — |")
        for paper in included:
            trigger = "/".join(
                [
                    "评分" if paper.get("scoreTrigger") else "",
                    "组合" if paper.get("portfolioTrigger") else "",
                ]
            ).strip("/") or "否"
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in (
                        f"{paper.get('workId', '未核实')}<br>{paper.get('title') or '未核实'}",
                        paper.get("publicationDate"),
                        (
                            f"角色 {paper.get('authorRole', '未核实')}<br>"
                            f"通讯 {paper.get('correspondingStatus', '未核实')}；"
                            f"资深 {paper.get('seniorStatus', '未核实')}；"
                            f"顺序 {paper.get('authorOrderStatus', '未核实')}<br>"
                            f"依据 {paper.get('roleBasis', '未核实')}<br>"
                            f"作者证据 IDs: {', '.join(string_list(paper.get('authorshipEvidenceSourceIds'))) or '未核实'}；"
                            f"定位 {paper.get('authorshipEvidenceLocator') or '未核实'}"
                        ),
                        (
                            f"{paper.get('methodCode', '未核实')}<br>"
                            f"tags: {', '.join(string_list(paper.get('methodFamilyTags'))) or '未记录'}<br>"
                            f"omics: {', '.join(string_list(paper.get('omicsModalities'))) or '不适用'}"
                        ),
                        (
                            f"{paper.get('translationCode', '未核实')} / "
                            f"{paper.get('clinicalOnlySubtype') or '不适用'}<br>"
                            f"{format_translation_evidence(paper.get('translationEvidence'))}"
                        ),
                        join_mapping(paper.get("evidenceFeatures")),
                        f"{paper.get('reviewDepth', '未核实')} / {paper.get('reviewActor', '未核实')} / {paper.get('reviewedAt', '未核实')} / {paper.get('reviewLocator', '未核实')}",
                        f"IDs: {', '.join(string_list(paper.get('sourceIds'))) or '未核实'}<br>URLs: {', '.join(string_list(paper.get('sourceUrls'))) or '未核实'}",
                        trigger,
                        "；".join(
                            format_conflict(item)
                            for item in paper.get("conflicts", [])
                            if isinstance(item, dict)
                        )
                        or "无",
                    )
                )
                + " |"
            )
        excluded = [
            paper
            for paper in candidate.get("papers", [])
            if isinstance(paper, dict) and paper.get("inclusionDecision") == "excluded"
        ]
        lines.extend(["", "排除记录："])
        if excluded:
            lines.extend(
                f"- {paper.get('workId', '未标识')}：{paper.get('exclusionReason', '未说明原因')}"
                for paper in excluded
            )
        else:
            lines.append("- 无。")
        conflicts = unresolved_conflicts(candidate)
        lines.extend(["", "未解决事项：" + ("；".join(conflicts) if conflicts else "无。"), ""])

    lines.extend(["## 全局未解决冲突", ""])
    if all_conflicts:
        for name, conflict in all_conflicts:
            lines.append(f"- {name}：{conflict}")
    else:
        lines.append("- 无。")
    held = [
        candidate
        for candidate in candidates
        if candidate.get("outreachControl", {}).get("status") in {"hold_no_capacity", "hold_user"}
    ]
    lines.extend(["", "## 联系暂停控制（不改变科学审计与 A/B/C）", ""])
    if held:
        lines.extend(
            [
                "| 导师 | 状态 | 原因 | 记录日期 | 适用范围 | 复核条件 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for candidate in held:
            outreach = candidate.get("outreachControl", {})
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in (
                        candidate.get("name") or candidate.get("candidateId"),
                        outreach.get("status"),
                        outreach.get("reason"),
                        outreach.get("recordedAt"),
                        outreach.get("scope"),
                        outreach.get("recheckCondition"),
                    )
                )
                + " |"
            )
    else:
        lines.append("- 无联系暂停记录。")
    lines.extend(
        [
            "",
            "本报告仅呈现研究证据、方法组合与临床转化深度，不包含套磁信或研究计划撰写。",
            "",
        ]
    )

    output = case_dir / "08-RESEARCH-METHOD-TRANSLATION-AUDIT.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    index_path = case_dir / "00-INDEX.md"
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8-sig")
        link_line = "- [08-RESEARCH-METHOD-TRANSLATION-AUDIT.md](08-RESEARCH-METHOD-TRANSLATION-AUDIT.md)：逐篇研究方法、临床转化深度与 MTG 独立适配度审计"
        if link_line not in index_text:
            marker = "## 未解决事项与限制"
            if marker in index_text:
                index_text = index_text.replace(marker, f"{link_line}\n\n{marker}", 1)
            else:
                index_text = index_text.rstrip() + f"\n\n{link_line}\n"
            index_path.write_text(index_text, encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
