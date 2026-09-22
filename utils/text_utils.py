"""
文本工具函数 — 高亮、摘要等
"""
import html
import re


def escape_html(text: str) -> str:
    """HTML 转义（展示层统一入口：& < > " '）"""
    return html.escape(text or "", quote=True)


def highlight_text(text: str, keyword: str) -> str:
    """将关键词用黄色背景高亮显示（HTML格式）

    调用方无需再自行转义：函数内部先 escape 再嵌高亮标签，
    避免标题/摘要里的 <>& 破坏标签或被当成 HTML 执行。
    """
    if not keyword or not text:
        return escape_html(text)
    escaped_text = escape_html(text)
    escaped_kw = escape_html(keyword)
    # 替换关键词为黄色背景高亮标签
    pattern = re.compile(re.escape(escaped_kw), re.IGNORECASE)
    highlighted = pattern.sub(
        f'<span style="background-color:#FFEB3B;color:#333;padding:1px 3px;border-radius:2px">{escaped_kw}</span>',
        escaped_text
    )
    return highlighted
