from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time
import json
import uuid
from datetime import datetime

from src.storage import get_db, Conversation
from src.api.schemas import QueryRequest, QueryResponse, SourceReference
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.service import LLMService

router = APIRouter()

# Initialize services
search_engine = HybridSearchEngine()
llm_service = LLMService()


@router.post("/query", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a natural language query"""
    
    start_time = time.time()
    
    try:
        # Perform hybrid search
        search_results = await search_engine.search(
            query=request.query,
            db=db,
            limit=10,
            source_types=request.filters.source_types if request.filters else None,
            date_range=request.filters.date_range if request.filters else None,
            tags=request.filters.tags if request.filters else None
        )
        
        # Get conversation history if conversation_id provided
        conversation_history = []
        if request.conversation_id:
            history_result = await db.execute(
                select(Conversation)
                .where(Conversation.id == request.conversation_id)
                .order_by(Conversation.created_at.desc())
                .limit(5)
            )
            history_conversations = history_result.scalars().all()
            
            for conv in reversed(history_conversations):
                conversation_history.extend([
                    {"role": "user", "content": conv.query},
                    {"role": "assistant", "content": conv.response or ""}
                ])
        
        # Generate LLM response
        response_text = await llm_service.generate_response(
            query=request.query,
            context_chunks=search_results,
            conversation_history=conversation_history
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create conversation record
        conversation_id = request.conversation_id or uuid.uuid4()
        context_chunk_ids = [result['chunk_id'] for result in search_results]
        
        conversation = Conversation(
            id=conversation_id,
            query=request.query,
            response=response_text,
            context_chunks=context_chunk_ids,
            response_time_ms=response_time_ms
        )
        
        db.add(conversation)
        await db.commit()
        
        # Build source references
        sources = []
        for result in search_results[:5]:  # Top 5 sources
            sources.append(SourceReference(
                document_id=result['document_id'],
                chunk_id=result['chunk_id'],
                title=result.get('title'),
                excerpt=result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                relevance_score=result['relevance_score'],
                source_type=result['source_type']
            ))
        
        return QueryResponse(
            conversation_id=conversation_id,
            response=response_text,
            sources=sources,
            response_time_ms=response_time_ms,
            created_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.websocket("/chat/stream")
async def websocket_chat(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for streaming chat"""
    
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") != "query":
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid message type"}
                }))
                continue
            
            query = message.get("data", {}).get("query", "")
            conversation_id = message.get("data", {}).get("conversation_id")
            
            if not query:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "data": {"message": "Query is required"}
                }))
                continue
            
            try:
                # Perform search
                search_results = await search_engine.search(
                    query=query,
                    db=db,
                    limit=10
                )
                
                # Get conversation history
                conversation_history = []
                if conversation_id:
                    try:
                        conv_uuid = uuid.UUID(conversation_id)
                        history_result = await db.execute(
                            select(Conversation)
                            .where(Conversation.id == conv_uuid)
                            .order_by(Conversation.created_at.desc())
                            .limit(5)
                        )
                        history_conversations = history_result.scalars().all()
                        
                        for conv in reversed(history_conversations):
                            conversation_history.extend([
                                {"role": "user", "content": conv.query},
                                {"role": "assistant", "content": conv.response or ""}
                            ])
                    except ValueError:
                        pass  # Invalid UUID, ignore
                
                # Stream response
                full_response = ""
                async for chunk in llm_service.generate_response_stream(
                    query=query,
                    context_chunks=search_results,
                    conversation_history=conversation_history
                ):
                    full_response += chunk
                    await websocket.send_text(json.dumps({
                        "type": "response_chunk",
                        "data": {
                            "content": chunk,
                            "is_final": False
                        }
                    }))
                
                # Send final message
                await websocket.send_text(json.dumps({
                    "type": "response_chunk",
                    "data": {
                        "content": "",
                        "is_final": True
                    }
                }))
                
                # Save conversation
                new_conversation_id = conversation_id or str(uuid.uuid4())
                context_chunk_ids = [result['chunk_id'] for result in search_results]
                
                conversation = Conversation(
                    id=uuid.UUID(new_conversation_id) if conversation_id else uuid.uuid4(),
                    query=query,
                    response=full_response,
                    context_chunks=context_chunk_ids
                )
                
                db.add(conversation)
                await db.commit()
                
                # Send sources
                sources = []
                for result in search_results[:5]:
                    sources.append({
                        "document_id": str(result['document_id']),
                        "chunk_id": str(result['chunk_id']),
                        "title": result.get('title'),
                        "excerpt": result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                        "relevance_score": result['relevance_score'],
                        "source_type": result['source_type']
                    })
                
                await websocket.send_text(json.dumps({
                    "type": "sources",
                    "data": {
                        "conversation_id": new_conversation_id,
                        "sources": sources
                    }
                }))
                
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": f"Processing failed: {str(e)}"}
                }))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": f"Connection error: {str(e)}"}
            }))
        except:
            pass