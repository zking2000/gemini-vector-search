from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func, Sequence
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.database import Base

class Document(Base):
    """Table for storing documents and their embedding vectors"""
    __tablename__ = "documents"

    # Use Sequence to explicitly specify id generation method
    id = Column(Integer, Sequence('document_id_seq'), primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)  # Replaced content with title
    doc_metadata = Column(Text, nullable=True)  # Can be stored as JSON string, including original metadata and embedding
    created_at = Column(DateTime, server_default=func.now())
    # If there's no updated_at column in the database table, remove it

    def __repr__(self):
        return f"<Document(id={self.id})>" 