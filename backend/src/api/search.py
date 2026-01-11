from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import time

from src.storage import get_db
from src.api.schemas import SearchResponse, SearchResult, SourceType
from src.retrieval.hybrid_search import HybridSearchEngine

router = APIRouter()
search_engine = HybridSearchEngine()


@router.get("", response_model=SearchResponse)
async def advanced_search(
    q: str = Query(..., description="Search query"),
    source_type: Optional[List[SourceType]] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Perform advanced search with filters"""
    
    start_time = time.time()
    
    # Build date range
    date_range = None
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range['start'] = date_from
        if date_to:
            date_range['end'] = date_to
    
    # Perform search
    results = await search_engine.search(
        query=q,
        db=db,
        limit=limit,
        source_types=source_type,
        date_range=date_range,
        tags=tags
    )
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    # Convert to response format
    search_results = [
        SearchResult(
            document_id=result['document_id'],
            chunk_id=result['chunk_id'],
            title=result.get('title'),
            content=result['content'],
            relevance_score=result['relevance_score'],
            source_type=result['source_type'],
            created_at=result['created_at']
        )
        for result in results
    ]
    
    return SearchResponse(
        results=search_results,
        total=len(search_results),
        query_time_ms=query_time_ms
    )