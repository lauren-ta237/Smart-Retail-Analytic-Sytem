from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from backend.app.core.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(50), default='user', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
