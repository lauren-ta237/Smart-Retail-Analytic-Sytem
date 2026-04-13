# process incoming data from vision system and store in db
from datetime import datetime

from backend.app.core.database import SessionLocal
from backend.app.models.customer_model import Customer
from backend.app.models.interaction_model import Interaction
from backend.app.models.zone_event_model import ZoneEvent
from backend.app.models.zone_model import Zone
from backend.app.schemas.customer_schema import CustomerCreate
from backend.app.services.customer_service import (
    create_customer,
    expire_stale_sessions,
    get_active_customer,
    mark_customer_seen,
    update_exit_time,
)
from backend.app.utils.logger import setup_logger

logger = setup_logger()

DEFAULT_ZONES = {
    1: "Entrance",
    2: "Shopping Floor",
    3: "Checkout",
}


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_timestamp(value):
    if value in (None, ""):
        return datetime.utcnow()

    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        except ValueError:
            try:
                return datetime.utcfromtimestamp(float(value))
            except (TypeError, ValueError):
                return datetime.utcnow()

    return datetime.utcnow()


def _ensure_zone(db, zone_id=None, zone_name=None):
    resolved_zone_id = _safe_int(zone_id)
    resolved_zone_name = zone_name or DEFAULT_ZONES.get(resolved_zone_id)

    if resolved_zone_id is None and not resolved_zone_name:
        return None

    zone = None
    if resolved_zone_id is not None:
        zone = db.query(Zone).filter(Zone.id == resolved_zone_id).first()

    if zone is None and resolved_zone_name:
        zone = db.query(Zone).filter(Zone.zone_name == resolved_zone_name).first()

    if zone:
        if resolved_zone_name and zone.zone_name != resolved_zone_name:
            zone.zone_name = resolved_zone_name
        return zone

    zone = Zone(
        id=resolved_zone_id,
        zone_name=resolved_zone_name or f"Zone {resolved_zone_id}",
        camera_id="vision-main",
    )
    db.add(zone)
    db.flush()
    return zone


def _ensure_default_zones(db):
    for zone_id, zone_name in DEFAULT_ZONES.items():
        _ensure_zone(db, zone_id=zone_id, zone_name=zone_name)


def _get_active_zone_event(db, customer_id):
    return (
        db.query(ZoneEvent)
        .filter(ZoneEvent.customer_id == customer_id, ZoneEvent.exit_time.is_(None))
        .order_by(ZoneEvent.entry_time.desc(), ZoneEvent.id.desc())
        .first()
    )


def _update_zone_presence(db, customer_id, zone_id, seen_at):
    resolved_zone_id = _safe_int(zone_id)
    if resolved_zone_id is None:
        return

    active_zone = _get_active_zone_event(db, customer_id)
    if active_zone and active_zone.zone_id == resolved_zone_id:
        return

    if active_zone and active_zone.zone_id != resolved_zone_id:
        active_zone.exit_time = seen_at

    db.add(
        ZoneEvent(
            customer_id=customer_id,
            zone_id=resolved_zone_id,
            entry_time=seen_at,
        )
    )


def _close_customer_session(db, tracker_id, seen_at):
    customer = update_exit_time(db, tracker_id, exited_at=seen_at)
    if customer:
        active_zone = _get_active_zone_event(db, customer.id)
        if active_zone and active_zone.exit_time is None:
            active_zone.exit_time = seen_at
    return customer


def process_event(data: dict):
    db = SessionLocal()

    customers = data.get("customers", [])
    interactions = data.get("interactions", [])
    exited_customer_ids = data.get("exited_customer_ids", [])
    seen_at = _coerce_timestamp(data.get("timestamp"))

    try:
        expired_sessions = expire_stale_sessions(db, now=seen_at)
        if expired_sessions:
            logger.info("Auto-closed %s stale customer sessions using the timeout cleanup", expired_sessions)

        _ensure_default_zones(db)
        customer_id_map = {}

        for customer in customers:
            tracker_id = _safe_int(customer.get("id") or customer.get("tracker_id"))
            if tracker_id is None:
                continue

            zone = _ensure_zone(db, customer.get("zone_id"), customer.get("zone_name"))
            db_customer = create_customer(
                db,
                CustomerCreate(
                    tracker_id=tracker_id,
                    entry_time=seen_at,
                ),
            )
            mark_customer_seen(db, tracker_id, seen_at)
            customer_id_map[tracker_id] = db_customer.id

            if zone is not None:
                _update_zone_presence(db, db_customer.id, zone.id, seen_at)

        for raw_tracker_id in exited_customer_ids:
            tracker_id = _safe_int(raw_tracker_id)
            if tracker_id is not None:
                _close_customer_session(db, tracker_id, seen_at)

        for item in interactions:
            tracker_id = _safe_int(item.get("customer_id") or item.get("tracker_id"))
            customer_pk = customer_id_map.get(tracker_id)

            if customer_pk is None and tracker_id is not None:
                existing_customer = get_active_customer(db, tracker_id) or (
                    db.query(Customer)
                    .filter(Customer.tracker_id == tracker_id)
                    .order_by(Customer.id.desc())
                    .first()
                )
                customer_pk = existing_customer.id if existing_customer else None

            if customer_pk is None:
                logger.warning("Skipping interaction with unknown tracker_id=%s", tracker_id)
                continue

            zone = _ensure_zone(db, item.get("zone_id"), item.get("zone_name"))
            if zone is not None:
                _update_zone_presence(db, customer_pk, zone.id, seen_at)

            db.add(
                Interaction(
                    customer_id=customer_pk,
                    zone_id=zone.id if zone is not None else _safe_int(item.get("zone_id")),
                    product_id=_safe_int(item.get("product_id")),
                    action=item.get("action") or item.get("interaction") or "detected",
                    timestamp=seen_at,
                )
            )

        db.commit()
        logger.info(
            "Processed live event payload: %s customers, %s interactions, %s exits",
            len(customers),
            len(interactions),
            len(exited_customer_ids),
        )
    except Exception:
        db.rollback()
        logger.exception("Failed to process live analytics payload")
        raise
    finally:
        db.close()