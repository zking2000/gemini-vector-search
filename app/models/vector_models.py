from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func, Sequence
from sqlalchemy.types import TypeDecorator, UserDefinedType
from app.db.database import Base
import numpy as np

class Vector(UserDefinedType):
    def get_col_spec(self):
        return "vector(3072)"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, list):
                return value
            if isinstance(value, np.ndarray):
                return value.tolist()
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, list):
                return value
            if isinstance(value, np.ndarray):
                return value.tolist()
            return value
        return process

class Document(Base):
    """Table for storing documents and their embedding vectors"""
    __tablename__ = "documents"

    # Use Sequence to explicitly specify id generation method
    id = Column(Integer, Sequence('document_id_seq'), primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)  # Replaced content with title
    doc_metadata = Column(Text, nullable=True)  # Can be stored as JSON string, including original metadata and embedding
    embedding = Column(Vector, nullable=True)  # 使用自定义的 Vector 类型
    created_at = Column(DateTime, server_default=func.now())
    chunking_strategy = Column(String(50), nullable=True)  # 新增字段：chunking策略（fixed_size或intelligent）
    # If there's no updated_at column in the database table, remove it

    def __repr__(self):
        return f"<Document(id={self.id})>" 