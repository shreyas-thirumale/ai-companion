# Second Brain AI Companion - System Architecture Diagram

```mermaid
graph TB
    %% User Interface Layer
    User[👤 User] --> Frontend[🌐 Frontend<br/>HTML + JavaScript<br/>TailwindCSS]
    
    %% Frontend Components
    Frontend --> Chat[💬 Chat Interface<br/>Real-time messaging<br/>Local storage]
    Frontend --> Upload[📤 Document Upload<br/>Drag & drop<br/>Multi-format support]
    Frontend --> DocList[📋 Document Manager<br/>View/Delete docs<br/>Search results]
    
    %% API Gateway
    Chat --> API[🚀 Flask API<br/>Vercel Serverless<br/>CORS enabled]
    Upload --> API
    DocList --> API
    
    %% Core API Endpoints
    API --> QueryEndpoint[🔍 /api/v1/query<br/>Natural language search]
    API --> UploadEndpoint[📁 /api/v1/documents/upload<br/>Multi-modal processing]
    API --> DocsEndpoint[📚 /api/v1/documents<br/>CRUD operations]
    API --> HealthEndpoint[❤️ /health<br/>System monitoring]
    
    %% Document Processing Pipeline
    UploadEndpoint --> FileValidation[✅ File Validation<br/>Size, type, format checks]
    FileValidation --> AudioProcessor[🎵 Audio Processing<br/>ElevenLabs API]
    FileValidation --> TextProcessor[📝 Text Processing<br/>UTF-8 decoding]
    FileValidation --> PDFProcessor[📄 PDF Processing<br/>Text extraction]
    
    %% External Services
    AudioProcessor --> ElevenLabs[🎙️ ElevenLabs<br/>Speech-to-Text API<br/>Whisper models]
    
    %% Search Engine
    QueryEndpoint --> SearchEngine[🔎 Hybrid Search Engine<br/>Semantic + Lexical + Temporal]
    SearchEngine --> FullTextSearch[📖 MongoDB Full-Text<br/>Stemming & relevance]
    SearchEngine --> SemanticSearch[🧠 Content Analysis<br/>Word matching & coverage]
    SearchEngine --> TemporalSearch[⏰ Temporal Filtering<br/>Natural language dates]
    
    %% Relevance Scoring
    FullTextSearch --> Scoring[📊 Advanced Scoring<br/>Phrase matching<br/>Coverage analysis<br/>Semantic boost]
    SemanticSearch --> Scoring
    TemporalSearch --> Scoring
    
    %% AI Response Generation
    Scoring --> LLMService[🤖 OpenRouter API<br/>GPT-4o-mini<br/>Context-aware responses]
    
    %% Database Layer
    UploadEndpoint --> MongoDB[(🍃 MongoDB Atlas<br/>Cloud Database<br/>Global distribution)]
    DocsEndpoint --> MongoDB
    SearchEngine --> MongoDB
    
    %% Database Collections
    MongoDB --> DocsCollection[📑 Documents Collection<br/>Content, metadata<br/>Full-text indexes]
    MongoDB --> ConversationsCollection[💭 Conversations<br/>Query history<br/>Response tracking]
    
    %% Data Storage Schema
    DocsCollection --> DocSchema[📋 Document Schema<br/>• id, title, content<br/>• source_type, file_size<br/>• created_at, processing_status]
    ConversationsCollection --> ConvSchema[💬 Conversation Schema<br/>• conversation_id, query<br/>• response, sources<br/>• created_at, response_time]
    
    %% Response Flow
    LLMService --> ResponseBuilder[🔧 Response Builder<br/>Source attribution<br/>Relevance scores]
    ResponseBuilder --> Frontend
    
    %% Environment & Configuration
    API --> EnvConfig[⚙️ Environment Config<br/>• MongoDB connection<br/>• API keys (OpenRouter, ElevenLabs)<br/>• CORS settings]
    
    %% Deployment Infrastructure
    Frontend -.-> Vercel[☁️ Vercel Platform<br/>Global CDN<br/>Automatic scaling]
    API -.-> Vercel
    MongoDB -.-> Atlas[🌍 MongoDB Atlas<br/>Multi-region<br/>Automatic backups]
    
    %% Styling
    classDef userLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef frontendLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef apiLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef processingLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef databaseLayer fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef infraLayer fill:#f5f5f5,stroke:#424242,stroke-width:2px
    
    class User userLayer
    class Frontend,Chat,Upload,DocList frontendLayer
    class API,QueryEndpoint,UploadEndpoint,DocsEndpoint,HealthEndpoint apiLayer
    class FileValidation,AudioProcessor,TextProcessor,PDFProcessor,SearchEngine,FullTextSearch,SemanticSearch,TemporalSearch,Scoring,ResponseBuilder processingLayer
    class ElevenLabs,LLMService externalLayer
    class MongoDB,DocsCollection,ConversationsCollection,DocSchema,ConvSchema databaseLayer
    class Vercel,Atlas,EnvConfig infraLayer
```

## Key Architecture Highlights

### 🏗️ **Serverless-First Design**
- Vercel deployment for automatic scaling
- Stateless API design for reliability
- Global edge distribution

### 🔄 **Multi-Modal Processing Pipeline**
- Audio → ElevenLabs Speech-to-Text
- Text → Direct processing
- PDF → Text extraction
- All formats → MongoDB storage

### 🔍 **Hybrid Search Engine**
- MongoDB full-text search
- Semantic content analysis
- Temporal query support
- Advanced relevance scoring

### 🎯 **Production-Ready Features**
- Health monitoring endpoints
- Comprehensive error handling
- Environment-based configuration
- Real-time user interface

### 📊 **Data Flow**
1. **Upload**: User → Frontend → API → Processing → MongoDB
2. **Query**: User → Frontend → API → Search → LLM → Response
3. **Retrieval**: MongoDB → Search Engine → Scoring → Results

This diagram captures the complete system architecture showing how all components work together to deliver intelligent knowledge management capabilities.