"""
数据库初始化 + FTS5
"""
import logging
import os
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

    # FTS5 和触发器单独处理，避免事务回滚影响其他操作
    _setup_fts5()


def _setup_fts5():
    """设置 FTS5 全文搜索索引"""
    from database import get_session
    with get_session() as session:
        # 清理旧的 FTS 表和触发器
        for trig in ["documents_ai", "documents_ad", "documents_au", "documents_au_del"]:
            session.execute(text(f"DROP TRIGGER IF EXISTS {trig}"))
        for tbl in ["documents_fts", "documents_fts_data", "documents_fts_idx",
                     "documents_fts_docsize", "documents_fts_config"]:
            session.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
        for tbl in ["fts_documents", "fts_documents_data", "fts_documents_idx",
                     "fts_documents_docsize", "fts_documents_config"]:
            session.execute(text(f"DROP TABLE IF EXISTS {tbl}"))

        # 创建独立的 FTS5 虚拟表（不用 content 同步，因为需要 jieba 预分词）
        session.execute(text("""
            CREATE VIRTUAL TABLE documents_fts
            USING fts5(title, doc_no, department, issuing_org, description, content_text)
        """))

        logger.info("FTS5 虚拟表创建完成（独立模式，需手动分词填充）")

    # 迁移和补提操作在单独的 session 中进行
    _migrate_paths()
    _extract_missing_text()
    _cleanup_obsolete_categories()

    logger.info("数据库初始化完成")


def _migrate_paths():
    """迁移旧的绝对路径为相对路径"""
    from database import get_session
    from database.models import Document
    from pathlib import Path
    import config
    try:
        with get_session() as session:
            docs = session.query(Document).filter(Document.file_path.isnot(None)).all()
            migrated = 0
            for doc in docs:
                fp = doc.file_path
                if fp and os.path.isabs(fp):
                    try:
                        rel = str(Path(fp).relative_to(config.DATA_DIR))
                        doc.file_path = rel
                        migrated += 1
                    except ValueError:
                        pass
            if migrated > 0:
                session.flush()
                logger.info(f"已迁移 {migrated} 条路径为相对路径")
    except Exception as e:
        logger.warning(f"路径迁移失败（不影响正常使用）: {e}")


def _extract_missing_text():
    """补提已有文档的正文"""
    from database import get_session
    from database.models import Document
    from utils.text_extractor import extract_text
    try:
        with get_session() as session:
            docs_needing_text = session.query(Document).filter(
                Document.is_deleted == False,
                (Document.content_text == None) | (Document.content_text == "")
            ).all()
            extracted = 0
            for doc in docs_needing_text:
                # 解析路径
                if doc.file_path:
                    if os.path.isabs(doc.file_path):
                        full_path = doc.file_path
                    else:
                        import config
                        full_path = str(config.DATA_DIR / doc.file_path)
                    if os.path.exists(full_path):
                        body_text = extract_text(full_path)
                        if body_text:
                            doc.content_text = body_text
                            extracted += 1
            if extracted > 0:
                session.flush()
                logger.info(f"已为 {extracted} 个文档补提正文")
    except Exception as e:
        logger.warning(f"正文补提失败（不影响正常使用）: {e}")


def _cleanup_obsolete_categories():
    """清理废弃的默认分类"""
    from database import get_session
    from database.models import Category
    try:
        with get_session() as session:
            obsolete = ["法律法规", "监管制度", "内部规章", "操作规程", "指导意见"]
            for name in obsolete:
                cat = session.query(Category).filter(Category.name == name).first()
                if cat:
                    session.execute(
                        text("UPDATE documents SET category_id = NULL WHERE category_id = :cid"),
                        {"cid": cat.id}
                    )
                    session.delete(cat)
                    logger.info(f"已清理废弃分类：{name}")
    except Exception as e:
        logger.warning(f"分类清理失败（不影响正常使用）: {e}")
