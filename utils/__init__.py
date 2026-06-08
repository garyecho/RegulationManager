"""
工具函数
"""
import hashlib


def file_hash(path: str) -> str:
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_doc_filename(name: str) -> tuple:
    """从文件名解析标题和文号（委托给 text_parser）"""
    from utils.text_parser import extract_title_and_doc_no
    from pathlib import Path
    return extract_title_and_doc_no(Path(name).stem)
