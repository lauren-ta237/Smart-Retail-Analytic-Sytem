import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.customer_model import Customer
from backend.app.schemas.customer_schema import CustomerCreate

SESSION_TIMEOUT_SECONDS = float(os.getenv("CUSTOMER_SESSION_TIMEOUT_SECONDS", "30"))


def get_active_customer(db: Session, tracker_id: int) -> Optional[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.tracker_id == tracker_id, Customer.exit_time.is_(None))
        .order_by(Customer.id.desc())
        .first()
    )


def create_customer(db: Session, customer: CustomerCreate):
    """
    Create a new customer entry in DB.
    Prevents duplicates using tracker_id while the visit is still active.
    """
    existing_customer = get_active_customer(db, customer.tracker_id)
    if existing_customer:
        return existing_customer

    entry_time = customer.entry_time or datetime.utcnow()
    db_customer = Customer(
        tracker_id=customer.tracker_id,
        entry_time=entry_time,
        last_seen=entry_time,
    )

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def mark_customer_seen(db: Session, tracker_id: int, seen_at: Optional[datetime] = None):
    """
    Refresh the active session heartbeat for a tracked customer.
    """
    db_customer = get_active_customer(db, tracker_id)
    if not db_customer:
        return None

    db_customer.last_seen = seen_at or datetime.utcnow()
    return db_customer


def expire_stale_sessions(
    db: Session,
    timeout_seconds: float = SESSION_TIMEOUT_SECONDS,
    now: Optional[datetime] = None,
) -> int:
    """
    Auto-close sessions that stopped reporting for longer than the timeout.
    This keeps active counts and visit duration realistic even if an exit event is missed.
    """
    now = now or datetime.utcnow()
    cutoff = now - timedelta(seconds=float(timeout_seconds))
    expired_count = 0

    stale_customers = (
        db.query(Customer)
        .filter(Customer.exit_time.is_(None))
        .order_by(Customer.id.asc())
        .all()
    )

    for customer in stale_customers:
        reference_time = customer.last_seen or customer.entry_time
        if reference_time is None or reference_time > cutoff:
            continue

        exit_time = min(now, reference_time + timedelta(seconds=float(timeout_seconds)))
        start_time = customer.entry_time or reference_time
        customer.exit_time = exit_time
        customer.last_seen = reference_time
        customer.visit_duration = max(0, int((exit_time - start_time).total_seconds()))
        expired_count += 1

    if expired_count:
        db.commit()

    return expired_count


def update_exit_time(db: Session, tracker_id: int, exited_at: Optional[datetime] = None):
    """
    Update exit time and visit duration for a customer using tracker_id.
    """
    db_customer = (
        db.query(Customer)
        .filter(Customer.tracker_id == tracker_id)
        .order_by(Customer.id.desc())
        .first()
    )

    if not db_customer:
        return None

    if db_customer.exit_time is not None:
        return db_customer

    exit_time = exited_at or datetime.utcnow()
    db_customer.exit_time = exit_time
    db_customer.last_seen = exit_time

    if db_customer.entry_time:
        db_customer.visit_duration = int((exit_time - db_customer.entry_time).total_seconds())
    else:
        db_customer.visit_duration = 0

    db.commit()
    db.refresh(db_customer)
    return db_customer