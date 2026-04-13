import pandas as pd
from backend.app.core.database import SessionLocal
from backend.app.models.customer_model import Customer
from backend.app.models.interaction_model import Interaction
from backend.app.models.zone_model import Zone
import datetime
import os

REPORTS_DIR = "../data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_daily_report():
    db = SessionLocal()
    today = datetime.date.today()

    # Example: Customer visits today
    customers = db.query(Customer).filter(Customer.entry_time >= today).all()
    df_customers = pd.DataFrame([{
        "id": c.id,
        "entry_time": c.entry_time,
        "exit_time": c.exit_time,
        "visit_duration": c.visit_duration
    } for c in customers])

    df_customers.to_csv(os.path.join(REPORTS_DIR, f"customer_report_{today}.csv"), index=False)

    # Example: Interactions per zone
    interactions = db.query(Interaction).all()
    df_interactions = pd.DataFrame([{
        "customer_id": i.customer_id,
        "zone_id": i.zone_id,
        "timestamp": i.timestamp
    } for i in interactions])

    df_interactions.to_csv(os.path.join(REPORTS_DIR, f"interaction_report_{today}.csv"), index=False)

    print(f"Reports generated in {REPORTS_DIR}")

if __name__ == "__main__":
    generate_daily_report()