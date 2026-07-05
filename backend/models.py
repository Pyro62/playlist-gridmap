from database import Base
from sqlalchemy import Integer, String, Column, DateTime, ForeignKey
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    spotify_id = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True) 
    isrc = Column(String, unique=True)# isrc code, unique for each track
    name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String)
    duration_ms = Column(Integer)
    preview_url = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Embedding(Base):
    __tablename__ = "embeddings"
    
    isrc = Column(String, ForeignKey("tracks.isrc"), primary_key=True)
    embedding = Column(Vector(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())