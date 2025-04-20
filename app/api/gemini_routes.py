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

# 创建一个统一的路由器，不再需要分开认证和非认证
router = APIRouter(prefix="/api/v1")
health_router = APIRouter(prefix="/api/v1")

# 创建服务实例
gemini_service = GeminiService()
vector_service = VectorService()

# 健康检查端点 - 不需要认证
@health_router.get("/health", 
                  summary="API健康检查", 
                  description="检查API服务是否正常运行，无需认证",
                  response_description="返回API服务的健康状态和当前时间戳")
async def health():
    """
    健康检查端点，用于验证服务是否正常运行
    
    不需要认证，可用于监控系统检查API可用性
    
    返回:
        dict: 包含状态和时间戳的字典
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 数据库状态端点 - 不需要认证
@health_router.get("/database-status", 
                  summary="数据库连接状态", 
                  description="检查数据库连接状态，无需认证",
                  response_description="返回数据库连接状态和当前时间戳")
async def database_status():
    """
    检查数据库连接状态
    
    不需要认证，可用于监控系统检查API可用性
    
    返回:
        dict: 包含数据库连接状态和时间戳的字典
        
    异常:
        HTTPException: 如果数据库连接失败
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
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")

# 以下所有端点都不需要认证

@router.post("/embedding", 
            response_model=EmbeddingResponse, 
            summary="生成文本嵌入向量", 
            description="将文本转换为嵌入向量表示，用于向量检索",
            response_description="返回生成的向量表示")
async def create_embedding(
    request: EmbeddingRequest,
):
    """
    生成文本的嵌入向量
    
    使用Gemini嵌入模型将输入文本转换为向量表示，用于相似度搜索
    
    参数:
        request: 包含待转换文本的请求对象
        
    返回:
        EmbeddingResponse: 包含嵌入向量的响应对象
        
    异常:
        HTTPException: 如果嵌入生成失败
    """
    try:
        embedding = await gemini_service.generate_embedding(request.text)
        return {"embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成嵌入失败: {str(e)}")

@router.post("/completion", 
            response_model=CompletionResponse, 
            summary="生成文本补全", 
            description="使用Gemini模型生成文本补全，可选择是否使用向量数据库中的相关文档作为上下文",
            response_description="返回生成的补全文本")
async def create_completion(
    request: CompletionRequest,
    db: Session = Depends(get_db),
):
    """
    生成文本补全
    
    使用Gemini模型生成文本补全，可选择是否使用向量数据库中的相关文档作为上下文
    
    参数:
        request: 包含提示文本和上下文配置的请求对象
        db: 数据库会话
        
    返回:
        CompletionResponse: 包含生成的补全文本的响应对象
        
    异常:
        HTTPException: 如果生成补全失败
    """
    try:
        context = None
        
        # 如果需要使用上下文
        if request.use_context and request.context_query:
            # 获取相似文档
            similar_docs = await vector_service.search_similar(
                db, 
                request.context_query, 
                request.max_context_docs
            )
            
            # 准备上下文
            if similar_docs:
                context = await gemini_service.prepare_context(request.context_query, similar_docs)
        
        # 生成补全
        completion = await gemini_service.generate_completion(request.prompt, context)
        return {"completion": completion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成补全失败: {str(e)}")

@router.post("/documents", 
            response_model=DocumentResponse, 
            summary="添加文档", 
            description="将单个文档添加到向量数据库，生成其嵌入向量用于后续检索",
            response_description="返回添加的文档信息")
async def add_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
):
    """
    添加文档到向量数据库
    
    将单个文档添加到数据库，生成其嵌入向量用于后续检索
    
    参数:
        request: 包含文档内容和元数据的请求对象
        db: 数据库会话
        
    返回:
        DocumentResponse: 包含新添加文档信息的响应对象
        
    异常:
        HTTPException: 如果添加文档失败
    """
    try:
        document = await vector_service.add_document(db, request.content, request.metadata)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加文档失败: {str(e)}")

@router.post("/query", 
            response_model=QueryResponse, 
            summary="查询相似文档", 
            description="在向量数据库中搜索与查询文本相似的文档，并返回详细信息",
            response_description="返回相似文档列表、上下文和摘要分析")
async def query_documents(
    request: QueryRequest,
    source_filter: Optional[str] = Query(None, description="按文档来源筛选结果", example="document1.pdf"),
    db: Session = Depends(get_db),
):
    """
    查询向量数据库中的相似文档
    
    在向量数据库中搜索与查询文本相似的文档，并返回详细信息、上下文和摘要分析
    
    参数:
        request: 包含查询文本和配置的请求对象
        source_filter: 可选的文档来源筛选条件
        db: 数据库会话
        
    返回:
        QueryResponse: 包含相似文档、上下文和摘要的响应对象
        
    异常:
        HTTPException: 如果查询失败
    """
    try:
        results = await vector_service.search_similar(db, request.query, request.limit, source_filter)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询相似文档失败: {str(e)}")

@router.post("/integration", 
            response_model=CompletionResponse, 
            summary="集成查询", 
            description="结合向量检索和文本生成的一体化API，可按文档来源筛选结果并返回详细调试信息",
            response_description="返回基于相关文档内容生成的回答")
async def integration_query(
    request: CompletionRequest,
    source_filter: Optional[str] = Query(None, description="按文档来源筛选结果", example="document1.pdf"),
    debug: bool = Query(False, description="返回详细的调试信息"),
    force_use_documents: bool = Query(False, description="强制使用文档内容回答，即使没有找到高相似度的匹配"),
    db: Session = Depends(get_db),
):
    """
    集成API：向量查询并将结果添加到提示中
    
    结合向量检索和文本生成的一体化API，可按文档来源筛选结果并返回详细调试信息
    
    参数:
        request: 包含提示文本和上下文查询的请求对象
        source_filter: 按文档来源筛选结果，例如特定的PDF文件名
        debug: 是否返回详细的调试信息
        force_use_documents: 强制使用文档内容回答，即使没有找到高相似度的匹配
        db: 数据库会话
        
    返回:
        CompletionResponse: 包含生成的回答的响应对象，如启用debug则包含调试信息
        
    异常:
        HTTPException: 如果集成查询失败
    """
    try:
        print(f"收到集成查询请求: {request.prompt}")
        print(f"上下文查询: {request.context_query or request.prompt}")
        
        # 判断是否为中文查询
        is_chinese_query = any('\u4e00' <= c <= '\u9fff' for c in request.prompt)
        print(f"是否为中文查询: {is_chinese_query}")
        
        # 先查询相关文档
        search_query = request.context_query or request.prompt
        
        # 对搜索查询进行扩展，提高对中文内容的匹配能力
        expanded_terms = []
        if "道教" in search_query:
            expanded_terms = ["道教", "老子", "道德经", "太上老君", "张道陵", "太极", "阴阳", "天师道", "五斗米道", "全真道"]
        elif "佛教" in search_query:
            expanded_terms = ["佛教", "释迦牟尼", "佛陀", "菩萨", "禅宗", "佛经", "如来", "佛祖", "涅槃", "菩提"]
        elif is_chinese_query:
            # 为其他中文查询添加一些常见的中文哲学和宗教术语
            expanded_terms = ["中国", "哲学", "历史", "传统", "文化", "典籍", "经典"]
        
        if expanded_terms:
            search_query = f"{search_query} {' '.join(expanded_terms)}"
            print(f"扩展后的搜索查询: {search_query}")
        
        # 增加返回的文档数量，提高找到相关内容的概率
        max_context_docs = request.max_context_docs
        if is_chinese_query:
            max_context_docs = max(max_context_docs, 10)  # 中文查询至少返回10个文档
        
        similar_docs = await vector_service.search_similar(
            db, 
            search_query, 
            max_context_docs,
            source_filter
        )
        
        print(f"找到 {len(similar_docs)} 个相关文档")
        
        # 为调试目的，打印前几个文档的内容片段
        if similar_docs:
            print("前3个文档内容片段:")
            for i, doc in enumerate(similar_docs[:3]):
                content_preview = doc.get("content", "")[:100].replace("\n", " ")
                similarity = doc.get("similarity", 0)
                print(f"  [{i+1}] 相似度:{similarity:.4f} - {content_preview}...")
        
        # 准备上下文
        context = None
        if similar_docs:
            context = await gemini_service.prepare_context(
                request.context_query or request.prompt, 
                similar_docs
            )
            print(f"生成上下文，长度: {len(context) if context else 0}")
        else:
            print("未找到相关文档")
        
        # 生成补全
        completion_prompt = request.prompt
        if context:
            if is_chinese_query:
                completion_prompt = f"""
你是一个知识渊博的助手，特别擅长回答中国历史和文化问题。
请基于以下参考资料回答用户的问题。如果参考资料中没有相关信息，请明确指出并说明哪些信息是缺失的。

参考资料:
{context}

用户问题: {request.prompt}

请用中文回答，并尽量详细解释相关概念。如果参考资料不足，请说明你的回答是基于一般知识而非系统中的文档。
"""
            else:
                completion_prompt = f"""
你是一个知识渊博的助手，特别擅长回答历史和文化问题。
请基于以下参考资料回答用户的问题。如果参考资料中没有相关信息，请明确指出。

参考资料:
{context}

用户问题: {request.prompt}
"""
        else:
            # 如果没有找到相关文档但用户强制要求使用文档内容
            if force_use_documents:
                # 获取系统中现有的文档
                try:
                    # 查询文档总数
                    doc_count = db.execute(text("SELECT COUNT(*) FROM documents")).scalar()
                    
                    # 如果有文档，尝试获取一些样本内容
                    if doc_count > 0:
                        # 获取最近的几个文档标题和来源
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
                            
                            source = metadata.get("source", "未知来源")
                            doc_samples.append(f"- ID: {doc.id}, 来源: {source}, 标题: {doc.title[:50]}...")
                        
                        doc_list = "\n".join(doc_samples)
                        
                        if is_chinese_query:
                            completion_prompt = f"""
你是一个知识渊博的助手，特别擅长回答中国历史和文化问题。

我检索了数据库中的所有文档（共{doc_count}个），但未能找到与"{request.prompt}"直接相关的内容。
以下是数据库中的一些文档示例:
{doc_list}

由于您选择了强制使用文档模式，我必须基于系统中的文档来回答。然而，系统中可能没有包含与这个问题相关的信息。

请对比您的问题和系统中的文档内容，考虑：
1. 是否需要重新上传包含相关信息的文档
2. 是否需要调整查询的表述方式以更好地匹配现有文档
3. 是否需要扩展系统的文档库来涵盖这个主题

用户问题: {request.prompt}

请用中文回答，并明确指出系统中可能缺少相关文档。
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
                    print(f"获取文档统计信息时出错: {e}")
                    # 使用默认提示
            
            if not force_use_documents:
                if is_chinese_query:
                    completion_prompt = f"""
你是一个知识渊博的助手，特别擅长回答中国历史和文化问题。
我没有找到任何与"{request.prompt}"相关的参考资料。请基于你的知识回答，但请明确指出你的回答不是基于系统中的文档内容。

可能的原因包括:
1. 数据库中可能没有包含相关主题的文档
2. 查询的表述方式与文档内容不匹配
3. 相关文档的向量表示与查询的向量表示相似度不够高

用户问题: {request.prompt}

请用中文回答，并尽量详细解释相关概念。同时，请明确说明你的回答是基于一般知识而非系统中的文档。
"""
                else:
                    completion_prompt = f"""
你是一个知识渊博的助手，特别擅长回答历史和文化问题。
我没有找到任何与"{request.prompt}"相关的参考资料。请基于你的知识回答，但请明确指出你的回答不是基于系统中的文档内容。

用户问题: {request.prompt}
"""
        
        print(f"生成补全提示，长度: {len(completion_prompt)}")
        completion = await gemini_service.generate_completion(completion_prompt)
        
        # 如果启用调试模式，返回更多信息
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
                                     "文档ID: " + str(d.get("id", "未知ID"))
                        } 
                        for d in similar_docs[:5]
                    ] if similar_docs else []
                }
            }
        
        return {"completion": completion}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"集成查询失败: {str(e)}")

@router.get("/documents", 
           response_model=List[Dict[str, Any]], 
           summary="获取文档列表", 
           description="获取文档列表，支持分页和按来源筛选",
           response_description="返回文档列表")
async def get_documents(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="返回的最大文档数量"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    source: Optional[str] = Query(None, description="按文档来源筛选")
):
    """
    获取文档列表，支持分页和筛选
    
    获取存储在数据库中的文档列表，支持分页和按来源筛选
    
    参数:
        db: 数据库会话
        limit: 返回的最大文档数量，范围1-100
        offset: 分页偏移量，用于分页查询
        source: 按文档来源筛选，例如特定的PDF文件名
        
    返回:
        List[Dict]: 文档列表，每个文档包含ID、标题、内容、元数据和创建时间
        
    异常:
        HTTPException: 如果获取文档列表失败
    """
    try:
        # 构建查询条件
        query = "SELECT id, title, doc_metadata, created_at FROM documents"
        params = {}
        
        if source:
            query += " WHERE doc_metadata::text LIKE :source"
            params["source"] = f"%{source}%"
            
        # 添加排序和分页
        query += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        # 执行查询
        result = db.execute(text(query), params).fetchall()
        
        # 处理结果
        documents = []
        for row in result:
            # 安全处理doc_metadata
            try:
                metadata = row.doc_metadata
                # 如果是字符串，尝试解析为JSON
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError as e:
                        print(f"解析文档id={row.id}的元数据失败: {e}")
                        metadata = {}
                # 如果不是字典类型，使用空字典
                elif not isinstance(metadata, dict):
                    print(f"文档id={row.id}的元数据不是有效的JSON或字典: {type(metadata)}")
                    metadata = {}
                
                # 删除嵌入向量以减少响应大小
                if "_embedding" in metadata:
                    del metadata["_embedding"]
            except Exception as e:
                print(f"处理文档id={row.id}的元数据时出错: {e}")
                metadata = {}
                
            documents.append({
                "id": row.id,
                "title": row.title,
                "content": row.title,  # 这里使用title作为content返回
                "metadata": metadata,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
            
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.post("/upload-pdf", 
            response_model=Dict[str, Any], 
            summary="上传PDF文件", 
            description="上传PDF文件，解析内容并存储到向量数据库，支持智能分块",
            response_description="返回处理结果，包括文件名、处理的块数量和文档ID列表")
async def upload_pdf(
    file: UploadFile = File(...),
    use_intelligent_chunking: bool = Query(True, description="是否使用Gemini进行智能分块"),
    chunk_size: int = Query(1000, description="如果不使用智能分块，固定分块大小"),
    overlap: int = Query(200, description="如果不使用智能分块，固定重叠大小"),
    clear_existing: bool = Query(False, description="上传前是否清空数据库中的文档"),
    db: Session = Depends(get_db),
):
    """上传PDF文件，解析内容并存储到向量数据库
    
    上传PDF文件，提取文本内容，分块处理并存储到向量数据库用于后续检索
    
    参数:
        file: 要上传的PDF文件
        use_intelligent_chunking: 是否使用Gemini进行智能分块
        chunk_size: 如果不使用智能分块，固定分块大小
        overlap: 如果不使用智能分块，固定重叠大小
        clear_existing: 上传前是否清空数据库，默认为False
        db: 数据库会话
        
    返回:
        Dict: 包含处理结果的字典，包括文件名、处理的块数量、文档ID列表等
        
    异常:
        HTTPException: 如果处理PDF文件失败
    """
    try:
        # 如果指定了清空数据库
        if clear_existing:
            try:
                # 检查document_chunks表是否存在
                inspector = inspect(db.bind)
                tables = inspector.get_table_names()
                chunks_exists = "document_chunks" in tables
                
                # 使用CASCADE参数处理外键依赖
                if chunks_exists:
                    db.execute(text("TRUNCATE TABLE documents CASCADE"))
                else:
                    db.execute(text("TRUNCATE TABLE documents RESTART IDENTITY"))
                db.commit()
                print(f"已清空数据库，准备导入新文档: {file.filename}")
            except Exception as e:
                db.rollback()
                print(f"清空数据库时出错: {e}")
                # 继续处理，不阻止上传
        
        # 检查文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
            
        # 读取PDF内容
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        
        # 提取文本
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            
        # 如果文本为空
        if not text.strip():
            raise HTTPException(status_code=400, detail="无法从PDF提取文本")
        
        # 存储到向量数据库的文档ID
        document_ids = []
            
        # 尝试使用智能分块策略
        chunking_method = "fixed_size"  # 默认为固定分块
        
        if use_intelligent_chunking:
            try:
                print("开始智能分块...")
                chunks = await gemini_service.intelligent_chunking(text, "pdf")
                
                if chunks and len(chunks) > 0:
                    print(f"智能分块成功，生成了{len(chunks)}个块")
                    chunking_method = "intelligent"
                    
                    # 存储分块内容
                    batch_size = 10  # 每批处理的块数
                    
                    # 优化：如果块太多，先进行采样测试以减少API调用
                    if len(chunks) > 50:
                        print(f"文档块数较多 ({len(chunks)}个)，先处理样本块以避免超出配额")
                        # 取样本块进行处理（前5个、中间5个和最后5个）
                        sample_indices = list(range(0, 5)) + list(range(len(chunks)//2-2, len(chunks)//2+3)) + list(range(len(chunks)-5, len(chunks)))
                        sample_chunks = [chunks[i] for i in sample_indices]
                        
                        # 处理样本块
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
                                    "pdf_filename": file.filename,  # 添加文件名字段
                                    "import_timestamp": datetime.now().isoformat(),  # 添加导入时间戳
                                    **chunk_data.get("metadata", {})
                                }
                            )
                            document_ids.append(document.id)
                            
                        # 只返回样本块的结果
                        return {
                            "success": True,
                            "filename": file.filename,
                            "chunks_processed": len(sample_indices),
                            "document_ids": document_ids,
                            "chunking_method": "intelligent_sampling",
                            "total_chunks": len(chunks),
                            "processed_chunks": len(sample_indices),
                            "note": "由于文档块数较多，只处理了部分样本块以避免API配额限制"
                        }
                    
                    # 如果块数适中，按批处理所有块
                    for i in range(0, len(chunks), batch_size):
                        batch = chunks[i:i+batch_size]
                        print(f"处理批次 {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}, 大小: {len(batch)}")
                        
                        # 并行处理批次
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
                                    "pdf_filename": file.filename,  # 添加文件名字段
                                    "import_timestamp": datetime.now().isoformat(),  # 添加导入时间戳
                                    **chunk_data.get("metadata", {})
                                }
                            )
                            tasks.append(task)
                        
                        # 等待批次完成
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # 处理结果
                        for result in batch_results:
                            if isinstance(result, Exception):
                                print(f"处理块时出错: {result}")
                            else:
                                document_ids.append(result.id)
                        
                        # 在批次之间短暂延迟，避免过快发送请求
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
                    print("智能分块返回空结果，回退到固定分块")
            except Exception as e:
                print(f"智能分块失败: {e}，回退到固定分块")
        
        # 使用传统的固定大小分块（作为备选或默认方法）
        print(f"使用固定分块: chunk_size={chunk_size}, overlap={overlap}")
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                chunks.append(current_chunk)
                # 保留一些重叠，以维持上下文连贯性
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk += sentence + ". "
                
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
            
        # 存储到向量数据库
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
                    "pdf_filename": file.filename,  # 添加文件名字段
                    "import_timestamp": datetime.now().isoformat()  # 添加导入时间戳
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
        raise HTTPException(status_code=500, detail=f"处理PDF文件失败: {str(e)}")

@router.post("/analyze-documents", 
            response_model=CompletionResponse, 
            summary="分析文档内容", 
            description="深入分析文档内容，提取关键概念和主题",
            response_description="返回详细的结构化文档分析结果")
async def analyze_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    深入分析文档内容，提取关键概念和主题
    
    检索相关文档并使用Gemini模型提供深入分析，包括关键概念、主题分类和重要信息点
    
    参数:
        request: 包含查询文本和限制数量的请求对象
        db: 数据库会话
        
    返回:
        CompletionResponse: 包含详细分析结果的响应对象
        
    异常:
        HTTPException: 如果分析文档失败
    """
    try:
        # 首先检索相关文档
        results = await vector_service.search_similar(db, request.query, request.limit)
        
        if not results:
            return {"completion": "未找到相关文档。请尝试调整查询或增加文档库。"}
        
        # 准备上下文
        context = await gemini_service.prepare_context(request.query, results)
        
        # 创建详细的分析提示
        analysis_prompt = f"""
你是一位专业的文档分析专家。请对以下内容进行深入分析，并提取关键主题和概念：

{context}

针对查询 "{request.query}"，请提供以下分析：

1. 主要概念：列出文档提到的所有关键概念，每个概念配以简短的解释。
2. 主题分类：将内容按主题进行分类。
3. 关键要点：总结文档中与查询相关的最重要信息点。
4. 完整回答：基于文档内容，对用户的查询提供全面且简洁的回答。

注意：如果文档内容被截断或不完整，请在回答中说明。
"""
        
        # 生成分析
        analysis = await gemini_service.generate_completion(analysis_prompt)
        
        return {"completion": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析文档失败: {str(e)}")

@router.post("/clear-alloydb", 
            response_model=Dict[str, Any], 
            summary="清空AlloyDB", 
            description="清空AlloyDB中的所有数据表，这是一个危险操作，需要确认参数",
            response_description="返回操作结果信息")
async def clear_alloydb(confirmation: str = Query(..., description="确认字符串，必须为'confirm_clear_alloydb'")):
    """
    清空AlloyDB中的所有数据表。极度谨慎使用！
    
    清空AlloyDB数据库中的所有表数据。为防止意外操作，需要提供确认参数
    
    参数:
        confirmation: 确认字符串，必须为'confirm_clear_alloydb'
        
    返回:
        Dict: 包含操作结果信息的字典
        
    异常:
        HTTPException: 如果确认参数不正确或清空操作失败
    """
    if confirmation != "confirm_clear_alloydb":
        raise HTTPException(status_code=400, detail="需要确认参数才能执行此操作")
    
    try:
        deleted_tables = 0
        table_counts = {}
        
        with engine.connect() as connection:
            # 获取所有表名
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # 先删除没有被引用的表(无外键依赖)
            for table in tables:
                try:
                    # 获取表中的记录数
                    count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_counts[table] = count
                    
                    # 使用DELETE而不是TRUNCATE
                    connection.execute(text(f"DELETE FROM {table}"))
                    deleted_tables += 1
                except Exception as e:
                    print(f"清空表 {table} 时出错: {e}")
            
            connection.commit()
            
            return {
                "status": "success", 
                "deleted_tables": deleted_tables,
                "table_counts": table_counts,
                "timestamp": datetime.now().isoformat()
            }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"清空AlloyDB时出错: {str(e)}")

@router.get("/documents/{document_id}", 
           response_model=Dict[str, Any], 
           summary="获取单个文档", 
           description="根据ID获取单个文档的详细信息",
           response_description="返回文档详情")
async def get_document(document_id: int = Path(..., description="文档ID"), db: Session = Depends(get_db)):
    """
    获取指定ID的文档
    
    根据文档ID获取单个文档的详细信息
    
    参数:
        document_id: 文档的唯一标识符
        db: 数据库会话
        
    返回:
        Dict: 包含文档详情的字典
        
    异常:
        HTTPException: 如果文档不存在或获取失败
    """
    try:
        # 尝试获取文档，首先尝试id作为整数
        result = db.execute(
            text("SELECT id, title, doc_metadata, created_at FROM documents WHERE id::text = :id"),
            {"id": str(document_id)}
        ).fetchone()
        
        if not result:
            # 如果没找到，可能需要尝试其他id格式
            raise HTTPException(status_code=404, detail=f"未找到ID为{document_id}的文档")
            
        # 安全处理doc_metadata
        try:
            metadata = result.doc_metadata
            # 如果是字符串，尝试解析为JSON
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError as e:
                    print(f"解析文档id={result.id}的元数据失败: {e}")
                    metadata = {}
            # 如果不是字典类型，使用空字典
            elif not isinstance(metadata, dict):
                print(f"文档id={result.id}的元数据不是有效的JSON或字典: {type(metadata)}")
                metadata = {}
            
            # 删除嵌入向量以减少响应大小
            if "_embedding" in metadata:
                del metadata["_embedding"]
        except Exception as e:
            print(f"处理文档id={result.id}的元数据时出错: {e}")
            metadata = {}
            
        return {
            "id": result.id,
            "title": result.title,
            "content": result.title,  # 这里使用title作为content返回
            "metadata": metadata,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}") 
