# Second Brain AI Companion - Project Structure

## Overview
This document outlines the project structure for the Second Brain AI companion system.

## Directory Structure
```
ai-companion/
├── docs/                          # System design documentation
│   ├── system-design.md          # Main system design document
│   ├── diagrams/                 # Architecture diagrams
│   └── api-specs/                # API specifications
├── backend/                       # Backend services
│   ├── src/
│   │   ├── ingestion/            # Data ingestion pipeline
│   │   ├── retrieval/            # Information retrieval system
│   │   ├── llm/                  # LLM integration
│   │   ├── api/                  # REST API endpoints
│   │   └── storage/              # Database models and connections
│   ├── requirements.txt          # Python dependencies
│   └── docker-compose.yml        # Local development setup
├── frontend/                      # React-based web interface
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── services/             # API client services
│   │   └── utils/                # Utility functions
│   ├── package.json
│   └── public/
├── tests/                         # Test files
├── scripts/                       # Deployment and utility scripts
└── README.md                      # Project documentation
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python) - for high-performance async API
- **Database**: PostgreSQL + pgvector for vector storage
- **Vector Search**: Sentence Transformers + FAISS/Chroma
- **LLM Integration**: OpenAI GPT-4 API
- **Task Queue**: Celery with Redis for async processing
- **File Processing**: 
  - Audio: Whisper API for transcription
  - Documents: PyPDF2, python-docx
  - Web: BeautifulSoup + requests

### Frontend
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query for server state
- **Real-time**: WebSocket for streaming responses

### Infrastructure
- **Containerization**: Docker
- **Deployment**: Railway/Render for quick deployment
- **Storage**: Local file system + cloud storage for production

## Key Design Decisions

1. **Hybrid Search Strategy**: Combine semantic (vector) and keyword (full-text) search
2. **Chunking Strategy**: Intelligent text chunking with overlap for context preservation
3. **Temporal Indexing**: Timestamp-based metadata for time-aware queries
4. **Modular Architecture**: Microservices-like structure for scalability