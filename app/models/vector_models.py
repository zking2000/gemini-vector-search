from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func, Sequence
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.database import Base

class Document(Base):
    """存储文档和其嵌入向量的表"""
    __tablename__ = "documents"

    # 使用Sequence来明确指定id生成方式
    id = Column(Integer, Sequence('document_id_seq'), primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)  # 将content替换为title
    doc_metadata = Column(Text, nullable=True)  # 可以存储为JSON字符串，包含原始metadata和embedding
    created_at = Column(DateTime, server_default=func.now())
    # 如果数据库表中没有updated_at列，就移除它

    def __repr__(self):
        return f"<Document(id={self.id})>" 