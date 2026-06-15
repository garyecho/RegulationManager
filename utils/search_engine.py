"""
FTS5 搜索引擎 + jieba 中文分词

核心思路：FTS5 的 unicode61 分词器对中文支持差，
所以用 jieba 预分词后存入 FTS5，搜索时也先分词再查询。
"""
import logging
from sqlalchemy import text
from database import get_session

logger = logging.getLogger(__name__)

try:
    import jieba
    jieba.setLogLevel(logging.WARNING)
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba 未安装，中文搜索效果会很差")


def tokenize(text_str: str) -> str:
    """用 jieba 中文分词，返回空格连接的词组"""
    if not text_str:
        return ""
    if HAS_JIEBA:
        words = jieba.cut_for_search(text_str)
        return " ".join(w.strip() for w in words if w.strip())
    return text_str


def index_document(doc_id: int, title: str, doc_no: str = "",
                   department: str = "", issuing_org: str = "",
                   description: str = "", content_text: str = ""):
    """将单个文档写入 FTS5 索引（分词后）"""
    with get_session() as session:
        # 先删除旧记录
        session.execute(text(
            "INSERT INTO documents_fts(documents_fts, rowid) VALUES('delete', :id)"
        ), {"id": doc_id})

        # 插入分词后的新记录
        session.execute(text("""
            INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
            VALUES (:id, :title, :doc_no, :department, :issuing_org, :description, :content_text)
        """), {
            "id": doc_id,
            "title": tokenize(title),
            "doc_no": tokenize(doc_no),
            "department": tokenize(department),
            "issuing_org": tokenize(issuing_org),
            "description": tokenize(description),
            "content_text": tokenize(content_text[:100000]),  # 限制长度避免索引过大
        })


def remove_from_index(doc_id: int):
    """从 FTS5 索引中移除文档"""
    with get_session() as session:
        session.execute(text(
            "INSERT INTO documents_fts(documents_fts, rowid) VALUES('delete', :id)"
        ), {"id": doc_id})


def search_fts(keyword: str, page: int = 1, page_size: int = 20) -> tuple:
    """FTS5 全文搜索（自动分词）"""
    # 对搜索关键词分词
    tokens = tokenize(keyword)
    terms = [t.strip() for t in tokens.split() if t.strip()]
    if not terms:
        return [], 0, 1

    # 构建 FTS5 查询：所有词都必须出现（AND 逻辑），支持前缀匹配
    fts_query = " AND ".join(f'"{t}"*' for t in terms)

    with get_session() as session:
        try:
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
        except Exception as e:
            logger.warning(f"FTS5 搜索失败: {e}")
            return [], 0, 1


def rebuild_index():
    """重建 FTS5 索引（从 documents 表重新填充，带分词）"""
    with get_session() as session:
        # 清空旧索引
        session.execute(text("DELETE FROM documents_fts"))
        # 从 documents 表重新填充（分词后写入）
        session.execute(text("""
            INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
            SELECT id,
                   title, doc_no, department, issuing_org, description,
                   content_text
            FROM documents WHERE is_deleted = 0
        """))

        # 对已有的索引进行分词更新（逐条处理，因为需要 jieba 分词）
        rows = session.execute(text(
            "SELECT rowid, title, doc_no, department, issuing_org, description, content_text FROM documents_fts"
        )).fetchall()

        for row in rows:
            rowid = row[0]
            session.execute(text("""
                UPDATE documents_fts SET
                    title = :title, doc_no = :doc_no, department = :department,
                    issuing_org = :issuing_org, description = :description, content_text = :content_text
                WHERE rowid = :rowid
            """), {
                "rowid": rowid,
                "title": tokenize(row[1]) if row[1] else "",
                "doc_no": tokenize(row[2]) if row[2] else "",
                "department": tokenize(row[3]) if row[3] else "",
                "issuing_org": tokenize(row[4]) if row[4] else "",
                "description": tokenize(row[5]) if row[5] else "",
                "content_text": tokenize(row[6][:100000]) if row[6] else "",
            })

    logger.info("FTS5 索引已重建（含 jieba 分词）")


def rebuild_full():
    """完整重建：补提正文 + 重建 FTS5 索引"""
    from database.migrations import _extract_missing_text, _setup_fts5
    _extract_missing_text()
    _setup_fts5()
    rebuild_index()
    logger.info("完整重建 FTS5 完成")
