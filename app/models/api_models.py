from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    """Document Base Model"""
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentCreate(BaseModel):
    """
    Document Creation Request Model
    """
    content: str = Field(..., description="Text content of the document, which will be converted to an embedding vector", 
                        example="Vector databases are database systems specifically designed for storing and retrieving vectors. They allow users to find semantically similar content through similarity search.")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Document metadata, can contain arbitrary key-value pairs",
                                              example={"source": "technical_document.pdf", "author": "John Smith", "date": "2024-05-01"})

class DocumentResponse(BaseModel):
    """
    Document Response Model
    """
    id: Any = Field(..., description="Unique identifier of the document")
    content: str = Field(..., description="Text content of the document")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Document metadata")
    
    class Config:
        from_attributes = True

class EmbeddingRequest(BaseModel):
    """
    Embedding Vector Generation Request Model
    """
    text: str = Field(..., description="Text content for generating embedding vector", 
                      example="Vector search refers to finding documents in a high-dimensional vector space that are closest to the query vector based on similarity")

class EmbeddingResponse(BaseModel):
    """
    Embedding Vector Response Model
    """
    embedding: List[float] = Field(..., description="Generated embedding vector, typically an array of floating-point numbers")

class CompletionRequest(BaseModel):
    """
    Text Completion Request Model
    """
    prompt: str = Field(..., description="Text prompt to be completed", 
                       example="Please explain what a vector database is and its main advantages")
    use_context: bool = Field(False, description="Whether to use context documents to assist generation")
    context_query: Optional[str] = Field(None, description="Query text for retrieving context, only effective when use_context is true",
                                        example="vector database advantages features")
    max_context_docs: int = Field(5, description="Maximum number of context documents, recommended between 1-10", ge=1, le=20)

class CompletionResponse(BaseModel):
    """
    Text Completion Response Model
    """
    completion: str = Field(..., description="Generated completion text")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information, only returned when debug=true is set in the request")

class QueryRequest(BaseModel):
    """
    Query Request Model
    """
    query: str = Field(..., description="Search query text, for which an embedding vector will be generated", 
                      example="How does vector search work?")
    limit: int = Field(5, description="Maximum number of results to return, default is 5, recommended between 1-20", ge=1, le=20)

class QueryResponse(BaseModel):
    """
    Query Response Model
    """
    results: List[Dict[str, Any]] = Field(..., description="List of query results, each containing document content, metadata, and similarity score")
    context: Optional[str] = Field(None, description="Context text prepared for LLM, merged from result contents")
    summary: Optional[str] = Field(None, description="Summary analysis of query results") 