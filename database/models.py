"""
SQLAlchemy ORM 模型 — 与实际数据库 schema 对齐
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean,
    PrimaryKeyConstraint, UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    icon = Column(String(50), default="")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    parent = relationship("Category", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False, default="#2d5aa0")
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    doc_no = Column(String(200), default="")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    effective_date = Column(String(10), default="")
    expiry_date = Column(String(10), default="")
    department = Column(String(200), default="")
    issuing_org = Column(String(200), default="")
    version_no = Column(String(20), nullable=False, default="1")
    file_path = Column(String(1000), nullable=False, default="")
    original_name = Column(String(500), nullable=False, default="")
    file_type = Column(String(10), nullable=False, default="")
    file_size = Column(Integer, nullable=False, default=0)
    file_hash = Column(String(64), nullable=False, default="")
    thumbnail_path = Column(String(1000), default="")
    content_text = Column(Text, default="")
    description = Column(Text, default="")
    tags_text = Column(String(500), default="")
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(String(100), nullable=False, default="admin")

    category = relationship("Category", back_populates="documents")
    tag_associations = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")


class DocumentTag(Base):
    __tablename__ = "document_tags"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("document_id", "tag_id"),
    )

    document = relationship("Document", back_populates="tag_associations")
    tag = relationship("Tag")


# ── 央行评级标准打分卡（模块 → 一级指标 → 二级指标 → 评级内容）──

class Scorecard(Base):
    """打分卡（按银行类型区分：城商农商民营 / 村镇银行）"""
    __tablename__ = "scorecards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    modules = relationship(
        "ScorecardModule", back_populates="scorecard",
        cascade="all, delete-orphan", order_by="ScorecardModule.sort_order",
    )


class ScorecardModule(Base):
    """模块（xls 列0），如「一、公司治理」"""
    __tablename__ = "scorecard_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scorecard_id = Column(Integer, ForeignKey("scorecards.id"), nullable=False)
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint("scorecard_id", "name", name="uq_scorecard_module_name"),
        Index("idx_scorecard_modules_scorecard", "scorecard_id"),
    )

    scorecard = relationship("Scorecard", back_populates="modules")
    sections = relationship(
        "ScorecardSection", back_populates="module",
        cascade="all, delete-orphan", order_by="ScorecardSection.sort_order",
    )


class ScorecardSection(Base):
    """一级指标（xls 列1），如「（一）组织架构」"""
    __tablename__ = "scorecard_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("scorecard_modules.id"), nullable=False)
    name = Column(String(300), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint("module_id", "name", name="uq_scorecard_section_name"),
        Index("idx_scorecard_sections_module", "module_id"),
    )

    module = relationship("ScorecardModule", back_populates="sections")
    items = relationship(
        "ScorecardItem", back_populates="section",
        cascade="all, delete-orphan", order_by="ScorecardItem.sort_order",
    )


class ScorecardItem(Base):
    """二级指标（xls 列2，占位 '0' 行已折叠），如「1.加强党的领导。」"""
    __tablename__ = "scorecard_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("scorecard_sections.id"), nullable=False)
    name = Column(String(500), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint("section_id", "name", name="uq_scorecard_item_name"),
        Index("idx_scorecard_items_section", "section_id"),
    )

    section = relationship("ScorecardSection", back_populates="items")
    checks = relationship(
        "ScorecardCheck", back_populates="item",
        cascade="all, delete-orphan", order_by="ScorecardCheck.sort_order",
    )


class ScorecardCheck(Base):
    """评级内容检查项（xls 一行：列3 内容 + 列5/6/7 说明字段）"""
    __tablename__ = "scorecard_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("scorecard_items.id"), nullable=False)
    content = Column(String(1000), default="")
    key_points = Column(Text, default="")
    regulation_basis = Column(Text, default="")
    review_materials = Column(Text, default="")
    ignored_auto_ids = Column(Text, default="[]")  # JSON list of doc_ids user removed; sync skips these
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    __table_args__ = (
        Index("idx_scorecard_checks_item", "item_id"),
    )

    item = relationship("ScorecardItem", back_populates="checks")
    document_links = relationship(
        "ScorecardCheckDocument", back_populates="check",
        cascade="all, delete-orphan",
    )


class ScorecardCheckDocument(Base):
    """检查项 ↔ 制度文档 关联（手动建立 / 引用自动识别建立）"""
    __tablename__ = "scorecard_check_documents"

    check_id = Column(Integer, ForeignKey("scorecard_checks.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    is_auto = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("check_id", "document_id"),
    )

    check = relationship("ScorecardCheck", back_populates="document_links")
    document = relationship("Document")
