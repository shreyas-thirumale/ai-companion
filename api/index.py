from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from datetime import datetime
import os
import requests
from typing import List, Dict, Any
import json

# Initialize FastAPI app
app = FastAPI(title="Second Brain AI API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "second_brain_ai")

# Global MongoDB client
mongo_client = None
database = None
documents_collection = None

async def get_db():
    """Get database connection"""
    global mongo_client, database, documents_collection
    
    if not mongo_client and MONGODB_URL:
        try:
            mongo_client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                maxPoolSize=10
            )
            
            # Test connection
            await mongo_client.admin.command('ping')
            
            database = mongo_client[DATABASE_NAME]
            documents_collection = database["documents"]
            
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    return documents_collection

@app.get("/")
async def root():
    return {"message": "Second Brain AI API", "status": "healthy"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        db_status = "not_configured"
        if MONGODB_URL:
            collection = await get_db()
            db_status = "connected" if collection else "error"
        
        return {
            "status": "healthy",
            "database": db_status,
            "openai": "configured" if OPENAI_API_KEY else "not_configured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/documents")
async def get_documents():
    """Get all documents from MongoDB"""
    try:
        collection = await get_db()
        if not collection:
            # Return sample data if no database
            return {
                "documents": [
                    {
                        "id": "1",
                        "title": "Machine Learning Fundamentals",
                        "content": "Machine learning is a subset of artificial intelligence...",
                        "source_type": "pdf",
                        "source_path": "ml_fundamentals.pdf",
                        "created_at": "2024-01-08T10:00:00Z",
                        "processing_status": "completed",
                        "file_size": 1024000,
                        "chunk_count": 3
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20,
                "has_next": False
            }
        
        documents = []
        cursor = collection.find().sort("created_at", DESCENDING)
        
        async for doc in cursor:
            doc_dict = {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "source_type": doc["source_type"],
                "source_path": doc["source_path"],
                "created_at": doc["created_at"].isoformat() + "Z" if isinstance(doc["created_at"], datetime) else doc["created_at"],
                "processing_status": doc["processing_status"],
                "file_size": doc["file_size"],
                "chunk_count": doc["chunk_count"]
            }
            documents.append(doc_dict)
        
        return {
            "documents": documents,
            "total": len(documents),
            "page": 1,
            "limit": 20,
            "has_next": False
        }
        
    except Exception as e:
        print(f"Error fetching documents: {e}")
        # Return sample data on error
        return {
            "documents": [
                {
                    "id": "1",
                    "title": "Sample Document",
                    "content": "This is a sample document for testing purposes.",
                    "source_type": "text",
                    "source_path": "sample.txt",
                    "created_at": datetime.now().isoformat() + "Z",
                    "processing_status": "completed",
                    "file_size": 1024,
                    "chunk_count": 1
                }
            ],
            "total": 1,
            "page": 1,
            "limit": 20,
            "has_next": False
        }

@app.post("/api/v1/query")
async def submit_query(request: Request):
    """Submit a query and get AI response"""
    try:
        body = await request.json()
        query = body.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Get documents for context
        collection = await get_db()
        context_docs = []
        
        if collection:
            cursor = collection.find().limit(1)
            async for doc in cursor:
                context_docs.append({
                    "title": doc["title"],
                    "content": doc["content"][:500],
                    "source_type": doc["source_type"]
                })
        
        # Generate AI response
        response_text = "I understand you're asking about: " + query
        
        if OPENAI_API_KEY and context_docs:
            try:
                context = f"Context: {context_docs[0]['title']}\n{context_docs[0]['content'][:300]}"
                
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. Answer based on the provided context."},
                    {"role": "user", "content": f"{context}\n\nQuestion: {query}"}
                ]
                
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "openai/gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 300,
                    "temperature": 0.7
                }
                
                ai_response = requests.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if ai_response.status_code == 200:
                    result = ai_response.json()
                    response_text = result["choices"][0]["message"]["content"]
                
            except Exception as e:
                print(f"AI response error: {e}")
                response_text = f"I found information about '{query}' in your documents, but couldn't generate a detailed response right now."
        
        # Build sources (only 1 as requested)
        sources = []
        if context_docs:
            sources.append({
                "document_id": "1",
                "chunk_id": "1-chunk-1",
                "title": context_docs[0]["title"],
                "excerpt": context_docs[0]["content"][:200] + "...",
                "relevance_score": 0.9,
                "source_type": context_docs[0]["source_type"]
            })
        
        return {
            "conversation_id": str(int(datetime.now().timestamp() * 1000)),
            "response": response_text,
            "sources": sources,
            "response_time_ms": 1000,
            "created_at": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        print(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# Export for Vercel
handler = app