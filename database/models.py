"""
SQLAlchemy ORM 模型 — 与实际数据库 schema 对齐
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, PrimaryKeyConstraint
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


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_no = Column(String(20), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now, nullable=False)
    note = Column(Text, default="")
    uploaded_by = Column(String(100), nullable=False, default="admin")


class RecycleBin(Base):
    __tablename__ = "recycle_bin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False)
    original_data = Column(Text, nullable=False)
    original_path = Column(String(1000), nullable=False)
    backup_path = Column(String(1000), default="")
    deleted_at = Column(DateTime, default=datetime.now, nullable=False)
    deleted_by = Column(String(100), nullable=False, default="admin")
    expire_at = Column(DateTime, nullable=True)
    is_permanent = Column(Boolean, nullable=False, default=False)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    detail = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
