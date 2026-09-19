"""
数据库引擎 + 会话管理
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

import config

logger = logging.getLogger(__name__)

engine = create_engine(config.DB_URL, echo=False)


def check_fts5_support() -> bool:
    """检测当前 SQLite 是否支持 FTS5 虚拟表"""
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test USING fts5(content)"
            ))
            conn.execute(text("DROP TABLE IF EXISTS _fts5_test"))
            conn.commit()
        return True
    except Exception as e:
        logger.warning(f"FTS5 不可用，将降级为 LIKE 模糊搜索: {e}")
        return False


FTS5_AVAILABLE = check_fts5_support()

@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
