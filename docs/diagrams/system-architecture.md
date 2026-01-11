# Second Brain AI Companion - System Architecture Diagrams

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FE[Frontend<br/>HTML/JS/TailwindCSS]
        UI[User Interface<br/>Chat & Document Management]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend<br/>Python Async]
        RL[Rate Limiting<br/>SlowAPI]
        VAL[Input Validation<br/>Pydantic]
    end
    
    subgraph "Processing Layer"
        WH[Local Whisper<br/>Audio Transcription]
        EMB[Embedding Generation<br/>OpenRouter API]
        PROC[Document Processing<br/>Text/PDF/Audio]
    end
    
    subgraph "Storage Layer"
        MDB[(MongoDB Atlas<br/>Documents & Embeddings)]
        CONV[(Conversations<br/>Chat History)]
    end
    
    subgraph "External Services"
        OR[OpenRouter<br/>GPT-4o-mini LLM]
        OAI[OpenAI Embeddings<br/>text-embedding-ada-002]
    end
    
    subgraph "Search Engine"
        HS[Hybrid Search<br/>Semantic + Lexical]
        TS[Temporal Search<br/>Time-aware Queries]
        RS[Relevance Scoring<br/>Advanced Algorithm]
    end
    
    %% Client connections
    FE --> API
    UI --> FE
    
    %% API layer connections
    API --> RL
    API --> VAL
    API --> PROC
    API --> HS
    
    %% Processing connections
    PROC --> WH
    PROC --> EMB
    EMB --> OAI
    
    %% Search connections
    HS --> TS
    HS --> RS
    HS --> MDB
    
    %% Storage connections
    API --> MDB
    API --> CONV
    
    %% External service connections
    API --> OR
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef processing fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef external fill:#ffebee
    classDef search fill:#f1f8e9
    
    class FE,UI frontend
    class API,RL,VAL api
    class WH,EMB,PROC processing
    class MDB,CONV storage
    class OR,OAI external
    class HS,TS,RS search
```

## 2. Data Ingestion Pipeline

```mermaid
flowchart TD
    START([User Uploads File]) --> VAL{File Validation}
    
    VAL -->|Valid| TYPE{File Type Detection}
    VAL -->|Invalid| ERR[Return Error<br/>Size/Format/Security]
    
    TYPE -->|Audio| AUDIO[Audio Processing]
    TYPE -->|Text/MD| TEXT[Text Processing]
    TYPE -->|PDF| PDF[PDF Processing]
    TYPE -->|Other| OTHER[Generic Processing]
    
    AUDIO --> WHISPER[Local Whisper<br/>Transcription]
    WHISPER --> AUDIO_META[Extract Audio Metadata<br/>Duration, Format, Size]
    AUDIO_META --> AUDIO_FORMAT[Format Transcription<br/>with Source Attribution]
    
    TEXT --> TEXT_DECODE[UTF-8 Decoding]
    TEXT_DECODE --> TEXT_CLEAN[Content Cleaning<br/>& Normalization]
    
    PDF --> PDF_EXTRACT[Text Extraction<br/>Layout Preservation]
    PDF_EXTRACT --> PDF_META[Metadata Extraction<br/>Author, Title, Date]
    
    OTHER --> PLACEHOLDER[Create Placeholder<br/>Content with Metadata]
    
    AUDIO_FORMAT --> EMBED
    TEXT_CLEAN --> EMBED
    PDF_META --> EMBED
    PLACEHOLDER --> EMBED
    
    EMBED[Generate Embedding<br/>OpenAI API via OpenRouter] --> STORE
    
    STORE[Store in MongoDB Atlas<br/>Document + Embedding] --> INDEX
    
    INDEX[Update Search Indexes<br/>Full-text + Temporal] --> SUCCESS
    
    SUCCESS([Document Ready<br/>for Search])
    
    %% Error handling
    EMBED -->|API Error| EMBED_FALLBACK[Store without Embedding<br/>Retry Later]
    EMBED_FALLBACK --> STORE
    
    %% Styling
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef storage fill:#e1f5fe
    classDef error fill:#ffebee
    classDef success fill:#f1f8e9
    
    class WHISPER,TEXT_DECODE,PDF_EXTRACT,EMBED process
    class VAL,TYPE decision
    class STORE,INDEX storage
    class ERR,EMBED_FALLBACK error
    class SUCCESS success
```

## 3. Hybrid Search Architecture

```mermaid
flowchart TD
    QUERY[User Query<br/>"What did I learn about ML last week?"] --> PARSE
    
    PARSE[Query Analysis] --> TEMPORAL{Temporal<br/>Expressions?}
    PARSE --> EMBED_Q[Generate Query<br/>Embedding]
    PARSE --> WORDS[Extract Keywords<br/>Filter Stop Words]
    
    TEMPORAL -->|Yes| TIME_PARSE[Parse Temporal<br/>"last week" → Date Range]
    TEMPORAL -->|No| SEARCH_PARALLEL
    TIME_PARSE --> TIME_FILTER[Apply Temporal Filter<br/>created_at: $gte, $lte]
    TIME_FILTER --> SEARCH_PARALLEL
    
    SEARCH_PARALLEL[Parallel Search Execution]
    
    EMBED_Q --> SEM_SEARCH[Semantic Search<br/>Cosine Similarity]
    WORDS --> LEX_SEARCH[Lexical Search<br/>MongoDB Full-text]
    
    SEM_SEARCH --> SEM_RESULTS[(Semantic Results<br/>similarity scores)]
    LEX_SEARCH --> LEX_RESULTS[(Lexical Results<br/>text scores)]
    
    SEM_RESULTS --> FUSION
    LEX_RESULTS --> FUSION
    
    FUSION[Result Fusion & Scoring] --> SCORE_CALC
    
    SCORE_CALC[Advanced Relevance Calculation] --> COMPONENTS
    
    COMPONENTS --> EXACT[Exact Phrase Matching<br/>0-80 points]
    COMPONENTS --> WORD[Word Coverage Analysis<br/>0-40 points with penalties]
    COMPONENTS --> SEMANTIC[Semantic Similarity Boost<br/>0-40 points]
    COMPONENTS --> CONTEXT[Context Relevance Check<br/>Content vs Filename]
    
    EXACT --> FINAL_SCORE
    WORD --> FINAL_SCORE
    SEMANTIC --> FINAL_SCORE
    CONTEXT --> FINAL_SCORE
    
    FINAL_SCORE[Normalize Score<br/>final_score / 150.0] --> THRESHOLD{Score > 15%?}
    
    THRESHOLD -->|Yes| INCLUDE[Include in Results]
    THRESHOLD -->|No| EXCLUDE[Exclude from Results]
    
    INCLUDE --> SORT[Sort by Relevance<br/>Descending]
    SORT --> TOP_K[Return Top 5 Results]
    
    TOP_K --> LLM[Send to LLM<br/>with Context]
    LLM --> RESPONSE[Generate Response<br/>with Source Attribution]
    
    %% Styling
    classDef query fill:#e1f5fe
    classDef process fill:#e8f5e8
    classDef search fill:#f3e5f5
    classDef scoring fill:#fff3e0
    classDef decision fill:#ffebee
    classDef result fill:#f1f8e9
    
    class QUERY query
    class PARSE,EMBED_Q,WORDS,TIME_PARSE,FUSION,SCORE_CALC process
    class SEM_SEARCH,LEX_SEARCH search
    class EXACT,WORD,SEMANTIC,CONTEXT,FINAL_SCORE scoring
    class TEMPORAL,THRESHOLD decision
    class TOP_K,LLM,RESPONSE result
```

## 4. Temporal Query Processing

```mermaid
flowchart TD
    INPUT[User Query<br/>"Show me documents from last month"] --> EXTRACT
    
    EXTRACT[Extract Temporal Expressions] --> PATTERNS
    
    PATTERNS[Pattern Matching] --> REL{Relative Time?}
    PATTERNS --> ABS{Absolute Time?}
    PATTERNS --> CTX{Context Dependent?}
    
    REL -->|"last week"| REL_CALC[Calculate Relative Date<br/>now - 7 days → range]
    REL -->|"yesterday"| REL_CALC
    REL -->|"this month"| REL_CALC
    
    ABS -->|"March 2024"| ABS_CALC[Parse Absolute Date<br/>2024-03-01 → 2024-03-31]
    ABS -->|"January 15th"| ABS_CALC
    
    CTX -->|"before meeting"| CTX_RESOLVE[Context Resolution<br/>Find reference event]
    
    REL_CALC --> DATE_RANGE[Create Date Range<br/>start_date, end_date]
    ABS_CALC --> DATE_RANGE
    CTX_RESOLVE --> DATE_RANGE
    
    DATE_RANGE --> MONGO_FILTER
    
    MONGO_FILTER[Apply MongoDB Filter<br/>created_at: {$gte: start, $lte: end}] --> TEMP_RESULTS
    
    TEMP_RESULTS[(Temporally Filtered<br/>Documents)] --> RELEVANCE
    
    RELEVANCE[Calculate Temporal Relevance] --> IN_RANGE{Document in<br/>Time Range?}
    
    IN_RANGE -->|Yes| HIGH_REL[High Relevance Score<br/>0.8 - 1.0]
    IN_RANGE -->|No| PROXIMITY[Calculate Proximity<br/>Exponential Decay]
    
    PROXIMITY --> LOW_REL[Lower Relevance Score<br/>0.1 - 0.5]
    
    HIGH_REL --> BOOST
    LOW_REL --> BOOST
    
    BOOST[Apply Temporal Boost<br/>final_score *= 1.1] --> FINAL_RESULTS
    
    FINAL_RESULTS[Temporally Ranked<br/>Search Results] --> TIMELINE
    
    TIMELINE[Present in Timeline<br/>Chronological Order] --> USER
    
    USER[User Sees Results<br/>with Temporal Context]
    
    %% Examples
    subgraph "Examples"
        EX1["last week" → 2024-01-01 to 2024-01-07]
        EX2["March 2024" → 2024-03-01 to 2024-03-31]
        EX3["before deadline" → Context lookup]
    end
    
    %% Styling
    classDef input fill:#e1f5fe
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef calculation fill:#f3e5f5
    classDef result fill:#f1f8e9
    classDef example fill:#f9f9f9
    
    class INPUT input
    class EXTRACT,MONGO_FILTER,RELEVANCE,BOOST process
    class REL,ABS,CTX,IN_RANGE decision
    class REL_CALC,ABS_CALC,DATE_RANGE,HIGH_REL,LOW_REL calculation
    class FINAL_RESULTS,TIMELINE,USER result
    class EX1,EX2,EX3 example
```

## 5. Database Schema and Relationships

```mermaid
erDiagram
    DOCUMENTS {
        ObjectId _id PK
        string id UK "Application ID"
        string title "Document title"
        text content "Full content/transcription"
        array embedding "1536-dim vector"
        string source_type "audio|pdf|text"
        string source_path "Original filename"
        datetime created_at "Ingestion timestamp"
        string processing_status "completed|pending|failed"
        long file_size "Size in bytes"
        int chunk_count "Estimated chunks"
    }
    
    CONVERSATIONS {
        ObjectId _id PK
        string id UK "Timestamp-based ID"
        text query "User question"
        text response "AI response"
        datetime created_at "Conversation time"
        int response_time_ms "Response latency"
        array context_chunks "Referenced document IDs"
    }
    
    SEARCH_INDEXES {
        string index_name PK
        string collection "Target collection"
        object definition "Index configuration"
        datetime created_at "Index creation time"
    }
    
    TEMPORAL_CACHE {
        string expression PK "Temporal expression"
        datetime start_date "Resolved start"
        datetime end_date "Resolved end"
        datetime cached_at "Cache timestamp"
        int ttl "Time to live"
    }
    
    %% Relationships
    DOCUMENTS ||--o{ CONVERSATIONS : "referenced_in"
    DOCUMENTS ||--|| SEARCH_INDEXES : "indexed_by"
    CONVERSATIONS ||--o{ TEMPORAL_CACHE : "may_use"
    
    %% Indexes
    DOCUMENTS ||--|| TEXT_INDEX : "title, content"
    DOCUMENTS ||--|| TEMPORAL_INDEX : "created_at"
    DOCUMENTS ||--|| TYPE_INDEX : "source_type"
    CONVERSATIONS ||--|| TIME_INDEX : "created_at DESC"
```

## 6. API Flow and Data Movement

```mermaid
sequenceDiagram
    participant U as User/Frontend
    participant API as FastAPI Backend
    participant VAL as Validation Layer
    participant PROC as Processing Layer
    participant WH as Whisper (Local)
    participant EMB as Embedding Service
    participant MDB as MongoDB Atlas
    participant OR as OpenRouter LLM
    
    %% Document Upload Flow
    Note over U,OR: Document Upload Flow
    U->>API: POST /api/v1/documents/upload
    API->>VAL: Validate file (size, type, security)
    VAL-->>API: Validation result
    
    alt File is Audio
        API->>PROC: Process audio file
        PROC->>WH: Transcribe audio locally
        WH-->>PROC: Transcription text
        PROC-->>API: Formatted transcription
    else File is Text/PDF
        API->>PROC: Extract text content
        PROC-->>API: Clean text content
    end
    
    API->>EMB: Generate embedding
    EMB->>OR: Call OpenAI embeddings API
    OR-->>EMB: 1536-dim vector
    EMB-->>API: Embedding vector
    
    API->>MDB: Store document + embedding
    MDB-->>API: Document ID
    API-->>U: Upload success response
    
    %% Query Flow
    Note over U,OR: Query Processing Flow
    U->>API: POST /api/v1/query
    API->>VAL: Validate query input
    VAL-->>API: Validated query
    
    par Parallel Search Execution
        API->>EMB: Generate query embedding
        EMB->>OR: Call embeddings API
        OR-->>EMB: Query vector
        EMB-->>API: Query embedding
    and
        API->>MDB: Full-text search
        MDB-->>API: Text search results
    and
        API->>MDB: Semantic similarity search
        MDB-->>API: Vector search results
    end
    
    API->>API: Hybrid scoring & ranking
    API->>OR: Generate response with context
    OR-->>API: LLM response
    
    API->>MDB: Store conversation
    MDB-->>API: Conversation ID
    API-->>U: Query response with sources
```

## 7. Deployment Architecture Options

```mermaid
graph TB
    subgraph "Local Development"
        LD[Local Development<br/>Environment]
        LD --> LPY[Python Backend<br/>localhost:8000]
        LD --> LFE[HTML Frontend<br/>File or HTTP Server]
        LD --> LWH[Local Whisper<br/>Base Model]
        LPY --> LMDB[MongoDB Atlas<br/>Cloud Connection]
        LPY --> LOR[OpenRouter API<br/>Remote Calls]
    end
    
    subgraph "Cloud Deployment Options"
        subgraph "Option 1: Vercel"
            VER[Vercel Platform]
            VER --> VPY[Python Backend<br/>Serverless Functions]
            VER --> VFE[Static Frontend<br/>CDN Distribution]
            VPY --> VMDB[MongoDB Atlas]
            VPY --> VOR[OpenRouter API]
        end
        
        subgraph "Option 2: Container Platform"
            CONT[Container Platform<br/>Railway/Render/DO]
            CONT --> CPY[Dockerized Backend<br/>Persistent Container]
            CONT --> CFE[Static Frontend<br/>Served by Backend]
            CPY --> CMDB[MongoDB Atlas]
            CPY --> COR[OpenRouter API]
        end
        
        subgraph "Option 3: Full Cloud"
            CLOUD[AWS/GCP/Azure]
            CLOUD --> CLAPI[API Gateway<br/>Load Balancer]
            CLOUD --> CLBE[Backend Instances<br/>Auto Scaling]
            CLOUD --> CLFE[Frontend CDN<br/>S3/CloudFront]
            CLBE --> CLMDB[MongoDB Atlas<br/>Multi-Region]
            CLBE --> CLOR[OpenRouter API<br/>High Availability]
        end
    end
    
    subgraph "Future: Local-First Option"
        LOCAL[Local-First Deployment]
        LOCAL --> LMONGO[Local MongoDB<br/>Self-Hosted]
        LOCAL --> LLLM[Local LLM<br/>Ollama/GPT4All]
        LOCAL --> LWHISPER[Local Whisper<br/>All Processing On-Device]
        LOCAL --> LAPI[Local API<br/>No External Calls]
    end
    
    %% External Services (Shared)
    subgraph "External Services"
        ATLAS[(MongoDB Atlas<br/>Global Cloud Database)]
        OPENROUTER[OpenRouter<br/>LLM API Gateway]
        OPENAI[OpenAI<br/>Embeddings API]
    end
    
    %% Connections to external services
    LMDB --> ATLAS
    LOR --> OPENROUTER
    VMDB --> ATLAS
    VOR --> OPENROUTER
    CMDB --> ATLAS
    COR --> OPENROUTER
    CLMDB --> ATLAS
    CLOR --> OPENROUTER
    
    OPENROUTER --> OPENAI
    
    %% Styling
    classDef local fill:#e8f5e8
    classDef cloud fill:#e1f5fe
    classDef container fill:#f3e5f5
    classDef external fill:#fff3e0
    classDef future fill:#f1f8e9
    
    class LD,LPY,LFE,LWH local
    class VER,VPY,VFE,CLOUD,CLAPI,CLBE,CLFE cloud
    class CONT,CPY,CFE container
    class ATLAS,OPENROUTER,OPENAI external
    class LOCAL,LMONGO,LLLM,LWHISPER,LAPI future
```

## 8. Security and Privacy Architecture

```mermaid
flowchart TD
    subgraph "Data Privacy Layers"
        INPUT[User Data Input] --> CLASSIFY{Data Classification}
        
        CLASSIFY -->|Sensitive Audio| LOCAL_PROC[Local Processing<br/>Whisper Transcription]
        CLASSIFY -->|Documents| CLOUD_PROC[Cloud Processing<br/>Embedding Generation]
        CLASSIFY -->|Queries| CLOUD_LLM[Cloud LLM<br/>Response Generation]
        
        LOCAL_PROC --> LOCAL_STORE[Local Temporary Storage<br/>Immediate Cleanup]
        CLOUD_PROC --> ENCRYPT[Encryption in Transit<br/>TLS 1.3]
        CLOUD_LLM --> ENCRYPT
        
        LOCAL_STORE --> SECURE_DELETE[Secure File Deletion<br/>After Processing]
        ENCRYPT --> CLOUD_STORE[Cloud Storage<br/>MongoDB Atlas]
    end
    
    subgraph "Access Control"
        USER[User Authentication] --> API_KEY[API Key Validation<br/>User-Controlled Keys]
        API_KEY --> RATE_LIMIT[Rate Limiting<br/>100 req/min]
        RATE_LIMIT --> INPUT_VAL[Input Validation<br/>File Size/Type/Content]
        INPUT_VAL --> SANITIZE[Data Sanitization<br/>XSS/Injection Prevention]
    end
    
    subgraph "Data Sovereignty"
        USER_CONTROL[User Data Control] --> OWN_KEYS[Own API Keys<br/>OpenRouter Account]
        USER_CONTROL --> DATA_EXPORT[Data Export<br/>Full MongoDB Access]
        USER_CONTROL --> DATA_DELETE[Data Deletion<br/>Right to be Forgotten]
        USER_CONTROL --> REGION_CHOICE[Region Selection<br/>MongoDB Atlas Regions]
    end
    
    subgraph "Security Measures"
        ENV_VARS[Environment Variables<br/>No Hardcoded Secrets] --> CORS[CORS Configuration<br/>Trusted Origins Only]
        CORS --> HTTPS[HTTPS Enforcement<br/>Production Deployment]
        HTTPS --> AUDIT[Audit Logging<br/>Access & Error Tracking]
        AUDIT --> MONITOR[Health Monitoring<br/>Anomaly Detection]
    end
    
    %% Privacy Trade-offs
    subgraph "Privacy Trade-offs"
        CLOUD_BENEFITS[Cloud Benefits<br/>• Multi-device sync<br/>• Automatic backups<br/>• Professional security]
        PRIVACY_CONCERNS[Privacy Considerations<br/>• Data in cloud<br/>• API calls logged<br/>• Vendor dependencies]
        
        CLOUD_BENEFITS -.->|vs| PRIVACY_CONCERNS
    end
    
    %% Future Local-First
    subgraph "Future: Local-First"
        LOCAL_DEPLOY[Local Deployment] --> LOCAL_DB[Local MongoDB<br/>No Cloud Storage]
        LOCAL_DEPLOY --> LOCAL_LLM[Local LLM<br/>Ollama/GPT4All]
        LOCAL_DEPLOY --> OFFLINE[Offline Capable<br/>No Internet Required]
        LOCAL_DEPLOY --> FULL_PRIVACY[Complete Privacy<br/>No Data Leaves Device]
    end
    
    %% Styling
    classDef privacy fill:#e8f5e8
    classDef security fill:#e1f5fe
    classDef control fill:#f3e5f5
    classDef tradeoff fill:#fff3e0
    classDef future fill:#f1f8e9
    
    class LOCAL_PROC,SECURE_DELETE,CLOUD_STORE privacy
    class API_KEY,RATE_LIMIT,INPUT_VAL,SANITIZE,ENV_VARS,CORS,HTTPS security
    class USER_CONTROL,OWN_KEYS,DATA_EXPORT,DATA_DELETE control
    class CLOUD_BENEFITS,PRIVACY_CONCERNS tradeoff
    class LOCAL_DEPLOY,LOCAL_DB,LOCAL_LLM,OFFLINE,FULL_PRIVACY future
```

These Mermaid diagrams provide comprehensive visual documentation of the Second Brain AI Companion system architecture, covering:

1. **High-Level Architecture** - Overall system components and relationships
2. **Data Ingestion Pipeline** - Step-by-step file processing workflow
3. **Hybrid Search Architecture** - Advanced search and relevance scoring
4. **Temporal Query Processing** - Time-aware query handling
5. **Database Schema** - Data models and relationships
6. **API Flow** - Sequence diagrams for key operations
7. **Deployment Options** - Various deployment architectures
8. **Security & Privacy** - Data protection and privacy measures

Each diagram is based on the actual working implementation and can be rendered in any Mermaid-compatible viewer or documentation system.