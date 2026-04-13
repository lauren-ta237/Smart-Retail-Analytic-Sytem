from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# import routes 
from backend.app.api import routes_analytics, routes_customers, routes_products, routes_auth
from backend.app.core.config import settings 
from backend.app.core.database import Base, engine
from backend.app.models import customer_model, interaction_model, zone_event_model, zone_model, user_model  # noqa: F401
from backend.app.utils.logger import setup_logger

# setup logging
logger = setup_logger()

app = FastAPI(
    title= 'Smart Retail Vision Analytics API',
    description= 'API backend for smart retail analytic system',
    version= '1.0.0'
)


@app.on_event('startup')
def ensure_database_schema():
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
    logger.info('Database schema ensured for dashboard analytics')

# enable cors for frontend
app.add_middleware(
    CORSMiddleware,
allow_origins = settings.ALLOWED_ORIGINS, 
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*']
)

# include API routes 
app.include_router(routes_auth.router, prefix='/api/auth', tags=['Auth'])
app.include_router(routes_analytics.router, prefix='/api/analytics',
                   tags=['Analytics'])
app.include_router(routes_customers.router, prefix='/api/customers',
                   tags=['Customers'])
app.include_router(routes_products.router, prefix='/api/products',
                   tags=['Products'])

dashboard_dir = Path(__file__).resolve().parents[2] / 'frontend' / 'dashboard'
if dashboard_dir.exists():
    app.mount('/dashboard', StaticFiles(directory=str(dashboard_dir), html=True), name='dashboard')

# root endpoint
@app.get('/')
async def root():
    return {'message': 'Smart Retail Vision Analytics Backend is running!'}