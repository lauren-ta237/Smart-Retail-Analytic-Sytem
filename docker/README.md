# Docker Guide for Smart Retail Vision Analytics

## Services included
- `app` - FastAPI backend + dashboard on `http://127.0.0.1:8000`
- `db` - PostgreSQL database on `localhost:5432`

## Start backend + dashboard + database
```powershell
docker compose up --build
```

## Start the full stack including vision
```powershell
docker compose --profile vision up --build
```

## Useful commands
```powershell
docker compose down
docker compose logs -f app
docker compose logs -f vision
docker compose logs -f db
```

## Camera notes
- Inside Docker, the `vision` service runs in **headless mode**.
- For best results on Windows, use an **RTSP/IP camera stream** or a video file path via `CAMERA_SOURCE`.
- If you want to use a local webcam directly, it is usually easier to run:
  ```powershell
  python -m scripts.run_vision
  ```
  while keeping the backend in Docker.

Example with RTSP:
```powershell
$env:CAMERA_SOURCE = 'rtsp://192.168.1.100:554/stream'
docker compose --profile vision up --build
```

## Database note
The compose file uses:
```env
DATABASE_URL_DOCKER=postgresql://postgres:postgres@db:5432/retail_db
```
for container-to-container access.
