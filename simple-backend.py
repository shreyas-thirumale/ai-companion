#!/usr/bin/env python3
"""
Second Brain AI Companion Backend with MongoDB Integration
Features: Audio transcription, document storage, intelligent search
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import whisper
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import tempfile
import os
import logging
import re
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

# Load Whisper model (using base model for balance of speed and accuracy)
logger = logging.getLogger(__name__)
print("🎵 Loading Whisper model for audio transcription...")
try:
    import whisper
    whisper_model = whisper.load_model("base")
    print("✅ Whisper model loaded successfully!")
    WHISPER_AVAILABLE = True
except ImportError:
    print("⚠️ Whisper not available - audio transcription disabled")
    whisper_model = None
    WHISPER_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Whisper loading failed: {e} - audio transcription disabled")
    whisper_model = None
    WHISPER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure OpenAI/OpenRouter from environment
import requests
import json

# OpenRouter configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "second_brain_ai")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is required")

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB Configuration from environment
DOCUMENTS_COLLECTION = "documents"
CONVERSATIONS_COLLECTION = "conversations"

# Global MongoDB client
mongo_client = None
database = None
documents_collection = None
conversations_collection = None

# Global MongoDB client
mongo_client = None
database = None
documents_collection = None
conversations_collection = None

app = FastAPI(title="Second Brain AI Companion", version="1.0.0")

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware with environment configuration
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
    
    try:
        print("🌐 Connecting to MongoDB Atlas...")
        
        # For Atlas, we need to specify additional options
        mongo_client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,         # 10 second connection timeout
            maxPoolSize=10                  # Connection pool size
        )
        
        # Test connection
        await mongo_client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Initialize database and collections
        database = mongo_client[DATABASE_NAME]
        documents_collection = database[DOCUMENTS_COLLECTION]
        conversations_collection = database[CONVERSATIONS_COLLECTION]
        
        # Create text indexes for better search
        try:
            await documents_collection.create_index([
                ("title", TEXT),
                ("content", TEXT)
            ])
            print("✅ Text indexes created successfully!")
        except Exception as e:
            print(f"ℹ️ Text indexes may already exist: {e}")
        
        # Create other useful indexes
        try:
            await documents_collection.create_index("created_at")
            await documents_collection.create_index("source_type")
            print("✅ Additional indexes created successfully!")
        except Exception as e:
            print(f"ℹ️ Additional indexes may already exist: {e}")
        
        # Initialize with sample data if collection is empty
        doc_count = await documents_collection.count_documents({})
        if doc_count == 0:
            await initialize_sample_data()
        else:
            print(f"ℹ️ Found {doc_count} existing documents in Atlas")
            # Update existing documents with embeddings if they don't have them
            await update_existing_embeddings()
            
    except Exception as e:
        print(f"❌ MongoDB Atlas connection failed: {e}")
        print("💡 Please check your Atlas connection string and network access")
        print("💡 Make sure your IP is whitelisted in Atlas Network Access")
        raise

async def initialize_sample_data():
    """Initialize with sample documents"""
    print("📝 Initializing sample documents...")
    
    sample_docs = [
        {
            "id": "1",
            "title": "Machine Learning Fundamentals",
            "content": """Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.

Key concepts include:
- Supervised learning: Learning from labeled examples
- Unsupervised learning: Finding patterns in unlabeled data
- Reinforcement learning: Learning through trial and error

Popular algorithms include linear regression, decision trees, neural networks, and support vector machines. The field has applications in computer vision, natural language processing, and predictive analytics.""",
            "source_type": "pdf",
            "source_path": "ml_fundamentals.pdf",
            "created_at": datetime.fromisoformat("2024-01-08T10:00:00"),
            "processing_status": "completed",
            "file_size": 1024000,
            "chunk_count": 3
        }
    ]
    
    # Generate embeddings for sample documents
    for doc in sample_docs:
        print(f"🧠 Generating embedding for: {doc['title']}")
        doc["embedding"] = await generate_embedding(doc["content"])
    
    await documents_collection.insert_many(sample_docs)
    print("✅ Sample documents initialized with embeddings!")

async def update_existing_embeddings():
    """Generate embeddings for existing documents that don't have them"""
    print("🔄 Checking for documents without embeddings...")
    
    cursor = documents_collection.find({"embedding": {"$exists": False}})
    updated_count = 0
    
    async for doc in cursor:
        print(f"🧠 Generating embedding for existing document: {doc['title']}")
        embedding = await generate_embedding(doc["content"])
        
        if embedding:
            await documents_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"embedding": embedding}}
            )
            updated_count += 1
    
    if updated_count > 0:
        print(f"✅ Updated {updated_count} documents with embeddings!")
    else:
        print("ℹ️ All documents already have embeddings")

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    if mongo_client:
        mongo_client.close()
        print("🔌 MongoDB connection closed")

async def validate_file_upload(file: UploadFile) -> Dict[str, Any]:
    """Validate uploaded file for security and size constraints"""
    
    # File size validation (50MB limit)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # File type validation
    allowed_extensions = {
        'text': ['.txt', '.md'],
        'pdf': ['.pdf'],
        'audio': ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.aiff', '.aif']
    }
    
    file_extension = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    is_allowed = False
    file_category = 'unknown'
    for category, extensions in allowed_extensions.items():
        if file_extension in extensions:
            is_allowed = True
            file_category = category
            break
    
    if not is_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join([ext for exts in allowed_extensions.values() for ext in exts])}"
        )
    
    # Basic content validation
    if not file.filename or len(file.filename.strip()) == 0:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    return {
        "content": content,
        "size": len(content),
        "category": file_category,
        "extension": file_extension
    }

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenRouter API with direct HTTP requests"""
    try:
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for embedding generation")
            return []
        
        # Truncate text if too long
        if len(text) > 8000:
            text = text[:8000]
            logger.warning("Text truncated for embedding generation")
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "text-embedding-ada-002",
            "input": text
        }
        
        response = requests.post(
            f"{OPENAI_BASE_URL}/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            embedding = result["data"][0]["embedding"]
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
        else:
            logger.error(f"Embedding API error: {response.status_code} - {response.text}")
            return []
        
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return []

def extract_temporal_expressions(query: str) -> Dict[str, Any]:
    """Extract temporal expressions from natural language query"""
    
    temporal_patterns = {
        # Relative time expressions
        r'last week': {'days': -7, 'type': 'relative_week'},
        r'this week': {'days': 0, 'type': 'current_week'},
        r'last month': {'months': -1, 'type': 'relative_month'},
        r'this month': {'months': 0, 'type': 'current_month'},
        r'yesterday': {'days': -1, 'type': 'relative_day'},
        r'today': {'days': 0, 'type': 'current_day'},
        r'last year': {'years': -1, 'type': 'relative_year'},
        
        # Specific time expressions
        r'in (\w+) (\d{4})': {'type': 'month_year'},
        r'on (\w+) (\d{1,2})': {'type': 'month_day'},
        r'before (.+)': {'type': 'before_context'},
        r'after (.+)': {'type': 'after_context'},
        r'during (.+)': {'type': 'during_context'},
    }
    
    found_expressions = []
    query_lower = query.lower()
    
    for pattern, config in temporal_patterns.items():
        matches = re.finditer(pattern, query_lower)
        for match in matches:
            found_expressions.append({
                'pattern': pattern,
                'match': match.group(),
                'config': config,
                'position': match.span()
            })
    
    return found_expressions

def resolve_temporal_expressions(temporal_expressions: List[Dict]) -> Dict[str, datetime]:
    """Convert temporal expressions to concrete date ranges"""
    
    now = datetime.now()
    date_range = {'start': None, 'end': None}
    
    for expr in temporal_expressions:
        config = expr['config']
        
        if config['type'] == 'relative_week':
            if config['days'] == -7:  # last week
                start_of_last_week = now - relativedelta(weeks=1)
                start_of_last_week = start_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0)
                start_of_last_week -= relativedelta(days=start_of_last_week.weekday())
                date_range['start'] = start_of_last_week
                date_range['end'] = start_of_last_week + relativedelta(days=6, hours=23, minutes=59, seconds=59)
                
        elif config['type'] == 'current_week':
            start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_week -= relativedelta(days=start_of_week.weekday())
            date_range['start'] = start_of_week
            date_range['end'] = now
            
        elif config['type'] == 'relative_month':
            if config['months'] == -1:  # last month
                start_of_last_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_of_last_month -= relativedelta(months=1)
                end_of_last_month = start_of_last_month + relativedelta(months=1) - relativedelta(seconds=1)
                date_range['start'] = start_of_last_month
                date_range['end'] = end_of_last_month
                
        elif config['type'] == 'current_month':
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_range['start'] = start_of_month
            date_range['end'] = now
            
        elif config['type'] == 'relative_day':
            if config['days'] == -1:  # yesterday
                yesterday = now - relativedelta(days=1)
                date_range['start'] = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                date_range['end'] = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                
        elif config['type'] == 'current_day':
            date_range['start'] = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_range['end'] = now
    
    return date_range

def calculate_temporal_relevance(doc_created_at: datetime, temporal_context: Dict) -> float:
    """Calculate temporal relevance score based on document creation time and query context"""
    
    if not temporal_context.get('start') or not temporal_context.get('end'):
        return 0.5  # Neutral score if no temporal context
    
    # Check if document falls within the temporal range
    if temporal_context['start'] <= doc_created_at <= temporal_context['end']:
        # Document is within the requested time range - high relevance
        range_duration = (temporal_context['end'] - temporal_context['start']).total_seconds()
        doc_position = (doc_created_at - temporal_context['start']).total_seconds()
        
        # Score based on position within range (more recent = higher score)
        position_score = 1.0 - (doc_position / range_duration) * 0.3
        return min(1.0, position_score)
    else:
        # Document is outside the range - calculate proximity penalty
        if doc_created_at < temporal_context['start']:
            time_diff = (temporal_context['start'] - doc_created_at).total_seconds()
        else:
            time_diff = (doc_created_at - temporal_context['end']).total_seconds()
        
        # Exponential decay based on time difference (30-day half-life)
        import math
        proximity_score = 0.5 * math.exp(-time_diff / (30 * 24 * 3600))
        return max(0.1, proximity_score)  # Minimum score of 0.1
    """Generate embedding using OpenAI API"""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation error: {e}")
        return []

async def search_documents(query: str) -> List[Dict[str, Any]]:
    """Ultra-strict search with zero tolerance for irrelevant matches"""
    
    try:
        search_results = []
        
        # Extract temporal expressions from query
        temporal_expressions = extract_temporal_expressions(query)
        temporal_context = {}
        
        if temporal_expressions:
            temporal_context = resolve_temporal_expressions(temporal_expressions)
            logger.info(f"🕒 Temporal context detected: {temporal_context}")
        
        # Generate query embedding for semantic search
        logger.debug(f"🔍 Generating query embedding...")
        query_embedding = await generate_embedding(query)
        
        # Prepare query for better matching - ULTRA STRICT WORD FILTERING
        query_lower = query.lower().strip()
        query_words = [word.strip('.,!?;:') for word in query_lower.split() if len(word) > 2]
        
        # ULTRA-STRICT stop words - much more comprehensive
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use',
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'what', 'about', 'when', 'where', 'some', 'more', 'very', 'into', 'just', 'only', 'over', 'also', 'back', 'after', 'first', 'well', 'year', 'work', 'such', 'make', 'even', 'most', 'take', 'than', 'many', 'come', 'could', 'should', 'through', 'being', 'before', 'here', 'between', 'both', 'under', 'again', 'while', 'last', 'might', 'great', 'little', 'still', 'public', 'read', 'know', 'never', 'may', 'another', 'same', 'any', 'these', 'give', 'most', 'us', 'like', 'good', 'want', 'look', 'think', 'find', 'right', 'long', 'much', 'need', 'part', 'place', 'tell', 'turn', 'call', 'move', 'live', 'seem', 'feel', 'try', 'ask', 'show', 'play', 'run', 'own', 'leave', 'point', 'help', 'keep', 'start', 'become', 'open', 'walk', 'talk', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'offer', 'remember', 'love', 'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill', 'remain'
        }
        
        # Extract meaningful query words with ULTRA-STRICT filtering
        meaningful_query_words = []
        for word in query_words:
            if (len(word) >= 4 and  # Minimum 4 characters (was 3)
                word not in stop_words and 
                not word.isdigit() and  # No pure numbers
                word.isalpha() and  # Only alphabetic words
                not word in ['that', 'this', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would', 'there', 'could', 'other']):  # Additional exclusions
                meaningful_query_words.append(word)
        
        logger.info(f"🔍 Query: '{query}' -> Meaningful words: {meaningful_query_words}")
        
        # If no meaningful words, return empty results
        if not meaningful_query_words:
            logger.info(f"❌ No meaningful words found in query '{query}' - returning empty results")
            return []
        
        # Get all documents for evaluation
        all_docs_query = {}
        if temporal_context.get('start') and temporal_context.get('end'):
            all_docs_query["created_at"] = {
                "$gte": temporal_context['start'],
                "$lte": temporal_context['end']
            }
            logger.info(f"🕒 Applied temporal filter: {temporal_context['start']} to {temporal_context['end']}")
        
        # Evaluate each document with ZERO TOLERANCE approach
        async for doc in documents_collection.find(all_docs_query):
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            
            # STEP 1: Check for exact phrase match (highest priority)
            exact_phrase_match = False
            if len(query_lower) > 6:  # Only for substantial queries
                if query_lower in content_lower or query_lower in title_lower:
                    exact_phrase_match = True
                    logger.info(f"✅ EXACT PHRASE MATCH: '{doc['title']}' contains '{query_lower}'")
            
            # STEP 2: Check word coverage - ULTRA STRICT
            matched_words = 0
            word_match_details = []
            
            for word in meaningful_query_words:
                if word in content_lower or word in title_lower:
                    matched_words += 1
                    content_count = content_lower.count(word)
                    title_count = title_lower.count(word)
                    word_match_details.append(f"{word}(c:{content_count},t:{title_count})")
            
            coverage_ratio = matched_words / len(meaningful_query_words) if meaningful_query_words else 0
            
            logger.debug(f"📊 Document '{doc['title']}': {matched_words}/{len(meaningful_query_words)} words matched ({coverage_ratio:.2f} coverage)")
            logger.debug(f"📝 Word matches: {word_match_details}")
            
            # STEP 3: ULTRA-STRICT DECISION LOGIC
            include_document = False
            relevance_score = 0.0
            
            if exact_phrase_match:
                # Exact phrase match = automatic inclusion with high score
                include_document = True
                relevance_score = 1.0  # 100%
                logger.info(f"✅ INCLUDED (exact phrase): '{doc['title']}' - 100% relevance")
                
            elif coverage_ratio >= 0.8:  # 80% or more words must match
                # High coverage = inclusion with good score
                include_document = True
                base_score = coverage_ratio * 0.7  # Max 70% for word coverage
                
                # Semantic similarity bonus (only for high coverage)
                semantic_score = 0
                if query_embedding and "embedding" in doc and doc["embedding"]:
                    doc_embedding = doc["embedding"]
                    dot_product = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                    magnitude_query = sum(a * a for a in query_embedding) ** 0.5
                    magnitude_doc = sum(a * a for a in doc_embedding) ** 0.5
                    
                    if magnitude_query > 0 and magnitude_doc > 0:
                        semantic_score = dot_product / (magnitude_query * magnitude_doc)
                
                # Only add semantic bonus if it's very high
                semantic_bonus = 0
                if semantic_score > 0.85:
                    semantic_bonus = 0.3  # Max 30% bonus
                elif semantic_score > 0.75:
                    semantic_bonus = 0.2  # 20% bonus
                elif semantic_score > 0.65:
                    semantic_bonus = 0.1  # 10% bonus
                
                relevance_score = min(base_score + semantic_bonus, 1.0)
                logger.info(f"✅ INCLUDED (high coverage): '{doc['title']}' - {relevance_score:.1%} relevance (coverage: {coverage_ratio:.2f}, semantic: {semantic_score:.3f})")
                
            else:
                # Low coverage = COMPLETE REJECTION
                include_document = False
                logger.debug(f"❌ REJECTED: '{doc['title']}' - coverage too low ({coverage_ratio:.2f})")
            
            # Add to results if included
            if include_document:
                search_results.append({
                    "document_id": doc["id"],
                    "chunk_id": f"{doc['id']}-chunk-1",
                    "title": doc["title"],
                    "content": doc["content"][:400] + "..." if len(doc["content"]) > 400 else doc["content"],
                    "relevance_score": relevance_score,
                    "source_type": doc["source_type"],
                    "created_at": doc["created_at"].isoformat() + "Z" if isinstance(doc["created_at"], datetime) else doc["created_at"],
                    "search_type": "ultra_strict_zero_tolerance",
                    "word_matches": matched_words,
                    "coverage_ratio": coverage_ratio,
                    "exact_phrase": exact_phrase_match,
                    "meaningful_words": len(meaningful_query_words)
                })
        
        # Sort by relevance score (descending)
        search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"✅ FINAL RESULTS: {len(search_results)} documents passed ultra-strict filtering")
        for result in search_results:
            logger.info(f"  - {result['title']}: {result['relevance_score']:.1%} relevance")
        
        # Return top results for AI processing
        return search_results[:3]
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
async def generate_openai_response(query: str, context_docs: List[Dict]) -> str:
    """Generate response using OpenRouter API with direct HTTP requests"""
    
    if not context_docs:
        return f"I don't have any information about '{query}' in your knowledge base. Your current documents contain information about machine learning, project management, and meeting notes. If you'd like me to help with questions about these topics or others, please upload relevant documents first."
    
    # Build context from user's documents
    context = "Context from your knowledge base:\n\n"
    for i, doc in enumerate(context_docs[:3], 1):
        context += f"[{i}] {doc['title']} ({doc['source_type'].upper()})\n{doc['content']}\n\n"
    
    # Create messages for document-based response
    messages = [
        {
            "role": "system",
            "content": """You are a helpful AI assistant that acts as a "second brain" for the user. You have access to their personal knowledge base.

Your role is to:
1. Answer questions based on the provided context from their documents
2. Synthesize information from multiple sources
3. Be conversational and helpful
4. Reference specific sources when providing information

Guidelines:
- Always base answers on the provided context
- Mention source documents when referencing information
- Be concise but comprehensive
- Use a friendly, conversational tone"""
        },
        {
            "role": "user", 
            "content": f"{context}\n\nQuestion: {query}"
        }
    ]
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "openai/gpt-4o-mini",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            # Return a response based on the documents we found, without OpenRouter
            doc_titles = [doc['title'] for doc in context_docs]
            return f"I found relevant information in your documents: {', '.join(doc_titles)}. However, I'm having trouble processing the response right now. Please try again or check the source documents directly."
        
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        # Return a response based on the documents we found, without OpenRouter
        doc_titles = [doc['title'] for doc in context_docs]
        return f"I found relevant information in your documents: {', '.join(doc_titles)}. However, I'm having trouble processing the response right now. Please try again or check the source documents directly."

# API Routes
@app.get("/")
async def root():
    return {"message": "Second Brain AI Companion API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health():
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        if mongo_client:
            await mongo_client.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        # Test OpenAI API (optional - might be expensive)
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
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}minute")
async def get_documents(request: Request):
    """Get all documents from MongoDB"""
    try:
        documents = []
        cursor = documents_collection.find().sort("created_at", DESCENDING)
        
        async for doc in cursor:
            # Convert MongoDB document to API format
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
        print(f"❌ Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

@app.post("/api/v1/documents/upload")
@limiter.limit(f"{RATE_LIMIT_REQUESTS//10}/{RATE_LIMIT_WINDOW}minute")  # Stricter limit for uploads
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload a document to MongoDB (supports text, PDF, and audio files)"""
    
    try:
        # Validate file upload
        validation_result = await validate_file_upload(file)
        content = validation_result["content"]
        file_category = validation_result["category"]
        
        logger.info(f"Processing {file_category} file: {file.filename} ({validation_result['size']} bytes)")
        
        # Read file content (already done in validation)
        # content = await file.read()  # Already done in validation
        
        # Determine file type and process accordingly
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        audio_extensions = ['mp3', 'wav', 'm4a', 'ogg', 'flac', 'aac', 'aiff', 'aif']
        
        if file_extension in audio_extensions:
            # Process audio file with transcription
            text_content = await transcribe_audio(content, file.filename, file.content_type)
            source_type = "audio"
        elif file.content_type == "text/plain" or file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
            source_type = "text"
        elif file.filename.endswith('.md'):
            text_content = content.decode('utf-8')
            source_type = "text"
        else:
            # For other file types, we'll create a placeholder
            text_content = f"Content from uploaded file: {file.filename}. This is a demo - in the full system, this would contain the actual extracted text from your {file.content_type or 'unknown'} file.\n\nFile size: {len(content)} bytes\nFile type: {file.content_type or 'unknown'}"
            source_type = "pdf"
        
        # Generate unique ID
        doc_count = await documents_collection.count_documents({})
        doc_id = str(doc_count + 1)
        
        # Generate embedding for semantic search
        print(f"🧠 Generating embedding for semantic search...")
        embedding = await generate_embedding(text_content)
        
        # Create new document for MongoDB
        new_doc = {
            "id": doc_id,
            "title": file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename,
            "content": text_content,
            "embedding": embedding,  # Store embedding for semantic search
            "source_type": source_type,
            "source_path": file.filename,
            "created_at": datetime.now(),
            "processing_status": "completed",
            "file_size": len(content),
            "chunk_count": max(1, len(text_content) // 500)  # Rough estimate
        }
        
        # Insert into MongoDB
        result = await documents_collection.insert_one(new_doc)
        
        if result.inserted_id:
            logger.info(f"✅ Uploaded {source_type} document to MongoDB: {file.filename} ({len(content)} bytes)")
            
            # Convert datetime for JSON response and remove MongoDB ObjectId
            response_doc = new_doc.copy()
            response_doc["created_at"] = new_doc["created_at"].isoformat() + "Z"
            # Remove the MongoDB _id field that gets added automatically
            if "_id" in response_doc:
                del response_doc["_id"]
            
            return {
                "success": True,
                "document": response_doc,
                "message": f"Successfully uploaded and processed {file.filename}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save document to database")
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def transcribe_audio(audio_content: bytes, filename: str, content_type: str) -> str:
    """Transcribe audio using local Whisper model"""
    
    if not WHISPER_AVAILABLE:
        return f"""[AUDIO FILE: {filename}]

Audio transcription is not available in this deployment.

File size: {len(audio_content)} bytes
Content type: {content_type}

[Audio transcription requires local Whisper installation]"""
    
    try:
        print(f"🎵 Starting transcription for: {filename}")
        
        # Save audio content to a temporary file
        import tempfile
        import os
        
        # Get file extension from filename
        file_extension = filename.split('.')[-1].lower() if '.' in filename else 'mp3'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using local Whisper model
            print(f"🔄 Transcribing audio with local Whisper...")
            result = whisper_model.transcribe(temp_file_path)
            transcript_text = result["text"].strip()
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if transcript_text:
                # Format the transcribed text with metadata
                transcribed_content = f"""[AUDIO TRANSCRIPTION from {filename}]

Transcribed Text:
{transcript_text}

[Transcription completed using local Whisper AI model]
[Original file: {filename}]
[File size: {len(audio_content)} bytes]
[Content type: {content_type}]"""
                
                print(f"✅ Successfully transcribed audio: {filename} ({len(transcript_text)} characters)")
                return transcribed_content
            else:
                print(f"⚠️ Empty transcription result for: {filename}")
                return f"""[AUDIO FILE: {filename}]

The audio file was processed but no speech was detected or the audio may be too quiet/unclear.

File size: {len(audio_content)} bytes
Content type: {content_type}

[No speech detected in audio]"""
                
        except Exception as whisper_error:
            # Clean up temp file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            print(f"❌ Whisper transcription error: {str(whisper_error)}")
            return f"""[AUDIO FILE: {filename}]

Audio transcription failed due to processing error: {str(whisper_error)}

This could be due to:
- Unsupported audio format (try MP3, WAV, or M4A)
- Corrupted audio file
- Audio file too long (Whisper works best with files under 25MB)

File size: {len(audio_content)} bytes
Content type: {content_type}

[Transcription failed - file stored but not processed]"""
            
    except Exception as e:
        print(f"❌ Audio transcription error: {str(e)}")
        return f"""[AUDIO FILE: {filename}]

This audio file was uploaded but could not be transcribed due to an error: {str(e)}

The file has been stored in your knowledge base, but without transcription it won't be searchable.

File size: {len(audio_content)} bytes
Content type: {content_type}

[Audio processing error - please try again or use a different audio format]"""

@app.post("/api/v1/query")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}minute")
async def submit_query(request: Request, request_data: dict):
    """Submit a query and get AI response using MongoDB search"""
    
    query = request_data.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    start_time = time.time()
    
    # Search documents using MongoDB
    search_results = await search_documents(query)
    
    # Generate AI response
    response_text = await generate_openai_response(query, search_results)
    
    response_time = int((time.time() - start_time) * 1000)
    
    # Save conversation to MongoDB
    conversation = {
        "id": str(int(time.time() * 1000)),  # Use timestamp as ID
        "query": query,
        "response": response_text,
        "created_at": datetime.now(),
        "response_time_ms": response_time
    }
    
    try:
        await conversations_collection.insert_one(conversation)
    except Exception as e:
        print(f"⚠️ Failed to save conversation: {e}")
    
    # Build sources for response - only include the single best match
    sources = []
    for result in search_results[:1]:  # Only take the first (best) result
        sources.append({
            "document_id": result["document_id"],
            "chunk_id": result["chunk_id"],
            "title": result["title"],
            "excerpt": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
            "relevance_score": result["relevance_score"],
            "source_type": result["source_type"]
        })
    
    return {
        "conversation_id": conversation["id"],
        "response": response_text,
        "sources": sources,
        "response_time_ms": response_time,
        "created_at": conversation["created_at"].isoformat() + "Z"
    }

@app.delete("/api/v1/documents/{document_id}")
@limiter.limit(f"{RATE_LIMIT_REQUESTS//5}/{RATE_LIMIT_WINDOW}minute")  # Stricter limit for deletes
async def delete_document(request: Request, document_id: str):
    """Delete a document from MongoDB"""
    
    try:
        logger.info(f"Attempting to delete document: {document_id}")
        
        # Check if document exists
        existing_doc = await documents_collection.find_one({"id": document_id})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the document
        result = await documents_collection.delete_one({"id": document_id})
        
        if result.deleted_count == 1:
            logger.info(f"✅ Successfully deleted document: {document_id}")
            return {
                "success": True,
                "message": f"Document '{existing_doc['title']}' deleted successfully",
                "deleted_document_id": document_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/api/v1/documents/{document_id}/download")
@limiter.limit(f"{RATE_LIMIT_REQUESTS//5}/{RATE_LIMIT_WINDOW}minute")  # Stricter limit for downloads
async def download_document(request: Request, document_id: str):
    """Download the original document file"""
    
    try:
        logger.info(f"Attempting to download document: {document_id}")
        
        # Find the document
        doc = await documents_collection.find_one({"id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get document details
        title = doc.get("title", "document")
        source_type = doc.get("source_type", "text")
        content = doc.get("content", "")
        
        # Determine file extension and content type based on source type
        if source_type == "audio":
            # For audio files, we can't recreate the original binary data
            # Instead, provide the transcription as a text file
            file_extension = "txt"
            content_type = "text/plain"
            filename = f"{title}_transcription.txt"
            file_content = content.encode('utf-8')
        elif source_type == "pdf":
            # For PDFs, we can't recreate the original PDF
            # Provide the extracted text as a text file
            file_extension = "txt"
            content_type = "text/plain"
            filename = f"{title}_extracted_text.txt"
            file_content = content.encode('utf-8')
        elif source_type == "text":
            # For text files, we can provide the original content
            file_extension = "txt"
            content_type = "text/plain"
            filename = f"{title}.txt"
            file_content = content.encode('utf-8')
        else:
            # Default to text
            file_extension = "txt"
            content_type = "text/plain"
            filename = f"{title}.txt"
            file_content = content.encode('utf-8')
        
        # Create response with proper headers for download
        from fastapi.responses import Response
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(file_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/v1/conversations")
async def get_conversations():
    """Get recent conversations from MongoDB"""
    try:
        conversations = []
        cursor = conversations_collection.find().sort("created_at", DESCENDING).limit(20)
        
        async for conv in cursor:
            conv_dict = {
                "id": conv["id"],
                "query": conv["query"],
                "response": conv["response"],
                "created_at": conv["created_at"].isoformat() + "Z" if isinstance(conv["created_at"], datetime) else conv["created_at"],
                "response_time_ms": conv.get("response_time_ms", 0)
            }
            conversations.append(conv_dict)
        
        return {
            "conversations": conversations,
            "total": len(conversations),
            "page": 1,
            "limit": 20
        }
    except Exception as e:
        print(f"❌ Error fetching conversations: {e}")
        return {"conversations": [], "total": 0, "page": 1, "limit": 20}

@app.get("/api/v1/analytics")
async def get_analytics():
    """Get analytics from MongoDB"""
    try:
        total_documents = await documents_collection.count_documents({})
        total_conversations = await conversations_collection.count_documents({})
        
        # Calculate total chunks and storage
        total_chunks = 0
        total_storage = 0
        
        async for doc in documents_collection.find():
            total_chunks += doc.get("chunk_count", 1)
            total_storage += doc.get("file_size", 0)
        
        # Calculate average response time
        avg_response_time = 0
        if total_conversations > 0:
            pipeline = [
                {"$group": {"_id": None, "avg_time": {"$avg": "$response_time_ms"}}}
            ]
            async for result in conversations_collection.aggregate(pipeline):
                avg_response_time = result.get("avg_time", 0)
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_queries": total_conversations,
            "avg_response_time_ms": avg_response_time,
            "storage_usage_mb": total_storage / (1024 * 1024),
            "popular_tags": [],
            "query_trends": []
        }
    except Exception as e:
        print(f"❌ Error fetching analytics: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "total_queries": 0,
            "avg_response_time_ms": 0,
            "storage_usage_mb": 0,
            "popular_tags": [],
            "query_trends": []
        }

if __name__ == "__main__":
    print("🧠 Starting Second Brain AI Companion Backend with MongoDB Atlas...")
    print("🔑 Using real OpenAI API via OpenRouter")
    print("🌐 MongoDB Atlas integration for cloud storage")
    print("📱 Frontend should connect to: http://localhost:8000")
    print("🔧 API Docs: http://localhost:8000/docs")
    print("")
    print("💡 Make sure to update MONGODB_URL with your Atlas connection string")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")