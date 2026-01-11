from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)
CORS(app)

# Try to load ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
print(f"🔍 ElevenLabs API key exists: {bool(ELEVENLABS_API_KEY)}")

# OpenRouter API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
print(f"🔍 OpenRouter API key exists: {bool(OPENAI_API_KEY)}")
print(f"🔍 OpenRouter base URL: {OPENAI_BASE_URL}")

# Remove Whisper loading code since we're using ElevenLabs API
WHISPER_AVAILABLE = False
print("🎵 Using ElevenLabs API for speech-to-text instead of local Whisper")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "second_brain_ai")

print(f"🔍 MONGODB_URL exists: {bool(MONGODB_URL)}")
print(f"🔍 DATABASE_NAME: {DATABASE_NAME}")

# Global MongoDB client
mongo_client = None
database = None
documents_collection = None

def get_db():
    """Get database connection"""
    global mongo_client, database, documents_collection
    
    if not mongo_client and MONGODB_URL:
        try:
            from pymongo import MongoClient
            
            print("🔄 Attempting MongoDB connection...")
            print(f"🔍 Connection string: {MONGODB_URL[:50]}...")  # Only show first 50 chars for security
            
            mongo_client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                maxPoolSize=10
            )
            
            # Test connection
            print("🔄 Testing MongoDB connection with ping...")
            mongo_client.admin.command('ping')
            
            database = mongo_client[DATABASE_NAME]
            documents_collection = database["documents"]
            
            print("✅ MongoDB connected successfully!")
            return documents_collection
            
        except Exception as e:
            print(f"❌ MongoDB connection error: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            return None
    elif not MONGODB_URL:
        print("❌ No MONGODB_URL environment variable found")
        return None
    
    return documents_collection

# Fallback sample data - will be updated with uploads
SAMPLE_DOCUMENTS = [
    {
        "id": "1",
        "title": "Machine Learning Fundamentals",
        "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. Key concepts include supervised learning, unsupervised learning, and reinforcement learning.",
        "source_type": "pdf",
        "source_path": "ml_fundamentals.pdf",
        "created_at": "2024-01-08T10:00:00Z",
        "processing_status": "completed",
        "file_size": 1024000,
        "chunk_count": 3
    }
]

# Global storage for uploaded documents (will persist during function lifetime)
uploaded_documents = []

@app.route('/')
def root():
    return jsonify({"message": "Second Brain AI API", "status": "healthy"})

@app.route('/test-db')
def test_db():
    try:
        collection = get_db()
        db_status = "connected" if collection is not None else "disconnected"
        
        return jsonify({
            "database": db_status,
            "mongodb_url_exists": bool(MONGODB_URL),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "database": "error",
            "error": str(e),
            "mongodb_url_exists": bool(MONGODB_URL),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/health')
def health():
    try:
        # Basic health check without MongoDB
        return jsonify({
            "status": "healthy",
            "mongodb_url_exists": bool(MONGODB_URL),
            "elevenlabs": "configured" if ELEVENLABS_API_KEY else "not_configured",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/documents')
def get_documents():
    collection = get_db()
    
    if collection is not None:
        try:
            print("📊 Querying MongoDB for documents...")
            # Get documents from MongoDB
            documents = []
            cursor = collection.find().sort("created_at", -1)
            
            for doc in cursor:
                doc_dict = {
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "source_type": doc["source_type"],
                    "source_path": doc["source_path"],
                    "created_at": doc["created_at"] if isinstance(doc["created_at"], str) else doc["created_at"].isoformat() + "Z",
                    "processing_status": doc["processing_status"],
                    "file_size": doc["file_size"],
                    "chunk_count": doc["chunk_count"]
                }
                documents.append(doc_dict)
            
            print(f"📊 Found {len(documents)} documents in MongoDB")
            
            # If no documents, add sample data
            if not documents:
                print("📊 No documents found, adding sample data...")
                for sample_doc in SAMPLE_DOCUMENTS:
                    sample_doc_copy = sample_doc.copy()
                    sample_doc_copy["created_at"] = datetime.fromisoformat(sample_doc["created_at"].replace("Z", ""))
                    collection.insert_one(sample_doc_copy)
                    print(f"✅ Added sample document: {sample_doc['title']}")
                documents = SAMPLE_DOCUMENTS
            
            return jsonify({
                "documents": documents,
                "total": len(documents),
                "page": 1,
                "limit": 20,
                "has_next": False,
                "source": "mongodb"
            })
            
        except Exception as e:
            print(f"❌ MongoDB query error: {e}")
            # Fallback to sample data + uploaded documents
            all_documents = SAMPLE_DOCUMENTS + uploaded_documents
            return jsonify({
                "documents": all_documents,
                "total": len(all_documents),
                "page": 1,
                "limit": 20,
                "has_next": False,
                "source": "fallback_with_uploads"
            })
    else:
        print("📊 No MongoDB connection, using sample data + uploaded documents")
        # No MongoDB connection, use sample data + uploaded documents
        all_documents = SAMPLE_DOCUMENTS + uploaded_documents
        return jsonify({
            "documents": all_documents,
            "total": len(all_documents),
            "page": 1,
            "limit": 20,
            "has_next": False,
            "source": "sample_with_uploads"
        })

def transcribe_audio_elevenlabs(audio_content, filename):
    """Transcribe audio using ElevenLabs Speech-to-Text API"""
    if not ELEVENLABS_API_KEY:
        return f"[AUDIO FILE: {filename}]\n\nElevenLabs API key not configured.\nFile size: {len(audio_content)} bytes\n\n[Audio transcription requires ElevenLabs API key]"
    
    try:
        import requests
        import tempfile
        import os
        
        # Save audio to temp file
        file_extension = filename.split('.')[-1].lower() if '.' in filename else 'mp3'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # ElevenLabs Speech-to-Text API endpoint
            url = "https://api.elevenlabs.io/v1/speech-to-text"
            
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            print(f"🔄 Transcribing {filename} with ElevenLabs API...")
            print(f"🔍 File size: {len(audio_content)} bytes")
            print(f"🔍 File extension: {file_extension}")
            print(f"🔍 Temp file path: {temp_file_path}")
            
            # Prepare the multipart form data - don't specify content type, let requests handle it
            with open(temp_file_path, 'rb') as audio_file:
                files = {
                    "file": (filename, audio_file.read(), f"audio/{file_extension}")
                }
                
                data = {
                    "model_id": "scribe_v2"
                }
                
                print(f"🔍 Sending request to ElevenLabs...")
                response = requests.post(url, headers=headers, files=files, data=data)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            print(f"🔍 ElevenLabs API response status: {response.status_code}")
            print(f"🔍 ElevenLabs API response: {response.text[:500]}...")
            
            if response.status_code == 200:
                result = response.json()
                transcript_text = result.get("text", "").strip()
                
                if transcript_text:
                    return f"[AUDIO TRANSCRIPTION from {filename}]\n\nTranscribed Text:\n{transcript_text}\n\n[Transcription completed using ElevenLabs API]\n[Original file: {filename}]\n[File size: {len(audio_content)} bytes]"
                else:
                    return f"[AUDIO FILE: {filename}]\n\nNo speech detected in audio.\n\nFile size: {len(audio_content)} bytes"
            else:
                error_msg = response.text
                return f"[AUDIO FILE: {filename}]\n\nElevenLabs API error ({response.status_code}): {error_msg}\n\nFile size: {len(audio_content)} bytes"
                
        except Exception as api_error:
            # Clean up temp file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return f"[AUDIO FILE: {filename}]\n\nElevenLabs API transcription failed: {str(api_error)}\n\nFile size: {len(audio_content)} bytes"
            
    except Exception as e:
        return f"[AUDIO FILE: {filename}]\n\nAudio processing error: {str(e)}\n\nFile size: {len(audio_content)} bytes"

def generate_ai_response(query, context_docs):
    """Generate AI response using OpenRouter API"""
    if not OPENAI_API_KEY:
        return f"I found relevant information about '{query}' in your documents, but AI response generation is not configured. Please set up the OpenRouter API key."
    
    if not context_docs:
        return f"I don't have any information about '{query}' in your knowledge base. Please upload relevant documents first."
    
    # Build context from user's documents
    context = "Context from your knowledge base:\n\n"
    for i, doc_info in enumerate(context_docs[:2], 1):  # Limit to top 2 documents
        doc = doc_info['doc']
        context += f"[{i}] {doc['title']} ({doc['source_type'].upper()})\n{doc['content'][:800]}{'...' if len(doc['content']) > 800 else ''}\n\n"
    
    # Create messages for document-based response
    messages = [
        {
            "role": "system",
            "content": """You are a helpful AI assistant that acts as a "second brain" for the user. You have access to their personal knowledge base.

Your role is to:
1. Answer questions based on the provided context from their documents
2. Synthesize information from multiple sources when available
3. Be conversational and helpful
4. Reference specific sources when providing information
5. Keep responses concise but comprehensive (2-3 paragraphs max)

Guidelines:
- Always base answers on the provided context
- Mention source documents when referencing information
- Be direct and specific in your answers
- Use a friendly, conversational tone
- If the context doesn't fully answer the question, say so"""
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
        
        print(f"🤖 Generating AI response for query: '{query}'")
        print(f"🔍 Using API key: {OPENAI_API_KEY[:20]}..." if OPENAI_API_KEY else "❌ No API key found")
        print(f"🔍 Using base URL: {OPENAI_BASE_URL}")
        
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"🔍 OpenRouter response status: {response.status_code}")
        print(f"🔍 OpenRouter response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            print(f"✅ AI response generated successfully")
            return ai_response
        else:
            print(f"❌ OpenRouter API error: {response.status_code}")
            print(f"❌ Error response body: {response.text}")
            # Fallback response
            doc_titles = [doc_info['doc']['title'] for doc_info in context_docs]
            return f"I found relevant information in your documents: {', '.join(doc_titles)}. However, I'm having trouble generating a response right now. Please check the source documents directly for details about '{query}'."
        
    except Exception as e:
        print(f"❌ AI response generation error: {e}")
        # Fallback response
        doc_titles = [doc_info['doc']['title'] for doc_info in context_docs]
        return f"I found relevant information in your documents: {', '.join(doc_titles)}. However, I'm having trouble generating a response right now. Please try again or check the source documents directly."

@app.route('/api/v1/documents/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Read file content
        content = file.read()
        
        # Determine file type and process content
        filename = file.filename.lower()
        if filename.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.aiff', '.aif')):
            # Audio file - try to transcribe with ElevenLabs API
            text_content = transcribe_audio_elevenlabs(content, file.filename)
            source_type = "audio"
        elif filename.endswith('.txt'):
            text_content = content.decode('utf-8')
            source_type = "text"
        elif filename.endswith('.md'):
            text_content = content.decode('utf-8')
            source_type = "text"
        elif filename.endswith('.pdf'):
            text_content = f"PDF content from {file.filename}. In a full implementation, this would contain the extracted text from the PDF file."
            source_type = "pdf"
        else:
            text_content = f"Content from {file.filename}. File type: {file.content_type or 'unknown'}"
            source_type = "document"
        
        collection = get_db()
        
        if collection is not None:
            # Get next ID from MongoDB
            doc_count = collection.count_documents({})
            doc_id = str(doc_count + 1)
        else:
            # Fallback ID
            doc_id = str(int(datetime.now().timestamp()))
        
        # Create new document
        new_doc = {
            "id": doc_id,
            "title": file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename,
            "content": text_content,
            "source_type": source_type,
            "source_path": file.filename,
            "created_at": datetime.now(),
            "processing_status": "completed",
            "file_size": len(content),
            "chunk_count": max(1, len(text_content) // 500)
        }
        
        if collection is not None:
            # Save to MongoDB
            collection.insert_one(new_doc.copy())
            print(f"✅ Document saved to MongoDB: {file.filename}")
        else:
            # Save to uploaded_documents list for this session
            uploaded_documents.append(new_doc.copy())
            print(f"✅ Document saved to memory: {file.filename}")
        
        # Convert datetime for JSON response
        response_doc = new_doc.copy()
        response_doc["created_at"] = new_doc["created_at"].isoformat() + "Z"
        
        return jsonify({
            "success": True,
            "document": response_doc,
            "message": f"Successfully uploaded {file.filename}",
            "saved_to": "mongodb" if collection is not None else "memory",
            "speech_to_text": "elevenlabs_api" if ELEVENLABS_API_KEY else "unavailable"
        })
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        collection = get_db()
        
        if collection is not None:
            # Delete from MongoDB
            result = collection.delete_one({"id": document_id})
            
            if result.deleted_count == 1:
                return jsonify({
                    "success": True,
                    "message": f"Document deleted successfully",
                    "deleted_document_id": document_id
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Document not found"
                }), 404
        else:
            return jsonify({
                "success": False,
                "error": "Database not available"
            }), 503
            
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/documents/<document_id>/download')
def download_document(document_id):
    try:
        collection = get_db()
        doc = None
        
        if collection is not None:
            # Find in MongoDB
            doc = collection.find_one({"id": document_id})
        
        if not doc:
            # Fallback to sample data
            for sample_doc in SAMPLE_DOCUMENTS:
                if sample_doc['id'] == document_id:
                    doc = sample_doc
                    break
        
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        
        # Create downloadable content
        content = doc['content']
        filename = f"{doc['title']}.txt"
        
        from flask import Response
        return Response(
            content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/query', methods=['POST'])
def submit_query():
    data = request.get_json()
    query = data.get('query', '') if data else ''
    
    collection = get_db()
    documents = []
    
    if collection is not None:
        try:
            # Get documents from MongoDB
            cursor = collection.find()
            for doc in cursor:
                documents.append(doc)
        except Exception as e:
            print(f"❌ Query error: {e}")
            documents = SAMPLE_DOCUMENTS
    else:
        documents = SAMPLE_DOCUMENTS
    
    print(f"🔍 Query: '{query}'")
    print(f"📊 Total documents to search: {len(documents)}")
    
    # Improved search algorithm
    relevant_docs = []
    query_lower = query.lower()
    query_words = [word.strip('.,!?;:') for word in query_lower.split() if len(word) > 2]
    
    # Remove common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'what', 'about', 'when', 'where', 'some', 'more', 'very', 'into', 'just', 'only', 'over', 'also', 'back', 'after', 'first', 'well', 'year', 'work', 'such', 'make', 'even', 'most', 'take', 'than', 'many', 'come', 'could', 'should', 'does'}
    
    meaningful_words = [word for word in query_words if word not in stop_words and len(word) >= 3]
    print(f"🔍 Meaningful query words: {meaningful_words}")
    
    if not meaningful_words:
        print("❌ No meaningful words found in query")
        return jsonify({
            "conversation_id": str(int(datetime.now().timestamp() * 1000)),
            "response": f"I couldn't find any meaningful search terms in your query: '{query}'. Please try asking about specific topics in your documents.",
            "sources": [],
            "response_time_ms": 100,
            "created_at": datetime.now().isoformat() + "Z"
        })
    
    # Score each document
    for doc in documents:
        content_lower = doc['content'].lower()
        title_lower = doc['title'].lower()
        
        # Calculate match score
        title_matches = 0
        content_matches = 0
        total_word_count = 0
        
        for word in meaningful_words:
            title_count = title_lower.count(word)
            content_count = content_lower.count(word)
            
            if title_count > 0:
                title_matches += title_count
            if content_count > 0:
                content_matches += content_count
                
            total_word_count += title_count + content_count
        
        # Calculate relevance score
        matched_words = sum(1 for word in meaningful_words if word in content_lower or word in title_lower)
        word_coverage = matched_words / len(meaningful_words) if meaningful_words else 0
        
        # Boost score for title matches and require at least some word coverage
        relevance_score = 0
        if word_coverage > 0:
            relevance_score = word_coverage * 0.7  # Base score from word coverage
            relevance_score += (title_matches * 0.3)  # Bonus for title matches
            relevance_score += min(total_word_count * 0.1, 0.3)  # Bonus for frequency, capped
        
        if relevance_score > 0.3:  # Only include documents with decent relevance
            relevant_docs.append({
                'doc': doc,
                'score': relevance_score,
                'matched_words': matched_words,
                'word_coverage': word_coverage,
                'title_matches': title_matches,
                'content_matches': content_matches
            })
            print(f"📄 '{doc['title']}': score={relevance_score:.3f}, coverage={word_coverage:.2f}, title_matches={title_matches}, content_matches={content_matches}")
    
    # Sort by relevance score
    relevant_docs.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"✅ Found {len(relevant_docs)} relevant documents")
    
    # Use the best relevant document or fallback
    if relevant_docs:
        print(f"✅ Using {len(relevant_docs)} relevant documents for AI response")
        
        # Generate AI response using the relevant documents
        response_text = generate_ai_response(query, relevant_docs)
        
        # Use the best match for sources
        best_match = relevant_docs[0]
        source_doc = best_match['doc']
        
        print(f"✅ Best match: '{source_doc['title']}' with score {best_match['score']:.3f}")
    else:
        print("❌ No relevant documents found")
        available_docs = [doc['title'] for doc in documents[:3]]
        response_text = f"I couldn't find specific information about '{query}' in your documents. Your knowledge base contains: {', '.join(available_docs)}. Try asking about these topics or upload more relevant documents."
        source_doc = None
    
    sources = []
    if relevant_docs:
        # Include top relevant documents as sources
        for doc_info in relevant_docs[:2]:  # Top 2 sources
            doc = doc_info['doc']
            sources.append({
                "document_id": doc["id"],
                "chunk_id": f"{doc['id']}-chunk-1",
                "title": doc["title"],
                "excerpt": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "relevance_score": doc_info['score'],
                "source_type": doc["source_type"]
            })
    
    return jsonify({
        "conversation_id": str(int(datetime.now().timestamp() * 1000)),
        "response": response_text,
        "sources": sources,
        "response_time_ms": 1000,
        "created_at": datetime.now().isoformat() + "Z"
    })

if __name__ == '__main__':
    app.run(debug=True)