"""
文档正文提取 — 从 PDF / DOCX 文件中提取纯文本
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 提取文本（PyMuPDF）"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"PDF 文本提取失败 {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """从 DOCX 提取文本（python-docx）"""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        # 也提取表格中的文字
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text.strip())
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"DOCX 文本提取失败 {file_path}: {e}")
        return ""


def extract_text(file_path: str) -> str:
    """根据文件类型自动提取文本"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    return ""
