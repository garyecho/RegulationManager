"""
文档服务
"""
import os
from pathlib import Path
import shutil
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import text as sql_text

import config
from database import get_session
from database.crud import DocumentCRUD
from models import DocumentData, SearchResult
from utils import file_hash

logger = logging.getLogger(__name__)


def _resolve_path(file_path: str) -> str:
    """将数据库中的路径解析为绝对路径（兼容旧的绝对路径和新的相对路径）"""
    if not file_path:
        return ""
    p = Path(file_path)
    if p.is_absolute():
        return file_path  # 旧数据：已经是绝对路径
    # 新数据：相对路径，基于 DATA_DIR 解析
    resolved = config.DATA_DIR / file_path
    return str(resolved)


def _to_dto(doc) -> DocumentData:
    """ORM Document -> DocumentData DTO"""
    tag_names = [assoc.tag.name for assoc in doc.tag_associations if assoc.tag]         if doc.tag_associations else []

    return DocumentData(
        id=doc.id,
        title=doc.title,
        doc_no=doc.doc_no,
        version_no=doc.version_no,
        category_id=doc.category_id,
        category_name=doc.category.name if doc.category else "",
        status=doc.status,
        issuing_org=doc.issuing_org or "",
        department=doc.department or "",
        effective_date=doc.effective_date or "",
        expiry_date=doc.expiry_date or "",
        description=doc.description or "",
        file_path=_resolve_path(doc.file_path),
        original_name=doc.original_name or "",
        file_type=doc.file_type or "",
        file_size=doc.file_size or 0,
        thumbnail_path=doc.thumbnail_path or "",
        content_text=doc.content_text or "",
        tags_text=doc.tags_text or "",
        created_by=doc.created_by or "admin",
        tags=tag_names,
        created_at=str(doc.created_at),
        updated_at=str(doc.updated_at),
    )


def _now_str() -> str:
    """当前时间戳字符串（用于 raw SQL 更新）"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def _disable_fts_triggers(session):
    """临时禁用 FTS 触发器，防止 raw SQL 操作触发 FTS 写入异常"""
    for trig in ("documents_au", "documents_ai", "documents_ad"):
        session.execute(sql_text(f"DROP TRIGGER IF EXISTS {trig}"))


def _delete_file(path: str):
    """安全删除物理文件"""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError as e:
            logger.warning(f"删除文件失败 {path}: {e}")


def _batch_toggle_deleted(doc_ids: List[int], deleted: bool) -> dict:
    """批量软删除/还原的统一实现"""
    success, failed = 0, 0
    now = _now_str()
    with get_session() as session:
        _disable_fts_triggers(session)
        for doc_id in doc_ids:
            try:
                result = session.execute(
                    sql_text("UPDATE documents SET is_deleted=:val, updated_at=:now "
                             "WHERE id=:id AND is_deleted=:old"),
                    {"val": int(deleted), "now": now, "id": doc_id, "old": int(not deleted)}
                )
                if result.rowcount > 0:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"批量操作失败 doc_id={doc_id}: {e}")
                failed += 1
    return {"success": success, "failed": failed}


# ── 查询 ──────────────────────────────────────────────────

def get_document_list(category_id: int = None, page: int = 1,
                      page_size: int = config.DEFAULT_PAGE_SIZE) -> SearchResult:
    with get_session() as session:
        docs, total, total_pages = DocumentCRUD.get_list(
            session, category_id=category_id, page=page, page_size=page_size
        )
        return SearchResult(
            documents=[_to_dto(d) for d in docs],
            total=total, page=page, total_pages=total_pages,
        )


def get_document(doc_id: int) -> Optional[DocumentData]:
    with get_session() as session:
        doc = DocumentCRUD.get_by_id(session, doc_id)
        return _to_dto(doc) if doc else None


def get_deleted_documents(page: int = 1,
                          page_size: int = config.DEFAULT_PAGE_SIZE) -> SearchResult:
    """获取已删除的文档（回收站）"""
    from database.models import Document
    with get_session() as session:
        q = session.query(Document).filter(Document.is_deleted == True)
        total = q.count()
        docs = q.order_by(Document.updated_at.desc()) \
                .offset((page - 1) * page_size) \
                .limit(page_size).all()
        total_pages = max(1, (total + page_size - 1) // page_size)
        return SearchResult(
            documents=[_to_dto(d) for d in docs],
            total=total, page=page, total_pages=total_pages,
        )


# ── 创建/上传 ─────────────────────────────────────────────

def upload_document(file_path: str, title: str, doc_no: str = "",
                    category_id: int = None, department: str = "",
                    issuing_org: str = "", effective_date: str = "",
                    description: str = "", tags: list = None,
                    status: str = None) -> Optional[DocumentData]:
    if not file_path or not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return None

    h = file_hash(file_path)
    dest_name = f"{h[:12]}_{os.path.basename(file_path)}"
    dest = config.DOCUMENTS_DIR / dest_name
    shutil.copy2(file_path, dest)

    # 自动识别状态：优先使用传入的 status，否则从标题+文件名检测
    if not status:
        from utils.text_parser import detect_status_from_name
        fname = os.path.splitext(os.path.basename(file_path))[0]
        status = detect_status_from_name(title) or detect_status_from_name(fname) or "active"

    # 提取文档正文
    from utils.text_extractor import extract_text
    content_text = extract_text(str(dest))

    # 存储相对路径（相对于 DATA_DIR），方便打包分发后在其他电脑上使用
    try:
        relative_path = str(dest.relative_to(config.DATA_DIR))
    except ValueError:
        relative_path = str(dest)

    with get_session() as session:
        doc = DocumentCRUD.create(
            session,
            title=title, doc_no=doc_no, category_id=category_id,
            department=department, issuing_org=issuing_org,
            effective_date=effective_date, description=description,
            file_path=relative_path, original_name=os.path.basename(file_path),
            file_type=ext.lstrip("."), file_hash=h,
            file_size=os.path.getsize(dest), created_by="admin",
            tags=tags or [], status=status,
            content_text=content_text,
        )
        return _to_dto(doc)


def batch_upload(file_paths: list, category_id: int = None) -> dict:
    from utils.text_parser import extract_title_and_doc_no, detect_status_from_name
    result = {"success": 0, "failed": 0, "skipped": 0}
    for fp in file_paths:
        try:
            stem = os.path.splitext(os.path.basename(fp))[0]
            title, doc_no = extract_title_and_doc_no(stem)
            detected_status = detect_status_from_name(title) or detect_status_from_name(stem)
            r = upload_document(fp, title=title, doc_no=doc_no,
                                category_id=category_id, status=detected_status or None)
            result["success" if r else "skipped"] += 1
        except Exception as e:
            logger.error(f"导入失败 {fp}: {e}")
            result["failed"] += 1
    return result


def update_document(doc_id: int, **kwargs) -> Optional[DocumentData]:
    """更新文档元数据（分类、状态、标题等），不修改文件"""
    with get_session() as session:
        doc = DocumentCRUD.update(session, doc_id, **kwargs)
        if not doc:
            return None
        return _to_dto(doc)


# ── 删除/恢复 ──────────────────────────────────────────────

def delete_document(doc_id: int) -> bool:
    """软删除文档（移入回收站）"""
    now = _now_str()
    with get_session() as session:
        _disable_fts_triggers(session)
        result = session.execute(
            sql_text("UPDATE documents SET is_deleted=1, updated_at=:now "
                     "WHERE id=:id AND is_deleted=0"),
            {"now": now, "id": doc_id}
        )
        return result.rowcount > 0


def restore_document(doc_id: int) -> bool:
    """从回收站恢复文档"""
    now = _now_str()
    with get_session() as session:
        _disable_fts_triggers(session)
        result = session.execute(
            sql_text("UPDATE documents SET is_deleted=0, updated_at=:now "
                     "WHERE id=:id AND is_deleted=1"),
            {"now": now, "id": doc_id}
        )
        return result.rowcount > 0


def permanent_delete(doc_id: int) -> bool:
    """永久删除文档"""
    with get_session() as session:
        _disable_fts_triggers(session)
        row = session.execute(
            sql_text("SELECT file_path FROM documents WHERE id=:id"), {"id": doc_id}
        ).fetchone()
        if not row:
            return False
        _delete_file(row[0])
        session.execute(sql_text("DELETE FROM documents WHERE id=:id"), {"id": doc_id})
        return True


# ── 批量操作 ──────────────────────────────────────────────

def batch_delete(doc_ids: List[int]) -> dict:
    """批量软删除（移入回收站）"""
    return _batch_toggle_deleted(doc_ids, deleted=True)


def batch_restore(doc_ids: List[int]) -> dict:
    """批量还原"""
    return _batch_toggle_deleted(doc_ids, deleted=False)


def batch_permanent_delete(doc_ids: List[int]) -> dict:
    """批量永久删除"""
    success, failed = 0, 0
    with get_session() as session:
        _disable_fts_triggers(session)
        for doc_id in doc_ids:
            try:
                row = session.execute(
                    sql_text("SELECT file_path FROM documents WHERE id=:id"), {"id": doc_id}
                ).fetchone()
                if row:
                    _delete_file(row[0])
                    session.execute(sql_text("DELETE FROM documents WHERE id=:id"), {"id": doc_id})
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"批量永久删除失败 doc_id={doc_id}: {e}")
                failed += 1
    return {"success": success, "failed": failed}
