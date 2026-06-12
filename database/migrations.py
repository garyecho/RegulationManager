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

            # 重新创建 FTS5（包含 content_text 正文内容）
            session.execute(text("""
                CREATE VIRTUAL TABLE documents_fts
                USING fts5(title, doc_no, department, issuing_org, description, content_text,
                           content='documents', content_rowid='id')
            """))

            # 重建 FTS 索引（从现有 documents 表填充）
            session.execute(text("""
                INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
                SELECT id, title, doc_no, department, issuing_org, description, content_text
                FROM documents WHERE is_deleted = 0
            """))

            # 触发器
            session.execute(text("""
                CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
                    VALUES (new.id, new.title, new.doc_no, new.department, new.issuing_org, new.description, new.content_text);
                END
            """))
            session.execute(text("""
                CREATE TRIGGER documents_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, doc_no, department, issuing_org, description, content_text)
                    VALUES ('delete', old.id, old.title, old.doc_no, old.department, old.issuing_org, old.description, old.content_text);
                END
            """))
            session.execute(text("""
                CREATE TRIGGER documents_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, doc_no, department, issuing_org, description, content_text)
                    VALUES ('delete', old.id, old.title, old.doc_no, old.department, old.issuing_org, old.description, old.content_text);
                    INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
                    VALUES (new.id, new.title, new.doc_no, new.department, new.issuing_org, new.description, new.content_text);
                END
            """))
            logger.info("FTS5 全文搜索索引已重建")
        except Exception as e:
            logger.warning(f"FTS5 不可用（全文搜索禁用）: {e}")

        # 迁移旧的绝对路径为相对路径（一次性，兼容打包分发）
        try:
            from database.models import Document
            from pathlib import Path
            import config
            docs = session.query(Document).filter(Document.file_path.isnot(None)).all()
            migrated = 0
            for doc in docs:
                fp = doc.file_path
                if fp and os.path.isabs(fp):
                    # 绝对路径 → 相对路径（相对于 DATA_DIR）
                    try:
                        rel = str(Path(fp).relative_to(config.DATA_DIR))
                        doc.file_path = rel
                        migrated += 1
                    except ValueError:
                        pass  # 路径不在 DATA_DIR 下，跳过
            if migrated > 0:
                session.flush()
                logger.info(f"已迁移 {migrated} 条路径为相对路径")
        except Exception as e:
            logger.warning(f"路径迁移失败（不影响正常使用）: {e}")

        # 补提已有文档的正文（一次性，content_text 为空且文件存在的记录）
        try:
            from database.models import Document
            from utils.text_extractor import extract_text
            import os
            docs_needing_text = session.query(Document).filter(
                Document.is_deleted == False,
                (Document.content_text == None) | (Document.content_text == "")
            ).all()
            extracted = 0
            for doc in docs_needing_text:
                if doc.file_path and os.path.exists(doc.file_path):
                    body_text = extract_text(doc.file_path)
                    if body_text:
                        doc.content_text = body_text
                        extracted += 1
            if extracted > 0:
                session.flush()
                logger.info(f"已为 {extracted} 个文档补提正文")
        except Exception as e:
            logger.warning(f"正文补提失败（不影响正常使用）: {e}")

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
