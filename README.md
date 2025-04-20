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

## API Detail

### 1. Integration Query Endpoint

`POST /api/v1/integration` is the core endpoint of the system, combining vector retrieval and AI generation functionality to provide a one-stop answer experience for users.

#### Request Body Structure

```json
{
    "prompt": "Your question, for example: How does Python handle exceptions?",
    "context_query": "Python exception try except",
    "max_context_docs": 5
}
```

#### Parameter Description

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| prompt | string | Yes | User's question or prompt, AI will generate answer based on this |
| context_query | string | No | Query text for vector retrieval, if not provided, use the value of prompt |
| max_context_docs | integer | No | Maximum number of documents to retrieve, default is 5, recommended range 1-10 |

#### Query Parameters

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| source_filter | string | No | Filter by document source, for example: `python_docs.pdf` |
| debug | boolean | No | Whether to return detailed debug information, default is false |
| force_use_documents | boolean | No | Force using document content to answer even if no high similarity match is found |

#### Response Structure

```json
{
    "completion": "Based on document content generated answer...",
    "debug_info": {
        "original_query": "Original Query",
        "search_query": "Search Query Extended",
        "docs_found": 5,
        "context_length": 1250,
        "document_snippets": [
            {
                "content": "Document Snippet 1...",
                "similarity": 0.85,
                "source": "python_docs.pdf"
            },
            {
                "content": "Document Snippet 2...",
                "similarity": 0.78,
                "source": "tutorial.pdf"
            }
        ]
    }
}
```

> Note: `debug_info` field only returns when request parameter `debug=true`

#### Usage Example

```bash
curl -X POST "http://localhost:8000/api/v1/integration" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How does Python handle exceptions?",
    "max_context_docs": 5
  }'
```

### 2. Upload PDF Endpoint

`POST /api/v1/upload-pdf` is used to upload PDF documents, the system will automatically extract text, chunk, and generate vectors for storage.

#### Request Body Structure

Submit data using `multipart/form-data` format:

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| file | file | Yes | PDF file to upload |
| use_intelligent_chunking | boolean | No | Whether to use Gemini for intelligent chunking, default is true |
| chunk_size | integer | No | If not using intelligent chunking, fixed chunk size, default 1000 |
| overlap | integer | No | If not using intelligent chunking, character count of overlap between chunks, default 200 |
| clear_existing | boolean | No | Whether to clear documents in the database before uploading, default is false |

#### Response Structure

```json
{
    "success": true,
    "filename": "uploaded_document.pdf",
    "chunks_processed": 15,
    "document_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    "chunking_method": "intelligent"
}
```

#### Usage Example

```bash
curl -X POST "http://localhost:8000/api/v1/upload-pdf" \
  -F "file=@/path/to/document.pdf" \
  -F "use_intelligent_chunking=true"
```

### 3. Vector Search Endpoint

`POST /api/v1/query` searches for documents similar to the query text in the vector database.

#### Request Body Structure

```json
{
    "query": "Search Query Text",
    "limit": 10
}
```

#### Parameter Description

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| query | string | Yes | Search query text |
| limit | integer | No | Limit on number of results returned, default is 5 |

#### Query Parameters

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| source_filter | string | No | Filter results by document source |

#### Response Structure

```json
{
    "results": [
        {
            "id": "1",
            "content": "Document Content...",
            "title": "Document Title",
            "metadata": {
                "source": "document.pdf",
                "page": 5,
                "chunk": 3
            },
            "similarity": 0.92
        },
        {
            "id": "2",
            "content": "Another Document Content...",
            "similarity": 0.85,
            "source": "another_doc.pdf"
        }
    ]
}
```

### 4. Text Generation Endpoint

`POST /api/v1/completion` uses Gemini model to generate text completion, and can choose whether to use related documents from the vector database as context.

#### Request Body Structure

```json
{
    "prompt": "Your question",
    "use_context": true,
    "context_query": "Search Related Content Query",
    "max_context_docs": 5
}
```

#### Parameter Description

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| prompt | string | Yes | Prompt for generating text |
| use_context | boolean | No | Whether to use vector search results as context, default is false |
| context_query | string | No | Query text for vector retrieval, need to enable use_context |
| max_context_docs | integer | No | Maximum number of documents used for context, default is 5 |

#### Response Structure

```json
{
    "completion": "Generated Text Content..."
}
```

### 5. Embedding Vector Generation Endpoint

`POST /api/v1/embedding` uses Gemini model to convert text to embedding vector representation for similarity search.

#### Request Body Structure

```json
{
    "text": "Text Content to Convert to Vector"
}
```

#### Response Structure

```json
{
    "embedding": [0.123, 0.456, 0.789, ...]
}
```

### 6. Document Analysis Endpoint

`POST /api/v1/analyze-documents` analyzes document content in depth to extract key concepts and themes.

#### Request Body Structure

```json
{
    "query": "Analyze Theme",
    "limit": 10
}
```

#### Parameter Description

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| query | string | Yes | Analyze theme or question |
| limit | integer | No | Maximum number of documents used for analysis, default is 5 |

#### Response Structure

```json
{
    "completion": "Detailed Structured Document Analysis Result..."
}
```

### 7. Get Document List Endpoint

`GET /api/v1/documents` retrieves the list of documents stored in the system, supporting pagination and filtering.

#### Query Parameters

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| limit | integer | No | Maximum number of documents to return, range 1-100, default is 20 |
| offset | integer | No | Pagination offset for pagination query, default is 0 |
| source | string | No | Filter by document source |

#### Response Structure

```json
[
    {
        "id": "1",
        "title": "Document Title",
        "content": "Document Content...",
        "metadata": {
            "source": "document.pdf",
            "page": 5
        },
        "created_at": "2023-10-20T12:30:45Z"
    },
    {
        "id": "2",
        "title": "Another Document Title",
        "content": "Another Document Content..."
    }
]
```

### 8. Get Single Document Endpoint

`GET /api/v1/documents/{document_id}` retrieves detailed information about a single document based on ID.

#### Path Parameters

| Parameter | Type | Required | Description |
|----------|------|--------|-------------|
| document_id | string/integer | Yes | Unique identifier for document |

#### Response Structure

```json
{
    "id": "1",
    "title": "Document Title",
    "content": "Document Content...",
    "metadata": {
        "source": "document.pdf",
        "page": 5,
        "chunk": 3
    },
    "created_at": "2023-10-20T12:30:45Z"
}
```

### 9. Health Check Endpoint

`GET /api/v1/health` checks whether the API service is running normally without authentication.

#### Response Structure

```json
{
    "status": "ok",
    "timestamp": "2023-10-20T12:30:45Z"
}
```

### 10. Database Status Endpoint

`GET /api/v1/database-status` checks the database connection status without authentication.

#### Response Structure

```json
{
    "status": "connected",
    "timestamp": "2023-10-20T12:30:45Z"
}
```

## Environment Setup

1. Copy the environment variable example file or use the installation script to automatically create
    ```
    cp .env.example .env
    ```

2. Edit `.env` file and fill in your API key and database configuration:
    ```
    GOOGLE_API_KEY=your_google_api_key
    DATABASE_URL=postgresql://username:password@localhost:5432/vector_db
    ```

### Directly Start Backend

```bash
python main.py

# Or use uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Use Bash Control Script

```bash
# Start service
./run.sh start

# Stop service
./run.sh stop

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

## Log Management

The system uses timestamp-named log files to ensure that new log files are created each time the service starts instead of overwriting historical records:

```
logs/
├── app_20231020_123045.log  # Historical Log
├── app_20231021_083012.log  # Historical Log
└── app_20231022_094517.log  # Latest Log
└── app_current.log -> app_20231022_094517.log  # Symbolic Link to Latest Log
```

### View Logs

You can view logs in the following ways:

1. **Use Control Script**:
    ```bash
    ./run.sh logs  # Display Latest Log
    ```

2. **Directly View Log Files**:
    ```bash
    # View Latest Log (Through Symbolic Link)
    tail -f logs/app_current.log
    
    # View Specific Log File
    less logs/app_20231022_094517.log
    ```

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

### API Interaction Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as GeminiRoutes
    participant GS as GeminiService
    participant VS as VectorService
    participant CS as CacheService
    participant DB as Database
    
    %% Health Check Flow
    C->>+R: GET /api/v1/health
    R->>R: Check Component Status
    R-->>-C: Return Health Status
    
    %% Document Upload Flow
    C->>+R: POST /api/v1/upload-pdf
    R->>+GS: Process PDF Document
    GS->>GS: Intelligent Chunking Processing
    GS->>+VS: Generate and Save Vectors
    VS->>DB: Store Vectors and Metadata
    VS-->>-GS: Return Save Result
    GS-->>-R: Return Processing Result
    R-->>-C: Return Upload Result
    
    %% Vector Search Flow
    C->>+R: POST /api/v1/search
    R->>+CS: Check Cache
    CS-->>R: Return Cache Result(Miss)
    R->>+GS: Generate Query Vector
    GS-->>-R: Return Query Vector
    R->>+VS: Execute Vector Search
    VS->>DB: Query Vector Database
    VS-->>-R: Return Search Results
    R->>+CS: Cache Result
    CS-->>-R: Confirm Cache
    R-->>-C: Return Search Results
    
    %% Integration Query Flow
    C->>+R: POST /api/v1/integration
    R->>+CS: Check Cache
    CS-->>R: Return Cache Result(Miss)
    R->>+GS: Generate Query Vector
    GS-->>-R: Return Query Vector
    R->>+VS: Execute Vector Search
    VS->>DB: Query Vector Database
    VS-->>-R: Return Search Results
    R->>+GS: Prepare Context
    GS-->>-R: Return Formatted Context
    R->>+GS: Generate Answer
    GS-->>-R: Return Generated Answer
    R->>+CS: Cache Result
    CS-->>-R: Confirm Cache
    R-->>-C: Return Integration Result
```

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

### Service Component Internal Logic

```mermaid
graph TB
    %% GeminiService Internal Logic
    subgraph "GeminiService"
        G1[Initialize Gemini Client] --> G2[Configure Model Parameters]
        G2 --> G3{Function Selection}
        G3 -->|Embedding Generation| G4[Call Embedding API]
        G3 -->|Text Generation| G5[Call Text API]
        G3 -->|Document Processing| G6[Intelligent Chunking]
        G4 --> G7[Vector Normalization]
        G5 --> G8[Post-Answer Processing]
        G6 --> G9[Metadata Extraction]
    end
    
    %% VectorService Internal Logic
    subgraph "VectorService"
        V1[Database Connection] --> V2{Operation Type}
        V2 -->|Index Documents| V3[Vector Storage]
        V2 -->|Similar Search| V4[KNN Search]
        V2 -->|Filtered Search| V5[Mixed Query]
        V3 --> V6[Batch Operation Optimization]
        V4 --> V7[Similarity Calculation]
        V5 --> V8[Result Merging and Sorting]
        V6 --> V9[Transaction Management]
        V7 --> V9
        V8 --> V9
    end
    
    %% CacheService Internal Logic
    subgraph "CacheService"
        C1[Initialize Cache] --> C2{Cache Strategy}
        C2 -->|Query| C3[Generate Cache Key]
        C2 -->|Cleanup| C4[Expiration Check]
        C2 -->|Update| C5[Entry Replacement]
        C3 --> C6[Read Cache]
        C4 --> C7[Regular Cleanup]
        C5 --> C8[Write Cache]
        C6 --> C9[Cache Hit Statistics]
        C7 --> C9
        C8 --> C9
    end
    
    %% Service Interactions
    G7 -.-> V3
    G9 -.-> V3
    V4 -.-> G5
    V5 -.-> G5
    G4 -.-> C8
    G5 -.-> C8
    V4 -.-> C8
    C6 -.-> G5
```

### Cache Mechanism and Middleware Flow

```mermaid
flowchart LR
    %% Cache Mechanism
    subgraph "Cache System"
        CQ[Cache Query] --> CH{Cache Hit?}
        CH -->|Yes| CR[Return Cache Result]
        CH -->|No| CP[Process Request]
        CP --> CS[Store Result]
        CS --> CR
    end
    
    %% Middleware Flow
    subgraph "Request Middleware Chain"
        R[Receive Request] --> M1[Logging Middleware]
        M1 --> M2[Authentication Middleware]
        M2 --> M3[Rate Limiting]
        M3 --> M4[Request Validation]
        M4 --> H[Routing Processing]
        H --> M5[Response Formatting]
        M5 --> M6[Error Handling]
        M6 --> M7[Logging Record]
        M7 --> S[Send Response]
    end
    
    %% Connect Cache to Middleware
    M4 -.-> CQ
    CR -.-> M5
    CP -.-> H
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