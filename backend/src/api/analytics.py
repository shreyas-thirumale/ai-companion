from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta

from src.storage import get_db, Document, Chunk, Conversation, Tag, DocumentTag
from src.api.schemas import AnalyticsResponse

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Get usage analytics"""
    
    # Total documents
    doc_count_result = await db.execute(select(func.count(Document.id)))
    total_documents = doc_count_result.scalar()
    
    # Total chunks
    chunk_count_result = await db.execute(select(func.count(Chunk.id)))
    total_chunks = chunk_count_result.scalar()
    
    # Total queries
    query_count_result = await db.execute(select(func.count(Conversation.id)))
    total_queries = query_count_result.scalar()
    
    # Average response time
    avg_time_result = await db.execute(
        select(func.avg(Conversation.response_time_ms))
        .where(Conversation.response_time_ms.isnot(None))
    )
    avg_response_time = avg_time_result.scalar() or 0.0
    
    # Storage usage (approximate)
    storage_result = await db.execute(
        select(func.sum(Document.file_size))
        .where(Document.file_size.isnot(None))
    )
    storage_bytes = storage_result.scalar() or 0
    storage_usage_mb = storage_bytes / (1024 * 1024)
    
    # Popular tags
    popular_tags_result = await db.execute(
        select(Tag.name, func.count(DocumentTag.document_id).label('count'))
        .join(DocumentTag)
        .group_by(Tag.name)
        .order_by(text('count DESC'))
        .limit(10)
    )
    popular_tags = [
        {"tag": row.name, "count": row.count}
        for row in popular_tags_result.fetchall()
    ]
    
    # Query trends (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    trends_result = await db.execute(
        select(
            func.date(Conversation.created_at).label('date'),
            func.count(Conversation.id).label('query_count')
        )
        .where(Conversation.created_at >= thirty_days_ago)
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    )
    query_trends = [
        {"date": str(row.date), "query_count": row.query_count}
        for row in trends_result.fetchall()
    ]
    
    return AnalyticsResponse(
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_queries=total_queries,
        avg_response_time_ms=float(avg_response_time),
        storage_usage_mb=float(storage_usage_mb),
        popular_tags=popular_tags,
        query_trends=query_trends
    )