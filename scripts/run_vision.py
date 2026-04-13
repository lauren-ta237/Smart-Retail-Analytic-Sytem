"""
Retail Analytics Pipeline (Production Ready - ByteTrack)

- Detects + tracks people (YOLO + ByteTrack)
- Uses an entry-zone confirmation step to avoid counting random detections
- Uses an exit delay so short occlusions do not instantly end a visit
- Tracks zone movement for dashboard analytics
- Detects interactions
- Generates heatmaps
- Sends structured events to backend API

Camera placement recommendation:
- Best setup is an overhead or entrance-facing camera
- Make sure the full entry/exit path is visible
- This makes entry-zone gating and delayed exit tracking much more reliable
"""

import cv2
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from backend.app.core.database import SessionLocal
from backend.app.schemas.customer_schema import CustomerCreate
from backend.app.services.customer_service import create_customer, update_exit_time
from vision.heatmap_generator import HeatmapGenerator
from vision.shelf_interaction import ShelfInteractionDetector
from vision.tracking.byte_tracker import CustomerTracker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# -------------------------------
# CONFIGURATION
# -------------------------------
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_CLIENT_HOST = "127.0.0.1" if BACKEND_HOST == "0.0.0.0" else BACKEND_HOST
API_URL = os.getenv(
    "VISION_EVENTS_URL",
    f"http://{BACKEND_CLIENT_HOST}:{BACKEND_PORT}/api/analytics/events",
)
HEALTHCHECK_URL = os.getenv(
    "VISION_HEALTHCHECK_URL",
    f"http://{BACKEND_CLIENT_HOST}:{BACKEND_PORT}/",
)
FRAME_DELAY = float(os.getenv("VISION_FRAME_DELAY", "0.01"))
REQUEST_TIMEOUT = float(os.getenv("VISION_REQUEST_TIMEOUT", "2.0"))
EVENT_POST_INTERVAL = float(os.getenv("VISION_POST_INTERVAL", "1.0"))

# Entry / exit tuning:
# - A person must first appear in the entry zone for a few frames before being counted.
# - A person must also remain missing for a short delay before we mark them as exited.
# This avoids counting random one-frame detections and prevents instant exits during occlusion.
ENTRY_ZONE_ID = int(os.getenv("VISION_ENTRY_ZONE_ID", "1"))
ENTRY_CONFIRM_FRAMES = int(os.getenv("VISION_ENTRY_CONFIRM_FRAMES", "3"))
EXIT_GRACE_SECONDS = float(os.getenv("VISION_EXIT_GRACE_SECONDS", "5.0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _parse_camera_source(value):
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return value


def _resolve_zone(frame_width, center_x):
    """
    Split the image into simple operational zones.

    Zone 1 is the dedicated entry zone used for count confirmation.
    This prevents the system from counting random detections that first appear
    deep inside the frame instead of entering through the expected walkway.
    """
    if frame_width <= 0:
        return {"zone_id": 2, "zone_name": "Shopping Floor"}

    ratio = center_x / max(frame_width, 1)
    if ratio < 0.33:
        return {"zone_id": 1, "zone_name": "Entrance"}
    if ratio < 0.66:
        return {"zone_id": 2, "zone_name": "Shopping Floor"}
    return {"zone_id": 3, "zone_name": "Checkout"}


def _initialize_track_state(zone_info, seen_at):
    return {
        "first_seen": seen_at,
        "last_seen": seen_at,
        "zone_id": zone_info["zone_id"],
        "zone_name": zone_info["zone_name"],
        "frames_seen": 0,
        "counted": False,
    }


def _update_track_state(state, zone_info, seen_at):
    state["last_seen"] = seen_at
    state["zone_id"] = zone_info["zone_id"]
    state["zone_name"] = zone_info["zone_name"]
    state["frames_seen"] = state.get("frames_seen", 0) + 1
    return state


def _should_confirm_entry(state):
    """Only confirm a customer after stable detection inside the entry zone."""
    return state.get("zone_id") == ENTRY_ZONE_ID and state.get("frames_seen", 0) >= ENTRY_CONFIRM_FRAMES


def _draw_zone_guides(frame):
    frame_height, frame_width = frame.shape[:2]
    markers = [
        (int(frame_width * 0.33), "Entry zone"),
        (int(frame_width * 0.66), "Shopping Floor"),
        (frame_width - 160, "Checkout / exit"),
    ]

    for x, _label in markers[:2]:
        cv2.line(frame, (x, 0), (x, frame_height), (168, 139, 250), 1)

    cv2.putText(frame, "Entry zone", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (168, 139, 250), 2)
    cv2.putText(frame, "Shopping Floor", (max(10, int(frame_width * 0.33) + 12), 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (168, 139, 250), 2)
    cv2.putText(frame, "Checkout / exit", (max(10, int(frame_width * 0.66) + 12), 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (168, 139, 250), 2)


def run_retail_analytics(camera_source=0):
    camera_source = _parse_camera_source(os.getenv("CAMERA_SOURCE", str(camera_source)))
    headless = os.getenv("VISION_HEADLESS", "false").strip().lower() in {"1", "true", "yes", "on"}

    logging.info("Opening camera source: %s (headless=%s)", camera_source, headless)
    logging.info(
        "Camera setup tip: use an overhead or entrance-facing view that covers the full entry/exit path for the most accurate counts."
    )
    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        logging.error("Cannot open video source")
        return

    session = requests.Session()

    try:
        health_response = session.get(HEALTHCHECK_URL, timeout=REQUEST_TIMEOUT)
        health_response.raise_for_status()
        logging.info("Backend connected at %s", API_URL)
    except requests.exceptions.RequestException as exc:
        logging.warning("Backend health check failed at startup: %s", exc)

    tracker = CustomerTracker()
    interaction_detector = ShelfInteractionDetector()
    heatmap = HeatmapGenerator()
    db = SessionLocal()

    saved_ids = set()
    customer_states = {}
    last_event_post = 0.0

    logging.info("Retail analytics system started (ByteTrack mode)")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.warning("Frame capture failed")
                break

            tracked = tracker.update(frame)
            current_time = time.time()
            current_ids = set()
            formatted_customers = []

            for obj in tracked:
                x1, y1, x2, y2 = obj["bbox"]
                customer_id = int(obj["id"])
                current_ids.add(customer_id)

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                zone_info = _resolve_zone(frame.shape[1], cx)

                state = customer_states.get(customer_id)
                if state is None:
                    state = _initialize_track_state(zone_info, current_time)
                    customer_states[customer_id] = state
                state = _update_track_state(state, zone_info, current_time)

                is_counted_customer = state.get("counted", False)
                just_confirmed_entry = False

                # Only count a shopper after a stable detection in the entry zone.
                # This helps ignore random detections that briefly appear in the frame.
                if not is_counted_customer and _should_confirm_entry(state):
                    try:
                        create_customer(
                            db,
                            CustomerCreate(
                                tracker_id=customer_id,
                                entry_time=datetime.utcnow(),
                            ),
                        )
                        saved_ids.add(customer_id)
                        state["counted"] = True
                        is_counted_customer = True
                        just_confirmed_entry = True
                        logging.info(
                            "Confirmed customer entry: %s after %s frames in the entry zone",
                            customer_id,
                            state.get("frames_seen", 0),
                        )
                    except Exception as exc:
                        logging.error("DB insert failed: %s", exc)

                box_color = (0, 255, 0) if is_counted_customer else (0, 165, 255)
                status_label = zone_info["zone_name"] if is_counted_customer else f"Waiting at entry ({state.get('frames_seen', 0)}/{ENTRY_CONFIRM_FRAMES})"

                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(
                    frame,
                    f"ID: {customer_id} | {status_label}",
                    (max(8, x1), max(24, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )

                if not is_counted_customer:
                    # Do not send unconfirmed tracks to analytics yet.
                    continue

                formatted_customers.append(
                    {
                        "id": customer_id,
                        "bbox": [x1, y1, x2, y2],
                        "center": [cx, cy],
                        "zone_id": zone_info["zone_id"],
                        "zone_name": zone_info["zone_name"],
                        "event": "entry" if just_confirmed_entry else "seen",
                    }
                )

            interactions = interaction_detector.detect_interactions(tracked, [])
            customer_lookup = {item["id"]: item for item in formatted_customers}
            for item in interactions:
                customer = customer_lookup.get(item.get("customer_id"))
                if customer:
                    item.setdefault("zone_id", customer.get("zone_id"))
                    item.setdefault("zone_name", customer.get("zone_name"))

            exited_customer_ids = []
            for customer_id, state in list(customer_states.items()):
                if customer_id in current_ids:
                    continue

                # Exit is intentionally delayed to avoid instant checkout/exit events
                # when a shopper is only briefly hidden by another person or shelf.
                if current_time - state.get("last_seen", current_time) >= EXIT_GRACE_SECONDS:
                    if state.get("counted"):
                        exited_customer_ids.append(customer_id)
                        try:
                            update_exit_time(db, customer_id, exited_at=datetime.utcnow())
                        except Exception as exc:
                            logging.error("Failed to update exit for customer %s: %s", customer_id, exc)
                        logging.info("Customer exited after %.1fs delay: %s", EXIT_GRACE_SECONDS, customer_id)
                    else:
                        logging.info("Dropped unconfirmed detection after %.1fs: %s", EXIT_GRACE_SECONDS, customer_id)

                    customer_states.pop(customer_id, None)
                    saved_ids.discard(customer_id)

            heatmap.update(frame, formatted_customers)
            output_frame = heatmap.render(frame)
            _draw_zone_guides(output_frame)

            payload = {
                "timestamp": current_time,
                "customers": formatted_customers,
                "interactions": interactions,
                "exited_customer_ids": exited_customer_ids,
            }

            if current_time - last_event_post >= EVENT_POST_INTERVAL:
                try:
                    response = session.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    last_event_post = current_time
                except requests.exceptions.RequestException as exc:
                    logging.warning("Backend event post failed: %s", exc)

            if not headless:
                cv2.imshow("Smart Retail Analytics (ByteTrack)", output_frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            time.sleep(FRAME_DELAY)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        db.close()
        session.close()
        logging.info("Retail analytics system stopped")


if __name__ == "__main__":
    try:
        run_retail_analytics()
    except KeyboardInterrupt:
        logging.info("Retail analytics system interrupted by user")