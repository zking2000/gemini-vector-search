from typing import List, Dict, Any, Optional, Tuple, Union
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text, inspect
from app.models.vector_models import Document
from app.services.gemini_service import GeminiService, APIRateLimitError
from app.services.db_service import DatabaseService
import traceback
from app.services.cache_service import cached
import time
import asyncio
from functools import wraps
from datetime import datetime
from app.db.database import get_db
import re

# 添加限流控制器
class RateLimiter:
    """API请求限流器"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内允许的最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps = []
        self._lock = asyncio.Lock()
        
    async def wait_if_needed(self) -> None:
        """检查是否可以发出新请求，必要时等待"""
        async with self._lock:
            current_time = time.time()
            
            # 移除超出时间窗口的时间戳
            self.request_timestamps = [t for t in self.request_timestamps 
                                      if current_time - t <= self.time_window]
            
            # 检查是否达到请求限制
            if len(self.request_timestamps) >= self.max_requests:
                # 计算最早请求时间加上时间窗口后的过期时间
                oldest_timestamp = min(self.request_timestamps)
                wait_time = oldest_timestamp + self.time_window - current_time
                
                if wait_time > 0:
                    print(f"API请求限流: 等待 {wait_time:.2f} 秒后继续")
                    start_wait = datetime.now().strftime("%H:%M:%S")
                    await asyncio.sleep(wait_time)
                    end_wait = datetime.now().strftime("%H:%M:%S")
                    print(f"限流等待结束 ({start_wait} -> {end_wait})")
                    # 清理超时的请求
                    current_time = time.time()
                    self.request_timestamps = [t for t in self.request_timestamps 
                                             if current_time - t <= self.time_window]
            
            # 记录新请求
            self.request_timestamps.append(current_time)

def rate_limited(func):
    """对异步函数应用速率限制的装饰器"""
    async def wrapper(self, *args, **kwargs):
        await self._rate_limiter.wait_if_needed()
        return await func(self, *args, **kwargs)
    return wrapper

class VectorService:
    """向量搜索服务，管理文档embedding和检索"""
    
    # Chinese to English keyword mapping for common terms
    # This helps bridging the gap between Chinese queries and English documents
    ZH_EN_KEYWORD_MAP = {
        # General
        "历史": ["history", "historical", "timeline", "chronicles"],
        "经济": ["economy", "economic", "finance", "financial", "market"],
        "政治": ["politics", "political", "government", "governance", "policy"],
        "社会": ["society", "social", "community", "public"],
        "文化": ["culture", "cultural", "heritage", "tradition"],
        "科学": ["science", "scientific", "research", "study"],
        "技术": ["technology", "technical", "engineering", "innovation"],
        "艺术": ["art", "artistic", "design", "creative"],
        "教育": ["education", "educational", "learning", "teaching", "academic"],
        "医学": ["medicine", "medical", "healthcare", "health", "clinical"],
        
        # Common topics
        "人工智能": ["artificial intelligence", "AI", "machine learning", "deep learning"],
        "气候变化": ["climate change", "global warming", "environmental", "sustainability"],
        "大数据": ["big data", "data analytics", "data science"],
        "区块链": ["blockchain", "cryptocurrency", "bitcoin", "distributed ledger"],
        "云计算": ["cloud computing", "cloud service", "cloud platform"],
        
        # Add more mappings as needed
    }
    
    def __init__(self, db_service: DatabaseService, gemini_service: GeminiService):
        self.db = db_service
        self.gemini = gemini_service
        self._search_cache = {}  # 搜索结果缓存
        self._rate_limiter = RateLimiter(max_requests=50, time_window=60)  # 50个请求/分钟
    
    def _expand_chinese_query(self, query: str) -> str:
        """
        Expand Chinese query with English equivalent terms to improve matching with English documents
        
        Args:
            query: Original Chinese query
            
        Returns:
            Expanded query with added English terms
        """
        expanded_terms = []
        
        # Check for each Chinese keyword in the query
        for zh_term, en_terms in self.ZH_EN_KEYWORD_MAP.items():
            if zh_term in query:
                # Add the first two English equivalent terms to avoid too much noise
                expanded_terms.extend(en_terms[:2])
        
        # If no terms were expanded but the query contains Chinese characters
        if not expanded_terms and any('\u4e00' <= c <= '\u9fff' for c in query):
            # Try to translate the query using Gemini
            try:
                import asyncio
                translate_prompt = f"Translate the following Chinese query to English for document search, keep it concise: '{query}'"
                
                # Create a temporary event loop for sync context if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're likely in a sync context being called during async execution
                        # Create a new temporary event loop
                        temp_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(temp_loop)
                        try:
                            translation = temp_loop.run_until_complete(
                                self.gemini.generate_completion(translate_prompt)
                            )
                        finally:
                            temp_loop.close()
                            asyncio.set_event_loop(loop)
                    else:
                        # Normal case, we can use the existing event loop
                        translation = loop.run_until_complete(
                            self.gemini.generate_completion(translate_prompt)
                        )
                except RuntimeError:
                    # Likely no event loop exists in this thread
                    translation = asyncio.run(
                        self.gemini.generate_completion(translate_prompt)
                    )
                
                # Clean up the translation
                translation = translation.strip('"\'').strip()
                
                # Add the translation to expanded terms if it's not empty and not already in the query
                if translation and translation.lower() not in query.lower():
                    expanded_terms.append(translation)
                
                print(f"Expanded Chinese query '{query}' with translation: '{translation}'")
            except Exception as e:
                print(f"Error translating query: {e}")
        
        # Construct the expanded query
        expanded_query = query
        if expanded_terms:
            expanded_terms_str = " ".join(expanded_terms)
            expanded_query = f"{query} {expanded_terms_str}"
            print(f"Expanded query from '{query}' to '{expanded_query}'")
        
        return expanded_query
    
    async def add_document(self, db: Session, content: str, metadata: Dict[str, Any] = None, chunking_strategy: str = None) -> Document:
        """
        Add a document to the database
        
        Args:
            db: Database session
            content: Document content
            metadata: Document metadata
            chunking_strategy: The chunking strategy used for this document ("fixed_size" or "intelligent")
        
        Returns:
            Added document object
        """
        try:
            # 确保content是字符串类型
            if content is None:
                content = ""
            elif isinstance(content, dict):
                # 尝试转换字典为字符串
                try:
                    content = json.dumps(content)
                    print(f"警告：content参数为字典类型，已自动转换为JSON字符串")
                except Exception as e:
                    raise ValueError(f"content参数必须是字符串类型，无法转换字典为JSON字符串: {e}")
            elif not isinstance(content, str):
                # 尝试进行通用转换
                try:
                    content = str(content)
                    print(f"警告：content参数为{type(content).__name__}类型，已自动转换为字符串")
                except Exception as e:
                    raise ValueError(f"content参数必须是字符串类型，无法转换{type(content).__name__}类型: {e}")
            
            # Generate embedding vector
            embedding = await self.gemini.generate_embedding(content)
            
            # Print debug information
            print(f"Adding document: content length={len(content)}, metadata={metadata}, chunking_strategy={chunking_strategy}")
            print(f"Embedding vector length={len(embedding)}")
            
            # Check database table structure
            inspector = inspect(db.bind)
            table_columns = inspector.get_columns("documents")
            column_names = [col['name'] for col in table_columns]
            print(f"Table structure: {column_names}")
            
            # Create document object based on updated Document model
            # Ensure title is not empty, use default value if content is empty
            if not content.strip():
                title = f"Document #{metadata.get('chunk', 'Unknown')} of {metadata.get('total_chunks', 'Unknown')}" if metadata else "Empty document"
            else:
                # If content is too long, it may need to be truncated
                max_title_length = 255  # Maximum length of String(255)
                title = content[:max_title_length] if len(content) > max_title_length else content
            
            # Merge metadata and embedding
            combined_metadata = metadata.copy() if metadata else {}
            # Add embedding vector to metadata
            combined_metadata["_embedding"] = embedding
            
            # Ensure doc_metadata is a JSON string
            doc_metadata_json = json.dumps(combined_metadata) if combined_metadata else None
            
            # Create document object - don't specify id, let database generate it
            doc = Document(
                title=title,
                doc_metadata=doc_metadata_json,
                chunking_strategy=chunking_strategy
            )
            
            # Save to database
            try:
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
            except Exception as db_error:
                # If error occurs, rollback and retry
                db.rollback()
                print(f"Database operation failed, trying rollback and retry: {db_error}")
                # Try again, this time explicitly specify an id
                import random
                doc.id = random.randint(1, 1000000)  # Generate a random ID
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
                
        except Exception as e:
            print(f"Error adding document to database: {e}")
            # Ensure session is rolled back
            try:
                db.rollback()
            except:
                pass
            raise
    
    @cached(ttl=24*3600)  # Cache for 24 hours
    @rate_limited
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本的embedding向量
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding向量列表
        """
        # 优化批处理大小，根据文本数量动态调整
        total_texts = len(texts)
        batch_size = 5  # 默认批次大小
        
        # 对大量文本优化批次大小
        if total_texts > 100:
            batch_size = 20
        elif total_texts > 50:
            batch_size = 10
            
        # 使用Gemini服务的批处理功能
        return await self.gemini.generate_embeddings_batch(texts, batch_size)
    
    @cached(ttl=3600)  # Cache for 1 hour
    async def search_similar_chunks(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search for document chunks most similar to the query text, with cache support
        
        Args:
            db: Database session
            query: Query text
            limit: Maximum number of results to return
            source_filter: Optional document source filter
            
        Returns:
            documents: List of similar document chunks
        """
        try:
            # Record search start
            print(f"Starting search for similar documents, query: '{query}'")
            
            # Check if it's a Chinese query and expand with English terms if needed
            is_chinese_query = any('\u4e00' <= c <= '\u9fff' for c in query)
            
            if is_chinese_query:
                # Expand the query with English equivalents to improve matching
                expanded_query = self._expand_chinese_query(query)
                
                # Use the expanded query for embedding generation if it's different
                if expanded_query != query:
                    print(f"Using expanded query for embedding: '{expanded_query}'")
                    embedding_query = expanded_query
                else:
                    embedding_query = query
            else:
                embedding_query = query
            
            # Generate embedding vector for query
            embeddings = await self.generate_embeddings([embedding_query])
            query_embedding = embeddings[0]
            query_dim = len(query_embedding)
            print(f"Query vector dimension: {query_dim}")
            
            # Build query SQL
            sql = """
                SELECT id, title, title as content, doc_metadata
                FROM documents
            """
            
            # Add filter conditions
            params = {}
            where_clauses = []
            
            if source_filter:
                where_clauses.append("doc_metadata::text LIKE :source")
                params["source"] = f"%{source_filter}%"
            
            # For Chinese queries, add additional text matching conditions
            if is_chinese_query:
                # This is a Chinese query, add content matching conditions to improve recall
                print("Chinese query detected, adding text matching conditions")
                
                # Split Chinese query into individual characters rather than phrases
                # More effective for Chinese where individual characters have meaning
                chinese_chars = [c for c in query if '\u4e00' <= c <= '\u9fff']
                
                # Only select meaningful characters (avoid filler words like "的", "是", etc.)
                meaningful_chars = []
                common_stopwords = ["的", "是", "了", "在", "和", "与", "或", "什么", "为", "吗"]
                
                for char in chinese_chars:
                    if char not in common_stopwords and len(char.strip()) > 0:
                        meaningful_chars.append(char)
                
                # Add English equivalent terms for title matching
                english_terms = []
                for zh_term, en_terms in self.ZH_EN_KEYWORD_MAP.items():
                    if zh_term in query:
                        english_terms.extend(en_terms)
                
                # Combine all terms for search condition
                all_search_terms = []
                
                # Add Chinese character conditions if available
                if meaningful_chars:
                    for i, char in enumerate(meaningful_chars):
                        all_search_terms.append((f"term_zh_{i}", f"%{char}%"))
                
                # Add English term conditions
                for i, term in enumerate(english_terms):
                    all_search_terms.append((f"term_en_{i}", f"%{term}%"))
                
                # If expanded_query has additional terms, add them too
                if is_chinese_query and expanded_query != query:
                    for i, term in enumerate(expanded_query.split()):
                        if term not in query and len(term) > 2:  # Only non-trivial additional terms
                            all_search_terms.append((f"term_ex_{i}", f"%{term}%"))
                
                # Build the query conditions
                if all_search_terms:
                    term_conditions = []
                    for param_name, param_value in all_search_terms:
                        term_conditions.append(f"title ILIKE :{param_name}")
                        params[param_name] = param_value
                    
                    # Connect term conditions with OR
                    if term_conditions:
                        where_clauses.append(f"({' OR '.join(term_conditions)})")
            else:
                # Regular English query, use standard word tokenization
                query_terms = [term for term in query.split() if len(term) > 2]  # Skip very short words
                if query_terms:
                    term_conditions = []
                    for i, term in enumerate(query_terms):
                        param_name = f"term_{i}"
                        term_conditions.append(f"title ILIKE :{param_name}")
                        params[param_name] = f"%{term}%"
                    
                    # Connect term conditions with OR
                    if term_conditions:
                        where_clauses.append(f"({' OR '.join(term_conditions)})")
            
            # Assemble WHERE clause
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                
            # Add limit - increase search range
            sql += " LIMIT 300"  # Increase document retrieval count to improve chances of finding relevant content
            
            print(f"Executing SQL: {sql}")
            print(f"Parameters: {params}")
            
            # Get documents
            result = db.execute(text(sql), params)
            
            # Calculate similarity in Python
            documents = []
            compatible_docs = 0
            incompatible_docs = 0
            processed_docs = 0
            
            for row in result:
                processed_docs += 1
                try:
                    # Extract embedding from doc_metadata
                    # Process doc_metadata, which may be dictionary or JSON string
                    if row.doc_metadata is None:
                        continue
                        
                    metadata = row.doc_metadata
                    # If it's a string, try to parse as JSON
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse metadata for document id={row.id}: {e}")
                            continue
                    # If not a dictionary type, skip
                    if not isinstance(metadata, dict):
                        print(f"Metadata for document id={row.id} is not a valid JSON or dictionary: {type(metadata)}")
                        continue
                        
                    doc_embedding = metadata.get("_embedding")
                    
                    if doc_embedding:
                        doc_dim = len(doc_embedding)
                        
                        # Calculate cosine similarity
                        try:
                            similarity = self.cosine_similarity(query_embedding, doc_embedding)
                            compatible_docs += 1
                            
                            # If Chinese query, boost relevance for documents with matching expanded terms
                            if is_chinese_query:
                                title = row.title or ""
                                boost = 0
                                
                                # Boost for English equivalent terms
                                for zh_term, en_terms in self.ZH_EN_KEYWORD_MAP.items():
                                    if zh_term in query:
                                        for en_term in en_terms:
                                            if en_term.lower() in title.lower():
                                                boost += 0.08  # Higher boost for mapped term matches
                                
                                # Add general term match boost as before
                                query_terms = [term for term in query.split() if len(term) > 1]
                                for term in query_terms:
                                    if term in title:
                                        boost += 0.05
                                
                                # Apply the total boost
                                if boost > 0:
                                    original_similarity = similarity
                                    similarity = min(1.0, similarity + boost)
                                    print(f"Document id={row.id}, cross-lingual match boosts similarity: {original_similarity:.4f} -> {similarity:.4f}")
                                    
                        except Exception as e:
                            print(f"Error processing document id={row.id}: {e}")
                            incompatible_docs += 1
                            continue
                        
                        # Add source file and import time information
                        pdf_filename = metadata.get("pdf_filename", metadata.get("source", "Unknown source"))
                        import_time = metadata.get("import_timestamp", "Unknown time")
                        chunk_info = f"{metadata.get('chunk', '?')}/{metadata.get('total_chunks', '?')}"
                        
                        # Get document content - use content field if available, otherwise use title
                        document_content = row.title
                        
                        # Create document record
                        cleaned_metadata = {k: v for k, v in metadata.items() if not k.startswith('_')}  # Exclude internal fields
                        documents.append({
                            "id": row.id,
                            "content": document_content,  # Use actual content, not just title
                            "title": row.title,
                            "metadata": cleaned_metadata,
                            "similarity": float(similarity),
                            "embedding_dim": doc_dim,
                            "source": pdf_filename,
                            "chunk_info": chunk_info,
                            "import_time": import_time
                        })
                except Exception as e:
                    print(f"Error processing document id={row.id}: {e}")
                    continue
            
            print(f"Processed {processed_docs} documents, with {compatible_docs} compatible documents and {incompatible_docs} incompatible documents")
            
            # Sort by similarity
            documents.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Check if we found sufficiently relevant documents
            if documents and documents[0]["similarity"] < 0.5:
                print(f"Warning: Highest similarity below 0.5: {documents[0]['similarity']}")
                # If highest similarity is less than 0.5, results may not be relevant enough
                
            # Only return top 'limit' results
            top_results = documents[:limit]
            if top_results:
                print(f"Returning {len(top_results)} results, highest similarity: {top_results[0]['similarity']}")
            else:
                print("No similar documents found")
                
            return top_results
        except Exception as e:
            print(f"Error querying similar documents: {e}")
            traceback.print_exc()
            return []
    
    # Add search_similar as an alias for search_similar_chunks to ensure API compatibility
    async def search_similar(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        Alias method for search_similar_chunks, maintains backward compatibility
        
        Args:
            db: Database session
            query: Query text
            limit: Maximum number of results to return
            source_filter: Optional document source filter
            
        Returns:
            documents: List of similar document chunks
        """
        return await self.search_similar_chunks(db, query, limit, source_filter)
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors, supporting different dimensions"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Check if vector dimensions don't match
        if vec1.shape[0] != vec2.shape[0]:
            print(f"Vector dimensions don't match: {vec1.shape[0]} vs {vec2.shape[0]}")
            
            # Standardize to smaller dimension
            min_dim = min(vec1.shape[0], vec2.shape[0])
            vec1 = vec1[:min_dim]
            vec2 = vec2[:min_dim]
            print(f"Truncated vectors to {min_dim} dimensions")
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # Avoid division by zero
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
            
        return dot_product / (norm_vec1 * norm_vec2)

    @rate_limited
    async def _compare_search_strategies_internal(self, db: Session, query: str, limit: int = 5, source_filter: Optional[str] = None) -> Dict:
        """内部方法：比较不同分块策略的搜索效果
        
        Args:
            db: 数据库会话
            query: 搜索查询
            limit: 返回结果数量
            source_filter: 可选的来源过滤器
            
        Returns:
            包含不同策略结果的比较字典
        """
        print(f"比较查询 '{query}' 的不同分块策略效果")
        
        # 生成查询向量
        start_time = time.time()
        query_embedding = await self.gemini.generate_embedding(query)
        embedding_time = (time.time() - start_time) * 1000  # 毫秒
        print(f"查询向量生成时间: {embedding_time:.2f}ms")
        
        # 定义要比较的策略
        strategies = ["fixed_size", "intelligent"]
        
        # 为每个策略收集结果
        results = {}
        
        for strategy in strategies:
            start_time = time.time()
            try:
                # 根据策略和向量搜索文档
                strategy_filter = f"metadata->>chunking_strategy = '{strategy}'"
                if source_filter:
                    combined_filter = f"({strategy_filter}) AND (metadata->>source LIKE '%{source_filter}%')"
                else:
                    combined_filter = strategy_filter
                
                # 执行搜索
                print(f"使用 {strategy} 策略搜索...")
                # 修改：不再使用不支持的custom_filter参数
                # db_results = await self.db.search_documents(
                #     query_embedding, 
                #     limit=limit, 
                #     custom_filter=combined_filter
                # )
                
                # 使用搜索策略参数
                # 先按策略搜索文档
                db_results = await self.db.search_documents_by_strategy(
                    query_embedding,
                    strategy=strategy,
                    limit=limit
                )
                
                # 调试输出：检查search_documents_by_strategy返回的结果格式
                print(f"search_documents_by_strategy返回结果数: {len(db_results)}")
                if db_results:
                    first_doc = db_results[0]
                    print(f"第一个文档数据结构: {list(first_doc.keys())}")
                    # 检查嵌入向量字段存在哪里
                    if "score" in first_doc:
                        print(f"score值: {first_doc.get('score')}")
                    
                    metadata = first_doc.get("metadata", {})
                    print(f"元数据字段: {list(metadata.keys())}")
                
                # 如果需要source_filter，在Python中进一步过滤
                if source_filter and db_results:
                    filtered_results = [
                        doc for doc in db_results 
                        if doc.get("metadata", {}).get("source", "").lower().find(source_filter.lower()) != -1
                    ]
                    print(f"应用source_filter后，结果从 {len(db_results)} 减少到 {len(filtered_results)}")
                    # 确保结果数不超过limit
                    db_results = filtered_results[:limit]
                
                # 测量时间
                search_time = (time.time() - start_time) * 1000  # 毫秒
                
                # 为每个文档附加分数
                documents = []
                total_similarity = 0
                
                for doc in db_results:
                    # 计算相似度分数
                    # 修复：从doc_metadata中提取embedding，而不是直接使用doc.get("embedding", [])
                    # 先尝试获取_embedding字段
                    try:
                        # 从元数据中获取embedding
                        doc_metadata = doc.get("metadata", {})
                        if not doc_metadata and isinstance(doc.get("doc_metadata"), str):
                            try:
                                doc_metadata = json.loads(doc.get("doc_metadata", "{}"))
                            except json.JSONDecodeError:
                                print(f"无法解析文档 {doc.get('id')} 的元数据JSON")
                                doc_metadata = {}
                                
                        # 尝试从元数据中获取embedding
                        doc_embedding = None
                        if "_embedding" in doc_metadata:
                            doc_embedding = doc_metadata.get("_embedding")
                        else:
                            # search_documents_by_strategy可能会将embedding放在不同位置
                            doc_embedding = doc.get("embedding", [])
                        
                        if not doc_embedding:
                            print(f"文档 {doc.get('id')} 没有embedding向量")
                            continue
                            
                        # 计算相似度
                        similarity = self.cosine_similarity(query_embedding, doc_embedding)
                        total_similarity += similarity
                        
                        document = {
                            "id": doc.get("id"),
                            "content": doc.get("content", "").strip(),
                            "score": similarity,
                            "metadata": doc.get("metadata", {})
                        }
                        documents.append(document)
                    except Exception as e:
                        print(f"处理文档 {doc.get('id')} 时出错: {str(e)}")
                        continue
                
                # 计算平均相似度
                avg_similarity = total_similarity / len(documents) if documents else 0
                
                # 存储结果
                results[strategy] = {
                    "count": len(documents),
                    "documents": documents,
                    "avg_similarity": avg_similarity,
                    "time_ms": search_time,
                    "source_filter": source_filter,
                    "strategy": strategy
                }
                
                print(f"{strategy} 策略找到 {len(documents)} 个文档，用时 {search_time:.2f}ms，平均相似度 {avg_similarity:.4f}")
                
            except Exception as e:
                print(f"{strategy} 策略搜索失败: {str(e)}")
                results[strategy] = {
                    "count": 0,
                    "documents": [],
                    "avg_similarity": 0,
                    "time_ms": 0,
                    "source_filter": source_filter,
                    "strategy": strategy,
                    "error": str(e)
                }
        
        # 确定最佳策略
        # 优先考虑：1) 有结果的策略；2) 平均相似度更高的策略；3) 如果相似度接近，考虑速度
        best_strategy = None
        best_score = -1
        
        for strategy in strategies:
            if strategy not in results:
                continue
                
            # 评分标准：相似度超过门槛值(0.75)的基础分，每个文档0.5分，相似度(0-1.0)乘以10，时间加成(最高1分)
            strategy_results = results[strategy]
            
            # 如果没有结果或者相似度过低，给一个低分
            if strategy_results["count"] == 0 or strategy_results["avg_similarity"] < 0.5:
                strategy_score = 0
            else:
                # 计算时间加成 (越快越高，最高1分)
                time_bonus = min(1.0, 2000 / max(strategy_results["time_ms"], 100))
                
                # 相似度加权
                similarity_score = strategy_results["avg_similarity"] * 10
                
                # 文档数量加权 (每个文档0.5分，最高5分)
                doc_count_score = min(5.0, strategy_results["count"] * 0.5)
                
                # 综合评分
                strategy_score = similarity_score + doc_count_score + time_bonus
            
            # 更新最佳策略
            if strategy_score > best_score:
                best_score = strategy_score
                best_strategy = strategy
        
        # 如果无法确定最佳策略，默认使用fixed_size
        if best_strategy is None:
            best_strategy = "fixed_size"
            
        # 评估原因
        evaluation_reason = "无法确定评估原因"
        if results[best_strategy]["count"] > 0:
            if best_strategy == "intelligent":
                if results["intelligent"]["avg_similarity"] > results["fixed_size"]["avg_similarity"]:
                    evaluation_reason = "智能分块策略找到相似度更高的文档"
                elif results["intelligent"]["count"] > results["fixed_size"]["count"]:
                    evaluation_reason = "智能分块策略找到更多相关文档"
                else:
                    evaluation_reason = "智能分块策略综合表现更好"
            else:
                if results["fixed_size"]["avg_similarity"] > results["intelligent"]["avg_similarity"]:
                    evaluation_reason = "固定分块策略找到相似度更高的文档"
                elif results["fixed_size"]["count"] > results["intelligent"]["count"]:
                    evaluation_reason = "固定分块策略找到更多相关文档"
                elif results["fixed_size"]["time_ms"] < results["intelligent"]["time_ms"]:
                    evaluation_reason = "固定分块策略检索速度更快"
                else:
                    evaluation_reason = "固定分块策略综合表现更好"
        else:
            evaluation_reason = "所有策略都未找到相关文档"
        
        # 创建与原始格式兼容的结构
        response = {
            "strategies": results,
            "best_strategy": best_strategy,
            "query": query,
            "evaluation": {
                "strategy": best_strategy,
                "reason": evaluation_reason,
                "scores": {
                    "fixed_size": {
                        "similarity": results["fixed_size"]["avg_similarity"],
                        "count": results["fixed_size"]["count"],
                        "time_ms": results["fixed_size"]["time_ms"]
                    },
                    "intelligent": {
                        "similarity": results["intelligent"]["avg_similarity"],
                        "count": results["intelligent"]["count"],
                        "time_ms": results["intelligent"]["time_ms"]
                    }
                }
            }
        }
        
        return response

    async def compare_search_strategies(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """比较不同的分块策略效果
        
        Args:
            query: 搜索查询
            limit: 限制返回结果数
            
        Returns:
            比较结果数据
        """
        # 生成查询缓存键
        cache_key = f"strategy_compare:{query}:{limit}"
        
        # 检查缓存
        if cache_key in self._search_cache:
            print(f"使用缓存的策略比较结果 - 查询: '{query}'")
            return self._search_cache[cache_key]
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 执行比较
            result = await self._compare_search_strategies_internal(db, query, limit)
            
            # 缓存结果
            self._search_cache[cache_key] = result
            
            return result
        except Exception as e:
            print(f"比较搜索策略失败: {str(e)}")
            traceback.print_exc()
            
            # 返回空结果结构
            return {
                "strategies": {
                    "fixed_size": {
                        "count": 0,
                        "documents": [],
                        "avg_similarity": 0,
                        "time_ms": 0
                    },
                    "intelligent": {
                        "count": 0,
                        "documents": [],
                        "avg_similarity": 0,
                        "time_ms": 0
                    }
                },
                "best_strategy": "fixed_size",
                "query": query,
                "evaluation": {
                    "strategy": "fixed_size",
                    "reason": "比较搜索策略时出错"
                }
            }

    async def add_documents_batch(self, db: Session, documents: List[Dict], batch_size: int = 10) -> List[Dict]:
        """批量添加文档，优化API调用
        
        根据文档总数自动调整批次大小，提供进度更新，并估计剩余时间
        
        Args:
            db: 数据库会话
            documents: 待添加的文档列表
            batch_size: 每批次处理的文档数，默认10
            
        Returns:
            成功添加的文档列表
        """
        start_time = time.time()
        total_docs = len(documents)
        processed_docs = 0
        successful_docs = []
        failed_docs = []
        
        # 根据总文档数自动调整批次大小
        if total_docs > 1000:
            batch_size = 50
        elif total_docs > 500:
            batch_size = 30
        elif total_docs > 100:
            batch_size = 20
        elif total_docs > 50:
            batch_size = 15
        
        print(f"开始批量处理 {total_docs} 个文档，批次大小: {batch_size}")
        
        batch_start_time = time.time()
        batch_times = []
        
        # 分批处理文档
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_count = len(batch)
            
            try:
                # 生成嵌入向量
                print(f"批次 {i//batch_size + 1}: 为 {batch_count} 个文档生成嵌入向量")
                batch_texts = [doc.get('content', '') for doc in batch]
                embeddings = await self.generate_embeddings(batch_texts)
                
                # 添加文档到数据库
                for j, doc in enumerate(batch):
                    try:
                        if not doc.get('content'):
                            print(f"警告: 跳过空内容文档 #{i + j + 1}")
                            failed_docs.append({**doc, "error": "空内容"})
                            continue
                            
                        doc_with_embedding = {
                            **doc,
                            "embedding": embeddings[j] if j < len(embeddings) else None
                        }
                        
                        if doc_with_embedding["embedding"] is None:
                            print(f"警告: 文档 #{i + j + 1} 嵌入向量生成失败")
                            failed_docs.append({**doc, "error": "嵌入向量生成失败"})
                            continue
                        
                        # 在这里使用传入的数据库会话
                        added_doc = await self.db.add_document(
                            db=db,
                            content=doc_with_embedding.get('content', ''),
                            embedding=doc_with_embedding.get('embedding'),
                            metadata=doc_with_embedding.get('metadata', {}),
                            chunking_strategy=doc_with_embedding.get('chunking_strategy', 'fixed_size')
                        )
                        
                        successful_docs.append(added_doc)
                        
                    except Exception as e:
                        print(f"添加文档 #{i + j + 1} 失败: {str(e)}")
                        failed_docs.append({**doc, "error": str(e)})
                
                processed_docs += batch_count
                
                # 计算进度和估计剩余时间
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                batch_times.append(batch_duration)
                
                avg_batch_time = sum(batch_times) / len(batch_times)
                remaining_batches = (total_docs - processed_docs) / batch_size
                est_remaining_time = remaining_batches * avg_batch_time
                
                progress = (processed_docs / total_docs) * 100
                print(f"进度: {progress:.1f}% ({processed_docs}/{total_docs})")
                print(f"批次用时: {batch_duration:.2f}秒, 估计剩余时间: {est_remaining_time:.2f}秒")
                
                # 重置批次开始时间
                batch_start_time = time.time()
                
                # 批次间添加小延迟，避免请求过于密集
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"处理批次失败: {str(e)}")
                traceback.print_exc()
                # 继续处理下一批
        
        total_duration = time.time() - start_time
        print(f"批量处理完成，总用时: {total_duration:.2f}秒")
        print(f"成功: {len(successful_docs)}, 失败: {len(failed_docs)}")
        
        return successful_docs

    @rate_limited
    async def search(self, query: str, limit: int = 5, source_filter: Optional[str] = None) -> List[Dict]:
        """搜索相似文档，带速率限制
        
        Args:
            query: 搜索查询
            limit: 返回结果数量
            source_filter: 可选的来源过滤器
            
        Returns:
            相似文档列表
        """
        # 生成查询缓存键
        cache_key = f"{query}:{limit}:{source_filter}"
        
        # 检查缓存
        if cache_key in self._search_cache:
            print("使用缓存的搜索结果")
            return self._search_cache[cache_key]
        
        try:
            # 生成查询向量
            query_embedding = await self.gemini.generate_embedding(query)
            
            # 搜索向量数据库
            results = await self.db.search_documents(
                query_embedding, 
                limit=limit,
                source_filter=source_filter
            )
            
            # 缓存结果
            self._search_cache[cache_key] = results
            return results
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

    async def add_documents(self, db: Session, documents: List[Dict]) -> List[Dict]:
        """将多个文档添加到数据库
        
        Args:
            db: 数据库会话
            documents: 要添加的文档列表，每个文档应包含 content 和可选的 metadata
            
        Returns:
            成功添加的文档列表
        """
        return await self.add_documents_batch(db, documents, batch_size=10) 