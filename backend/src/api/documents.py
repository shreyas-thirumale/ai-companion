from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
import os
import shutil

from src.storage import get_db, Document, DocumentTag, Tag
from src.api.schemas import DocumentResponse, DocumentListResponse, SourceType
from src.config import settings
from src.ingestion.tasks import process_document_task

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),  # JSON string of tag names
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document"""
    
    # Validate file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Determine source type from file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    source_type_mapping = {
        '.pdf': SourceType.PDF,
        '.txt': SourceType.TEXT,
        '.md': SourceType.TEXT,
        '.docx': SourceType.TEXT,
        '.mp3': SourceType.AUDIO,
        '.m4a': SourceType.AUDIO,
        '.wav': SourceType.AUDIO,
        '.jpg': SourceType.IMAGE,
        '.jpeg': SourceType.IMAGE,
        '.png': SourceType.IMAGE,
        '.gif': SourceType.IMAGE,
    }
    
    if file_ext not in source_type_mapping:
        raise HTTPException(status_code=422, detail="Unsupported file type")
    
    source_type = source_type_mapping[file_ext]
    
    # Save file
    file_path = os.path.join(settings.upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    document = Document(
        source_path=file_path,
        source_type=source_type.value,
        title=os.path.splitext(file.filename)[0],
        file_size=file.size,
        processing_status="pending"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Process tags if provided
    if tags:
        import json
        try:
            tag_names = json.loads(tags)
            for tag_name in tag_names:
                # Get or create tag
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                tag = result.scalar_one_or_none()
                
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    await db.commit()
                    await db.refresh(tag)
                
                # Create document-tag association
                doc_tag = DocumentTag(document_id=document.id, tag_id=tag.id)
                db.add(doc_tag)
            
            await db.commit()
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON
    
    # Queue document for processing
    process_document_task.delay(str(document.id))
    
    return DocumentResponse(
        id=document.id,
        source_path=document.source_path,
        source_type=document.source_type,
        title=document.title,
        author=document.author,
        created_at=document.created_at,
        ingested_at=document.ingested_at,
        file_size=document.file_size,
        processing_status=document.processing_status,
        metadata=document.metadata,
        tags=[],
        chunk_count=0
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    source_type: Optional[SourceType] = None,
    tags: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    """List user documents with pagination and filtering"""
    
    if limit > 100:
        limit = 100
    
    offset = (page - 1) * limit
    
    # Build query
    query = select(Document)
    
    if source_type:
        query = query.where(Document.source_type == source_type.value)
    
    if tags:
        # Filter by tags (documents that have ALL specified tags)
        for tag_name in tags:
            query = query.join(DocumentTag).join(Tag).where(Tag.name == tag_name)
    
    # Get total count
    count_query = select(func.count(Document.id))
    if source_type:
        count_query = count_query.where(Document.source_type == source_type.value)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get documents
    query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Convert to response format
    document_responses = []
    for doc in documents:
        # Get chunk count
        chunk_count_result = await db.execute(
            select(func.count()).select_from(
                select(1).where(Document.id == doc.id).join(Document.chunks).subquery()
            )
        )
        chunk_count = chunk_count_result.scalar() or 0
        
        document_responses.append(DocumentResponse(
            id=doc.id,
            source_path=doc.source_path,
            source_type=doc.source_type,
            title=doc.title,
            author=doc.author,
            created_at=doc.created_at,
            ingested_at=doc.ingested_at,
            file_size=doc.file_size,
            processing_status=doc.processing_status,
            metadata=doc.metadata,
            tags=[],  # TODO: Load tags
            chunk_count=chunk_count
        ))
    
    return DocumentListResponse(
        documents=document_responses,
        total=total,
        page=page,
        limit=limit,
        has_next=offset + limit < total
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get document details"""
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chunk count
    chunk_count_result = await db.execute(
        select(func.count()).select_from(
            select(1).where(Document.id == document.id).join(Document.chunks).subquery()
        )
    )
    chunk_count = chunk_count_result.scalar() or 0
    
    return DocumentResponse(
        id=document.id,
        source_path=document.source_path,
        source_type=document.source_type,
        title=document.title,
        author=document.author,
        created_at=document.created_at,
        ingested_at=document.ingested_at,
        file_size=document.file_size,
        processing_status=document.processing_status,
        metadata=document.metadata,
        tags=[],  # TODO: Load tags
        chunk_count=chunk_count
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if it exists
    if os.path.exists(document.source_path):
        os.remove(document.source_path)
    
    # Delete document (cascades to chunks and tags)
    await db.delete(document)
    await db.commit()
    
    return None