from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    """文档基础模型"""
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentCreate(BaseModel):
    """
    创建文档的请求模型
    """
    content: str = Field(..., description="文档的文本内容，这将被转换为嵌入向量", 
                        example="向量数据库是一种专门用于存储和检索向量的数据库系统。它允许用户通过相似度搜索找到语义上相似的内容。")
    metadata: Optional[Dict[str, Any]] = Field({}, description="文档的元数据，可以包含任意键值对",
                                              example={"source": "技术文档.pdf", "author": "张三", "date": "2024-05-01"})

class DocumentResponse(BaseModel):
    """
    文档响应模型
    """
    id: Any = Field(..., description="文档的唯一标识符")
    content: str = Field(..., description="文档的文本内容")
    metadata: Optional[Dict[str, Any]] = Field({}, description="文档的元数据")
    
    class Config:
        from_attributes = True

class EmbeddingRequest(BaseModel):
    """
    生成嵌入向量的请求模型
    """
    text: str = Field(..., description="需要生成嵌入向量的文本内容", 
                      example="向量搜索是指通过相似度查询在高维向量空间中找到最接近查询向量的文档")

class EmbeddingResponse(BaseModel):
    """
    嵌入向量的响应模型
    """
    embedding: List[float] = Field(..., description="生成的嵌入向量，通常是一个浮点数数组")

class CompletionRequest(BaseModel):
    """
    文本补全请求模型
    """
    prompt: str = Field(..., description="需要补全的文本提示", 
                       example="请解释什么是向量数据库以及它的主要优势")
    use_context: bool = Field(False, description="是否使用上下文文档辅助生成")
    context_query: Optional[str] = Field(None, description="用于检索上下文的查询文本，仅当use_context为true时有效",
                                        example="向量数据库 优势 特点")
    max_context_docs: int = Field(5, description="最大上下文文档数量，建议1-10之间", ge=1, le=20)

class CompletionResponse(BaseModel):
    """
    文本补全响应模型
    """
    completion: str = Field(..., description="生成的补全文本")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="调试信息，仅当请求中设置debug=true时返回")

class QueryRequest(BaseModel):
    """
    查询请求模型
    """
    query: str = Field(..., description="搜索查询文本，系统会为此生成嵌入向量", 
                      example="向量搜索的工作原理是什么？")
    limit: int = Field(5, description="返回结果的最大数量，默认为5，建议1-20之间", ge=1, le=20)

class QueryResponse(BaseModel):
    """
    查询响应模型
    """
    results: List[Dict[str, Any]] = Field(..., description="查询结果列表，每个结果包含文档内容、元数据和相似度分数")
    context: Optional[str] = Field(None, description="为LLM准备的上下文文本，由结果内容合并而成")
    summary: Optional[str] = Field(None, description="对查询结果的摘要分析") 