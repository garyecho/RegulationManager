"""
数据库初始化 + FTS5
"""
import logging
from sqlalchemy import text
from database import engine
from database.models import Base

logger = logging.getLogger(__name__)


def init_database():
    """创建表结构 + FTS5 虚拟表"""
    Base.metadata.create_all(engine)

    from database import get_session
    with get_session() as session:
        # 修复旧数据：NOT NULL 字段为 NULL 的记录设默认值
        session.execute(text(
            "UPDATE documents SET file_size = 0 WHERE file_size IS NULL"
        ))
        session.execute(text(
            "UPDATE documents SET created_by = 'admin' WHERE created_by IS NULL"
        ))

        # FTS5 全文搜索虚拟表（安全创建，损坏时自动清理重建）
        try:
            # 先清理可能损坏的 FTS 表和触发器
            for trig in ["documents_ai", "documents_ad", "documents_au"]:
                session.execute(text(f"DROP TRIGGER IF EXISTS {trig}"))
            for tbl in ["documents_fts", "documents_fts_data", "documents_fts_idx",
                        "documents_fts_docsize", "documents_fts_config"]:
                session.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
            # 同时清理旧版 fts_documents 表
            for tbl in ["fts_documents", "fts_documents_data", "fts_documents_idx",
                        "fts_documents_docsize", "fts_documents_config"]:
                session.execute(text(f"DROP TABLE IF EXISTS {tbl}"))

            # 重新创建 FTS5
            session.execute(text("""
                CREATE VIRTUAL TABLE documents_fts
                USING fts5(title, doc_no, department, issuing_org, description,
                           content='documents', content_rowid='id')
            """))

            # 重建 FTS 索引（从现有 documents 表填充）
            session.execute(text("""
                INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description)
                SELECT id, title, doc_no, department, issuing_org, description
                FROM documents WHERE is_deleted = 0
            """))

            # 触发器
            session.execute(text("""
                CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description)
                    VALUES (new.id, new.title, new.doc_no, new.department, new.issuing_org, new.description);
                END
            """))
            session.execute(text("""
                CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, doc_no, department, issuing_org, description)
                    VALUES ('delete', old.id, old.title, old.doc_no, old.department, old.issuing_org, old.description);
                END
            """))
            session.execute(text("""
                CREATE TRIGGER documents_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, doc_no, department, issuing_org, description)
                    VALUES ('delete', old.id, old.title, old.doc_no, old.department, old.issuing_org, old.description);
                    INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description)
                    VALUES (new.id, new.title, new.doc_no, new.department, new.issuing_org, new.description);
                END
            """))
            logger.info("FTS5 全文搜索索引已重建")
        except Exception as e:
            logger.warning(f"FTS5 不可用（全文搜索禁用）: {e}")

        # 清理废弃的默认分类（一次性，删除后此段不再触发）
        from database.crud import CategoryCRUD
        from database.models import Category
        obsolete = ["法律法规", "监管制度", "内部规章", "操作规程", "指导意见"]
        for name in obsolete:
            cat = session.query(Category).filter(Category.name == name).first()
            if cat:
                # 将该分类下的文档归入未分类
                session.execute(
                    text("UPDATE documents SET category_id = NULL WHERE category_id = :cid"),
                    {"cid": cat.id}
                )
                session.delete(cat)
                logger.info(f"已清理废弃分类：{name}")

    logger.info("数据库初始化完成")
