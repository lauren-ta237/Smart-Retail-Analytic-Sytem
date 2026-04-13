# Smart Retail Vision Analytics

A professional-grade, end-to-end retail intelligence platform. This system leverages Computer Vision (YOLO + ByteTrack) to monitor shopper behavior and integrates LLM-powered agents to provide actionable business insights in real-time.

## 🚀 System Architecture

- **Vision Pipeline**: Real-time person tracking, entry/exit gating, and zone-based interaction detection.
- **AI Agent**: A robust LLM service that analyzes historical and live data to suggest staffing adjustments and product promotions.
- **Backend**: High-performance FastAPI server with JWT authentication, secure user management, and automated session cleanup.
- **Infrastructure**: Dockerized environment for consistent deployment and scalability.
- **Dashboard**: A responsive analytics interface featuring real-time alerts, trend visualizations, and professional reporting (CSV/JSON/PDF).

### 2.5 Docker Deployment (Recommended)
To spin up the entire stack including the database:
```powershell
docker-compose up --build
```

### 2.6 Running Tests
```powershell
pytest tests/
```

## 🛠️ Prerequisites

- Python 3.9+
- OpenRouter API Key (for the Retail AI Agent)
- A webcam or IP camera feed

## ⚙️ Installation & Setup

### 1. Environment Configuration
Create a `.env` file in the root directory and configure the following variables:
```env
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=google/gemini-2.0-flash-lite-preview-02-05:free
VISION_ENTRY_CONFIRM_FRAMES=3
VISION_EXIT_GRACE_SECONDS=5.0
```

### 2. Backend Services
The backend handles data persistence and the AI logic.
```powershell
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn backend.app.main:app --reload
```

### 3. Vision Pipeline
This process handles the real-time video processing and sends events to the backend.
```powershell
# Run the tracking system
python scripts/run_vision.py
```
*Note: For best results, use an overhead or entrance-facing camera view.*

### 4. Accessing the Dashboard
Once the backend is running, open your browser to:
`http://127.0.0.1:8000/dashboard/`

## 📊 Key Features

### Intelligent Tracking
The system uses **ByteTrack** for robust person identification, even during temporary occlusions. It features an **Entry Zone Confirmation** step to prevent false positives from background movement.

### AI-Driven Insights
Powered by `RobustLLMService`, the system generates:
- **Key Insights**: Analysis of customer behavior patterns.
- **Staffing Recommendations**: Optimization of floor coverage based on peak hours.
- **Product Hotspots**: Identification of high-engagement items and zones.

### Operational Alerts
Real-time browser notifications for:
- High in-store traffic congestion.
- Sudden entry surges.
- System anomalies or API quota warnings.

## 🔒 Security
- **JWT Authentication**: All analytics endpoints are protected via Bearer tokens.
- **Input Validation**: Strict regex-based username validation and secure password hashing via `bcrypt`.
- **Audit Logging**: Backend logging for all registration and authentication attempts.

## 📝 Reporting
Managers can export data for external review:
- **JSON**: Full system state and historical intelligence, featuring automated ISO-8601 export timestamps for data auditing.
- **CSV**: Spreadsheet-ready summary of trends and alerts.
- **Print/PDF**: Formatted dashboard views for physical reporting with "Generated on" metadata included in report headers.

---
*Developed as a comprehensive solution for modern retail data challenges.*