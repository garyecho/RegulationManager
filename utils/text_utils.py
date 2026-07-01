"""
文本工具函数 — 高亮、摘要等
"""
import re


def highlight_text(text: str, keyword: str) -> str:
    """将关键词用黄色背景高亮显示（HTML格式）"""
    if not keyword or not text:
        return text
    # 转义 HTML 特殊字符
    escaped_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped_kw = keyword.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 替换关键词为黄色背景高亮标签
    pattern = re.compile(re.escape(escaped_kw), re.IGNORECASE)
    highlighted = pattern.sub(
        f'<span style="background-color:#FFEB3B;color:#333;padding:1px 3px;border-radius:2px">{escaped_kw}</span>',
        escaped_text
    )
    return highlighted
