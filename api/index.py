#!/usr/bin/env python3
"""
Vercel serverless function for Second Brain AI Companion
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import json
import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import requests
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import tempfile
import logging
import re
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING

# Load environment variables
load_dotenv()

# Configure OpenAI/OpenRouter from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "second_brain_ai")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))

# Validate required environment variables
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found")
if not MONGODB_URL:
    print("WARNING: MONGODB_URL not found")

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB Configuration
DOCUMENTS_COLLECTION = "documents"
CONVERSATIONS_COLLECTION = "conversations"

# Global MongoDB client
mongo_client = None
database = None
documents_collection = None
conversations_collection = None

# Whisper availability
WHISPER_AVAILABLE = False

app = FastAPI(title="Second Brain AI Companion", version="1.0.0")

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def connect_to_mongo():
    """Initialize MongoDB Atlas connection"""
    global mongo_client, database, documents_collection, conversations_collection
    
    if not MONGODB_URL:
        logger.error("MongoDB URL not configured")
        return False
    
    try:
        logger.info("Connecting to MongoDB Atlas...")
        
        mongo_client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            maxPoolSize=10
        )
        
        # Test connection
        await mongo_client.admin.command('ping')
        logger.info("MongoDB Atlas connection successful!")
        
        # Initialize database and collections
        database = mongo_client[DATABASE_NAME]
        documents_collection = database[DOCUMENTS_COLLECTION]
        conversations_collection = database[CONVERSATIONS_COLLECTION]
        
        return True
        
    except Exception as e:
        logger.error(f"MongoDB Atlas connection failed: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.get("/")
async def root():
    return {"message": "Second Brain AI Companion API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Test database connection
        if mongo_client:
            await mongo_client.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        openai_status = "configured" if OPENAI_API_KEY else "not_configured"
        
        return {
            "status": "healthy",
            "database": db_status,
            "openai": openai_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/v1/documents")
async def get_documents(request: Request):
    """Get all documents from MongoDB"""
    try:
        if not documents_collection:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        documents = []
        cursor = documents_collection.find().sort("created_at", DESCENDING)
        
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
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

# Export the app for Vercel
handler = app