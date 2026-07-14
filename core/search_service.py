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

            # 构建结果，附带搜索摘要
            results = []
            for doc in ordered:
                dto = _to_dto(doc)
                # 从正文或标题中提取搜索摘要
                if f.keyword:
                    snippet = extract_snippet(doc.content_text or "", f.keyword)
                    if not snippet:
                        snippet = extract_snippet(doc.title or "", f.keyword)
                    dto.snippet = snippet
                results.append(dto)

            return SearchResult(
                documents=results,
                total=total, page=f.page, total_pages=total_pages,
            )

    # 降级到模糊搜索
    with get_session() as session:
        docs, total, total_pages = DocumentCRUD.get_list(
            session, category_id=f.category_id,
            page=f.page, page_size=f.page_size,
            keyword=f.keyword,
        )
        # 降级搜索也附带摘要
        results = []
        for doc in docs:
            dto = _to_dto(doc)
            if f.keyword:
                snippet = extract_snippet(doc.content_text or "", f.keyword)
                if not snippet:
                    snippet = extract_snippet(doc.title or "", f.keyword)
                dto.snippet = snippet
            results.append(dto)

        return SearchResult(
            documents=results,
            total=total, page=f.page, total_pages=total_pages,
        )
