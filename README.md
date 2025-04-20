# Gemini Vector Search System

A document retrieval and analysis system based on Google Gemini model, supporting PDF document upload, intelligent chunking, vector search, and question answering functionality based on document content.

## System Architecture

```mermaid
graph TD
    %% Define nodes
    Client[Client]
    PDF[PDF File]
    Query[User Query]
    Response[Response Result]
    
    %% API Layer
    subgraph API["API Layer"]
        A1[Health Check API]
        A2[Document Management API]
        A3[Vector Query API]
        A4[Text Generation API]
        A5[PDF Upload API]
    end
    
    %% Service Layer
    subgraph Services["Service Layer"]
        B1[GeminiService]
        B2[VectorService]
    end
    
    %% Function Modules
    subgraph Functions["Function Modules"]
        C1[Embedding Generation]
        C2[Vector Search]
        C3[Intelligent Chunking]
        C4[Context Preparation]
        C5[Text Completion]
    end
    
    %% Data Flow
    subgraph Data["Data Flow"]
        D[(Vector Database)]
        E[Embedding Vectors]
        F[Similarity Calculation]
        G[Document Chunking]
        H[Context Generation]
        I[Response Generation]
    end
    
    %% Client calls API layer
    Client --> A1
    Client --> A2
    Client --> A3
    Client --> A4
    Client --> A5
    
    %% API layer connections to service layer
    A1 --> B1
    A2 --> B2
    A3 --> B1
    A3 --> B2
    A4 --> B1
    A5 --> B1
    A5 --> B2
    
    %% Service layer connections to function modules
    B1 --> C1
    B1 --> C3
    B1 --> C4
    B1 --> C5
    B2 --> C2
    
    %% Function module connections to data flow
    C1 --> E
    C2 --> F
    C3 --> G
    C4 --> H
    C5 --> I
    
    %% Database connections
    E --> D
    F --> D
    
    %% Document processing flow
    PDF --> A5
    A5 --> C3
    G --> C1
    
    %% Query flow
    Query --> A3
    F --> H
    H --> C5
    I --> Response
```

## Main Processing Flow

```mermaid
sequenceDiagram
    participant Client as User
    participant API
    participant GS as GeminiService
    participant VS as VectorService
    participant DB as Database
    
    %% Document upload flow
    Note over Client,DB: Document Upload Flow
    Client->>API: 1. Upload PDF document
    API->>GS: 2. Call intelligent chunking
    GS-->>API: 3. Return document chunks
    
    loop For each document chunk
        API->>GS: 4a. Generate embedding vector
        GS-->>API: 4b. Return embedding vector
        API->>VS: 4c. Add document and vector to database
        VS->>DB: 4d. Store document and vector
        DB-->>VS: 4e. Storage confirmation
        VS-->>API: 4f. Processing complete
    end
    
    API-->>Client: 5. Upload success response
    
    %% Query flow
    Note over Client,DB: Query Processing Flow
    Client->>API: 1. Send query request
    API->>GS: 2. Generate query embedding vector
    GS-->>API: 3. Return query vector
    
    API->>VS: 4. Search similar documents
    VS->>DB: 5. Retrieve documents
    DB-->>VS: 6. Return document set
    VS->>VS: 7. Calculate similarity and sort
    VS-->>API: 8. Return relevant documents
    
    API->>GS: 9. Prepare context
    GS-->>API: 10. Return formatted context
    API->>GS: 11. Generate answer
    GS-->>API: 12. Return generated answer
    API-->>Client: 13. Return query results
```

## Code Structure

```mermaid
graph TD
    %% Main Application Components
    MainApp[main.py] --> App[app directory]
    App --> ApiDir[api]
    App --> ServicesDir[services]
    App --> ModelsDir[models]
    App --> DbDir[db]
    App --> CoreDir[core]
    App --> AuthDir[auth]
    App --> LogsDir[logs]
    
    %% API Layer
    ApiDir --> GeminiRoutes[gemini_routes.py]
    
    %% Service Layer
    ServicesDir --> GeminiService[gemini_service.py]
    ServicesDir --> VectorService[vector_service.py]
    ServicesDir --> CacheService[cache_service.py]
    
    %% Model Layer
    ModelsDir --> ApiModels[api_models.py]
    ModelsDir --> VectorModels[vector_models.py]
    
    %% Database Layer
    DbDir --> Database[database.py]
    DbDir --> InitDb[init_db.py]
    
    %% Core Layer
    CoreDir --> Config[config.py]
    CoreDir --> Middleware[middleware.py]
    
    %% Document Directory
    Docs[documents directory] --> DocsFiles[Document Related Files]
    
    %% Static Resources
    Static[static directory] --> StaticFiles[Static Resource Files]
    
    %% Relationship Description
    MainApp -- "Call" --> ApiDir
    GeminiRoutes -- "Call" --> ServicesDir
    GeminiService -- "Use" --> ModelsDir
    VectorService -- "Use" --> ModelsDir
    ServicesDir -- "Use" --> DbDir
    ApiDir -- "Use" --> CoreDir
    ServicesDir -- "Configure" --> CoreDir
```

## Code Structure Detailed Diagram

### Data Model Relationship Diagram

```mermaid
classDiagram
    class VectorDocument {
        +String id
        +String content
        +String source_name
        +String metadata
        +List~Float~ embedding
        +DateTime created_at
        +insertDocument()
        +findSimilar()
        +deleteDocuments()
    }
    
    class APIRequest {
        +String prompt
        +String context_query
        +int max_context_docs
        +String source_filter
        +bool debug
        +validate()
    }
    
    class APIResponse {
        +String completion
        +DebugInfo debug_info
        +toJSON()
    }
    
    class DebugInfo {
        +String original_query
        +String search_query
        +int docs_found
        +int context_length
        +List~String~ document_snippets
    }
    
    class CacheEntry {
        +String key
        +Any value
        +DateTime expiry
        +bool isExpired()
    }
    
    APIRequest --> APIResponse : Generate
    APIResponse *-- DebugInfo : Contains
    APIRequest --> VectorDocument : Query
    VectorDocument --> VectorDocument : Similar Matching
```

### Query Processing Flow

```mermaid
flowchart TB
    %% Main Flow
    subgraph "Query Processing Flow"
        A[Receive User Query] --> B[Generate Query Vector]
        B --> C[Vector Database Retrieval]
        C --> D[Result Similarity Sorting]
        D --> E[Prepare Context]
        E --> F[Use Gemini to Generate Answer]
        F --> G[Return Result]
    end
    
    subgraph "Document Processing Flow"
        H[Upload PDF Document] --> I[Intelligent Document Chunking]
        I --> J[Generate Block Embedding Vectors]
        J --> K[Store Vectors and Metadata]
        K --> L[Build Index]
    end
    
    subgraph "Service Components"
        API[API Layer] --> GS[GeminiService]
        API --> VS[VectorService]
        API --> CS[CacheService]
        GS --> Google[Google Gemini API]
        VS --> DB[(Vector Database)]
    end
    
    %% Connect Flow to Components
    A -.-> API
    G -.-> API
    B -.-> GS
    E -.-> GS
    F -.-> GS
    C -.-> VS
    D -.-> VS
    K -.-> VS
    L -.-> VS
```

### Document Processing and Vector Indexing Detailed Flow

```mermaid
graph TB
    %% Entry
    Start[Start Document Processing] --> P1[Receive PDF File]
    
    %% PDF Processing
    P1 --> P2[PDF Text Extraction]
    P2 --> P3[Text Cleaning]
    P3 --> P4[Text Chunking Decision]
    
    %% Chunking Strategy
    P4 --> PS1{Chunking Strategy}
    PS1 -->|Fixed Size| PS2[Fixed Size Chunking]
    PS1 -->|Intelligent Chunking| PS3[Paragraph/Chapter Chunking]
    PS1 -->|Mixed Strategy| PS4[Size+Semantic Boundary]
    
    %% Chunk Processing
    PS2 --> P5[Text Chunk Generation]
    PS3 --> P5
    PS4 --> P5
    P5 --> P6[Metadata Extraction]
    P6 --> P7[Embedding Vector Generation]
    
    %% Embedding Vector Processing
    P7 --> V1[Vector Normalization]
    V1 --> V2[Dimension Processing]
    V2 --> V3[Vector Persistence]
    
    %% Index Building
    V3 --> I1[Build Index]
    I1 --> I2{Index Type}
    I2 -->|Tree Index| I3[Create Tree Structure]
    I2 -->|Hash Index| I4[Create Hash Table]
    I2 -->|Mixed Index| I5[Multi-Index Structure]
    
    %% Index Optimization
    I3 --> I6[Index Optimization]
    I4 --> I6
    I5 --> I6
    I6 --> I7[Index Compression]
    I7 --> I8[Index Verification]
    
    %% End
    I8 --> End[Processing Complete]
    
    %% Additional Operations
    P3 -.->|Question Detection| E1[Error Handling]
    P7 -.->|Generation Failure| E1
    E1 -.->|Retry| P3
    E1 -.->|Give Up| End
    
    %% Cache
    P6 -.->|Cache Metadata| C1[Update Metadata Cache]
    V3 -.->|Cache Vectors| C2[Update Vector Cache]
```

### Data Flow and Storage Layer Interaction

```mermaid
graph TB
    %% Main Data Flow
    Client[Client] -->|Request| API[API Layer]
    API -->|Text| GS[GeminiService]
    API -->|Vector| VS[VectorService]
    
    %% Service Layer Data Flow
    GS -->|Embedding Request| Google[Google Gemini API]
    Google -->|Embedding Vectors| GS
    GS -->|Vector Data| VS
    VS -->|Document Data| DB[(Database)]
    
    %% Database Layer Structure
    DB -->|Entity Table| DB1[Document Table]
    DB -->|Vector Table| DB2[Vector Table]
    DB -->|Metadata Table| DB3[Metadata Table]
    DB -->|User Table| DB4[User Table]
    
    %% Cache Layer Structure
    Cache[(Cache)] -->|Query Cache| C1[Query Result Cache]
    Cache -->|Vector Cache| C2[Vector Data Cache]
    Cache -->|Session Cache| C3[User Session Cache]
    
    %% Service and Cache Interactions
    GS <-->|Read/Write| Cache
    VS <-->|Read/Write| Cache
    API <-->|Read/Write| Cache
    
    %% Background Task
    Task[Background Task] -->|Index Maintenance| DB
    Task -->|Cache Cleanup| Cache
    Task -->|Status Monitoring| Monitor[Monitoring System]
    
    %% Monitoring Flow
    Monitor -->|Performance Metrics| Dashboard[Management Dashboard]
    Monitor -->|Alert| Alert[Alert System]
``` 

## Main Features

1. **Document Management**
   - PDF document upload and parsing
   - Intelligent document chunking
   - Document vector storage

2. **Vector Search**
   - Semantic similarity retrieval
   - Document source filtering

3. **Intelligent Q&A**
   - Question answering based on document content
   - Structured content analysis
   - Automatic summary generation

### Directly Start Backend

```bash
python main.py

# Or use uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Use Bash Control Script

```bash
# Start service
./run.sh start-backend

# Stop service
./run.sh stop-backend

# View status
./run.sh status

# View logs
./run.sh logs
```

### Command Line Options

| Option | Description | Default Value |
|--------|-------------|-------------|
| `--host` | Service Host | 0.0.0.0 |
| `--port` | Service Port | 8000 |
| `--auto-reload` | Enable Auto Reload | false |
| `--logs` | Start with Logs | false |
| `--help`, `-h` | Display Help Information | - |

## Use Swagger API Documentation

The system has built-in Swagger API documentation interface, which can be accessed through the browser:

```
http://localhost:8000/docs
```

Swagger documentation provides:

1. Detailed description of all API endpoints
2. Structure of request and response models
3. Parameter description and example values
4. Online testing functionality, directly test API in browser

## References and Resources

In the development of this Gemini Vector Search System, we referenced the following technical resources:

### Google Gemini API

- [Google Generative AI Official Documentation](https://ai.google.dev/docs)
- [Gemini API Reference](https://ai.google.dev/api/python/google/generativeai)
- [Gemini Embedding Models](https://ai.google.dev/docs/embeddings_guide)

### Vector Retrieval and RAG Technology

- [Best Practices for Retrieval Augmented Generation (RAG)](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Google Vector Search Documentation](https://cloud.google.com/vertex-ai/docs/vector-search/overview)
- [Practical Guide to Building RAG Applications](https://towardsdatascience.com/a-practical-guide-to-building-rag-applications-e9923bee2aa2)

### Document Intelligent Processing

- [PDF Processing and Text Extraction](https://pypdf2.readthedocs.io/en/latest/)
- [Intelligent Document Chunking Techniques](https://www.pinecone.io/learn/chunking-strategies/)
- [LangChain Document Processing Framework](https://python.langchain.com/docs/modules/data_connection/document_transformers/)

### FastAPI Framework

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy and FastAPI Integration](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### Frontend Technologies

- [Ant Design React UI Library](https://ant.design/docs/react/introduce)
- [React Framework Documentation](https://react.dev/learn)

### System Architecture

- [Vector Database Design Patterns](https://www.singlestore.com/blog/vector-database-design-patterns/)
- [Building High-Performance RAG System Architecture](https://www.databricks.com/blog/llm-rag-platform-upgrade-how-build-high-accuracy-retrieval-augmented-generation-applications)