#run it like this: scripts/start_server.sh
#python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Smart Retail Analytics - Start All Services
# ------------------------------------------------------------------

# Load environment variables from .env
export $(grep -v '^#' ../.env | xargs)

echo "Environment variables loaded from ../.env"

# Activate Python virtual environment
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "Virtual environment not found. Please create one at ../venv"
    exit 1
fi

# -------------------------------
# Start Backend API
# -------------------------------
echo "Starting backend API..."

# For development: use --reload
# For production: use gunicorn with uvicorn workers
# Example production command:
# gunicorn -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8000 --workers 4

uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info &

BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# -------------------------------
# Start Vision Pipeline
# -------------------------------
echo "Starting vision pipeline..."
python scripts/run_vision.py &

VISION_PID=$!
echo "Vision pipeline started with PID $VISION_PID"

# -------------------------------
# Start Report Generator (Optional)
# -------------------------------
# This example runs the report generator once at startup
# For daily reports, schedule with cron or Windows Task Scheduler
echo "Generating initial reports..."
python scripts/generate_reports.py &

REPORT_PID=$!
echo "Report generator started with PID $REPORT_PID"

# -------------------------------
# Monitor processes
# -------------------------------
echo "All services started successfully!"
echo "Backend PID: $BACKEND_PID, Vision PID: $VISION_PID, Report PID: $REPORT_PID"

# Wait for all processes
wait $BACKEND_PID $VISION_PID $REPORT_PID

# -------------------------------
# Notes:
# - Press Ctrl+C to stop all services
# - For production, consider using supervisor, systemd, or docker-compose
# -------------------------------