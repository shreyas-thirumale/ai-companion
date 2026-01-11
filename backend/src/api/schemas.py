from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class SourceType(str, Enum):
    AUDIO = "audio"
    PDF = "pdf"
    WEB = "web"
    TEXT = "text"
    IMAGE = "image"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    id: UUID
    name: str
    color: str
    auto_generated: bool

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    source_path: str
    source_type: SourceType
    title: Optional[str]
    author: Optional[str]
    created_at: datetime
    ingested_at: datetime
    file_size: Optional[int]
    processing_status: ProcessingStatus
    metadata: Optional[Dict[str, Any]]
    tags: List[TagResponse] = []
    chunk_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int
    has_next: bool


class QueryFilters(BaseModel):
    source_types: Optional[List[SourceType]] = None
    date_range: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None
    filters: Optional[QueryFilters] = None


class SourceReference(BaseModel):
    document_id: UUID
    chunk_id: UUID
    title: Optional[str]
    excerpt: str
    relevance_score: float
    source_type: SourceType


class QueryResponse(BaseModel):
    conversation_id: UUID
    response: str
    sources: List[SourceReference]
    response_time_ms: int
    created_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    query: str
    response: Optional[str]
    created_at: datetime
    response_time_ms: Optional[int]

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int
    limit: int


class SearchResult(BaseModel):
    document_id: UUID
    chunk_id: UUID
    title: Optional[str]
    content: str
    relevance_score: float
    source_type: SourceType
    created_at: datetime


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query_time_ms: int


class AnalyticsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    avg_response_time_ms: float
    storage_usage_mb: float
    popular_tags: List[Dict[str, Any]]
    query_trends: List[Dict[str, Any]]