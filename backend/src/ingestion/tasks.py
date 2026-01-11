from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from uuid import UUID

from src.config import settings
from src.storage.models import Document, Chunk
from src.ingestion.processors import (
    AudioProcessor,
    DocumentProcessor, 
    TextProcessor,
    ImageProcessor
)
from src.ingestion.chunker import IntelligentChunker
from src.ingestion.embedder import EmbeddingGenerator

# Initialize Celery
celery_app = Celery(
    "second_brain",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Database session for Celery tasks
engine = create_engine(settings.database_url_sync)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task
def process_document_task(document_id: str):
    """Process a document asynchronously"""
    
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
        if not document:
            return {"error": "Document not found"}
        
        # Update status
        document.processing_status = "processing"
        db.commit()
        
        # Initialize processors
        processors = {
            "audio": AudioProcessor(),
            "pdf": DocumentProcessor(),
            "text": TextProcessor(),
            "image": ImageProcessor()
        }
        
        chunker = IntelligentChunker()
        embedder = EmbeddingGenerator()
        
        # Process based on source type
        processor = processors.get(document.source_type)
        if not processor:
            document.processing_status = "failed"
            db.commit()
            return {"error": f"No processor for type: {document.source_type}"}
        
        # Extract content
        try:
            content_data = processor.process(document.source_path)
        except Exception as e:
            document.processing_status = "failed"
            document.metadata = {"error": str(e)}
            db.commit()
            return {"error": f"Processing failed: {str(e)}"}
        
        # Update document metadata
        document.title = content_data.get("title", document.title)
        document.author = content_data.get("author", document.author)
        document.metadata = content_data.get("metadata", {})
        
        # Chunk content
        chunks_data = chunker.chunk_content(
            content_data["content"],
            source_type=document.source_type,
            metadata=content_data.get("metadata", {})
        )
        
        # Generate embeddings and save chunks
        for i, chunk_data in enumerate(chunks_data):
            embedding = embedder.generate_embedding(chunk_data["content"])
            
            chunk = Chunk(
                document_id=document.id,
                content=chunk_data["content"],
                chunk_index=i,
                token_count=chunk_data.get("token_count"),
                embedding=embedding,
                metadata=chunk_data.get("metadata", {})
            )
            db.add(chunk)
        
        # Update document status
        document.processing_status = "completed"
        db.commit()
        
        return {"status": "completed", "chunks_created": len(chunks_data)}
        
    except Exception as e:
        # Update document status on error
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
        if document:
            document.processing_status = "failed"
            document.metadata = {"error": str(e)}
            db.commit()
        
        return {"error": str(e)}
    
    finally:
        db.close()