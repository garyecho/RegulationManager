"""
搜索服务
"""
from sqlalchemy import select

from database import get_session
from database.crud import DocumentCRUD
from database.models import Document
from models import SearchFilter, SearchResult
from utils.search_engine import search_fts, extract_snippet
from core.document_service import _to_dto


def _build_results(docs, keyword: str):
    """按文档列表组装 DTO，附带搜索摘要"""
    results = []
    for doc in docs:
        dto = _to_dto(doc)
        if keyword:
            snippet = extract_snippet(doc.content_text or "", keyword)
            if not snippet:
                snippet = extract_snippet(doc.title or "", keyword)
            dto.snippet = snippet
        results.append(dto)
    return results


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
            stmt = select(Document).where(
                Document.id.in_(doc_ids),
                Document.is_deleted == False
            )
            docs = session.execute(stmt).scalars().all()
            id_map = {d.id: d for d in docs}
            ordered = [id_map[i] for i in doc_ids if i in id_map]

            return SearchResult(
                documents=_build_results(ordered, f.keyword),
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
            documents=_build_results(docs, f.keyword),
            total=total, page=f.page, total_pages=total_pages,
        )
