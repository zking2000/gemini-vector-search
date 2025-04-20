# Gemini向量搜索系统

基于Google Gemini模型的文档检索和分析系统，支持PDF文档上传、智能分块、向量搜索以及基于文档内容的问答功能。

## 系统架构

```mermaid
graph TD
    %% 定义节点
    Client[客户端]
    PDF[PDF文件]
    Query[用户查询]
    Response[应答结果]
    
    %% API层
    subgraph API["API层"]
        A1[健康检查接口]
        A2[文档管理接口]
        A3[向量查询接口]
        A4[文本生成接口]
        A5[PDF上传接口]
    end
    
    %% 服务层
    subgraph Services["服务层"]
        B1[GeminiService]
        B2[VectorService]
    end
    
    %% 功能模块
    subgraph Functions["功能模块"]
        C1[嵌入生成]
        C2[向量搜索]
        C3[智能分块]
        C4[上下文准备]
        C5[文本补全]
    end
    
    %% 数据流
    subgraph Data["数据流"]
        D[(向量数据库)]
        E[嵌入向量]
        F[相似度计算]
        G[文档分块]
        H[上下文生成]
        I[应答生成]
    end
    
    %% 客户端调用API层
    Client --> A1
    Client --> A2
    Client --> A3
    Client --> A4
    Client --> A5
    
    %% API层到服务层的连接
    A1 --> B1
    A2 --> B2
    A3 --> B1
    A3 --> B2
    A4 --> B1
    A5 --> B1
    A5 --> B2
    
    %% 服务层到功能模块的连接
    B1 --> C1
    B1 --> C3
    B1 --> C4
    B1 --> C5
    B2 --> C2
    
    %% 功能模块到数据流的连接
    C1 --> E
    C2 --> F
    C3 --> G
    C4 --> H
    C5 --> I
    
    %% 数据库连接
    E --> D
    F --> D
    
    %% 文档处理流程
    PDF --> A5
    A5 --> C3
    G --> C1
    
    %% 查询流程
    Query --> A3
    F --> H
    H --> C5
    I --> Response
```

## 主要处理流程

```mermaid
sequenceDiagram
    participant Client as 用户
    participant API
    participant GS as GeminiService
    participant VS as VectorService
    participant DB as 数据库
    
    %% 文档上传流程
    Note over Client,DB: 文档上传流程
    Client->>API: 1. 上传PDF文档
    API->>GS: 2. 调用智能分块
    GS-->>API: 3. 返回文档块
    
    loop 对每个文档块
        API->>GS: 4a. 生成嵌入向量
        GS-->>API: 4b. 返回嵌入向量
        API->>VS: 4c. 添加文档和向量到数据库
        VS->>DB: 4d. 存储文档和向量
        DB-->>VS: 4e. 存储确认
        VS-->>API: 4f. 处理完成
    end
    
    API-->>Client: 5. 上传成功响应
    
    %% 查询流程
    Note over Client,DB: 查询处理流程
    Client->>API: 1. 发送查询请求
    API->>GS: 2. 生成查询嵌入向量
    GS-->>API: 3. 返回查询向量
    
    API->>VS: 4. 搜索相似文档
    VS->>DB: 5. 检索文档
    DB-->>VS: 6. 返回文档集
    VS->>VS: 7. 计算相似度并排序
    VS-->>API: 8. 返回相关文档
    
    API->>GS: 9. 准备上下文
    GS-->>API: 10. 返回格式化上下文
    API->>GS: 11. 生成回答
    GS-->>API: 12. 返回生成的回答
    API-->>Client: 13. 返回查询结果
```

## 主要功能

1. **文档管理**
   - PDF文档上传和解析
   - 智能文档分块
   - 文档向量化存储

2. **向量搜索**
   - 语义相似度检索
   - 按文档源过滤

3. **智能问答**
   - 基于文档内容的问答
   - 结构化内容分析
   - 自动摘要生成

## API详解

### 1. 集成查询端点

`POST /api/v1/integration` 是系统的核心端点，结合了向量检索和AI生成功能，为用户提供一站式问答体验。

#### 请求体结构

```json
{
    "prompt": "你想提问的问题，例如：Python如何处理异常？",
    "context_query": "Python 异常 try except",
    "max_context_docs": 5
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 用户的问题或提示，AI将基于此生成回答 |
| context_query | string | 否 | 用于向量检索的查询文本，如果不提供则使用prompt的值 |
| max_context_docs | integer | 否 | 检索的最大文档数量，默认为5，建议范围1-10 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_filter | string | 否 | 按文档来源筛选，例如：`python_docs.pdf` |
| debug | boolean | 否 | 是否返回详细的调试信息，默认为false |
| force_use_documents | boolean | 否 | 强制使用文档内容回答，即使没有找到高相似度的匹配 |

#### 响应结构

```json
{
    "completion": "基于文档内容生成的回答...",
    "debug_info": {
        "original_query": "原始查询",
        "search_query": "扩展后的搜索查询",
        "docs_found": 5,
        "context_length": 1250,
        "document_snippets": [
            {
                "content": "文档片段1...",
                "similarity": 0.85,
                "source": "python_docs.pdf"
            },
            {
                "content": "文档片段2...",
                "similarity": 0.78,
                "source": "tutorial.pdf"
            }
        ]
    }
}
```

> 注意：`debug_info` 字段仅在请求参数中 `debug=true` 时返回

#### 使用示例

```bash
curl --location 'http://localhost:8000/api/v1/integration' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "Python中如何优雅地处理异常？",
    "context_query": "Python 异常处理 最佳实践",
    "max_context_docs": 5
}'
```

### 2. 上传PDF端点

`POST /api/v1/upload-pdf` 用于上传PDF文档，系统会自动提取文本、分块并生成向量存储。

#### 请求体结构

使用 `multipart/form-data` 格式提交数据：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 要上传的PDF文件 |
| use_intelligent_chunking | boolean | 否 | 是否使用Gemini进行智能分块，默认为true |
| chunk_size | integer | 否 | 如果不使用智能分块，固定分块大小，默认1000 |
| overlap | integer | 否 | 如果不使用智能分块，块之间的重叠字符数，默认200 |
| clear_existing | boolean | 否 | 上传前是否清空数据库中的文档，默认为false |

#### 响应结构

```json
{
    "success": true,
    "filename": "example.pdf",
    "chunks_processed": 25,
    "document_ids": ["1", "2", "3", "..."],
    "chunking_method": "intelligent_chunking",
    "total_chunks": 25,
    "processed_chunks": 25
}
```

#### 使用示例

```bash
curl --location 'http://localhost:8000/api/v1/upload-pdf' \
--form 'file=@"/path/to/document.pdf"' \
--form 'use_intelligent_chunking="true"'
```

### 3. 向量搜索端点

`POST /api/v1/query` 在向量数据库中搜索与查询文本相似的文档。

#### 请求体结构

```json
{
    "query": "搜索查询文本",
    "limit": 10
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索查询文本 |
| limit | integer | 否 | 返回结果数量限制，默认为5 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_filter | string | 否 | 按文档来源筛选结果 |

#### 响应结构

```json
{
    "results": [
        {
            "id": "1",
            "content": "文档内容...",
            "title": "文档标题",
            "metadata": {
                "source": "document.pdf",
                "chunk": 1,
                "total_chunks": 25
            },
            "similarity": 0.92,
            "source": "document.pdf"
        },
        {
            "id": "2",
            "content": "另一个文档内容...",
            "similarity": 0.85,
            "source": "another_doc.pdf"
        }
    ]
}
```

### 4. 文本生成端点

`POST /api/v1/completion` 使用Gemini模型生成文本补全，可选择是否使用向量数据库中的相关文档作为上下文。

#### 请求体结构

```json
{
    "prompt": "你想提问的问题",
    "use_context": true,
    "context_query": "搜索相关内容的查询",
    "max_context_docs": 5
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 用于生成文本的提示 |
| use_context | boolean | 否 | 是否使用向量搜索结果作为上下文，默认为false |
| context_query | string | 否 | 用于向量检索的查询文本，需启用use_context |
| max_context_docs | integer | 否 | 上下文使用的最大文档数量，默认为5 |

#### 响应结构

```json
{
    "completion": "生成的文本内容..."
}
```

### 5. 嵌入向量生成端点

`POST /api/v1/embedding` 使用Gemini模型将文本转换为嵌入向量表示，用于相似度搜索。

#### 请求体结构

```json
{
    "text": "要转换为向量的文本内容"
}
```

#### 响应结构

```json
{
    "embedding": [0.1, 0.2, 0.3, ...]
}
```

### 6. 文档分析端点

`POST /api/v1/analyze-documents` 深入分析文档内容，提取关键概念和主题。

#### 请求体结构

```json
{
    "query": "分析主题",
    "limit": 10
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 分析主题或问题 |
| limit | integer | 否 | 分析使用的最大文档数量，默认为5 |

#### 响应结构

```json
{
    "completion": "详细的结构化文档分析结果..."
}
```

### 7. 获取文档列表端点

`GET /api/v1/documents` 获取存储在系统中的文档列表，支持分页和筛选。

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 返回的最大文档数量，范围1-100，默认为20 |
| offset | integer | 否 | 分页偏移量，用于分页查询，默认为0 |
| source | string | 否 | 按文档来源筛选 |

#### 响应结构

```json
[
    {
        "id": "1",
        "title": "文档标题",
        "content": "文档内容...",
        "metadata": {
            "source": "document.pdf",
            "chunk": 1,
            "total_chunks": 25
        },
        "created_at": "2023-01-01T12:00:00.000Z"
    },
    {
        "id": "2",
        "title": "另一个文档标题",
        "content": "另一个文档内容..."
    }
]
```

### 8. 获取单个文档端点

`GET /api/v1/documents/{document_id}` 根据ID获取单个文档的详细信息。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | string/integer | 是 | 文档的唯一标识符 |

#### 响应结构

```json
{
    "id": "1",
    "title": "文档标题",
    "content": "文档内容...",
    "metadata": {
        "source": "document.pdf",
        "chunk": 1,
        "total_chunks": 25
    },
    "created_at": "2023-01-01T12:00:00.000Z"
}
```

### 9. 健康检查端点

`GET /api/v1/health` 检查API服务是否正常运行，无需认证。

#### 响应结构

```json
{
    "status": "ok",
    "timestamp": "2023-01-01T12:00:00.000Z"
}
```

### 10. 数据库状态端点

`GET /api/v1/database-status` 检查数据库连接状态，无需认证。

#### 响应结构

```json
{
    "status": "connected",
    "timestamp": "2023-01-01T12:00:00.000Z"
}
```

## 环境设置

1. 复制环境变量示例文件或使用安装脚本自动创建
   ```
   cp .env.example .env
   ```

2. 编辑`.env`文件，填入你的API密钥和数据库配置:
   ```
   GOOGLE_API_KEY=your_google_api_key
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=gemini
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=password
   ```

### 直接启动后端

```bash
python main.py

# 或使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 使用Bash控制脚本

```bash
# 启动服务
./run.sh start

# 停止服务
./run.sh stop

# 查看状态
./run.sh status

# 查看日志
./run.sh logs
```

### 命令行选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 服务主机 | 0.0.0.0 |
| `--port` | 服务端口 | 8000 |
| `--auto-reload` | 启用自动重载 | false |
| `--logs` | 启动后显示日志 | false |
| `--help`, `-h` | 显示帮助信息 | - |

## 日志管理

系统采用时间戳命名的日志文件，确保每次启动都会创建新的日志文件而不会覆盖历史记录：

```
logs/
├── app_20231020_123045.log  # 历史日志
├── app_20231021_083012.log  # 历史日志
└── app_20231022_094517.log  # 最新日志
└── app_current.log -> app_20231022_094517.log  # 指向最新日志的符号链接
```

### 查看日志

可以通过以下方式查看日志：

1. **使用控制脚本**：
   ```bash
   ./run.sh logs  # 显示最新日志
   ```

2. **直接查看日志文件**：
   ```bash
   # 查看最新日志（通过符号链接）
   tail -f logs/app_current.log
   
   # 查看特定日志文件
   less logs/app_20231022_094517.log
   ```

## 使用Swagger API文档

系统内置了Swagger API文档界面，可以通过浏览器访问:

```
http://localhost:8000/docs
```

Swagger文档提供了:

1. 所有API端点的详细说明
2. 请求和响应模型的结构
3. 参数说明和示例值
4. 在线测试功能，可直接在浏览器中测试API

## 代码结构

```mermaid
graph TD
    %% 主要应用组件
    MainApp[main.py] --> App[app目录]
    App --> ApiDir[api]
    App --> ServicesDir[services]
    App --> ModelsDir[models]
    App --> DbDir[db]
    App --> CoreDir[core]
    App --> AuthDir[auth]
    App --> LogsDir[logs]
    
    %% API层
    ApiDir --> GeminiRoutes[gemini_routes.py]
    
    %% 服务层
    ServicesDir --> GeminiService[gemini_service.py]
    ServicesDir --> VectorService[vector_service.py]
    ServicesDir --> CacheService[cache_service.py]
    
    %% 模型层
    ModelsDir --> ApiModels[api_models.py]
    ModelsDir --> VectorModels[vector_models.py]
    
    %% 数据库层
    DbDir --> Database[database.py]
    DbDir --> InitDb[init_db.py]
    
    %% 核心层
    CoreDir --> Config[config.py]
    CoreDir --> Middleware[middleware.py]
    
    %% 文档目录
    Docs[documents目录] --> DocsFiles[文档相关文件]
    
    %% 静态资源
    Static[static目录] --> StaticFiles[静态资源文件]
    
    %% 关系描述
    MainApp -- "调用" --> ApiDir
    GeminiRoutes -- "调用" --> ServicesDir
    GeminiService -- "使用" --> ModelsDir
    VectorService -- "使用" --> ModelsDir
    ServicesDir -- "使用" --> DbDir
    ApiDir -- "使用" --> CoreDir
    ServicesDir -- "配置" --> CoreDir
```

## 代码结构详细图

### API交互流程

```mermaid
sequenceDiagram
    participant C as 客户端
    participant R as GeminiRoutes
    participant GS as GeminiService
    participant VS as VectorService
    participant CS as CacheService
    participant DB as 数据库
    
    %% 健康检查流程
    C->>+R: GET /api/v1/health
    R->>R: 检查组件状态
    R-->>-C: 返回健康状态
    
    %% 文档上传流程
    C->>+R: POST /api/v1/upload-pdf
    R->>+GS: 处理PDF文档
    GS->>GS: 智能分块处理
    GS->>+VS: 生成并保存向量
    VS->>DB: 存储向量和元数据
    VS-->>-GS: 返回保存结果
    GS-->>-R: 返回处理结果
    R-->>-C: 返回上传结果
    
    %% 向量搜索流程
    C->>+R: POST /api/v1/search
    R->>+CS: 检查缓存
    CS-->>R: 返回缓存结果(未命中)
    R->>+GS: 生成查询向量
    GS-->>-R: 返回查询向量
    R->>+VS: 执行向量搜索
    VS->>DB: 查询向量数据库
    VS-->>-R: 返回搜索结果
    R->>+CS: 缓存结果
    CS-->>-R: 确认缓存
    R-->>-C: 返回搜索结果
    
    %% 集成查询流程
    C->>+R: POST /api/v1/integration
    R->>+CS: 检查缓存
    CS-->>R: 返回缓存结果(未命中)
    R->>+GS: 生成查询向量
    GS-->>-R: 返回查询向量
    R->>+VS: 执行向量搜索
    VS->>DB: 查询向量数据库
    VS-->>-R: 返回搜索结果
    R->>+GS: 准备上下文
    GS-->>-R: 返回格式化上下文
    R->>+GS: 生成回答
    GS-->>-R: 返回生成的回答
    R->>+CS: 缓存结果
    CS-->>-R: 确认缓存
    R-->>-C: 返回集成结果
```

### 数据模型关系图

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
    
    APIRequest --> APIResponse : 生成
    APIResponse *-- DebugInfo : 包含
    APIRequest --> VectorDocument : 查询
    VectorDocument --> VectorDocument : 相似匹配
```

### 服务组件内部逻辑

```mermaid
graph TB
    %% GeminiService内部逻辑
    subgraph "GeminiService"
        G1[初始化Gemini客户端] --> G2[配置模型参数]
        G2 --> G3{功能选择}
        G3 -->|嵌入生成| G4[调用嵌入API]
        G3 -->|文本生成| G5[调用文本API]
        G3 -->|文档处理| G6[智能分块]
        G4 --> G7[向量标准化]
        G5 --> G8[应答后处理]
        G6 --> G9[元数据提取]
    end
    
    %% VectorService内部逻辑
    subgraph "VectorService"
        V1[数据库连接] --> V2{操作类型}
        V2 -->|索引文档| V3[向量入库]
        V2 -->|相似搜索| V4[KNN搜索]
        V2 -->|过滤搜索| V5[混合查询]
        V3 --> V6[批量操作优化]
        V4 --> V7[相似度计算]
        V5 --> V8[结果合并排序]
        V6 --> V9[事务管理]
        V7 --> V9
        V8 --> V9
    end
    
    %% CacheService内部逻辑
    subgraph "CacheService"
        C1[初始化缓存] --> C2{缓存策略}
        C2 -->|查询| C3[生成缓存键]
        C2 -->|清理| C4[过期检查]
        C2 -->|更新| C5[条目替换]
        C3 --> C6[读取缓存]
        C4 --> C7[定期清理]
        C5 --> C8[写入缓存]
        C6 --> C9[缓存命中统计]
        C7 --> C9
        C8 --> C9
    end
    
    %% 服务间交互
    G7 -.-> V3
    G9 -.-> V3
    V4 -.-> G5
    V5 -.-> G5
    G4 -.-> C8
    G5 -.-> C8
    V4 -.-> C8
    C6 -.-> G5
    C6 -.-> V4
```

### 缓存机制和中间件流程

```mermaid
flowchart LR
    %% 缓存机制
    subgraph "缓存系统"
        CQ[缓存查询] --> CH{缓存命中?}
        CH -->|是| CR[返回缓存结果]
        CH -->|否| CP[处理请求]
        CP --> CS[存储结果]
        CS --> CR
    end
    
    %% 中间件流程
    subgraph "请求中间件链"
        R[接收请求] --> M1[日志中间件]
        M1 --> M2[认证中间件]
        M2 --> M3[速率限制]
        M3 --> M4[请求验证]
        M4 --> H[路由处理]
        H --> M5[响应格式化]
        M5 --> M6[错误处理]
        M6 --> M7[日志记录]
        M7 --> S[发送响应]
    end
    
    %% 连接缓存与中间件
    M4 -.-> CQ
    CR -.-> M5
    CP -.-> H
```

### 查询处理流程

```mermaid
flowchart TB
    %% 主要流程
    subgraph "查询处理流程"
        A[接收用户查询] --> B[生成查询向量]
        B --> C[向量数据库检索]
        C --> D[结果相似度排序]
        D --> E[准备上下文]
        E --> F[使用Gemini生成回答]
        F --> G[返回结果]
    end
    
    subgraph "文档处理流程"
        H[上传PDF文档] --> I[文档智能分块]
        I --> J[生成块嵌入向量]
        J --> K[存储向量和元数据]
        K --> L[构建索引]
    end
    
    subgraph "服务组件"
        API[API层] --> GS[GeminiService]
        API --> VS[VectorService]
        API --> CS[CacheService]
        
        GS <--> VS
        GS --> CS
        VS --> CS
    end
    
    %% 连接流程与组件
    A -.-> API
    G -.-> API
    H -.-> API
    L -.-> VS
```

### 文档处理和向量索引详细流程

```mermaid
graph TB
    %% 入口
    Start[开始文档处理] --> P1[接收PDF文件]
    
    %% PDF处理
    P1 --> P2[PDF文本提取]
    P2 --> P3[文本清理]
    P3 --> P4[文本分块决策]
    
    %% 分块策略
    P4 --> PS1{分块策略}
    PS1 -->|固定大小| PS2[按字数分块]
    PS1 -->|智能分块| PS3[按段落/章节分块]
    PS1 -->|混合策略| PS4[大小+语义边界]
    
    %% 块处理
    PS2 --> P5[文本块生成]
    PS3 --> P5
    PS4 --> P5
    P5 --> P6[元数据提取]
    P6 --> P7[嵌入向量生成]
    
    %% 嵌入向量处理
    P7 --> V1[向量归一化]
    V1 --> V2[维度处理]
    V2 --> V3[向量持久化]
    
    %% 索引构建
    V3 --> I1[构建索引]
    I1 --> I2{索引类型}
    I2 -->|树索引| I3[创建树结构]
    I2 -->|哈希索引| I4[创建哈希表]
    I2 -->|混合索引| I5[多索引结构]
    
    %% 索引优化
    I3 --> I6[索引优化]
    I4 --> I6
    I5 --> I6
    I6 --> I7[索引压缩]
    I7 --> I8[索引验证]
    
    %% 结束
    I8 --> End[处理完成]
    
    %% 额外操作
    P3 -.->|问题检测| E1[错误处理]
    P7 -.->|生成失败| E1
    E1 -.->|重试| P3
    E1 -.->|放弃| End
    
    %% 缓存
    P6 -.->|缓存元数据| C1[更新元数据缓存]
    V3 -.->|缓存向量| C2[更新向量缓存]
```

### 数据流转和存储层交互

```mermaid
graph TB
    %% 主要数据流
    Client[客户端] -->|请求| API[API层]
    API -->|文本| GS[GeminiService]
    API -->|向量| VS[VectorService]
    
    %% 服务层数据流
    GS -->|嵌入请求| Google[Google Gemini API]
    Google -->|嵌入向量| GS
    GS -->|向量数据| VS
    VS -->|文档数据| DB[(数据库)]
    
    %% 数据库层结构
    DB -->|实体表| DB1[文档表]
    DB -->|向量表| DB2[向量表]
    DB -->|元数据表| DB3[元数据表]
    DB -->|用户表| DB4[用户表]
    
    %% 缓存层结构
    Cache[(缓存)] -->|查询缓存| C1[查询结果缓存]
    Cache -->|向量缓存| C2[向量数据缓存]
    Cache -->|会话缓存| C3[用户会话缓存]
    
    %% 服务与缓存交互
    GS <-->|读写| Cache
    VS <-->|读写| Cache
    API <-->|读写| Cache
    
    %% 后台任务
    Task[后台任务] -->|索引维护| DB
    Task -->|缓存清理| Cache
    Task -->|状态监控| Monitor[监控系统]
    
    %% 监控流
    Monitor -->|性能指标| Dashboard[管理仪表盘]
    Monitor -->|告警| Alert[告警系统]
``` 