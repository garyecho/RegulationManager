"""
CRUD 操作
"""
from typing import Optional, List
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database.models import Document, Category, DocumentTag, Tag


class CategoryCRUD:
    @staticmethod
    def get_all(session: Session) -> List[Category]:
        return session.query(Category).order_by(Category.sort_order, Category.id).all()

    @staticmethod
    def get_by_id(session: Session, cat_id: int) -> Optional[Category]:
        return session.query(Category).filter(Category.id == cat_id).first()

    @staticmethod
    def create(session: Session, name: str, parent_id: int = None) -> Category:
        cat = Category(name=name, parent_id=parent_id)
        session.add(cat)
        session.flush()
        return cat

    @staticmethod
    def exists(session: Session, name: str) -> bool:
        return session.query(Category).filter(Category.name == name).first() is not None

    @staticmethod
    def delete(session: Session, cat_id: int) -> dict:
        """删除分类，返回 {success, doc_count}，文档归入未分类"""
        cat = session.query(Category).filter(Category.id == cat_id).first()
        if not cat:
            return {"success": False, "doc_count": 0}
        # 统计该分类下的文档数
        doc_count = session.query(Document).filter(
            Document.category_id == cat_id, Document.is_deleted == False
        ).count()
        # 文档归入未分类
        session.execute(
            text("UPDATE documents SET category_id = NULL WHERE category_id = :cid"),
            {"cid": cat_id}
        )
        session.delete(cat)
        session.flush()
        return {"success": True, "doc_count": doc_count}


class TagCRUD:
    @staticmethod
    def get_or_create(session: Session, name: str, color: str = "#2d5aa0") -> Tag:
        tag = session.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name, color=color)
            session.add(tag)
            session.flush()
        return tag


class DocumentCRUD:
    @staticmethod
    def get_list(session: Session, category_id: int = None,
                 page: int = 1, page_size: int = 20,
                 keyword: str = None) -> tuple:
        q = session.query(Document).filter(Document.is_deleted == False)

        if category_id is not None:
            q = q.filter(Document.category_id == category_id)

        if keyword:
            # 转义 LIKE 通配符
            escaped = keyword.replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            q = q.filter(
                (Document.title.like(pattern, escape='\\')) |
                (Document.doc_no.like(pattern, escape='\\')) |
                (Document.department.like(pattern, escape='\\')) |
                (Document.issuing_org.like(pattern, escape='\\'))
            )

        total = q.count()
        docs = q.order_by(Document.updated_at.desc()) \
                .offset((page - 1) * page_size) \
                .limit(page_size).all()
        total_pages = max(1, (total + page_size - 1) // page_size)
        return docs, total, total_pages

    @staticmethod
    def get_by_id(session: Session, doc_id: int) -> Optional[Document]:
        return session.query(Document).filter(
            Document.id == doc_id, Document.is_deleted == False
        ).first()

    @staticmethod
    def create(session: Session, **kwargs) -> Document:
        tags = kwargs.pop("tags", [])
        doc = Document(**kwargs)
        session.add(doc)
        session.flush()

        # 处理标签关联
        for tag_name in tags:
            if not tag_name or not tag_name.strip():
                continue
            tag_obj = TagCRUD.get_or_create(session, tag_name.strip())
            tag_obj.usage_count += 1
            session.add(DocumentTag(document_id=doc.id, tag_id=tag_obj.id))

        session.flush()
        return doc

    @staticmethod
    def update(session: Session, doc_id: int, **kwargs) -> Optional[Document]:
        tags = kwargs.pop("tags", None)
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return None
        for k, v in kwargs.items():
            if hasattr(doc, k):
                setattr(doc, k, v)
        if tags is not None:
            # 删除旧关联
            old_assocs = session.query(DocumentTag).filter(
                DocumentTag.document_id == doc_id
            ).all()
            for assoc in old_assocs:
                session.delete(assoc)
            # 创建新关联
            for tag_name in tags:
                if not tag_name or not tag_name.strip():
                    continue
                tag_obj = TagCRUD.get_or_create(session, tag_name.strip())
                tag_obj.usage_count += 1
                session.add(DocumentTag(document_id=doc_id, tag_id=tag_obj.id))
        session.flush()
        return doc

    @staticmethod
    def count(session: Session) -> int:
        return session.query(Document).filter(Document.is_deleted == False).count()

    @staticmethod
    def count_by_category(session: Session) -> dict:
        rows = session.query(
            Document.category_id, func.count(Document.id)
        ).filter(Document.is_deleted == False).group_by(Document.category_id).all()
        return {r[0]: r[1] for r in rows}
