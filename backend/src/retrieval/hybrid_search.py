from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, and_, or_
from datetime import datetime, timedelta
import re
import logging

from src.storage.models import Document, Chunk
from src.ingestion.embedder import EmbeddingGenerator
from src.api.schemas import SourceType

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """Hybrid search engine combining semantic and keyword search"""
    
    def __init__(self):
        self.embedder = EmbeddingGenerator()
    
    async def search(self,
                    query: str,
                    db: AsyncSession,
                    limit: int = 10,
                    source_types: Optional[List[SourceType]] = None,
                    date_range: Optional[Dict[str, str]] = None,
                    tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search"""
        
        # Parse temporal expressions in query
        temporal_filter = self._parse_temporal_query(query)
        if temporal_filter and not date_range:
            date_range = temporal_filter
        
        # Generate query embedding for semantic search
        query_embedding = self.embedder.generate_embedding(query)
        
        # Perform parallel searches
        semantic_results = await self._semantic_search(
            query_embedding, db, limit * 2, source_types, date_range, tags
        )
        
        keyword_results = await self._keyword_search(
            query, db, limit * 2, source_types, date_range, tags
        )
        
        # Fuse results using Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            semantic_results, keyword_results, limit
        )
        
        return fused_results
    
    async def _semantic_search(self,
                              query_embedding: List[float],
                              db: AsyncSession,
                              limit: int,
                              source_types: Optional[List[SourceType]] = None,
                              date_range: Optional[Dict[str, str]] = None,
                              tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        
        # Build base query
        query_stmt = select(
            Chunk.id,
            Chunk.content,
            Chunk.metadata,
            Document.id.label('document_id'),
            Document.title,
            Document.source_type,
            Document.created_at,
            # Calculate cosine similarity
            (1 - func.cosine_distance(Chunk.embedding, query_embedding)).label('similarity')
        ).join(Document)
        
        # Apply filters
        query_stmt = self._apply_filters(query_stmt, source_types, date_range, tags)
        
        # Order by similarity and limit
        query_stmt = query_stmt.order_by(text('similarity DESC')).limit(limit)
        
        try:
            result = await db.execute(query_stmt)
            rows = result.fetchall()
            
            return [
                {
                    'chunk_id': row.id,
                    'document_id': row.document_id,
                    'content': row.content,
                    'title': row.title,
                    'source_type': row.source_type,
                    'created_at': row.created_at,
                    'relevance_score': float(row.similarity),
                    'search_type': 'semantic',
                    'metadata': row.metadata or {}
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _keyword_search(self,
                             query: str,
                             db: AsyncSession,
                             limit: int,
                             source_types: Optional[List[SourceType]] = None,
                             date_range: Optional[Dict[str, str]] = None,
                             tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Perform keyword search using full-text search"""
        
        # Prepare search query for PostgreSQL full-text search
        search_query = self._prepare_search_query(query)
        
        # Build base query
        query_stmt = select(
            Chunk.id,
            Chunk.content,
            Chunk.metadata,
            Document.id.label('document_id'),
            Document.title,
            Document.source_type,
            Document.created_at,
            # Calculate text search rank
            func.ts_rank(
                func.to_tsvector('english', Chunk.content),
                func.plainto_tsquery('english', search_query)
            ).label('rank')
        ).join(Document).where(
            func.to_tsvector('english', Chunk.content).match(
                func.plainto_tsquery('english', search_query)
            )
        )
        
        # Apply filters
        query_stmt = self._apply_filters(query_stmt, source_types, date_range, tags)
        
        # Order by rank and limit
        query_stmt = query_stmt.order_by(text('rank DESC')).limit(limit)
        
        try:
            result = await db.execute(query_stmt)
            rows = result.fetchall()
            
            return [
                {
                    'chunk_id': row.id,
                    'document_id': row.document_id,
                    'content': row.content,
                    'title': row.title,
                    'source_type': row.source_type,
                    'created_at': row.created_at,
                    'relevance_score': float(row.rank),
                    'search_type': 'keyword',
                    'metadata': row.metadata or {}
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _apply_filters(self, query_stmt, source_types, date_range, tags):
        """Apply filters to search query"""
        
        # Source type filter
        if source_types:
            source_type_values = [st.value for st in source_types]
            query_stmt = query_stmt.where(Document.source_type.in_(source_type_values))
        
        # Date range filter
        if date_range:
            if 'start' in date_range:
                start_date = datetime.fromisoformat(date_range['start'])
                query_stmt = query_stmt.where(Document.created_at >= start_date)
            
            if 'end' in date_range:
                end_date = datetime.fromisoformat(date_range['end'])
                query_stmt = query_stmt.where(Document.created_at <= end_date)
        
        # Tags filter (if implemented)
        if tags:
            # This would require joining with document_tags and tags tables
            # Simplified for now
            pass
        
        return query_stmt
    
    def _prepare_search_query(self, query: str) -> str:
        """Prepare query for PostgreSQL full-text search"""
        
        # Remove special characters and normalize
        cleaned_query = re.sub(r'[^\w\s]', ' ', query)
        
        # Split into words and remove empty strings
        words = [word.strip() for word in cleaned_query.split() if word.strip()]
        
        # Join with spaces for plainto_tsquery
        return ' '.join(words)
    
    def _reciprocal_rank_fusion(self,
                               semantic_results: List[Dict[str, Any]],
                               keyword_results: List[Dict[str, Any]],
                               limit: int,
                               k: int = 60) -> List[Dict[str, Any]]:
        """Fuse results using Reciprocal Rank Fusion"""
        
        # Create score dictionaries
        scores = {}
        
        # Add semantic search scores
        for rank, result in enumerate(semantic_results):
            chunk_id = result['chunk_id']
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score
        
        # Add keyword search scores
        for rank, result in enumerate(keyword_results):
            chunk_id = result['chunk_id']
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score
        
        # Create result lookup
        all_results = {}
        for result in semantic_results + keyword_results:
            chunk_id = result['chunk_id']
            if chunk_id not in all_results:
                all_results[chunk_id] = result
        
        # Sort by fused score
        sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final results
        fused_results = []
        for chunk_id, score in sorted_chunks[:limit]:
            if chunk_id in all_results:
                result = all_results[chunk_id].copy()
                result['relevance_score'] = score
                result['search_type'] = 'hybrid'
                fused_results.append(result)
        
        return fused_results
    
    def _parse_temporal_query(self, query: str) -> Optional[Dict[str, str]]:
        """Parse temporal expressions from query"""
        
        query_lower = query.lower()
        now = datetime.now()
        
        # Define temporal patterns
        temporal_patterns = {
            r'\blast week\b': {
                'start': (now - timedelta(weeks=1)).isoformat(),
                'end': now.isoformat()
            },
            r'\byesterday\b': {
                'start': (now - timedelta(days=1)).isoformat(),
                'end': (now - timedelta(days=1) + timedelta(hours=23, minutes=59)).isoformat()
            },
            r'\blast month\b': {
                'start': (now - timedelta(days=30)).isoformat(),
                'end': now.isoformat()
            },
            r'\btoday\b': {
                'start': now.replace(hour=0, minute=0, second=0).isoformat(),
                'end': now.isoformat()
            },
            r'\bthis week\b': {
                'start': (now - timedelta(days=now.weekday())).isoformat(),
                'end': now.isoformat()
            }
        }
        
        # Check for matches
        for pattern, date_range in temporal_patterns.items():
            if re.search(pattern, query_lower):
                return date_range
        
        return None