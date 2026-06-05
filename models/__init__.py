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
