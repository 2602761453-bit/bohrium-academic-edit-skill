#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小编辑 / 语义保持 校验器（academic-edit-minimal）

三道守恒守卫（限定强度、数字/单位、引用与图表指向）+ 输出契约检查。
只用标准库，无网络。

用法:
    python3 scripts/check_minimal_edit.py --case /input/case.json --result /app/output/result.json
    python3 scripts/check_minimal_edit.py --case case.json --result result.json --json
    python3 scripts/check_minimal_edit.py --case case.json --result result.json --source manuscript.md

退出码:
    0  通过
    2  守恒守卫违规（数字/单位、引用、图表、限定强度、否定、相关性升格）
    3  输出契约或字段缺失/非法
    4  输入不可读（文件缺失、JSON 解析失败、正文找不到）
"""

import argparse
import json
import re
import sys

try:  # 保证中文报告在任何终端都不乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover
    pass

# ---------------------------------------------------------------- 词表

# 限定强度：等级越高主张越强
HEDGE_LEVELS = {
    5: ["prove", "proves", "proved", "demonstrate", "demonstrates", "demonstrated",
        "confirm", "confirms", "confirmed", "establish", "establishes", "established",
        "always", "necessarily", "definitely", "conclusively", "undoubtedly",
        "证明", "证实", "确认", "必然", "总是", "毫无疑问"],
    4: ["show", "shows", "shown", "indicate", "indicates", "indicated",
        "significantly", "significant", "strongly", "clearly", "supports", "support",
        "表明", "显著", "强烈", "明显支持"],
    3: ["suggest", "suggests", "suggested", "associated with", "correlated with",
        "correlates with", "related to", "consistent with", "implies",
        "提示", "相关于", "支持", "暗示"],
    2: ["may", "might", "could", "can", "appears", "appear", "seems", "seem",
        "possibly", "presumably", "likely", "unlikely", "tends to", "tend to",
        "可能", "或许", "似乎", "推测", "倾向于"],
    1: ["remains unclear", "is unclear", "is unknown", "unknown", "warrants further",
        "preliminary", "limited evidence", "has yet to", "尚不清楚", "尚不明确",
        "有待", "初步", "证据有限"],
}

NEGATION = ["not", "no", "never", "none", "neither", "nor", "without", "except",
            "excluding", "only", "unless", "cannot", "fails to", "fail to",
            "不", "未", "无", "非", "没有", "不能", "仅", "只", "除非", "无法"]

CAUSAL_STRONG = ["cause", "causes", "caused", "causing", "leads to", "lead to",
                 "led to", "results in", "result in", "resulted in", "drives",
                 "drive", "responsible for", "due to", "causal",
                 "导致", "引起", "造成", "决定"]
ASSOC_WEAK = ["associated with", "correlated with", "correlates with", "related to",
              "consistent with", "相关于", "相关"]

UNITS = (r"mg|mL|mM|nM|M|kg|g|L|l|dL|°C|K|min|h|hr|hrs|s|ms|day|days|week|weeks|"
         r"month|months|year|years|nm|μm|µm|mm|cm|km|Hz|kHz|MHz|GHz|Da|kDa|mol|"
         r"mmol|μmol|U|IU|rpm|bp|kb")

NUMBER_RE = re.compile(
    r"(?<![\w.])[-+±]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?(?:\s?(?:%|" + UNITS + r")\b)?"
)
CITATION_RE = re.compile(
    r"\[\s*\d+(?:\s*[-,–—]\s*\d+)*\s*\]"
    r"|\(\s*[A-Z][A-Za-z'\-]+(?:\s+(?:et\s+al\.?|and|&)\s+[A-Za-z'\-]+)*\s*,\s*\d{4}[a-z]?\s*\)"
)
FIGURE_RE = re.compile(
    r"\b(?:Fig(?:ure)?\.?|Table|Eq(?:uation)?\.?|Section|Sec\.?)\s*\(?\d+[A-Za-z]?\)?"
    r"|[图表]\s*\d+",
    re.IGNORECASE,
)
# 带连字符的标识符（FEV-1、IL-6R、COVID-19）与字母数字混合名（FEV1、IL6、rs12345）
HYPHEN_ID_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:[-‐‑][A-Za-z0-9]+)+\b")
ALNUM_ID_RE = re.compile(r"\b[A-Za-z]+\d+[A-Za-z0-9]*\b")
RANGE_RE = re.compile(r"(?<=\d)\s*[-–—]\s*(?=\d)")

REQUIRED_EDIT_FIELDS = ("sent_id", "location", "original", "revised", "type", "reason", "guards")
REQUIRED_GUARDS = ("numbers_ok", "citations_ok", "figures_ok", "hedge_ok", "negation_ok")
VALID_STATUS = ("success", "partial", "insufficient_material")


class Finding:
    def __init__(self, code, where, message):
        self.code = code
        self.where = where
        self.message = message

    def __str__(self):
        return f"[{self.code}] {self.where}: {self.message}"


# ---------------------------------------------------------------- 基础工具

def normalize(text):
    text = text.replace("\u00b5", "μ").replace("−", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[ \t]+", " ", text)
    return text.lower()


def multiset(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def diff_multiset(a, b):
    missing = {k: v for k, v in a.items() if b.get(k, 0) < v}
    added = {k: v for k, v in b.items() if a.get(k, 0) < v}
    return missing, added


def number_multiset(text):
    """数值 + 单位。先剔除引用、图表指向与标识符，避免把 [12]、FEV-1 当成数值。"""
    work = CITATION_RE.sub(" ", text)
    work = FIGURE_RE.sub(" ", work)
    work = HYPHEN_ID_RE.sub(" ", work)
    work = ALNUM_ID_RE.sub(" ", work)
    work = RANGE_RE.sub(" ", work)  # 3-5 视作 3 和 5 两个数
    found = NUMBER_RE.findall(work)
    return multiset(re.sub(r"\s+", "", normalize(t)) for t in found)


def citation_multiset(text):
    return multiset(re.sub(r"\s+", "", normalize(t)) for t in CITATION_RE.findall(text))


def figure_multiset(text):
    return multiset(re.sub(r"\s+", "", normalize(t)) for t in FIGURE_RE.findall(text))


def _is_cjk(marker):
    return any("\u4e00" <= ch <= "\u9fff" for ch in marker)


def hits(marker, low):
    """整词匹配英文标记，子串匹配中文标记。"""
    if _is_cjk(marker):
        return low.count(marker)
    pattern = r"(?<![a-z0-9])" + re.escape(marker) + r"(?![a-z0-9])"
    return len(re.findall(pattern, low))


def hedge_levels(text):
    low = normalize(text)
    levels = set()
    for level, markers in HEDGE_LEVELS.items():
        for marker in markers:
            if hits(marker, low):
                levels.add(level)
                break
    return levels


def negation_count(text):
    low = normalize(text)
    return sum(hits(marker, low) for marker in NEGATION)


def has_marker(markers, text):
    low = normalize(text)
    return any(hits(marker, low) for marker in markers)


# ---------------------------------------------------------------- 守卫

def guard_pair(edit, findings):
    where = edit.get("sent_id") or edit.get("location") or "?"
    original = edit.get("original") or ""
    revised = edit.get("revised") or ""
    if original == revised or not isinstance(original, str) or not isinstance(revised, str):
        return

    miss, add = diff_multiset(number_multiset(original), number_multiset(revised))
    if miss or add:
        findings.append(Finding("number-changed", where, f"数字/单位丢失={miss} 新增={add}"))

    miss, add = diff_multiset(citation_multiset(original), citation_multiset(revised))
    if miss or add:
        findings.append(Finding("citation-changed", where, f"引用丢失={miss} 新增={add}"))

    miss, add = diff_multiset(figure_multiset(original), figure_multiset(revised))
    if miss or add:
        findings.append(Finding("figure-ref-changed", where, f"图表/章节指向丢失={miss} 新增={add}"))

    lv_o, lv_r = hedge_levels(original), hedge_levels(revised)
    if lv_o != lv_r:
        direction = "加强" if max(lv_r or {0}) > max(lv_o or {0}) else "削弱"
        findings.append(Finding("hedge-strength-changed", where,
                                f"限定强度 {sorted(lv_o)} -> {sorted(lv_r)}（{direction}）"))

    n_o, n_r = negation_count(original), negation_count(revised)
    if n_o != n_r:
        findings.append(Finding("negation-scope-changed", where, f"否定/限定词数量 {n_o} -> {n_r}"))

    if has_marker(ASSOC_WEAK, original) and has_marker(CAUSAL_STRONG, revised):
        findings.append(Finding("causal-escalation", where, "原文为相关性表述，改后出现因果表述"))
    if (has_marker(CAUSAL_STRONG, original) and has_marker(ASSOC_WEAK, revised)
            and not has_marker(CAUSAL_STRONG, revised)):
        findings.append(Finding("causal-weakening", where, "原文为因果表述，改后降级为相关性"))


def guard_global(source, polished, findings):
    for builder, code, label in (
        (number_multiset, "number-dropped", "数字/单位"),
        (citation_multiset, "citation-dropped", "引用编号"),
        (figure_multiset, "figure-ref-dropped", "图表/章节指向"),
    ):
        missing, _ = diff_multiset(builder(source), builder(polished))
        for token, count in sorted(missing.items()):
            findings.append(Finding(code, "polished_text",
                                    f"原文{label} {token!r} 出现 {count} 次，润色后不足"))


def guard_contract(case, result, findings):
    def fail(message):
        findings.append(Finding("contract", "result.json", message))

    if not isinstance(result, dict):
        fail("result.json 顶层不是对象")
        return

    case_id = case.get("case_id")
    if case_id is not None and result.get("case_id") != case_id:
        fail(f"case_id 不一致：期望 {case_id!r}，实际 {result.get('case_id')!r}")

    status = result.get("status")
    if status not in VALID_STATUS:
        fail(f"status 非法：{status!r}，应为 {list(VALID_STATUS)}")
    if status in ("partial", "insufficient_material") and not result.get("status_reason"):
        fail("status 非 success 时必须给出 status_reason")

    contract = case.get("output_contract") or {}
    keys = set(contract.keys()) if isinstance(contract, dict) else set()
    missing = sorted(k for k in keys if k not in result)
    if missing:
        fail(f"output_contract 缺少键：{missing}")

    for field in ("polished_text", "edits", "terminology", "evidence", "uncertainty"):
        if field not in result:
            fail(f"缺少字段 {field}")

    edits = result.get("edits")
    if not isinstance(edits, list):
        fail("edits 必须是数组")
    else:
        for index, edit in enumerate(edits):
            if not isinstance(edit, dict):
                fail(f"edits[{index}] 不是对象")
                continue
            for field in REQUIRED_EDIT_FIELDS:
                if field not in edit:
                    fail(f"edits[{index}] 缺少字段 {field}")
            guards = edit.get("guards") or {}
            for name in REQUIRED_GUARDS:
                if not isinstance(guards.get(name), bool):
                    fail(f"edits[{index}].guards.{name} 缺失或不是布尔值")

    evidence = result.get("evidence")
    if not isinstance(evidence, dict):
        fail("evidence 必须是对象")
    else:
        for key in ("numbers", "citations", "figures"):
            if key not in evidence:
                fail(f"evidence 缺少 {key}")

    if not isinstance(result.get("terminology"), list):
        fail("terminology 必须是数组")
    if not isinstance(result.get("uncertainty"), list):
        fail("uncertainty 必须是数组")


# ---------------------------------------------------------------- 主流程

def read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        print(f"ERROR: 文件不存在: {path}", file=sys.stderr)
        sys.exit(4)
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON 解析失败: {path}: {exc}", file=sys.stderr)
        sys.exit(4)


def find_source_text(case, source_path):
    if source_path:
        try:
            with open(source_path, encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            print(f"ERROR: 无法读取正文: {exc}", file=sys.stderr)
            sys.exit(4)
    for key in ("text", "manuscript", "source_text", "content", "original_text"):
        value = case.get(key)
        if isinstance(value, str) and value.strip():
            return value
    print("ERROR: case.json 里找不到正文；请用 --source 指定正文文件", file=sys.stderr)
    sys.exit(4)


def main():
    parser = argparse.ArgumentParser(description="最小编辑/语义保持校验器")
    parser.add_argument("--case", required=True, help="输入 case.json")
    parser.add_argument("--result", required=True, help="输出 result.json")
    parser.add_argument("--source", help="正文文件（case.json 里没有正文时使用）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    args = parser.parse_args()

    case = read_json(args.case)
    result = read_json(args.result)
    if not isinstance(case, dict):
        print("ERROR: case.json 顶层不是对象", file=sys.stderr)
        sys.exit(4)

    source = find_source_text(case, args.source)
    findings = []

    edits = result.get("edits") if isinstance(result, dict) else None
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                guard_pair(edit, findings)

    polished = result.get("polished_text") if isinstance(result, dict) else None
    if isinstance(polished, str):
        guard_global(source, polished, findings)

    guard_contract(case, result, findings)

    contract_issues = [f for f in findings if f.code == "contract"]
    guard_issues = [f for f in findings if f.code != "contract"]

    report = {
        "case_id": case.get("case_id"),
        "status": result.get("status") if isinstance(result, dict) else None,
        "edits_checked": len(edits) if isinstance(edits, list) else 0,
        "contract_issues": [str(f) for f in contract_issues],
        "guard_issues": [str(f) for f in guard_issues],
        "passed": not findings,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"case_id: {report['case_id']}  status: {report['status']}  edits: {report['edits_checked']}")
        if not findings:
            print("PASS: 守恒守卫与输出契约全部通过")
        else:
            for finding in findings:
                print("FAIL " + str(finding))
            print(f"共 {len(findings)} 条问题（契约 {len(contract_issues)} / 守卫 {len(guard_issues)}）")

    if contract_issues:
        sys.exit(3)
    if guard_issues:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
