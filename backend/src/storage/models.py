from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Boolean, ARRAY, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from .database import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_path = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False)  # 'audio', 'pdf', 'web', 'text', 'image'
    title = Column(Text)
    author = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ingested_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    file_size = Column(BigInteger)
    metadata = Column(JSONB)
    processing_status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    document_tags = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer)
    embedding = Column(Vector(384))  # MiniLM embedding dimension
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))  # Future: multi-user support
    query = Column(Text, nullable=False)
    response = Column(Text)
    context_chunks = Column(ARRAY(UUID(as_uuid=True)))  # Array of chunk IDs used
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    response_time_ms = Column(Integer)


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7))  # Hex color
    auto_generated = Column(Boolean, default=False)
    
    # Relationships
    document_tags = relationship("DocumentTag", back_populates="tag", cascade="all, delete-orphan")


class DocumentTag(Base):
    __tablename__ = "document_tags"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    document = relationship("Document", back_populates="document_tags")
    tag = relationship("Tag", back_populates="document_tags")