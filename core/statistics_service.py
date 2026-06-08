"""
统计服务
"""
from sqlalchemy import func

from database import get_session
from database.crud import DocumentCRUD, CategoryCRUD
from database.models import Document


def get_summary() -> dict:
    """获取统计数据"""
    with get_session() as session:
        total_docs = DocumentCRUD.count(session)
        total_cats = len(CategoryCRUD.get_all(session))

        # 一次 GROUP BY 查询替代5次单独查询
        rows = session.query(
            Document.status, func.count(Document.id)
        ).filter(Document.is_deleted == False).group_by(Document.status).all()
        status_counts = {status: count for status, count in rows}

        deleted = session.query(func.count(Document.id)).filter(
            Document.is_deleted == True
        ).scalar() or 0

        return {
            "total_docs": total_docs,
            "total_categories": total_cats,
            "active_count": status_counts.get("active", 0),
            "archived_count": status_counts.get("archived", 0),
            "superseded_count": status_counts.get("superseded", 0),
            "expired_count": status_counts.get("expired", 0),
            "deleted_count": deleted,
        }
