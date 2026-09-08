"""
央行评级标准打分卡服务

层级：打分卡（银行类型）→ 模块 → 一级指标 → 二级指标 → 评级内容检查项
"""
import difflib
import html
import json
import logging
import re
import unicodedata
from typing import List, Optional, Tuple
from urllib.parse import quote

from sqlalchemy.orm import selectinload

from database import get_session
from database.models import (
    Document, Scorecard, ScorecardModule, ScorecardSection, ScorecardItem,
    ScorecardCheck, ScorecardCheckDocument,
)
from models import ScorecardData, ScorecardNode, ScorecardCheckData, ScorecardHit, DocumentData

logger = logging.getLogger(__name__)

# rename_node 支持的层级 → (ORM 类, 父级外键列名)
_NODE_KINDS = {
    "module": (ScorecardModule, "scorecard_id"),
    "section": (ScorecardSection, "module_id"),
    "item": (ScorecardItem, "section_id"),
}


def _escape_like(keyword: str) -> str:
    """转义 LIKE 通配符（与 database/crud.py 写法一致）"""
    return keyword.replace("%", "\\%").replace("_", "\\_")


def _doc_to_dto(doc: Document) -> DocumentData:
    """仅取界面展示与打开文件所需字段"""
    import config
    from pathlib import Path

    file_path = doc.file_path or ""
    if file_path and not Path(file_path).is_absolute():
        file_path = str(config.DATA_DIR / file_path)
    return DocumentData(
        id=doc.id,
        title=doc.title,
        doc_no=doc.doc_no or "",
        file_path=file_path,
        original_name=doc.original_name or "",
        file_type=doc.file_type or "",
    )


def _check_to_dto(check: ScorecardCheck) -> ScorecardCheckData:
    documents = []
    for link in check.document_links:
        if link.document is not None and not link.document.is_deleted:
            dto = _doc_to_dto(link.document)
            dto.is_auto = bool(link.is_auto)
            documents.append(dto)
    return ScorecardCheckData(
        id=check.id,
        content=check.content or "",
        key_points=check.key_points or "",
        regulation_basis=check.regulation_basis or "",
        review_materials=check.review_materials or "",
        documents=documents,
    )


# ── 查询 ──────────────────────────────────────────────────

def get_scorecards() -> List[ScorecardData]:
    """全部打分卡（银行类型）"""
    with get_session() as session:
        rows = session.query(Scorecard).order_by(Scorecard.id).all()
        return [ScorecardData(id=r.id, name=r.name, description=r.description or "") for r in rows]


def get_tree(scorecard_id: int) -> List[ScorecardNode]:
    """某打分卡的完整四层树（模块 → 一级 → 二级 → 检查项）"""
    with get_session() as session:
        modules = (
            session.query(ScorecardModule)
            .options(
                selectinload(ScorecardModule.sections)
                .selectinload(ScorecardSection.items)
                .selectinload(ScorecardItem.checks)
                .selectinload(ScorecardCheck.document_links)
                .selectinload(ScorecardCheckDocument.document)
            )
            .filter(ScorecardModule.scorecard_id == scorecard_id)
            .order_by(ScorecardModule.sort_order, ScorecardModule.id)
            .all()
        )

        tree = []
        for module in modules:
            module_node = ScorecardNode(id=module.id, name=module.name, kind="module")
            for section in module.sections:
                section_node = ScorecardNode(id=section.id, name=section.name, kind="section")
                for item in section.items:
                    item_node = ScorecardNode(id=item.id, name=item.name, kind="item")
                    item_node.checks = [_check_to_dto(c) for c in item.checks]
                    section_node.children.append(item_node)
                module_node.children.append(section_node)
            tree.append(module_node)
        return tree


def get_checks(item_id: int) -> List[ScorecardCheckData]:
    """某二级指标下的检查项"""
    with get_session() as session:
        checks = (
            session.query(ScorecardCheck)
            .options(
                selectinload(ScorecardCheck.document_links)
                .selectinload(ScorecardCheckDocument.document)
            )
            .filter(ScorecardCheck.item_id == item_id)
            .order_by(ScorecardCheck.sort_order, ScorecardCheck.id)
            .all()
        )
        return [_check_to_dto(c) for c in checks]


def get_check(check_id: int) -> Optional[ScorecardCheckData]:
    """单条检查项全字段 + 关联制度"""
    with get_session() as session:
        check = (
            session.query(ScorecardCheck)
            .options(
                selectinload(ScorecardCheck.document_links)
                .selectinload(ScorecardCheckDocument.document)
            )
            .filter(ScorecardCheck.id == check_id)
            .first()
        )
        return _check_to_dto(check) if check else None


# ── 编辑 ──────────────────────────────────────────────────

def rename_node(kind: str, node_id: int, new_name: str) -> bool:
    """重命名 模块/一级指标/二级指标；同父级下不得重名，名称不得为空"""
    if kind not in _NODE_KINDS:
        logger.warning(f"未知节点类型：{kind}")
        return False
    name = (new_name or "").strip()
    if not name:
        return False

    model, parent_field = _NODE_KINDS[kind]
    try:
        with get_session() as session:
            node = session.query(model).filter(model.id == node_id).first()
            if not node:
                return False
            if node.name == name:
                return True  # 无变化

            parent_id = getattr(node, parent_field)
            duplicated = (
                session.query(model)
                .filter(
                    getattr(model, parent_field) == parent_id,
                    model.name == name,
                    model.id != node_id,
                )
                .first()
            )
            if duplicated:
                logger.info(f"同层重名，拒绝重命名：{kind} #{node_id} → {name}")
                return False

            node.name = name
            session.flush()
            return True
    except Exception as e:
        logger.error(f"重命名失败 {kind} #{node_id}: {e}")
        return False


def update_check(check_id: int, **fields) -> bool:
    """更新检查项文本字段（content / key_points / regulation_basis / review_materials）"""
    allowed = {"content", "key_points", "regulation_basis", "review_materials"}
    updates = {k: (v or "").strip() for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    if "content" in updates and not updates["content"]:
        return False  # 评级内容不得为空

    try:
        with get_session() as session:
            check = session.query(ScorecardCheck).filter(ScorecardCheck.id == check_id).first()
            if not check:
                return False
            for key, value in updates.items():
                setattr(check, key, value)
            session.flush()
            return True
    except Exception as e:
        logger.error(f"检查项更新失败 #{check_id}: {e}")
        return False


# ── 制度关联 ──────────────────────────────────────────────

def set_check_documents(check_id: int, doc_ids: List[int]) -> bool:
    """整体替换检查项的关联制度（0..N 份），忽略不存在/已软删的文档"""
    try:
        with get_session() as session:
            check = session.query(ScorecardCheck).filter(ScorecardCheck.id == check_id).first()
            if not check:
                return False

            valid_ids = []
            if doc_ids:
                rows = (
                    session.query(Document.id)
                    .filter(Document.id.in_(list(set(doc_ids))), Document.is_deleted == False)
                    .all()
                )
                valid_ids = [r[0] for r in rows]

            session.query(ScorecardCheckDocument).filter(
                ScorecardCheckDocument.check_id == check_id
            ).delete(synchronize_session=False)
            for doc_id in valid_ids:
                session.add(ScorecardCheckDocument(check_id=check_id, document_id=doc_id))
            session.flush()
            return True
    except Exception as e:
        logger.error(f"关联制度失败 check #{check_id}: {e}")
        return False


def find_documents(keyword: str = "", limit: int = 50) -> List[DocumentData]:
    """制度选择器数据源：按标题/文号模糊查找未删除的文档"""
    with get_session() as session:
        query = session.query(Document).filter(Document.is_deleted == False)
        keyword = (keyword or "").strip()
        if keyword:
            pattern = f"%{_escape_like(keyword)}%"
            query = query.filter(
                Document.title.like(pattern, escape="\\")
                | Document.doc_no.like(pattern, escape="\\")
            )
        rows = query.order_by(Document.updated_at.desc()).limit(limit).all()
        return [_doc_to_dto(r) for r in rows]


# ── 搜索 ──────────────────────────────────────────────────

def _snippet(text: str, keyword: str, span: int = 30) -> str:
    """截取关键词周围文本作为摘要"""
    if not text:
        return ""
    pos = text.find(keyword)
    if pos == -1:
        return text[: span * 2].strip()
    start = max(0, pos - span)
    end = min(len(text), pos + len(keyword) + span)
    snippet = text[start:end].replace("\n", " ").strip()
    return ("..." if start > 0 else "") + snippet + ("..." if end < len(text) else "")


def search(scorecard_id: int, keyword: str) -> List[ScorecardHit]:
    """在指定打分卡内做全字段关键词搜索，返回可定位到树节点的命中列表"""
    keyword = (keyword or "").strip()
    if not keyword:
        return []

    hits = []  # type: List[ScorecardHit]
    with get_session() as session:
        modules = (
            session.query(ScorecardModule)
            .options(
                selectinload(ScorecardModule.sections)
                .selectinload(ScorecardSection.items)
                .selectinload(ScorecardItem.checks)
            )
            .filter(ScorecardModule.scorecard_id == scorecard_id)
            .order_by(ScorecardModule.sort_order, ScorecardModule.id)
            .all()
        )

        for module in modules:
            if keyword in (module.name or ""):
                hits.append(ScorecardHit(
                    kind="module", id=module.id, ids_chain=[module.id],
                    path=module.name, matched_field="模块", snippet=module.name,
                ))
            for section in module.sections:
                if keyword in (section.name or ""):
                    hits.append(ScorecardHit(
                        kind="section", id=section.id, ids_chain=[module.id, section.id],
                        path=f"{module.name} / {section.name}",
                        matched_field="一级指标", snippet=section.name,
                    ))
                for item in section.items:
                    if keyword in (item.name or ""):
                        hits.append(ScorecardHit(
                            kind="item", id=item.id,
                            ids_chain=[module.id, section.id, item.id],
                            path=f"{module.name} / {section.name} / {item.name}",
                            matched_field="二级指标", snippet=item.name,
                        ))
                    for check in item.checks:
                        for field_name, value in (
                            ("评级内容", check.content),
                            ("评分要点", check.key_points),
                            ("监管依据", check.regulation_basis),
                            ("需调阅材料", check.review_materials),
                        ):
                            if value and keyword in value:
                                hits.append(ScorecardHit(
                                    kind="check", id=check.id,
                                    ids_chain=[module.id, section.id, item.id, check.id],
                                    path=f"{module.name} / {section.name} / {item.name}",
                                    matched_field=field_name,
                                    snippet=_snippet(value, keyword),
                                ))
                                break  # 同一检查项只报首个命中字段
    return hits


# ── 引用识别与自动超链（v1.1）────────────────────────────

# 《标题》+ 可选（文号），或独立（文号）；文号必须以「号」结尾以减少误报
_CITATION_RE = re.compile(
    r"《(?P<title>[^《》]{2,80})》(?:\s*[（(](?P<no1>[^（）()《》]{2,50}?号)\s*[）)])?"
    r"|[（(](?P<no2>[^（）()《》]{2,50}?号)\s*[）)]"
)


def _norm_no(s: str) -> str:
    """文号归一化：全角转半角、去空白与各类括号，便于等价比较"""
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"[\s（）()〔〕\[\]【】]+", "", s)


def extract_citations(text: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """提取制度引用，返回 (标题或None, 文号或None) 列表"""
    out = []
    for m in _CITATION_RE.finditer(text or ""):
        title, no = m.group("title"), m.group("no1") or m.group("no2")
        if title or no:
            out.append((title, no))
    return out


def match_document(
    title: Optional[str], no: Optional[str], docs: List[Document]
) -> Optional[Document]:
    """按 文号精确 → 标题全等 → 标题互含 → 相似度≥0.75 匹配"""
    if no:
        target = _norm_no(no)
        for d in docs:
            if d.doc_no and _norm_no(d.doc_no) == target:
                return d
    if title:
        t = title.strip()
        for d in docs:
            if d.title.strip() == t:
                return d
        for d in docs:
            if t in d.title or d.title in t:
                return d
        scored = sorted(
            docs, key=lambda d: difflib.SequenceMatcher(None, t, d.title).ratio(), reverse=True
        )
        if scored and difflib.SequenceMatcher(None, t, scored[0].title).ratio() >= 0.75:
            return scored[0]
    return None


def _resolve_citation(title: Optional[str], no: Optional[str]) -> Optional[int]:
    """引用 → 文档 id（未匹配返回 None）"""
    if not (title or no):
        return None
    with get_session() as session:
        docs = session.query(Document).filter(Document.is_deleted == False).all()
        doc = match_document(title, no, docs)
        return doc.id if doc else None


def render_linked_html(text: str, dark_theme: bool = False) -> str:
    """把文本中的制度引用渲染为超链 HTML：已匹配蓝链 doc://{id}，未匹配灰链 missing://

    Args:
        text: 原始文本
        dark_theme: 是否为深色主题，控制内联颜色
    """
    def _repl(m):
        title, no = m.group("title"), m.group("no1") or m.group("no2")
        doc_id = _resolve_citation(title, no)
        label = html.escape(m.group(0))
        if doc_id:
            return f'<a href="doc://{doc_id}">{label}</a>'
        return f'<a href="missing://{quote(m.group(0))}">{label}</a>'

    return _CITATION_RE.sub(_repl, html.escape(text or ""))

    return _CITATION_RE.sub(_repl, html.escape(text or ""))


def sync_auto_links(check_id: int) -> int:
    """扫描检查项三字段中的引用，自动补充关联（is_auto=True，已存在不重复）。

    用户移除的自动关联记入 check.ignored_auto_ids（JSON），sync 会跳过它们。
    调用 clear_ignored_auto_ids 可恢复全部忽略记录（重新识别）。
    """
    try:
        with get_session() as session:
            check = session.query(ScorecardCheck).filter(ScorecardCheck.id == check_id).first()
            if not check:
                return 0
            ignored = set(json.loads(check.ignored_auto_ids or "[]"))
            citations, seen = [], set()
            for text in (check.key_points, check.regulation_basis, check.review_materials):
                for title, no in extract_citations(text or ""):
                    key = (title, _norm_no(no or ""))
                    if key not in seen:
                        seen.add(key)
                        citations.append((title, no))
            if not citations:
                return 0
            docs = session.query(Document).filter(Document.is_deleted == False).all()
            existing = {
                r[0] for r in session.query(ScorecardCheckDocument.document_id)
                .filter(ScorecardCheckDocument.check_id == check_id)
            }
            added = 0
            for title, no in citations:
                doc = match_document(title, no, docs)
                if doc is not None and doc.id not in existing and doc.id not in ignored:
                    session.add(ScorecardCheckDocument(
                        check_id=check_id, document_id=doc.id, is_auto=True,
                    ))
                    existing.add(doc.id)
                    added += 1
            if added:
                logger.info(f"检查项 #{check_id} 自动识别新增关联 {added} 条")
            return added
    except Exception as e:
        logger.error(f"自动识别关联失败 check #{check_id}: {e}")
        return 0


def ignore_auto_links(check_id: int, doc_ids: List[int]) -> None:
    """将用户移除的自动关联 doc_id 记入忽略清单（sync 时跳过）"""
    if not doc_ids:
        return
    try:
        with get_session() as session:
            check = session.query(ScorecardCheck).filter(ScorecardCheck.id == check_id).first()
            if not check:
                return
            existing = set(json.loads(check.ignored_auto_ids or "[]"))
            existing.update(doc_ids)
            check.ignored_auto_ids = json.dumps(sorted(existing))
            session.flush()
    except Exception as e:
        logger.error(f"忽略自动关联失败 check #{check_id}: {e}")


def clear_ignored_auto_ids(check_id: int) -> None:
    """清空忽略清单（「重新识别」时调用，让 sync 重新生成全部自动关联）"""
    try:
        with get_session() as session:
            check = session.query(ScorecardCheck).filter(ScorecardCheck.id == check_id).first()
            if check:
                check.ignored_auto_ids = "[]"
                session.flush()
    except Exception as e:
        logger.error(f"清空忽略清单失败 check #{check_id}: {e}")
