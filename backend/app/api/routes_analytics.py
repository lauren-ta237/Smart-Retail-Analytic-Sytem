# backend/app/api/routes_analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai.llm_service import get_llm_service
from ai.tools.analytics_tools import AnalyticsTools
from backend.app.core import security
from backend.app.core.database import get_db
from backend.app.schemas.analytics_schema import AIQuestionRequest, AIQuestionResponse
from backend.app.services.analytic_service import process_event

router = APIRouter()


@router.post("/events")
def receive_event(payload: dict):
    """
    Receives real-time data from the vision system and stores it.
    """
    process_event(payload)
    return {"status": "received"}


@router.post("/ask", response_model=AIQuestionResponse)
def ask_ai(request: AIQuestionRequest, db: Session = Depends(get_db)):
    """
    Ask the retail AI a question using live + historical store intelligence.
    """
    service = get_llm_service()
    return service.answer_live_question(request.question, db)


@router.get("/test-openai")
def test_openai():
    """
    Force a direct OpenAI call from the backend and log the result immediately.
    """
    service = get_llm_service()
    return service.test_connection()


@router.get("/dashboard-summary")
def dashboard_summary(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Returns the combined data used by the dashboard UI.
    """
    tools = AnalyticsTools(db)
    summary = tools.build_dashboard_summary()
    summary["llm_status"] = get_llm_service().get_status()
    return summary


@router.get("/alerts")
def realtime_alerts(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Returns the latest live alerts for the dashboard alert center.
    """
    tools = AnalyticsTools(db)
    live_data = tools.build_live_context()
    historical_data = tools.build_historical_context()
    return {
        "generated_at": live_data.get("generated_at"),
        "alerts": tools.get_live_alerts(live_data, historical_data),
    }


@router.get("/live-context")
def live_context(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Returns the live context snapshot currently used by the AI assistant.
    """
    tools = AnalyticsTools(db)
    return tools.build_live_context()


@router.get("/historical-context")
def historical_context(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Returns historical intelligence derived from past customer and interaction data.
    """
    tools = AnalyticsTools(db)
    return tools.build_historical_context()


@router.get("/overview")
def analytics_overview(current_user=Depends(security.get_current_user), db: Session = Depends(get_db)):
    """
    Returns a live + historical analytics overview.
    """
    tools = AnalyticsTools(db)
    customer_snapshot = tools.get_customer_snapshot()
    historical = tools.build_historical_context()
    zone_traffic = tools.get_zone_traffic()
    entry_exit = tools.get_entry_exit_summary()

    return {
        "total_customers": customer_snapshot.get("total_customers", 0),
        "active_sessions": customer_snapshot.get("active_customers", 0),
        "entries_today": entry_exit.get("entries_today", 0),
        "exits_today": entry_exit.get("exits_today", 0),
        "top_products": tools.get_top_products(),
        "peak_hours": tools.get_peak_hours(),
        "top_zone": zone_traffic[0] if zone_traffic else None,
        "zone_traffic": zone_traffic,
        "customer_trend": historical.get("customer_trend", []),
        "average_visit_duration": historical.get("average_visit_duration", {}),
        "repeat_customers": historical.get("repeat_customers", []),
    }


@router.get("/reports")
def analytics_reports(current_user=Depends(security.require_admin)):
    """
    Example endpoint: Returns a list of reports.
    """
    return {
        "reports": [
            {"id": 1, "name": "Daily Sales"},
            {"id": 2, "name": "Customer Visits"},
            {"id": 3, "name": "AI Live Snapshot"},
            {"id": 4, "name": "Historical Intelligence"},
            {"id": 5, "name": "Dashboard Summary"}
        ]
    }