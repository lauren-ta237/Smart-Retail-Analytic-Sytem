import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer

from backend.app.core.database import Base


class ZoneEvent(Base):
    __tablename__ = "zone_events"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    exit_time = Column(DateTime, nullable=True)


# Backward-compatible alias
zone_event = ZoneEvent
