from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
import tempfile
import os
import PyPDF2
import textwrap
from io import BytesIO
import asyncio
from sqlalchemy import text
from datetime import datetime
import json
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import traceback

from app.db.database import get_db, engine
from app.models.api_models import (
    CompletionRequest, CompletionResponse, 
    EmbeddingRequest, EmbeddingResponse,
    DocumentCreate, DocumentResponse,
    QueryRequest, QueryResponse
)
from app.services.gemini_service import GeminiService
from app.services.vector_service import VectorService

# Create a unified router, no longer need separate authenticated and non-authenticated routes
router = APIRouter(prefix="/api/v1")
health_router = APIRouter(prefix="/api/v1")

# Create service instances
gemini_service = GeminiService()
vector_service = VectorService()

# Health check endpoint - no authentication required
@health_router.get("/health", 
                  summary="API Health Check", 
                  description="Check if the API service is running properly, no authentication required",
                  response_description="Returns the health status of the API service and the current timestamp")
async def health():
    """
    Health check endpoint to verify if the service is running properly
    
    No authentication required, can be used by monitoring systems to check API availability
    
    Returns:
        dict: Dictionary containing status and timestamp
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Database status endpoint - no authentication required
@health_router.get("/database-status", 
                  summary="Database Connection Status", 
                  description="Check database connection status, no authentication required",
                  response_description="Returns database connection status and current timestamp")
async def database_status():
    """
    Check database connection status
    
    No authentication required, can be used by monitoring systems to check API availability
    
    Returns:
        dict: Dictionary containing database connection status and timestamp
        
    Exceptions:
        HTTPException: If database connection fails
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result:
                return {
                    "status": "connected",
                    "timestamp": datetime.now().isoformat()
                }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# All endpoints below do not require authentication

@router.post("/embedding", 
            response_model=EmbeddingResponse, 
            summary="Generate Text Embedding Vector", 
            description="Convert text to embedding vector representation for vector retrieval",
            response_description="Returns the generated vector representation")
async def create_embedding(
    request: EmbeddingRequest,
):
    """
    Generate embedding vectors for text
    
    Use Gemini embedding model to convert input text to vector representation for similarity search
    
    Parameters:
        request: Request object containing the text to be converted
        
    Returns:
        EmbeddingResponse: Response object containing the embedding vector
        
    Exceptions:
        HTTPException: If embedding generation fails
    """
    try:
        embedding = await gemini_service.generate_embedding(request.text)
        return {"embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.post("/completion", 
            response_model=CompletionResponse, 
            summary="Generate Text Completion", 
            description="Use Gemini model to generate text completion, optionally using relevant documents from the vector database as context",
            response_description="Returns the generated completion text")
async def create_completion(
    request: CompletionRequest,
    db: Session = Depends(get_db),
):
    """
    Generate text completion
    
    Use Gemini model to generate text completion, optionally using relevant documents from the vector database as context
    
    Parameters:
        request: Request object containing prompt text and context configuration
        db: Database session
        
    Returns:
        CompletionResponse: Response object containing the generated completion text
        
    Exceptions:
        HTTPException: If completion generation fails
    """
    try:
        context = None
        
        # If context is needed
        if request.use_context and request.context_query:
            # Get similar documents
            similar_docs = await vector_service.search_similar(
                db, 
                request.context_query, 
                request.max_context_docs
            )
            
            # Prepare context
            if similar_docs:
                context = await gemini_service.prepare_context(request.context_query, similar_docs)
        
        # Determine task complexity based on prompt length and content
        complexity = "normal"
        if request.model_complexity in ["simple", "normal", "complex"]:
            # Use user-specified complexity if provided
            complexity = request.model_complexity
        elif len(request.prompt) > 1000 or "详细" in request.prompt or "complex" in request.prompt.lower():
            complexity = "complex"
        elif len(request.prompt) < 100 and not any(term in request.prompt.lower() for term in ["explain", "analyze", "compare", "evaluate"]):
            complexity = "simple"
        
        # Generate completion with complexity hint
        completion = await gemini_service.generate_completion(
            prompt=request.prompt, 
            context=context,
            complexity=complexity,
            use_cache=not request.disable_cache
        )
        
        return {"completion": completion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion generation failed: {str(e)}")

@router.post("/documents", 
            response_model=DocumentResponse, 
            summary="Add Document", 
            description="Add a single document to the vector database, generating its embedding vector for later retrieval",
            response_description="Returns information about the added document")
async def add_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
):
    """
    Add document to the vector database
    
    Add a single document to the database, generating its embedding vector for later retrieval
    
    Parameters:
        request: Request object containing document content and metadata
        db: Database session
        
    Returns:
        DocumentResponse: Response object containing information about the newly added document
        
    Exceptions:
        HTTPException: If adding the document fails
    """
    try:
        document = await vector_service.add_document(db, request.content, request.metadata)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

@router.post("/query", 
            response_model=QueryResponse, 
            summary="Query Similar Documents", 
            description="Search for documents similar to the query text in the vector database, and return detailed information",
            response_description="Returns a list of similar documents, context, and summary analysis")
async def query_documents(
    request: QueryRequest,
    source_filter: Optional[str] = Query(None, description="Filter results by document source", example="document1.pdf"),
    db: Session = Depends(get_db),
):
    """
    Query similar documents in the vector database
    
    Search for documents similar to the query text in the vector database, and return detailed information, context, and summary analysis
    
    Parameters:
        request: Request object containing query text and configuration
        source_filter: Optional document source filter condition
        db: Database session
        
    Returns:
        QueryResponse: Response object containing similar documents, context, and summary
        
    Exceptions:
        HTTPException: If the query fails
    """
    try:
        results = await vector_service.search_similar(db, request.query, request.limit, source_filter)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query similar documents: {str(e)}")

@router.post("/integration", 
            response_model=CompletionResponse, 
            summary="Integration Query", 
            description="Integrated API combining vector retrieval and text generation, can filter results by document source and return detailed debugging information",
            response_description="Returns answer generated based on related document content")
async def integration_query(
    request: CompletionRequest,
    source_filter: Optional[str] = Query(None, description="Filter results by document source", example="document1.pdf"),
    debug: bool = Query(False, description="Return detailed debugging information"),
    force_use_documents: bool = Query(False, description="Force use document content answer even if no high similarity match found"),
    db: Session = Depends(get_db),
):
    """
    Integrated API: Vector query and result addition to prompt
    
    Integrated API combining vector retrieval and text generation, can filter results by document source and return detailed debugging information
    
    Parameters:
        request: Request object containing prompt text and context query
        source_filter: Filter results by document source, for example specific PDF file name
        debug: Whether to return detailed debugging information
        force_use_documents: Force use document content answer even if no high similarity match found
        db: Database session
        
    Returns:
        CompletionResponse: Response object containing the generated answer, if debug enabled then includes debugging information
        
    Exceptions:
        HTTPException: If integration query fails
    """
    try:
        print(f"Received integration query request: {request.prompt}")
        print(f"Context query: {request.context_query or request.prompt}")
        
        # Check if it's a Chinese query
        is_chinese_query = any('\u4e00' <= c <= '\u9fff' for c in request.prompt)
        print(f"Is Chinese query: {is_chinese_query}")
        
        # First query related documents
        search_query = request.context_query or request.prompt
        
        # Expand search query to improve matching ability for Chinese content
        expanded_terms = []
        if "道教" in search_query:
            expanded_terms = ["道教", "老子", "道德经", "太上老君", "张道陵", "太极", "阴阳", "天师道", "五斗米道", "全真道"]  # Taoism, Laozi, Tao Te Ching, Supreme Old Lord, Zhang Daoling, Taiji, Yin-Yang, Celestial Masters, Five Pecks of Rice, Complete Perfection
        elif "佛教" in search_query:
            expanded_terms = ["佛教", "释迦牟尼", "佛陀", "菩萨", "禅宗", "佛经", "如来", "佛祖", "涅槃", "菩提"]  # Buddhism, Shakyamuni, Buddha, Bodhisattva, Zen, Buddhist Scriptures, Tathagata, Founder of Buddhism, Nirvana, Bodhi
        elif is_chinese_query:
            # Add some common Chinese philosophy and religious terms for other Chinese queries
            expanded_terms = ["中国", "哲学", "历史", "传统", "文化", "典籍", "经典"]  # China, philosophy, history, tradition, culture, ancient books, classics
        
        if expanded_terms:
            search_query = f"{search_query} {' '.join(expanded_terms)}"
            print(f"Expanded search query: {search_query}")
        
        # Increase return document count to improve probability of finding related content
        max_context_docs = request.max_context_docs
        if is_chinese_query:
            max_context_docs = max(max_context_docs, 10)  # Chinese query at least returns 10 documents
        
        similar_docs = await vector_service.search_similar(
            db, 
            search_query, 
            max_context_docs,
            source_filter
        )
        
        print(f"Found {len(similar_docs)} related documents")
        
        # For debugging purposes, print content snippets of the first few documents
        if similar_docs:
            print("First 3 document content snippets:")
            for i, doc in enumerate(similar_docs[:3]):
                content_preview = doc.get("content", "")[:100].replace("\n", " ")
                similarity = doc.get("similarity", 0)
                print(f"  [{i+1}] Similarity: {similarity:.4f} - {content_preview}...")
        
        # Prepare context
        context = None
        if similar_docs:
            context = await gemini_service.prepare_context(
                request.context_query or request.prompt, 
                similar_docs
            )
            print(f"Generated context, length: {len(context) if context else 0}")
        else:
            print("No related documents found")
        
        # Generate completion
        completion_prompt = request.prompt
        if context:
            if is_chinese_query:
                completion_prompt = f"""
You are a knowledgeable assistant tasked with answering questions based ONLY on the provided reference material.

IMPORTANT INSTRUCTIONS:
1. You are given English documents but the user is asking in Chinese.
2. You must answer in Chinese.
3. You must ONLY use information found in the reference material.
4. Do NOT use your general knowledge unless absolutely necessary to explain concepts in the documents.
5. If the reference material does not contain the answer, clearly state this in Chinese.
6. Translate relevant information from the English documents into Chinese to answer the query.
7. When referencing specific points from the documents, mention which document they came from.

Reference material:
{context}

User question (in Chinese): {request.prompt}

Provide a comprehensive answer in Chinese, based strictly on the information in the reference material.
"""
            else:
                completion_prompt = f"""
You are a knowledgeable assistant, especially skilled at answering questions using ONLY the information in the provided reference material.
Please answer the user's question based on the following reference material. If the reference material does not contain relevant information, please clearly indicate which information is missing.

Reference material:
{context}

User question: {request.prompt}
"""
        else:
            # If no related documents found but user forces use of document content
            if force_use_documents:
                # Get existing documents in the system
                try:
                    # Query document count
                    doc_count = db.execute(text("SELECT COUNT(*) FROM documents")).scalar()
                    
                    # If there are documents, try to get some sample content
                    if doc_count > 0:
                        # Get recent document titles and sources
                        recent_docs = db.execute(
                            text("SELECT id, title, doc_metadata FROM documents ORDER BY id DESC LIMIT 5")
                        ).fetchall()
                        
                        doc_samples = []
                        for doc in recent_docs:
                            metadata = {}
                            if doc.doc_metadata:
                                try:
                                    if isinstance(doc.doc_metadata, str):
                                        metadata = json.loads(doc.doc_metadata)
                                    else:
                                        metadata = doc.doc_metadata
                                except:
                                    pass
                            
                            source = metadata.get("source", "Unknown source")
                            doc_samples.append(f"- ID: {doc.id}, Source: {source}, Title: {doc.title[:50]}...")
                        
                        doc_list = "\n".join(doc_samples)
                        
                        if is_chinese_query:
                            completion_prompt = f"""
非常抱歉，我在系统中搜索了所有文档（共 {doc_count} 个），但未能找到与您的问题"{request.prompt}"直接相关的内容。

以下是系统中的一些文档示例：
{doc_list}

由于您选择了强制使用文档内容模式，我必须基于系统中的文档回答问题，但系统中可能没有与此问题相关的信息。

请考虑以下几点：
1. 是否需要上传包含相关信息的文档
2. 是否需要调整查询措辞以更好地匹配现有文档
3. 是否需要扩展文档库以涵盖这个主题

您的问题是：{request.prompt}

我必须声明，系统中可能缺少相关文档。
"""
                        else:
                            completion_prompt = f"""
I am a knowledgeable assistant, especially skilled at answering questions about history and culture.

I searched through all documents in the database ({doc_count} total) but couldn't find any directly relevant to "{request.prompt}".
Here are some sample documents in the system:
{doc_list}

Since you've selected the force_use_documents mode, I must base my answer on documents in the system. However, the system may not contain information related to this question.

Please compare your question with the documents in the system and consider:
1. Whether you need to upload documents containing the relevant information
2. Whether you need to adjust your query wording to better match existing documents
3. Whether you need to expand the document library to cover this topic

User question: {request.prompt}

Please clearly indicate that the system may be missing relevant documents.
"""
                except Exception as e:
                    print(f"Failed to get document statistics: {e}")
                    # Use default prompt
            
            if not force_use_documents:
                if is_chinese_query:
                    completion_prompt = f"""
非常抱歉，我在系统中没有找到与"{request.prompt}"相关的参考资料。

可能的原因包括：
1. 数据库中可能没有与此主题相关的文档
2. 查询措辞与文档内容不匹配
3. 相关文档的向量表示与查询向量表示的相似度不够高

您的问题是：{request.prompt}

请注意，以下回答基于通用知识而非系统中的文档内容。
"""
                else:
                    completion_prompt = f"""
You are a knowledgeable assistant, especially skilled at answering questions about history and culture.
I couldn't find any reference material related to "{request.prompt}". Please answer based on your knowledge, but please clearly indicate that your answer is not based on system document content.

User question: {request.prompt}
"""
        
        print(f"Generated completion prompt, length: {len(completion_prompt)}")
        completion = await gemini_service.generate_completion(completion_prompt)
        
        # If debug mode enabled, return more information
        if debug:
            return {
                "completion": completion,
                "debug_info": {
                    "original_query": request.prompt,
                    "is_chinese_query": is_chinese_query,
                    "search_query": search_query,
                    "docs_found": len(similar_docs),
                    "context_length": len(context) if context else 0,
                    "document_snippets": [
                        {
                            "content": d.get("content", "")[:150] + "...",
                            "similarity": d.get("similarity", 0),
                            "source": d.get("metadata", {}).get("source", "") or 
                                     d.get("source", "") or 
                                     d.get("metadata", {}).get("pdf_filename", "") or 
                                     "Document ID: " + str(d.get("id", "Unknown ID"))
                        } 
                        for d in similar_docs[:5]
                    ] if similar_docs else []
                }
            }
        
        # When debug is false, explicitly return response without debug_info
        # Use CompletionResponse model's field pattern to ensure proper response
        return CompletionResponse(
            completion=completion,
            debug_info=None
        ).dict(exclude_none=True)  # This excludes None values from the response
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Integration query failed: {str(e)}")

@router.get("/documents", 
           response_model=List[Dict[str, Any]], 
           summary="Get Document List", 
           description="Get document list, supports paging and source filtering",
           response_description="Returns document list")
async def get_documents(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Page offset for paging query"),
    source: Optional[str] = Query(None, description="Filter by document source, for example specific PDF file name")
):
    """
    Get document list, supports paging and filtering
    
    Get document list from the database, supports paging and filtering by source
    
    Parameters:
        db: Database session
        limit: Maximum number of documents to return, range 1-100
        offset: Page offset for paging query
        source: Filter by document source, for example specific PDF file name
        
    Returns:
        List[Dict]: Document list, each document contains ID, title, content, metadata, and creation time
        
    Exceptions:
        HTTPException: If failed to get document list
    """
    try:
        # Build query conditions
        query = "SELECT id, title, doc_metadata, created_at FROM documents"
        params = {}
        
        if source:
            query += " WHERE doc_metadata::text LIKE :source"
            params["source"] = f"%{source}%"
            
        # Add sorting and paging
        query += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        # Execute query
        result = db.execute(text(query), params).fetchall()
        
        # Process results
        documents = []
        for row in result:
            # Safe handling doc_metadata
            try:
                metadata = row.doc_metadata
                # If it's a string, try to parse as JSON
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse document id={row.id} metadata: {e}")
                        metadata = {}
                # If not dictionary type, use empty dictionary
                elif not isinstance(metadata, dict):
                    print(f"Document id={row.id} metadata is not valid JSON or dictionary: {type(metadata)}")
                    metadata = {}
                
                # Delete embedding vector to reduce response size
                if "_embedding" in metadata:
                    del metadata["_embedding"]
            except Exception as e:
                print(f"Failed to handle document id={row.id} metadata: {e}")
                metadata = {}
                
            documents.append({
                "id": row.id,
                "title": row.title,
                "content": row.title,  # Use title as content return
                "metadata": metadata,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
            
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document list: {str(e)}")

@router.post("/upload-pdf", 
            response_model=Dict[str, Any], 
            summary="Upload PDF File", 
            description="Upload PDF file, parse content and store to vector database, supports intelligent chunking",
            response_description="Returns processing result, including file name, processed chunk count, and document ID list")
async def upload_pdf(
    file: UploadFile = File(...),
    use_intelligent_chunking: bool = Query(True, description="Whether to use Gemini for intelligent chunking"),
    chunk_size: int = Query(1000, description="If not using intelligent chunking, fixed chunk size"),
    overlap: int = Query(200, description="If not using intelligent chunking, fixed overlap size"),
    clear_existing: bool = Query(False, description="Clear documents in database before upload"),
    db: Session = Depends(get_db),
):
    """Upload PDF file, parse content and store to vector database
    
    Upload PDF file, extract text content, process and store to vector database for later retrieval
    
    Parameters:
        file: PDF file to upload
        use_intelligent_chunking: Whether to use Gemini for intelligent chunking
        chunk_size: If not using intelligent chunking, fixed chunk size
        overlap: If not using intelligent chunking, fixed overlap size
        clear_existing: Clear database before upload, default False
        db: Database session
        
    Returns:
        Dict: Dictionary containing processing result, including file name, processed chunk count, document ID list, etc
        
    Exceptions:
        HTTPException: If processing PDF file fails
    """
    try:
        # If specified clear database
        if clear_existing:
            try:
                # Check if document_chunks table exists
                inspector = inspect(db.bind)
                tables = inspector.get_table_names()
                chunks_exists = "document_chunks" in tables
                
                # Use CASCADE parameter to handle foreign key dependencies
                if chunks_exists:
                    db.execute(text("TRUNCATE TABLE documents CASCADE"))
                else:
                    db.execute(text("TRUNCATE TABLE documents RESTART IDENTITY"))
                db.commit()
                print(f"Cleared database, preparing to import new document: {file.filename}")
            except Exception as e:
                db.rollback()
                print(f"Failed to clear database: {e}")
                # Continue processing, do not block upload
        
        # Check file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
        # Read PDF content
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        
        # Extract text
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            
        # If text is empty
        if not text.strip():
            raise HTTPException(status_code=400, detail="Cannot extract text from PDF")
        
        # Document ID to store in vector database
        document_ids = []
            
        # Try using intelligent chunking strategy
        chunking_method = "fixed_size"  # Default to fixed chunk
        
        if use_intelligent_chunking:
            try:
                print("Starting intelligent chunking...")
                chunks = await gemini_service.intelligent_chunking(text, "pdf")
                
                if chunks and len(chunks) > 0:
                    print(f"Intelligent chunking succeeded, generated {len(chunks)} chunks")
                    chunking_method = "intelligent"
                    
                    # Store chunk content
                    batch_size = 10  # Chunks to process per batch
                    
                    # Optimization: If too many chunks, first perform sampling test to reduce API calls
                    if len(chunks) > 50:
                        print(f"Document has many chunks ({len(chunks)}), first process sample chunks to avoid exceeding quota")
                        # Take sample chunks for processing (first 5, middle 5, and last 5)
                        sample_indices = list(range(0, 5)) + list(range(len(chunks)//2-2, len(chunks)//2+3)) + list(range(len(chunks)-5, len(chunks)))
                        sample_chunks = [chunks[i] for i in sample_indices]
                        
                        # Process sample chunks
                        for i, chunk_index in enumerate(sample_indices):
                            chunk_data = chunks[chunk_index]
                            document = await vector_service.add_document(
                                db, 
                                content=chunk_data["content"], 
                                metadata={
                                    "source": file.filename,
                                    "chunk": chunk_index + 1,
                                    "total_chunks": len(chunks),
                                    "strategy": "intelligent_chunking_sample",
                                    "pdf_filename": file.filename,  # Add file name field
                                    "import_timestamp": datetime.now().isoformat(),  # Add import timestamp
                                    **chunk_data.get("metadata", {})
                                }
                            )
                            document_ids.append(document.id)
                            
                        # Return only sample chunk results
                        return {
                            "success": True,
                            "filename": file.filename,
                            "chunks_processed": len(sample_indices),
                            "document_ids": document_ids,
                            "chunking_method": "intelligent_sampling",
                            "total_chunks": len(chunks),
                            "processed_chunks": len(sample_indices),
                            "note": "Since document has many chunks, only processed some sample chunks to avoid API quota limit"
                        }
                    
                    # If chunk count is moderate, process all chunks in batches
                    for i in range(0, len(chunks), batch_size):
                        batch = chunks[i:i+batch_size]
                        print(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}, size: {len(batch)}")
                        
                        # Process batch in parallel
                        tasks = []
                        for j, chunk_data in enumerate(batch):
                            chunk_index = i + j
                            task = vector_service.add_document(
                                db, 
                                content=chunk_data["content"], 
                                metadata={
                                    "source": file.filename,
                                    "chunk": chunk_index + 1,
                                    "total_chunks": len(chunks),
                                    "strategy": "intelligent_chunking",
                                    "pdf_filename": file.filename,  # Add file name field
                                    "import_timestamp": datetime.now().isoformat(),  # Add import timestamp
                                    **chunk_data.get("metadata", {})
                                }
                            )
                            tasks.append(task)
                        
                        # Wait for batch completion
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Process results
                        for result in batch_results:
                            if isinstance(result, Exception):
                                print(f"Failed to process chunk: {result}")
                            else:
                                document_ids.append(result.id)
                        
                        # Brief delay between batches to avoid sending requests too quickly
                        if i + batch_size < len(chunks):
                            await asyncio.sleep(1)
                    
                    return {
                        "success": True,
                        "filename": file.filename,
                        "chunks_processed": len(chunks),
                        "document_ids": document_ids,
                        "chunking_method": chunking_method
                    }
                else:
                    print("Intelligent chunking returned empty result, falling back to fixed chunk")
            except Exception as e:
                print(f"Intelligent chunking failed: {e}, falling back to fixed chunk")
        
        # Use traditional fixed size chunking (as fallback or default method)
        print(f"Using fixed chunking: chunk_size={chunk_size}, overlap={overlap}")
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk)
                # Keep some overlap to maintain context continuity
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk += sentence + ". "
                
        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        # Store to vector database
        for i, chunk in enumerate(chunks):
            document = await vector_service.add_document(
                db, 
                content=chunk, 
                metadata={
                    "source": file.filename,
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                    "strategy": "fixed_size",
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "pdf_filename": file.filename,  # Add file name field
                    "import_timestamp": datetime.now().isoformat()  # Add import timestamp
                }
            )
            document_ids.append(document.id)
            
        return {
            "success": True,
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "document_ids": document_ids,
            "chunking_method": "fixed_size",
            "chunk_size": chunk_size,
            "overlap": overlap
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF file: {str(e)}")

@router.post("/analyze-documents", 
            response_model=CompletionResponse, 
            summary="Analyze Document Content", 
            description="Deeply analyze document content, extract key concepts and themes",
            response_description="Returns detailed structured document analysis result")
async def analyze_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Deeply analyze document content, extract key concepts and themes
    
    Retrieve related documents and use Gemini model for deep analysis, including key concepts, theme classification, and important information points
    
    Parameters:
        request: Request object containing query text and limit count
        db: Database session
        
    Returns:
        CompletionResponse: Response object containing detailed analysis result
        
    Exceptions:
        HTTPException: If failed to analyze document
    """
    try:
        # First retrieve related documents
        results = await vector_service.search_similar(db, request.query, request.limit)
        
        if not results:
            return {"completion": "No related documents found. Please try adjusting query or increasing document library."}
        
        # Prepare context
        context = await gemini_service.prepare_context(request.query, results)
        
        # Create detailed analysis prompt
        analysis_prompt = f"""
You are a professional document analysis expert. Please perform deep analysis on the following content and extract key themes and concepts:

{context}

For query "{request.query}", please provide the following analysis:

1. Main concepts: List all key concepts mentioned in the document, each with a brief explanation.
2. Theme classification: Categorize content by theme.
3. Key points: Summarize the most important information points related to the query from the document.
4. Complete answer: Provide a comprehensive and concise answer based on document content for the user's query.

Note: If document content is truncated or incomplete, please indicate in the answer.
"""
        
        # Generate analysis
        analysis = await gemini_service.generate_completion(analysis_prompt)
        
        return {"completion": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {str(e)}")

@router.post("/clear-alloydb", 
            response_model=Dict[str, Any], 
            summary="Clear AlloyDB", 
            description="Clear all data tables in AlloyDB, this is a dangerous operation, need to confirm parameters",
            response_description="Returns operation result information")
async def clear_alloydb(confirmation: str = Query(..., description="Confirm string, must be 'confirm_clear_alloydb'")):
    """
    Clear all data tables in AlloyDB. Extremely cautious use!
    
    Clear all table data in AlloyDB database. To prevent accidental operations, need to provide confirmation parameter
    
    Parameters:
        confirmation: Confirm string, must be 'confirm_clear_alloydb'
        
    Returns:
        Dict: Dictionary containing operation result information
        
    Exceptions:
        HTTPException: If confirmation parameter is incorrect or clear operation fails
    """
    if confirmation != "confirm_clear_alloydb":
        raise HTTPException(status_code=400, detail="Need to confirm parameters to execute this operation")
    
    try:
        deleted_tables = 0
        table_counts = {}
        
        with engine.connect() as connection:
            # Get all table names
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # First delete tables not referenced (no foreign key dependencies)
            for table in tables:
                try:
                    # Get record count in table
                    count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_counts[table] = count
                    
                    # Use DELETE instead of TRUNCATE
                    connection.execute(text(f"DELETE FROM {table}"))
                    deleted_tables += 1
                except Exception as e:
                    print(f"Failed to clear table {table}: {e}")
            
            connection.commit()
            
            return {
                "status": "success", 
                "deleted_tables": deleted_tables,
                "table_counts": table_counts,
                "timestamp": datetime.now().isoformat()
            }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear AlloyDB: {str(e)}")

@router.get("/documents/{document_id}", 
           response_model=Dict[str, Any], 
           summary="Get Single Document", 
           description="Get detailed information about a single document based on ID",
           response_description="Returns document details")
async def get_document(document_id: int = Path(..., description="Document ID"), db: Session = Depends(get_db)):
    """
    Get document by specified ID
    
    Get detailed information about a single document based on document ID
    
    Parameters:
        document_id: Document's unique identifier
        db: Database session
        
    Returns:
        Dict: Dictionary containing document details
        
    Exceptions:
        HTTPException: If document does not exist or retrieval fails
    """
    try:
        # Try to get document, first try id as integer
        result = db.execute(
            text("SELECT id, title, doc_metadata, created_at FROM documents WHERE id::text = :id"),
            {"id": str(document_id)}
        ).fetchone()
        
        if not result:
            # If not found, may need to try other id format
            raise HTTPException(status_code=404, detail=f"No document found with ID {document_id}")
            
        # Safe handling doc_metadata
        try:
            metadata = result.doc_metadata
            # If it's a string, try to parse as JSON
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse document id={result.id} metadata: {e}")
                    metadata = {}
            # If not dictionary type, use empty dictionary
            elif not isinstance(metadata, dict):
                print(f"Document id={result.id} metadata is not valid JSON or dictionary: {type(metadata)}")
                metadata = {}
            
            # Delete embedding vector to reduce response size
            if "_embedding" in metadata:
                del metadata["_embedding"]
        except Exception as e:
            print(f"Failed to handle document id={result.id} metadata: {e}")
            metadata = {}
            
        return {
            "id": result.id,
            "title": result.title,
            "content": result.title,  # Use title as content return
            "metadata": metadata,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}") 
