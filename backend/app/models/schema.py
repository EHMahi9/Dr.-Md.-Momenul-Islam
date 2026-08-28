"""
SQLAlchemy database models for sources, documents, chunks, and query logs.
Designed for PostgreSQL with pgvector, fully compatible with SQLite for local development.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)  # e.g. DOC-NHS-004
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    licence = Column(String, default="Open Government Licence v3.0")
    attribution = Column(String, default="Contains information from NHS England, licensed under the current version of the Open Government Licence.")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chunks = relationship("Chunk", back_populates="source")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True)  # e.g. DOC-NHS-004-HYB-001
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    text = Column(Text, nullable=False)
    char_length = Column(Integer, nullable=False)
    is_overview = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    source = relationship("Source", back_populates="chunks")

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_query = Column(Text, nullable=False)
    normalized_query = Column(Text, nullable=True)
    top_chunk_id = Column(String, nullable=True)
    top_chunk_score = Column(Float, nullable=True)
    strategy_used = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
