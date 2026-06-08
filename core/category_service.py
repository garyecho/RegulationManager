"""
分类服务
"""
from typing import List, Optional
from database import get_session
from database.crud import CategoryCRUD, DocumentCRUD
from models import CategoryData


def _to_dto(cat, doc_counts: dict) -> CategoryData:
    dto = CategoryData(
        id=cat.id,
        name=cat.name,
        parent_id=cat.parent_id,
        doc_count=doc_counts.get(cat.id, 0),
    )
    if cat.children:
        dto.children = [_to_dto(c, doc_counts) for c in cat.children]
    return dto


def get_category_tree() -> List[CategoryData]:
    with get_session() as session:
        cats = CategoryCRUD.get_all(session)
        doc_counts = DocumentCRUD.count_by_category(session)
        # 只取顶级（无 parent）
        top = [c for c in cats if c.parent_id is None]
        return [_to_dto(c, doc_counts) for c in top]


def get_all_categories() -> List[CategoryData]:
    with get_session() as session:
        cats = CategoryCRUD.get_all(session)
        doc_counts = DocumentCRUD.count_by_category(session)
        return [_to_dto(c, doc_counts) for c in cats]


def add_category(name: str) -> Optional[CategoryData]:
    with get_session() as session:
        if CategoryCRUD.exists(session, name):
            return None
        cat = CategoryCRUD.create(session, name)
        return CategoryData(id=cat.id, name=cat.name)


def delete_category(cat_id: int) -> dict:
    """
    删除分类，返回 {success, doc_count, cat_name}
    文档归入未分类（category_id=NULL）
    """
    with get_session() as session:
        cat = CategoryCRUD.get_by_id(session, cat_id)
        if not cat:
            return {"success": False, "doc_count": 0, "cat_name": ""}
        cat_name = cat.name
        result = CategoryCRUD.delete(session, cat_id)
        result["cat_name"] = cat_name
        return result
