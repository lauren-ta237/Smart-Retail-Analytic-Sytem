from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from backend.app.core.database import Base
from backend.app.models.customer_model import Customer  # noqa: F401
from backend.app.models.zone_model import Zone  # noqa: F401
import datetime


class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=True)
    product_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


# Backward-compatible alias
interaction = Interaction