# Architecture Diagrams

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Chat Interface]
        WS[WebSocket Client]
    end
    
    subgraph "API Layer"
        API[FastAPI Gateway]
        Auth[Authentication]
        Rate[Rate Limiting]
    end
    
    subgraph "Processing Layer"
        Ingest[Ingestion Pipeline]
        Retrieval[Retrieval Engine]
        LLM[LLM Service]
    end
    
    subgraph "Storage Layer"
        PG[(PostgreSQL + pgvector)]
        Redis[(Redis Cache)]
        Files[File Storage]
    end
    
    subgraph "External Services"
        OpenAI[OpenAI API]
        Whisper[Whisper API]
    end
    
    UI --> API
    WS --> API
    API --> Auth
    API --> Rate
    API --> Ingest
    API --> Retrieval
    API --> LLM
    
    Ingest --> PG
    Ingest --> Files
    Ingest --> Redis
    
    Retrieval --> PG
    Retrieval --> Redis
    
    LLM --> OpenAI
    Ingest --> Whisper
    
    style UI fill:#e1f5fe
    style API fill:#f3e5f5
    style PG fill:#e8f5e8
    style OpenAI fill:#fff3e0
```

## 2. Data Ingestion Pipeline

```mermaid
graph LR
    subgraph "Input Sources"
        Audio[Audio Files]
        Docs[Documents]
        Web[Web URLs]
        Text[Plain Text]
        Images[Images]
    end
    
    subgraph "Processing Pipeline"
        Queue[Task Queue]
        
        subgraph "Processors"
            AudioProc[Audio Processor<br/>Whisper API]
            DocProc[Document Processor<br/>PyPDF2, docx]
            WebProc[Web Scraper<br/>BeautifulSoup]
            TextProc[Text Processor<br/>NLP Pipeline]
            ImgProc[Image Processor<br/>OCR + Vision]
        end
        
        Chunker[Intelligent Chunker]
        Embedder[Embedding Generator]
    end
    
    subgraph "Storage"
        DB[(Database)]
        Vector[(Vector Index)]
        FileStore[File Storage]
    end
    
    Audio --> Queue
    Docs --> Queue
    Web --> Queue
    Text --> Queue
    Images --> Queue
    
    Queue --> AudioProc
    Queue --> DocProc
    Queue --> WebProc
    Queue --> TextProc
    Queue --> ImgProc
    
    AudioProc --> Chunker
    DocProc --> Chunker
    WebProc --> Chunker
    TextProc --> Chunker
    ImgProc --> Chunker
    
    Chunker --> Embedder
    Embedder --> DB
    Embedder --> Vector
    
    Audio --> FileStore
    Docs --> FileStore
    Images --> FileStore
    
    style Queue fill:#fff3e0
    style Chunker fill:#e8f5e8
    style Embedder fill:#e1f5fe
```

## 3. Hybrid Search Architecture

```mermaid
graph TB
    Query[User Query]
    
    subgraph "Query Processing"
        Parser[Query Parser]
        Intent[Intent Detection]
        Temporal[Temporal Extraction]
    end
    
    subgraph "Search Strategies"
        Semantic[Semantic Search<br/>Vector Similarity]
        Keyword[Keyword Search<br/>Full-text Search]
        Meta[Metadata Search<br/>Faceted Search]
        Time[Temporal Search<br/>Time-based Filtering]
    end
    
    subgraph "Result Processing"
        Fusion[Result Fusion<br/>RRF Algorithm]
        Ranking[Relevance Ranking]
        Context[Context Selection]
    end
    
    subgraph "Response Generation"
        LLM[LLM Service]
        Stream[Response Streaming]
    end
    
    Query --> Parser
    Parser --> Intent
    Parser --> Temporal
    
    Intent --> Semantic
    Intent --> Keyword
    Intent --> Meta
    Temporal --> Time
    
    Semantic --> Fusion
    Keyword --> Fusion
    Meta --> Fusion
    Time --> Fusion
    
    Fusion --> Ranking
    Ranking --> Context
    Context --> LLM
    LLM --> Stream
    
    style Parser fill:#e1f5fe
    style Fusion fill:#e8f5e8
    style LLM fill:#fff3e0
```

## 4. Database Schema Relationships

```mermaid
erDiagram
    DOCUMENTS ||--o{ CHUNKS : contains
    DOCUMENTS ||--o{ DOCUMENT_TAGS : has
    TAGS ||--o{ DOCUMENT_TAGS : tagged_with
    CHUNKS ||--o{ CONVERSATION_CHUNKS : referenced_in
    CONVERSATIONS ||--o{ CONVERSATION_CHUNKS : uses
    
    DOCUMENTS {
        uuid id PK
        text source_path
        varchar source_type
        text title
        text author
        timestamp created_at
        timestamp ingested_at
        bigint file_size
        jsonb metadata
        varchar processing_status
    }
    
    CHUNKS {
        uuid id PK
        uuid document_id FK
        text content
        integer chunk_index
        integer token_count
        vector embedding
        jsonb metadata
        timestamp created_at
        tsvector content_tsvector
    }
    
    CONVERSATIONS {
        uuid id PK
        uuid user_id
        text query
        text response
        uuid_array context_chunks
        timestamp created_at
        integer response_time_ms
    }
    
    TAGS {
        uuid id PK
        varchar name
        varchar color
        boolean auto_generated
    }
    
    DOCUMENT_TAGS {
        uuid document_id FK
        uuid tag_id FK
    }
```

## 5. Temporal Query Processing Flow

```mermaid
graph TD
    Query[User Query: "What did I work on last week?"]
    
    subgraph "Temporal Analysis"
        Extract[Extract Temporal Expression<br/>"last week"]
        Resolve[Resolve to Date Range<br/>2024-01-08 to 2024-01-14]
        Context[Determine Temporal Context<br/>content_time vs ingestion_time]
    end
    
    subgraph "Search Execution"
        Filter[Apply Temporal Filter]
        Search[Execute Hybrid Search]
        Boost[Apply Temporal Boosting]
    end
    
    subgraph "Result Processing"
        Rank[Rank by Relevance + Recency]
        Select[Select Top Results]
        Generate[Generate Response]
    end
    
    Query --> Extract
    Extract --> Resolve
    Resolve --> Context
    Context --> Filter
    Filter --> Search
    Search --> Boost
    Boost --> Rank
    Rank --> Select
    Select --> Generate
    
    style Extract fill:#e1f5fe
    style Filter fill:#e8f5e8
    style Generate fill:#fff3e0
```

## 6. Scalability Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Application Load Balancer]
    end
    
    subgraph "API Tier (Auto-scaling)"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N]
    end
    
    subgraph "Processing Tier"
        Queue[Redis Task Queue]
        Worker1[Celery Worker 1]
        Worker2[Celery Worker 2]
        WorkerN[Celery Worker N]
    end
    
    subgraph "Storage Tier"
        Primary[(Primary DB)]
        Replica1[(Read Replica 1)]
        Replica2[(Read Replica 2)]
        Cache[(Redis Cache)]
    end
    
    subgraph "External Services"
        CDN[CDN for Static Assets]
        ObjectStore[Object Storage]
        Monitoring[Monitoring & Logging]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Queue
    API2 --> Queue
    API3 --> Queue
    
    Queue --> Worker1
    Queue --> Worker2
    Queue --> WorkerN
    
    API1 --> Primary
    API1 --> Replica1
    API1 --> Replica2
    API1 --> Cache
    
    Worker1 --> Primary
    Worker2 --> Primary
    WorkerN --> Primary
    
    API1 --> ObjectStore
    Worker1 --> ObjectStore
    
    style LB fill:#e1f5fe
    style Queue fill:#fff3e0
    style Primary fill:#e8f5e8
```