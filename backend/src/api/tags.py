from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.storage import get_db, Tag
from src.api.schemas import TagResponse, TagCreate

router = APIRouter()


@router.get("", response_model=List[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """List all tags"""
    
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            auto_generated=tag.auto_generated
        )
        for tag in tags
    ]


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    
    # Check if tag already exists
    result = await db.execute(select(Tag).where(Tag.name == tag_data.name))
    existing_tag = result.scalar_one_or_none()
    
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    # Create new tag
    tag = Tag(
        name=tag_data.name,
        color=tag_data.color,
        auto_generated=False
    )
    
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        auto_generated=tag.auto_generated
    )