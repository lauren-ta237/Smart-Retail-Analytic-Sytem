from sqlalchemy import text

from backend.app.core.database import Base, engine
from backend.app.models.customer_model import Customer
from backend.app.models.interaction_model import Interaction
from backend.app.models.zone_event_model import ZoneEvent
from backend.app.models.zone_model import Zone

print("Creating tables...")
Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS tracker_id INTEGER"))
    connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS entry_time TIMESTAMP"))
    connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP"))
    connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS exit_time TIMESTAMP"))
    connection.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS visit_duration INTEGER"))
    connection.execute(text("UPDATE customers SET last_seen = entry_time WHERE last_seen IS NULL AND entry_time IS NOT NULL"))
    connection.execute(text("ALTER TABLE interactions ADD COLUMN IF NOT EXISTS zone_id INTEGER"))
    connection.execute(text("ALTER TABLE interactions ADD COLUMN IF NOT EXISTS product_id INTEGER"))
    connection.execute(text("ALTER TABLE interactions ADD COLUMN IF NOT EXISTS action VARCHAR(50)"))

print("Done.")