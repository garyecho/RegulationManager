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
        index_document_in_session(
            session, doc_id, title, doc_no, department, issuing_org,
            description, content_text,
        )


def index_document_in_session(session, doc_id: int, title: str,
                              doc_no: str = "", department: str = "",
                              issuing_org: str = "", description: str = "",
                              content_text: str = ""):
    """在调用方事务中更新单个文档的 FTS5 索引。"""
    import config
    exists = session.execute(text(
        "SELECT COUNT(*) FROM documents_fts WHERE rowid = :id"
    ), {"id": doc_id}).scalar() or 0

    if exists > 0:
        session.execute(text("""
            DELETE FROM documents_fts WHERE rowid = :id
        """), {"id": doc_id})

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
        "content_text": tokenize(content_text[:config.MAX_CONTENT_INDEX_LEN]),
    })


def remove_from_index(doc_id: int):
    """从 FTS5 索引中移除文档"""
    with get_session() as session:
        remove_from_index_in_session(session, doc_id)


def remove_from_index_in_session(session, doc_id: int):
    """在调用方事务中移除单个文档的 FTS5 索引。"""
    exists = session.execute(text(
        "SELECT COUNT(*) FROM documents_fts WHERE rowid = :id"
    ), {"id": doc_id}).scalar() or 0

    if exists > 0:
        session.execute(text(
            "DELETE FROM documents_fts WHERE rowid = :id"
        ), {"id": doc_id})


def extract_snippet(content_text: str, keyword: str, max_len: int = 150) -> str:
    """从正文内容中提取包含关键词的完整句子"""
    if not content_text or not keyword:
        return ""

    # 找到关键词在正文中的位置
    pos = content_text.find(keyword)
    if pos == -1:
        # 尝试分词后的匹配
        return ""

    # 找到包含关键词的完整句子
    # 向前找句子开头（句号、问号、感叹号、换行）
    import re
    sentence_start = 0
    for punct in ['。', '？', '！', '\n', '.', '?', '!']:
        idx = content_text.rfind(punct, 0, pos)
        if idx != -1:
            sentence_start = idx + 1
            break

    # 向后找句子结尾
    sentence_end = len(content_text)
    for punct in ['。', '？', '！', '\n', '.', '?', '!']:
        idx = content_text.find(punct, pos + len(keyword))
        if idx != -1:
            sentence_end = idx + 1
            break

    # 截取句子
    snippet = content_text[sentence_start:sentence_end].strip()

    # 清理换行符和多余空格
    snippet = re.sub(r'[\r\n\t]+', ' ', snippet)
    snippet = re.sub(r'\s+', ' ', snippet).strip()

    # 如果句子太长，截取关键词周围的片段
    if len(snippet) > max_len:
        snippet_len = len(snippet)
        kw_pos_in_snippet = snippet.find(keyword)
        if kw_pos_in_snippet != -1:
            start = max(0, kw_pos_in_snippet - max_len // 3)
            end = min(snippet_len, kw_pos_in_snippet + len(keyword) + max_len * 2 // 3)
            snippet = snippet[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < snippet_len:
                snippet = snippet + "..."

    # 添加省略号
    if sentence_start > 0:
        snippet = "..." + snippet
    if sentence_end < len(content_text):
        snippet = snippet + "..."

    return snippet


def search_fts(keyword: str, page: int = 1, page_size: int = 20) -> tuple:
    """FTS5 全文搜索（自动分词）"""
    # 对搜索关键词分词
    tokens = tokenize(keyword)
    # 过滤并清理分词结果，移除 FTS5 查询语法字符
    terms = [t.replace('"', '').replace("'", '').strip()
             for t in tokens.split() if t.strip()]
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


def rebuild_index(progress_callback=None):
    """重建 FTS5 索引（从 documents 表重新填充，带分词）
    
    Args:
        progress_callback: 进度回调函数 callback(current, total, message)
    """
    import config
    with get_session() as session:
        # 清空旧索引
        session.execute(text("DELETE FROM documents_fts"))

        # 获取所有需要索引的文档
        rows = session.execute(text(
            "SELECT id, title, doc_no, department, issuing_org, description, content_text "
            "FROM documents WHERE is_deleted = 0"
        )).fetchall()

        total = len(rows)

        # 插入分词后的内容（一次性写入，避免 INSERT + UPDATE 双写）
        for i, row in enumerate(rows):
            rowid = row[0]
            session.execute(text("""
                INSERT INTO documents_fts(rowid, title, doc_no, department, issuing_org, description, content_text)
                VALUES (:id, :title, :doc_no, :department, :issuing_org, :description, :content_text)
            """), {
                "id": rowid,
                "title": tokenize(row[1]) if row[1] else "",
                "doc_no": tokenize(row[2]) if row[2] else "",
                "department": tokenize(row[3]) if row[3] else "",
                "issuing_org": tokenize(row[4]) if row[4] else "",
                "description": tokenize(row[5]) if row[5] else "",
                "content_text": tokenize((row[6] or "")[:config.MAX_CONTENT_INDEX_LEN]),
            })

            # 报告进度
            if progress_callback:
                progress_callback(i + 1, total, f"正在索引: {row[1][:20] if row[1] else '文档'}")

    logger.info("FTS5 索引已重建（含 jieba 分词）")


def rebuild_full(progress_callback=None):
    """完整重建：补提正文 + 重建 FTS5 索引"""
    from database.migrations import _extract_missing_text, _setup_fts5
    _extract_missing_text(progress_callback=progress_callback)
    _setup_fts5()
    rebuild_index(progress_callback=progress_callback)
    logger.info("完整重建 FTS5 完成")
