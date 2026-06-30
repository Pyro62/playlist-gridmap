from database import Base
from sqlalchemy import Integer, String, Column, DateTime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    spotify_id = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)