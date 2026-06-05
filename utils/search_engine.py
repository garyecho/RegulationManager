"""
FTS5 搜索引擎 + jieba 分词
"""
import logging
from typing import List
from sqlalchemy import text
from database import get_session

logger = logging.getLogger(__name__)

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba 未安装，中文搜索将使用原始文本")


def tokenize(text_str: str) -> str:
    """中文分词"""
    if HAS_JIEBA:
        return " ".join(jieba.cut_for_search(text_str))
    return text_str


def search_fts(keyword: str, page: int = 1, page_size: int = 20) -> tuple:
    """FTS5 全文搜索"""
    tokens = tokenize(keyword)
    # 构建 FTS5 查询：每个词加 * 前缀匹配
    terms = [t.strip() for t in tokens.split() if t.strip()]
    if not terms:
        return [], 0, 1
    fts_query = " OR ".join(f'"{t}"*' for t in terms)

    with get_session() as session:
        # 计算总数
        count_sql = text("""
            SELECT COUNT(*) FROM documents_fts
            WHERE documents_fts MATCH :query
        """)
        total = session.execute(count_sql, {"query": fts_query}).scalar() or 0

        # 搜索结果
        offset = (page - 1) * page_size
        search_sql = text("""
            SELECT rowid, rank FROM documents_fts
            WHERE documents_fts MATCH :query
            ORDER BY rank
            LIMIT :limit OFFSET :offset
        """)
        rows = session.execute(search_sql, {
            "query": fts_query, "limit": page_size, "offset": offset
        }).fetchall()

        doc_ids = [r[0] for r in rows]
        total_pages = max(1, (total + page_size - 1) // page_size)

        return doc_ids, total, total_pages


def rebuild_index():
    """重建 FTS5 索引"""
    with get_session() as session:
        session.execute(text(
            "INSERT INTO documents_fts(documents_fts) VALUES('rebuild')"
        ))
    logger.info("FTS5 索引已重建")
