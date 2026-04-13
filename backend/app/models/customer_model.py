import datetime

from sqlalchemy import Column, DateTime, Integer

from backend.app.core.database import Base


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    tracker_id = Column(Integer, index=True)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    exit_time = Column(DateTime, nullable=True)
    visit_duration = Column(Integer, nullable=True)