"""
搜索服务
"""
from database import get_session
from database.crud import DocumentCRUD
from models import SearchFilter, SearchResult, DocumentData
from utils.search_engine import search_fts


def _to_dto(doc) -> DocumentData:
    tag_names = []
    if doc.tag_associations:
        tag_names = [assoc.tag.name for assoc in doc.tag_associations if assoc.tag]

    return DocumentData(
        id=doc.id, title=doc.title, doc_no=doc.doc_no,
        version_no=doc.version_no, category_id=doc.category_id,
        category_name=doc.category.name if doc.category else "",
        status=doc.status, issuing_org=doc.issuing_org or "",
        department=doc.department or "",
        effective_date=doc.effective_date or "",
        expiry_date=doc.expiry_date or "",
        description=doc.description or "",
        file_path=doc.file_path or "", original_name=doc.original_name or "",
        file_type=doc.file_type or "",
        file_size=doc.file_size if doc.file_size else 0,
        tags=tag_names,
        created_at=str(doc.created_at), updated_at=str(doc.updated_at),
    )


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
            from sqlalchemy import select
            from database.models import Document
            stmt = select(Document).where(Document.id.in_(doc_ids))
            docs = session.execute(stmt).scalars().all()
            # 保持 FTS 排序
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
