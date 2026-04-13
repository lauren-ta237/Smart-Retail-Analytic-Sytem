from sqlalchemy import Column, Integer, String

from backend.app.core.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True)
    zone_name = Column("Zone_name", String, unique=True)
    camera_id = Column(String)

    @property
    def Zone_name(self):  # backward-compatible alias
        return self.zone_name

    @Zone_name.setter
    def Zone_name(self, value):
        self.zone_name = value