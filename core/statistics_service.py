"""
统计服务
"""
from database import get_session
from database.crud import DocumentCRUD, CategoryCRUD
from database.models import Document
from sqlalchemy import func


def get_summary() -> dict:
    """获取统计数据"""
    with get_session() as session:
        total_docs = DocumentCRUD.count(session)
        total_cats = len(CategoryCRUD.get_all(session))

        # 按状态统计
        active = session.query(func.count(Document.id)).filter(
            Document.is_deleted == False, Document.status == "active"
        ).scalar() or 0
        archived = session.query(func.count(Document.id)).filter(
            Document.is_deleted == False, Document.status == "archived"
        ).scalar() or 0
        superseded = session.query(func.count(Document.id)).filter(
            Document.is_deleted == False, Document.status == "superseded"
        ).scalar() or 0
        expired = session.query(func.count(Document.id)).filter(
            Document.is_deleted == False, Document.status == "expired"
        ).scalar() or 0
        deleted = session.query(func.count(Document.id)).filter(
            Document.is_deleted == True
        ).scalar() or 0

        return {
            "total_docs": total_docs,
            "total_categories": total_cats,
            "active_count": active,
            "archived_count": archived,
            "superseded_count": superseded,
            "expired_count": expired,
            "deleted_count": deleted,
        }
