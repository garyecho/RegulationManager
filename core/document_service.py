"""
文档服务
"""
import os
import shutil
import logging
from typing import Optional, List

import config
from database import get_session
from database.crud import DocumentCRUD
from models import DocumentData, SearchResult
from utils import file_hash

logger = logging.getLogger(__name__)


def _to_dto(doc) -> DocumentData:
    # 从关联的 tag 表获取标签名
    tag_names = []
    if doc.tag_associations:
        tag_names = [assoc.tag.name for assoc in doc.tag_associations if assoc.tag]

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
        file_path=doc.file_path or "",
        original_name=doc.original_name or "",
        file_type=doc.file_type or "",
        file_size=doc.file_size if doc.file_size else 0,
        thumbnail_path=doc.thumbnail_path or "",
        content_text=doc.content_text or "",
        tags_text=doc.tags_text or "",
        created_by=doc.created_by or "admin",
        tags=tag_names,
        created_at=str(doc.created_at),
        updated_at=str(doc.updated_at),
    )


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


def upload_document(file_path: str, title: str, doc_no: str = "",
                    category_id: int = None, department: str = "",
                    issuing_org: str = "", effective_date: str = "",
                    description: str = "", tags: list = None) -> Optional[DocumentData]:
    if not file_path or not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return None

    # 复制文件到文档目录
    h = file_hash(file_path)
    dest_name = f"{h[:12]}_{os.path.basename(file_path)}"
    dest = config.DOCUMENTS_DIR / dest_name
    shutil.copy2(file_path, dest)

    # 获取文件大小
    file_size = os.path.getsize(dest)

    with get_session() as session:
        doc = DocumentCRUD.create(
            session,
            title=title,
            doc_no=doc_no,
            category_id=category_id,
            department=department,
            issuing_org=issuing_org,
            effective_date=effective_date,
            description=description,
            file_path=str(dest),
            original_name=os.path.basename(file_path),
            file_type=ext.lstrip("."),
            file_hash=h,
            file_size=file_size,
            created_by="admin",
            tags=tags or [],
        )
        return _to_dto(doc)


def batch_upload(file_paths: list, category_id: int = None) -> dict:
    result = {"success": 0, "failed": 0, "skipped": 0}
    for fp in file_paths:
        try:
            from utils import parse_doc_filename
            title, doc_no = parse_doc_filename(os.path.basename(fp))
            r = upload_document(fp, title=title, doc_no=doc_no, category_id=category_id)
            if r:
                result["success"] += 1
            else:
                result["skipped"] += 1
        except Exception as e:
            logger.error(f"导入失败 {fp}: {e}")
            result["failed"] += 1
    return result


def get_deleted_documents(page: int = 1,
                          page_size: int = config.DEFAULT_PAGE_SIZE) -> SearchResult:
    """获取已删除的文档（回收站）"""
    with get_session() as session:
        from database.models import Document
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


def delete_document(doc_id: int) -> bool:
    """软删除文档（移入回收站）"""
    from sqlalchemy import text
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with get_session() as session:
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        result = session.execute(
            text("UPDATE documents SET is_deleted=1, updated_at=:now WHERE id=:id AND is_deleted=0"),
            {"now": now, "id": doc_id}
        )
        return result.rowcount > 0


def restore_document(doc_id: int) -> bool:
    """从回收站恢复文档"""
    from sqlalchemy import text
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with get_session() as session:
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        result = session.execute(
            text("UPDATE documents SET is_deleted=0, updated_at=:now WHERE id=:id AND is_deleted=1"),
            {"now": now, "id": doc_id}
        )
        return result.rowcount > 0


def permanent_delete(doc_id: int) -> bool:
    """永久删除文档"""
    from sqlalchemy import text
    with get_session() as session:
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        row = session.execute(
            text("SELECT file_path FROM documents WHERE id=:id"), {"id": doc_id}
        ).fetchone()
        if row:
            if row[0] and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                except OSError as e:
                    logger.warning(f"删除文件失败 {row[0]}: {e}")
            session.execute(text("DELETE FROM documents WHERE id=:id"), {"id": doc_id})
            return True
        return False


# ── 批量操作 ──────────────────────────────────────────────

def batch_delete(doc_ids: List[int]) -> dict:
    """批量软删除（移入回收站），用 raw SQL 绕过 FTS 触发器"""
    success, failed = 0, 0
    from sqlalchemy import text
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with get_session() as session:
        # 先禁用触发器，防止 FTS 写入
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        for doc_id in doc_ids:
            try:
                result = session.execute(
                    text("UPDATE documents SET is_deleted=1, updated_at=:now WHERE id=:id AND is_deleted=0"),
                    {"now": now, "id": doc_id}
                )
                if result.rowcount > 0:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"批量删除失败 doc_id={doc_id}: {e}")
                failed += 1
    return {"success": success, "failed": failed}


def batch_restore(doc_ids: List[int]) -> dict:
    """批量还原，用 raw SQL 绕过 FTS 触发器"""
    success, failed = 0, 0
    from sqlalchemy import text
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with get_session() as session:
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        for doc_id in doc_ids:
            try:
                result = session.execute(
                    text("UPDATE documents SET is_deleted=0, updated_at=:now WHERE id=:id AND is_deleted=1"),
                    {"now": now, "id": doc_id}
                )
                if result.rowcount > 0:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"批量还原失败 doc_id={doc_id}: {e}")
                failed += 1
    return {"success": success, "failed": failed}


def batch_permanent_delete(doc_ids: List[int]) -> dict:
    """批量永久删除，用 raw SQL"""
    success, failed = 0, 0
    from sqlalchemy import text
    with get_session() as session:
        session.execute(text("DROP TRIGGER IF EXISTS documents_au"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ai"))
        session.execute(text("DROP TRIGGER IF EXISTS documents_ad"))
        for doc_id in doc_ids:
            try:
                # 先获取文件路径
                row = session.execute(
                    text("SELECT file_path FROM documents WHERE id=:id"), {"id": doc_id}
                ).fetchone()
                if row:
                    if row[0] and os.path.exists(row[0]):
                        try:
                            os.remove(row[0])
                        except OSError as e:
                            logger.warning(f"删除文件失败 {row[0]}: {e}")
                    session.execute(text("DELETE FROM documents WHERE id=:id"), {"id": doc_id})
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"批量永久删除失败 doc_id={doc_id}: {e}")
                failed += 1
    return {"success": success, "failed": failed}
