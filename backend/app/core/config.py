from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # App Configuration
    APP_NAME: str = 'Smart Retail Analytics'
    APP_ENV: str = 'development'
    DEBUG: bool = True

    # Security
    API_KEY: str = 'sra_4c8d9e2f1a6b7d3c9e0f4a1b6d'
    SECURITY_SECRET_KEY: str = 'sra_4c8d9e2f1a6b7d3c9e0f4a1b6d'
    SECURITY_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = 'postgresql://postgres:l#urenT-123@localhost:5432/retail_db'

    # Backend
    BACKEND_HOST: str = '0.0.0.0'
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: list = ['http://localhost:3000']

    # Redis
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379

    # Camera Configuration
    CAMERA_1_SOURCE: str = '0'
    CAMERA_2_SOURCE: str = 'rtsp://192.168.1.100:554/stream'

    # Model Paths
    PERSON_MODEL: str = 'vision/models/yolov8n.pt'
    PRODUCT_MODEL: str = 'vision/models/product_detector.pt'

    # Tracking Configuration
    TRACKER_TYPE: str = 'bytetrack'
    TRACK_MAX_AGE: int = 30
    TRACK_CONFIDENCE: float = 0.4

    # GPU/Device Configuration
    DEVICE: str = 'cuda'
    GPU_MEMORY_LIMIT: int = 4096

    # Data Directories
    DATA_DIR: str = 'data'
    VIDEO_STORAGE: str = 'data/videos'
    HEATMAP_STORAGE: str = 'data/heatmaps'
    LOG_DIR: str = 'data/logs'

    # OpenAI Configuration
    OPENAI_API_KEY: str = ''
    OPENAI_MODEL: str = 'gpt-4o-mini'
    OPENAI_TIMEOUT: int = 20

    # YOLO Configuration
    YOLO_IMGSZ: int = 640
    YOLO_IOU: float = 0.45
    YOLO_MAX_DET: int = 40
    YOLO_PERSON_ONLY: bool = True
    YOLO_VID_STRIDE: int = 1

    # Vision Service Configuration
    VISION_REQUEST_TIMEOUT: float = 2.0
    VISION_POST_INTERVAL: float = 1.0


settings = Settings()