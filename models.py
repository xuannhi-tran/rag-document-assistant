from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    upload_date = Column(DateTime, nullable=False, server_default = func.now())
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    # Browser-generated random id. NULL = legacy row from before sessions existed;
    # such rows never match any session and are removed by app/purge.py.
    session_id = Column(String(36), nullable=True, index=True)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(384), nullable=False)

    document = relationship("Document", back_populates="chunks")