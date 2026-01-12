# Second Brain AI Companion

A personal knowledge management system that ingests multi-modal data and provides intelligent conversational access through natural language queries. Built as a comprehensive full-stack AI application demonstrating modern system architecture and implementation practices.

**Live Demo**: https://ai-companion-proj.vercel.app

## Overview

This system processes documents, audio files, and text content to create a searchable knowledge base with AI-powered query capabilities. Users can upload various file types and interact with their content through natural language conversations.

### Key Features

- **Multi-modal ingestion**: PDF, text, audio files with automatic transcription
- **Hybrid search**: Combines semantic similarity and keyword matching for optimal relevance
- **AI-powered responses**: Natural language answers synthesized from document content
- **Temporal queries**: Time-aware search ("what did I work on last week?")
- **Real-time interface**: Responsive chat UI with file management

## Architecture

### System Design

- **Frontend**: Single-page application with HTML/JavaScript and TailwindCSS
- **Backend**: Flask API deployed as serverless functions on Vercel
- **Database**: MongoDB Atlas for document storage and metadata
- **AI Services**: OpenRouter (GPT-4o-mini) for response generation, ElevenLabs for audio transcription
- **Search Engine**: Multi-signal hybrid approach with relevance scoring

### Technology Stack

**Backend:**
- Flask (Python) - REST API
- MongoDB Atlas - Document storage
- OpenRouter API - LLM integration
- ElevenLabs API - Speech-to-text transcription

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- TailwindCSS - Styling framework
- Responsive design with drag-and-drop file upload

**Deployment:**
- Vercel - Serverless hosting
- Environment-based configuration
- Production-ready error handling

## Quick Start

### Prerequisites

- OpenRouter API key
- ElevenLabs API key (optional, for audio transcription)
- MongoDB Atlas cluster

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-companion
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run locally**
   ```bash
   # Backend API
   python api/index.py
   
   # Frontend (serve index.html)
   python -m http.server 8080
   ```

### Deployment

The application is configured for Vercel deployment:

```bash
vercel --prod
```

Environment variables are managed through the Vercel dashboard.

## Project Structure

```
├── api/
│   └── index.py              # Flask API backend
├── frontend/                 # React/TypeScript alternative implementation
├── backend/                  # Structured FastAPI alternative
├── index.html               # Main frontend application
├── vercel.json              # Deployment configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── SYSTEM_DESIGN_FINAL.md  # Comprehensive architecture documentation
```

## Implementation Details

### Search Algorithm

The hybrid search engine combines multiple signals:

1. **Semantic matching**: Context-aware relevance through word coverage analysis
2. **Lexical search**: Exact phrase and keyword matching
3. **Temporal filtering**: Time-based query support with natural language parsing
4. **Relevance scoring**: Multi-factor scoring with configurable thresholds

### Data Processing Pipeline

1. **File validation**: Type checking and size limits
2. **Content extraction**: Format-specific processing (text, PDF, audio)
3. **Indexing**: Full-text search indexes with metadata
4. **Storage**: MongoDB with comprehensive document metadata

### API Design

RESTful endpoints with comprehensive error handling:

- `GET /api/v1/documents` - Document listing
- `POST /api/v1/documents/upload` - File upload and processing
- `POST /api/v1/query` - Natural language queries
- `DELETE /api/v1/documents/{id}` - Document management

## Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MONGODB_URL=your_mongodb_atlas_connection_string

# Optional
ELEVENLABS_API_KEY=your_elevenlabs_api_key
DATABASE_NAME=second_brain_ai
CORS_ORIGINS=*
```

### MongoDB Setup

1. Create MongoDB Atlas cluster
2. Configure network access (allow all IPs for demo: 0.0.0.0/0)
3. Create database user with read/write permissions
4. Update connection string in environment variables

## Performance Considerations

- **Serverless architecture**: Optimized for Vercel's execution environment
- **Connection pooling**: Efficient database connection management
- **Error handling**: Comprehensive fallback mechanisms
- **Rate limiting**: API protection and resource management

## Security

- **Environment variables**: Sensitive data stored securely
- **Input validation**: File type and size restrictions
- **Error handling**: No sensitive information in error responses
- **CORS configuration**: Controlled cross-origin access

## Documentation

- **System Design**: Comprehensive architecture documentation in `SYSTEM_DESIGN_FINAL.md`
- **API Documentation**: Inline code documentation and error handling
- **Deployment Guide**: Environment setup and configuration instructions

---

*Built as a demonstration of full-stack AI system architecture and implementation capabilities.*