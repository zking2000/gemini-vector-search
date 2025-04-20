from typing import List, Dict, Any
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text, inspect
from app.models.vector_models import Document
from app.services.gemini_service import GeminiService
import traceback
from app.services.cache_service import cached

class VectorService:
    """向量数据库服务"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
    
    async def add_document(self, db: Session, content: str, metadata: Dict[str, Any] = None) -> Document:
        """添加文档到向量数据库"""
        try:
            # 生成嵌入向量
            embedding = await self.gemini_service.generate_embedding(content)
            
            # 打印调试信息
            print(f"添加文档: 内容长度={len(content)}, 元数据={metadata}")
            print(f"嵌入向量长度={len(embedding)}")
            
            # 检查数据库表结构
            inspector = inspect(db.bind)
            table_columns = inspector.get_columns("documents")
            column_names = [col['name'] for col in table_columns]
            print(f"表结构: {column_names}")
            
            # 根据更新后的Document模型创建文档对象
            # 确保title不为空，如果内容为空，使用默认值
            if not content.strip():
                title = f"文档 #{metadata.get('chunk', '未知')} of {metadata.get('total_chunks', '未知')}" if metadata else "空文档"
            else:
                # 如果内容过长，可能需要截断
                max_title_length = 255  # String(255)的最大长度
                title = content[:max_title_length] if len(content) > max_title_length else content
            
            # 将metadata和embedding合并
            combined_metadata = metadata.copy() if metadata else {}
            # 将embedding向量添加到metadata中
            combined_metadata["_embedding"] = embedding
            
            # 确保doc_metadata是JSON字符串
            doc_metadata_json = json.dumps(combined_metadata) if combined_metadata else None
            
            # 创建文档对象 - 不指定id，让数据库生成
            doc = Document(
                title=title,
                doc_metadata=doc_metadata_json
            )
            
            # 保存到数据库
            try:
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
            except Exception as db_error:
                # 如果出现错误，回滚并重试
                db.rollback()
                print(f"数据库操作失败，尝试回滚和重试: {db_error}")
                # 再次尝试，这次显式指定一个id
                import random
                doc.id = random.randint(1, 1000000)  # 生成一个随机ID
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
                
        except Exception as e:
            print(f"添加文档到数据库时出错: {e}")
            # 确保会话被回滚
            try:
                db.rollback()
            except:
                pass
            raise
    
    @cached(ttl=24*3600)  # 缓存24小时
    async def generate_embeddings(self, text, model_name="embedding-001"):
        """
        为文本生成向量嵌入，支持缓存
        
        参数:
            text: 文本内容
            model_name: 嵌入模型名称
            
        返回:
            文本的向量表示
        """
        return await self.gemini_service.generate_embedding(text)
    
    @cached(ttl=3600)  # 缓存1小时
    async def search_similar_chunks(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        搜索与查询文本最相似的文档块，支持缓存
        
        Args:
            db: 数据库会话
            query: 查询文本
            limit: 返回结果数量限制
            source_filter: 可选的文档来源筛选
            
        Returns:
            documents: 相似文档块列表
        """
        try:
            # 记录开始搜索
            print(f"开始搜索相似文档，查询: '{query}'")
            
            # 生成查询的嵌入向量
            query_embedding = await self.generate_embeddings(query)
            query_dim = len(query_embedding)
            print(f"查询向量维度: {query_dim}")
            
            # 构建查询SQL
            sql = """
                SELECT id, title, title as content, doc_metadata
                FROM documents
            """
            
            # 添加筛选条件
            params = {}
            where_clauses = []
            
            if source_filter:
                where_clauses.append("doc_metadata::text LIKE :source")
                params["source"] = f"%{source_filter}%"
            
            # 对于中文查询，可以添加额外的文本匹配条件
            if any('\u4e00' <= c <= '\u9fff' for c in query):
                # 这是一个中文查询，添加内容匹配条件以提高召回率
                print("检测到中文查询，添加文本匹配条件")
                
                # 将中文查询拆分成单个字符，而不是整个短语
                # 对中文更有效，因为中文单字有独立含义
                chinese_chars = [c for c in query if '\u4e00' <= c <= '\u9fff']
                
                # 只选择有意义的字符（避免"是"、"的"等虚词）
                meaningful_chars = []
                common_stopwords = ["的", "是", "了", "在", "和", "与", "或", "什么", "为", "吗"]
                
                for char in chinese_chars:
                    if char not in common_stopwords and len(char.strip()) > 0:
                        meaningful_chars.append(char)
                
                # 如果有单字，添加进搜索条件
                if meaningful_chars:
                    term_conditions = []
                    for i, char in enumerate(meaningful_chars):
                        param_name = f"term_{i}"
                        term_conditions.append(f"title ILIKE :{param_name}")
                        params[param_name] = f"%{char}%"
                    
                    # 使用OR连接各个词条件
                    if term_conditions:
                        where_clauses.append(f"({' OR '.join(term_conditions)})")
                else:
                    # 如果没有找到有意义的字符，退回到原始逻辑
                    query_terms = [term for term in query.split() if len(term) > 1]
                    if query_terms:
                        term_conditions = []
                        for i, term in enumerate(query_terms):
                            param_name = f"term_{i}"
                            term_conditions.append(f"title ILIKE :{param_name}")
                            params[param_name] = f"%{term}%"
                        
                        # 使用OR连接各个词条件
                        if term_conditions:
                            where_clauses.append(f"({' OR '.join(term_conditions)})")
            
            # 组装WHERE子句
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                
            # 添加数量限制 - 增加搜索范围
            sql += " LIMIT 300"  # 增加检索的文档数量以提高查找相关内容的机会
            
            print(f"执行SQL: {sql}")
            print(f"参数: {params}")
            
            # 获取文档
            result = db.execute(text(sql), params)
            
            # 在Python中计算相似度
            documents = []
            compatible_docs = 0
            incompatible_docs = 0
            processed_docs = 0
            
            for row in result:
                processed_docs += 1
                try:
                    # 从doc_metadata中提取embedding
                    # 处理doc_metadata，可能是字典或JSON字符串
                    if row.doc_metadata is None:
                        continue
                        
                    metadata = row.doc_metadata
                    # 如果是字符串，尝试解析为JSON
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError as e:
                            print(f"解析文档id={row.id}的元数据失败: {e}")
                            continue
                    # 如果现在不是字典类型，跳过
                    if not isinstance(metadata, dict):
                        print(f"文档id={row.id}的元数据不是有效的JSON或字典: {type(metadata)}")
                        continue
                        
                    doc_embedding = metadata.get("_embedding")
                    
                    if doc_embedding:
                        doc_dim = len(doc_embedding)
                        
                        # 计算余弦相似度
                        try:
                            similarity = self.cosine_similarity(query_embedding, doc_embedding)
                            compatible_docs += 1
                            
                            # 如果是中文查询且标题包含查询词，提高相似度得分
                            if any('\u4e00' <= c <= '\u9fff' for c in query):
                                title = row.title or ""
                                query_terms = [term for term in query.split() if len(term) > 1]
                                boost = 0
                                for term in query_terms:
                                    if term in title:
                                        boost += 0.05  # 每个匹配词增加0.05的分数
                                
                                if boost > 0:
                                    original_similarity = similarity
                                    similarity = min(1.0, similarity + boost)
                                    print(f"文档id={row.id}，标题匹配提升相似度: {original_similarity} -> {similarity}")
                                    
                        except Exception as e:
                            print(f"处理文档id={row.id}时出错: {e}")
                            incompatible_docs += 1
                            continue
                        
                        # 添加源文件和导入时间信息
                        pdf_filename = metadata.get("pdf_filename", metadata.get("source", "未知来源"))
                        import_time = metadata.get("import_timestamp", "未知时间")
                        chunk_info = f"{metadata.get('chunk', '?')}/{metadata.get('total_chunks', '?')}"
                        
                        # 获取文档内容 - 优先使用content字段，如果为空则使用title
                        document_content = row.title
                        
                        # 创建文档记录
                        cleaned_metadata = {k: v for k, v in metadata.items() if not k.startswith('_')}  # 排除内部字段
                        documents.append({
                            "id": row.id,
                            "content": document_content,  # 使用实际内容，而不是简单使用title
                            "title": row.title,
                            "metadata": cleaned_metadata,
                            "similarity": float(similarity),
                            "embedding_dim": doc_dim,
                            "source": pdf_filename,
                            "chunk_info": chunk_info,
                            "import_time": import_time
                        })
                except Exception as e:
                    print(f"处理文档id={row.id}时出错: {e}")
                    continue
            
            print(f"处理了 {processed_docs} 个文档，其中 {compatible_docs} 个兼容文档，{incompatible_docs} 个不兼容文档")
            
            # 按相似度排序
            documents.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 检查是否找到足够相关的文档
            if documents and documents[0]["similarity"] < 0.5:
                print(f"警告: 最高相似度低于0.5: {documents[0]['similarity']}")
                # 如果最高相似度小于0.5，可能结果不够相关
                
            # 只返回前limit个结果
            top_results = documents[:limit]
            if top_results:
                print(f"返回 {len(top_results)} 个结果，最高相似度: {top_results[0]['similarity']}")
            else:
                print("未找到相似文档")
                
            return top_results
        except Exception as e:
            print(f"查询相似文档时出错: {e}")
            traceback.print_exc()
            return []
    
    # 添加search_similar作为search_similar_chunks的别名，确保API兼容性
    async def search_similar(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        search_similar_chunks的别名方法，保持向后兼容
        
        Args:
            db: 数据库会话
            query: 查询文本
            limit: 返回结果数量限制
            source_filter: 可选的文档来源筛选
            
        Returns:
            documents: 相似文档块列表
        """
        return await self.search_similar_chunks(db, query, limit, source_filter)
    
    def cosine_similarity(self, vec1, vec2):
        """计算两个向量的余弦相似度，支持不同维度的向量"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 检查向量维度是否不匹配
        if vec1.shape[0] != vec2.shape[0]:
            print(f"向量维度不匹配: {vec1.shape[0]} vs {vec2.shape[0]}")
            
            # 统一成较小的维度
            min_dim = min(vec1.shape[0], vec2.shape[0])
            vec1 = vec1[:min_dim]
            vec2 = vec2[:min_dim]
            print(f"截断向量至 {min_dim} 维度")
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # 避免除以零
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
            
        return dot_product / (norm_vec1 * norm_vec2) 