from database import Base
from sqlalchemy import Integer, String, Column, DateTime, ForeignKey, Float
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
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Embedding(Base):
    __tablename__ = "embeddings"
    
    isrc = Column(String, ForeignKey("tracks.isrc"), primary_key=True)
    embedding = Column(Vector(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PreviewEmbedding(Base):
    __tablename__ = "previewembeddings"
    
    isrc = Column(String, ForeignKey("tracks.isrc"), primary_key=True)
    embedding = Column(Vector(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DeadLetter(Base):
    __tablename__ = "deadletters"

    id = Column(Integer, primary_key=True) 
    isrc = Column(String, unique=True)# isrc code, unique for each track
    name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    failed_at = Column(DateTime(timezone=True), server_default=func.now())

class TrackCoordinate(Base):
    __tablename__ = "trackcoordinates"

    id = Column(Integer, primary_key=True)
    isrc = Column(String, unique=True)# isrc code, unique for each track

    x_coordinate = Column(Float, nullable=False)
    y_coordinate = Column(Float, nullable=False)

    name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    image_url = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
