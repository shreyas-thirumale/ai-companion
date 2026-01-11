from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.storage import get_db, Conversation
from src.api.schemas import ConversationListResponse, ConversationResponse

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history"""
    
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Get total count
    count_result = await db.execute(select(func.count(Conversation.id)))
    total = count_result.scalar()
    
    # Get conversations
    result = await db.execute(
        select(Conversation)
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=conv.id,
                query=conv.query,
                response=conv.response,
                created_at=conv.created_at,
                response_time_ms=conv.response_time_ms
            )
            for conv in conversations
        ],
        total=total,
        page=page,
        limit=limit
    )