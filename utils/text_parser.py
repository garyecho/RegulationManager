"""
文本解析工具 — 智能文号提取
"""
import re
from typing import Optional, Tuple


# ── 文号正则模式（按匹配优先级排列）──

# 模式A：带年份+序号的标准文号，如 银保监发〔2021〕17号、国办发〔2020〕1号
_RE_DOC_NO_STANDARD = re.compile(
    r"(?:银保监办?发|银监发|银监会|国办发|国务院|中国人民银行|证监会|保监会|财政部|发改委)"
    r"[〔\[（(]\d{4}[〕\]）)]\s*\d+\s*号"
)

# 模式B：通用文号 — 机构名+年份括号+序号+号
_RE_DOC_NO_GENERAL = re.compile(
    r"[\u4e00-\u9fff]{2,20}"           # 机构名（2-20个汉字）
    r"[〔\[（(]"                         # 左括号
    r"\d{4}"                             # 年份
    r"[〕\]）)]"                         # 右括号
    r"\s*\d+\s*号"                       # 序号+号
)

# 模式C：带"令"格式，如 中国银行保险监督管理委员会令2022年第1号
_RE_DOC_NO_LING = re.compile(
    r"[\u4e00-\u9fff]{2,20}令\s*\d{4}\s*年\s*第\s*\d+\s*号"
)

# 模式D：括号内年份+序号，如 （2021）17号、〔2020〕1号
_RE_DOC_NO_BRACKET = re.compile(
    r"[〔\[（(]\d{4}[〕\]）)]\s*\d+\s*号"
)


def extract_doc_no(text: str) -> str:
    """
    从标题或文件名中智能提取文号。

    优先级：
      1. 「——」「—」「-」分隔符后面的内容
      2. 标准文号正则（已知机构前缀）
      3. 通用文号正则
      4. "令"格式文号
      5. 括号年份+序号
    """
    if not text or not text.strip():
        return ""

    text = text.strip()

    # ── 规则1：「——」「—」「-」分隔符 ──
    # 按优先级匹配：—— > — > -
    separator = None
    for sep in ("——", "—", "-"):
        if sep in text:
            separator = sep
            break
    if separator:
        # 取最后一个分隔符后面的内容（避免标题本身含分隔符的情况）
        idx = text.rfind(separator)
        candidate = text[idx + len(separator):].strip()
        # 去掉文件扩展名
        candidate = re.sub(r"\.\w+$", "", candidate).strip()
        # 如果分隔符后面的内容看起来像文号（包含数字和"号"，或包含括号年份）
        if candidate and (
            "号" in candidate
            or re.search(r"\d{4}", candidate)
            or len(candidate) <= 40  # 文号一般不会太长
        ):
            return candidate

    # ── 规则2：标准文号（已知机构前缀）──
    m = _RE_DOC_NO_STANDARD.search(text)
    if m:
        return m.group().strip()

    # ── 规则3：通用文号 ──
    m = _RE_DOC_NO_GENERAL.search(text)
    if m:
        return m.group().strip()

    # ── 规则4："令"格式 ──
    m = _RE_DOC_NO_LING.search(text)
    if m:
        return m.group().strip()

    # ── 规则5：括号年份+序号 ──
    m = _RE_DOC_NO_BRACKET.search(text)
    if m:
        return m.group().strip()

    return ""


def extract_title_and_doc_no(text: str) -> Tuple[str, str]:
    """
    同时提取标题和文号。
    返回 (title, doc_no)
    """
    doc_no = extract_doc_no(text)

    # 从原标题中去掉文号部分，得到干净的标题
    title = text.strip()
    if doc_no:
        # 去掉「——文号」「—文号」「-文号」部分（按优先级尝试）
        stripped = False
        for sep in ("——", "—", "-"):
            if sep in title:
                idx = title.rfind(sep)
                candidate_after = title[idx + len(sep):].strip()
                candidate_after = re.sub(r"\.\w+$", "", candidate_after).strip()
                if candidate_after == doc_no:
                    title = title[:idx].strip()
                    stripped = True
                    break
        if not stripped:
            # 直接去掉文号字符串
            title = title.replace(doc_no, "").strip()

    # 去掉文件扩展名
    title = re.sub(r"\.\w+$", "", title).strip()

    return title or text.strip(), doc_no


def detect_status_from_name(text: str) -> str:
    """
    从标题或文件名中检测文档状态。
    如果包含"已废止"/"废止"/"失效"关键词，返回 "expired"。
    否则返回 ""（由调用方决定默认值）。
    """
    if not text:
        return ""
    keywords = ("已废止", "废止", "失效")
    for kw in keywords:
        if kw in text:
            return "expired"
    return ""


# ── 兼容旧接口 ──

def parse_doc_filename(name: str) -> tuple:
    """从文件名解析标题和文号（兼容旧调用）"""
    from pathlib import Path
    stem = Path(name).stem
    return extract_title_and_doc_no(stem)
