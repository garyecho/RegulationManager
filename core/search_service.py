"""
搜索服务
"""
from sqlalchemy import select

from database import get_session
from database.crud import DocumentCRUD
from database.models import Document
from models import SearchFilter, SearchResult
from utils.search_engine import search_fts
from core.document_service import _to_dto


def search(f: SearchFilter) -> SearchResult:
    # 先尝试 FTS5
    try:
        doc_ids, total, total_pages = search_fts(
            f.keyword, page=f.page, page_size=f.page_size
        )
    except Exception:
        doc_ids = []

    if doc_ids:
        with get_session() as session:
            stmt = select(Document).where(Document.id.in_(doc_ids))
            docs = session.execute(stmt).scalars().all()
            id_map = {d.id: d for d in docs}
            ordered = [id_map[i] for i in doc_ids if i in id_map]
            return SearchResult(
                documents=[_to_dto(d) for d in ordered],
                total=total, page=f.page, total_pages=total_pages,
            )

    # 降级到模糊搜索
    with get_session() as session:
        docs, total, total_pages = DocumentCRUD.get_list(
            session, category_id=f.category_id,
            page=f.page, page_size=f.page_size,
            keyword=f.keyword,
        )
        return SearchResult(
            documents=[_to_dto(d) for d in docs],
            total=total, page=f.page, total_pages=total_pages,
        )
