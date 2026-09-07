"""
DTO 数据传输对象（与 ORM 解耦）
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class CategoryData:
    id: int
    name: str
    parent_id: Optional[int] = None
    doc_count: int = 0
    children: List["CategoryData"] = field(default_factory=list)


@dataclass
class DocumentData:
    id: int
    title: str
    doc_no: str = ""
    version_no: str = "1"
    category_id: Optional[int] = None
    category_name: str = ""
    status: str = "active"
    issuing_org: str = ""
    department: str = ""
    effective_date: str = ""
    expiry_date: str = ""
    description: str = ""
    file_path: str = ""
    original_name: str = ""
    file_type: str = ""
    file_size: int = 0
    thumbnail_path: str = ""
    content_text: str = ""
    tags_text: str = ""
    created_by: str = "admin"
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    snippet: str = ""  # 搜索结果摘要
    is_auto: bool = False  # 关联制度是否由引用自动识别建立（v1.1）


@dataclass
class SearchResult:
    documents: List[DocumentData] = field(default_factory=list)
    total: int = 0
    page: int = 1
    total_pages: int = 1


@dataclass
class SearchFilter:
    keyword: str = ""
    category_id: Optional[int] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20


# ── 央行评级标准打分卡 ──

@dataclass
class ScorecardData:
    id: int
    name: str
    description: str = ""


@dataclass
class ScorecardCheckData:
    """评级内容检查项（叶子节点）"""
    id: int
    content: str = ""
    key_points: str = ""
    regulation_basis: str = ""
    review_materials: str = ""
    documents: List[DocumentData] = field(default_factory=list)


@dataclass
class ScorecardNode:
    """打分卡树节点：模块 / 一级指标 / 二级指标 通用结构"""
    id: int
    name: str
    kind: str = "module"  # module | section | item
    children: List["ScorecardNode"] = field(default_factory=list)
    checks: List[ScorecardCheckData] = field(default_factory=list)


@dataclass
class ScorecardHit:
    """搜索命中项，ids_chain 用于在树中逐层定位"""
    kind: str  # module | section | item | check
    id: int
    ids_chain: List[int] = field(default_factory=list)
    path: str = ""
    matched_field: str = ""
    snippet: str = ""
