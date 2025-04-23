"""
数据库服务模块，提供向量数据库操作功能
"""
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_, and_
from app.models.vector_models import Document
from datetime import datetime


class DatabaseService:
    """数据库操作服务，提供向量数据库的CRUD操作"""
    
    def __init__(self, db_session: Session):
        """
        初始化数据库服务
        
        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db = db_session
    
    async def add_document(self, content: str, embedding: List[float], 
                          metadata: Dict[str, Any] = None, 
                          chunking_strategy: str = None) -> Document:
        """
        添加文档到数据库
        
        Args:
            content: 文档内容
            embedding: 文档的向量表示
            metadata: 文档元数据
            chunking_strategy: 分块策略
            
        Returns:
            添加的文档对象
        """
        try:
            # 准备元数据字段，确保包含embedding
            combined_metadata = metadata.copy() if metadata else {}
            combined_metadata["_embedding"] = embedding
            
            # 转换为JSON字符串
            metadata_json = json.dumps(combined_metadata)
            
            # 创建标题（使用内容的前255个字符）
            max_title_length = 255
            title = content[:max_title_length] if len(content) > max_title_length else content
            
            # 创建文档对象
            doc = Document(
                title=title,
                doc_metadata=metadata_json,
                chunking_strategy=chunking_strategy
            )
            
            # 保存到数据库
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            
            return doc
        except Exception as e:
            self.db.rollback()
            print(f"添加文档失败: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict]) -> List[Document]:
        """
        批量添加文档到数据库
        
        Args:
            documents: 文档列表，每个文档包含content、embedding和metadata
            
        Returns:
            添加的文档对象列表
        """
        added_docs = []
        
        try:
            for doc_data in documents:
                content = doc_data.get("content", "")
                embedding = doc_data.get("embedding", [])
                metadata = doc_data.get("metadata", {})
                chunking_strategy = doc_data.get("chunking_strategy")
                
                # 添加文档
                doc = await self.add_document(
                    content=content,
                    embedding=embedding,
                    metadata=metadata,
                    chunking_strategy=chunking_strategy
                )
                
                added_docs.append(doc)
            
            return added_docs
        except Exception as e:
            print(f"批量添加文档失败: {e}")
            return added_docs  # 返回成功添加的部分
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            相似度得分 (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 确保向量维度一致
        if vec1.shape[0] != vec2.shape[0]:
            # 取较小的维度
            min_dim = min(vec1.shape[0], vec2.shape[0])
            vec1 = vec1[:min_dim]
            vec2 = vec2[:min_dim]
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # 避免除零错误
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
            
        return float(dot_product / (norm_vec1 * norm_vec2))
    
    async def search_documents(self, query_embedding: List[float], 
                              limit: int = 5, 
                              source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query_embedding: 查询向量
            limit: 最大结果数
            source_filter: 来源过滤条件
            
        Returns:
            相似文档列表
        """
        try:
            # 构建基础查询
            sql = """
                SELECT id, title, doc_metadata
                FROM documents
            """
            
            # 添加过滤条件
            params = {}
            where_clauses = []
            
            if source_filter:
                where_clauses.append("doc_metadata::text ILIKE :source")
                params["source"] = f"%{source_filter}%"
            
            # 组装WHERE子句
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            # 增加查询范围，后续在Python中排序
            sql += " LIMIT 300"
            
            # 执行查询
            result = self.db.execute(text(sql), params)
            
            # 计算相似度并排序
            documents = []
            
            for row in result:
                try:
                    # 从元数据中提取向量
                    if row.doc_metadata is None:
                        continue
                    
                    # 解析元数据JSON
                    metadata = row.doc_metadata
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            continue
                    
                    doc_embedding = metadata.get("_embedding")
                    
                    if doc_embedding:
                        # 计算相似度
                        similarity = self.cosine_similarity(query_embedding, doc_embedding)
                        
                        # 清理元数据，排除内部字段
                        cleaned_metadata = {k: v for k, v in metadata.items() if not k.startswith('_')}
                        
                        # 添加文档
                        documents.append({
                            "id": row.id,
                            "title": row.title,
                            "content": row.title,  # 使用title作为content
                            "metadata": cleaned_metadata,
                            "similarity": similarity,
                            "chunking_strategy": metadata.get("chunking_strategy")
                        })
                except Exception as e:
                    print(f"处理文档id={row.id}时出错: {e}")
                    continue
            
            # 按相似度排序
            documents.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 返回前limit个结果
            return documents[:limit]
            
        except Exception as e:
            print(f"搜索文档时出错: {e}")
            return []
    
    async def search_documents_by_strategy(self, query_embedding: List[float], 
                                          strategy: str,
                                          limit: int = 5) -> List[Dict[str, Any]]:
        """
        根据分块策略搜索文档
        
        Args:
            query_embedding: 查询向量
            strategy: 分块策略 (fixed_size, paragraph等)
            limit: 最大结果数
            
        Returns:
            相似文档列表
        """
        try:
            # 构建带策略过滤的查询
            sql = """
                SELECT id, title, doc_metadata
                FROM documents
                WHERE chunking_strategy = :strategy
            """
            
            # 添加过滤条件
            params = {"strategy": strategy}
            
            # 增加查询范围
            sql += " LIMIT 300"
            
            # 执行查询
            result = self.db.execute(text(sql), params)
            
            # 计算相似度并排序
            documents = []
            
            for row in result:
                try:
                    # 处理元数据
                    if row.doc_metadata is None:
                        continue
                    
                    metadata = row.doc_metadata
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            continue
                    
                    doc_embedding = metadata.get("_embedding")
                    
                    if doc_embedding:
                        # 计算相似度
                        similarity = self.cosine_similarity(query_embedding, doc_embedding)
                        
                        # 创建文档记录
                        cleaned_metadata = {k: v for k, v in metadata.items() if not k.startswith('_')}
                        documents.append({
                            "id": row.id,
                            "content": row.title,
                            "metadata": cleaned_metadata,
                            "score": similarity,
                            "chunking_strategy": strategy,
                            "embedding": doc_embedding  # 添加embedding向量以便外部代码访问
                        })
                except Exception as e:
                    print(f"处理文档id={row.id}时出错: {e}")
                    continue
            
            # 按相似度排序
            documents.sort(key=lambda x: x["score"], reverse=True)
            
            # 返回前limit个结果
            return documents[:limit]
            
        except Exception as e:
            print(f"根据策略搜索文档时出错: {e}")
            return []
    
    async def get_documents_count(self, strategy: Optional[str] = None) -> int:
        """
        获取文档数量
        
        Args:
            strategy: 可选的分块策略过滤
            
        Returns:
            文档数量
        """
        try:
            query = self.db.query(func.count(Document.id))
            
            if strategy:
                query = query.filter(Document.chunking_strategy == strategy)
                
            return query.scalar() or 0
        except Exception as e:
            print(f"获取文档数量时出错: {e}")
            return 0
    
    async def delete_document(self, document_id: int) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否成功删除
        """
        try:
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            
            if not doc:
                return False
                
            self.db.delete(doc)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"删除文档时出错: {e}")
            return False 