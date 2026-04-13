# These tools make your AI aware. without them the AI will only guess
# this is the brain that prepares data for AI

from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text

from backend.app.services.customer_service import SESSION_TIMEOUT_SECONDS, expire_stale_sessions


class AnalyticsTools:
    # Tools used by the AI agent to retrieve analytics data.

    def __init__(self, db):
        self.db = db
        self.bind = db.get_bind() if hasattr(db, "get_bind") else getattr(db, "bind", None)
        self.inspector = inspect(self.bind) if self.bind is not None else None

    def _table_exists(self, table_name: str) -> bool:
        return bool(self.inspector and self.inspector.has_table(table_name))

    def _columns(self, table_name: str):
        if not self._table_exists(table_name):
            return set()
        return {column["name"] for column in self.inspector.get_columns(table_name)}

    def _rows(self, query: str, params=None):
        try:
            result = self.db.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
        except Exception:
            if hasattr(self.db, "rollback"):
                self.db.rollback()
            return []

    def _scalar(self, query: str, params=None):
        try:
            result = self.db.execute(text(query), params or {})
            row = result.first()
            return row[0] if row else 0
        except Exception:
            if hasattr(self.db, "rollback"):
                self.db.rollback()
            return 0

    def _zone_name_expr(self, alias: str = "z"):
        zone_columns = self._columns("zones")
        if "zone_name" in zone_columns:
            return f"{alias}.zone_name"
        if "Zone_name" in zone_columns:
            return f'{alias}."Zone_name"'
        return None

    def get_customer_snapshot(self):
        columns = self._columns("customers")
        if not columns:
            return {
                "total_customers": 0,
                "active_customers": 0,
                "recent_customers": [],
            }

        expire_stale_sessions(self.db, timeout_seconds=SESSION_TIMEOUT_SECONDS)

        id_column = next(
            (name for name in ["tracker_id", "tracking_id", "customer_id", "id"] if name in columns),
            "id",
        )
        time_column = next(
            (name for name in ["last_seen", "entry_time", "first_seen", "timestamp", "created_at"] if name in columns),
            None,
        )

        total_customers = self._scalar("SELECT COUNT(*) FROM customers") or 0

        if "exit_time" in columns:
            active_customers = self._scalar("SELECT COUNT(*) FROM customers WHERE exit_time IS NULL") or 0
        else:
            active_customers = total_customers

        recent_customers = []
        if time_column:
            recent_customers = self._rows(
                f"""
                SELECT {id_column} AS tracker_id, {time_column} AS seen_at
                FROM customers
                ORDER BY {time_column} DESC NULLS LAST
                LIMIT 5
                """
            )

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "recent_customers": recent_customers,
            "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
        }

    def get_entry_exit_summary(self):
        customer_columns = self._columns("customers")
        if not customer_columns:
            return {
                "entries_today": 0,
                "exits_today": 0,
                "open_sessions": 0,
                "completed_visits": 0,
            }

        expire_stale_sessions(self.db, timeout_seconds=SESSION_TIMEOUT_SECONDS)

        entries_today = 0
        exits_today = 0
        if "entry_time" in customer_columns:
            entries_today = self._scalar(
                "SELECT COUNT(*) FROM customers WHERE entry_time IS NOT NULL AND entry_time >= CURRENT_DATE"
            ) or 0

        if "exit_time" in customer_columns:
            exits_today = self._scalar(
                "SELECT COUNT(*) FROM customers WHERE exit_time IS NOT NULL AND exit_time >= CURRENT_DATE"
            ) or 0
            open_sessions = self._scalar("SELECT COUNT(*) FROM customers WHERE exit_time IS NULL") or 0
            completed_visits = self._scalar("SELECT COUNT(*) FROM customers WHERE exit_time IS NOT NULL") or 0
        else:
            open_sessions = self._scalar("SELECT COUNT(*) FROM customers") or 0
            completed_visits = 0

        return {
            "entries_today": int(entries_today),
            "exits_today": int(exits_today),
            "open_sessions": int(open_sessions),
            "completed_visits": int(completed_visits),
            "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
        }

    def get_zone_traffic(self):
        zones_available = self._table_exists("zones")
        zone_name_expr = self._zone_name_expr("z")

        if self._table_exists("zone_events") and zones_available:
            label_expr = f"COALESCE({zone_name_expr}, 'Zone ' || ze.zone_id::text)" if zone_name_expr else "'Zone ' || ze.zone_id::text"
            return self._rows(
                f"""
                SELECT {label_expr} AS zone,
                       COUNT(*) AS visits,
                       ROUND(COALESCE(AVG(EXTRACT(EPOCH FROM (COALESCE(ze.exit_time, CURRENT_TIMESTAMP) - ze.entry_time))), 0) / 60.0, 2) AS avg_minutes
                FROM zone_events ze
                LEFT JOIN zones z ON z.id = ze.zone_id
                GROUP BY zone
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        if self._table_exists("zone_events"):
            return self._rows(
                """
                SELECT 'Zone ' || zone_id::text AS zone,
                       COUNT(*) AS visits,
                       0 AS avg_minutes
                FROM zone_events
                WHERE zone_id IS NOT NULL
                GROUP BY zone_id
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        interaction_columns = self._columns("interactions")
        if "zone_id" in interaction_columns and zones_available:
            label_expr = f"COALESCE({zone_name_expr}, 'Zone ' || i.zone_id::text)" if zone_name_expr else "'Zone ' || i.zone_id::text"
            return self._rows(
                f"""
                SELECT {label_expr} AS zone,
                       COUNT(*) AS visits,
                       0 AS avg_minutes
                FROM interactions i
                LEFT JOIN zones z ON z.id = i.zone_id
                WHERE i.zone_id IS NOT NULL
                GROUP BY zone
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        if "zone_id" in interaction_columns:
            return self._rows(
                """
                SELECT 'Zone ' || zone_id::text AS zone,
                       COUNT(*) AS visits,
                       0 AS avg_minutes
                FROM interactions
                WHERE zone_id IS NOT NULL
                GROUP BY zone_id
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        return []

    def get_top_products(self):
        interaction_columns = self._columns("interactions")
        if not interaction_columns:
            return []

        if "product_id" in interaction_columns and self._table_exists("products"):
            return self._rows(
                """
                SELECT COALESCE(p.name, 'Product ' || i.product_id::text) AS product,
                       COUNT(*) AS interactions
                FROM interactions i
                LEFT JOIN products p ON p.id = i.product_id
                WHERE i.product_id IS NOT NULL
                GROUP BY product
                ORDER BY interactions DESC
                LIMIT 5
                """
            )

        if "product_id" in interaction_columns:
            return self._rows(
                """
                SELECT 'Product ' || product_id::text AS product,
                       COUNT(*) AS interactions
                FROM interactions
                WHERE product_id IS NOT NULL
                GROUP BY product_id
                ORDER BY interactions DESC
                LIMIT 5
                """
            )

        if "action" in interaction_columns:
            return self._rows(
                """
                SELECT action AS product, COUNT(*) AS interactions
                FROM interactions
                WHERE action IS NOT NULL
                GROUP BY action
                ORDER BY interactions DESC
                LIMIT 5
                """
            )

        return []

    def get_peak_hours(self):
        interaction_columns = self._columns("interactions")
        if "timestamp" in interaction_columns:
            return self._rows(
                """
                SELECT EXTRACT(HOUR FROM timestamp) AS hour,
                       COUNT(*) AS visits
                FROM interactions
                GROUP BY hour
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        customer_columns = self._columns("customers")
        if "entry_time" in customer_columns:
            return self._rows(
                """
                SELECT EXTRACT(HOUR FROM entry_time) AS hour,
                       COUNT(*) AS visits
                FROM customers
                GROUP BY hour
                ORDER BY visits DESC
                LIMIT 5
                """
            )

        return []

    def get_customer_trend(self, days: int = 14):
        customer_columns = self._columns("customers")
        time_column = next(
            (name for name in ["entry_time", "first_seen", "timestamp", "created_at"] if name in customer_columns),
            None,
        )
        if not time_column:
            return []

        return self._rows(
            f"""
            SELECT DATE({time_column}) AS day,
                   COUNT(*) AS visits
            FROM customers
            GROUP BY DATE({time_column})
            ORDER BY day DESC
            LIMIT {int(days)}
            """
        )

    def get_repeat_customers(self, limit: int = 5):
        customer_columns = self._columns("customers")
        tracker_column = next(
            (name for name in ["tracker_id", "tracking_id", "customer_id"] if name in customer_columns),
            None,
        )
        if not tracker_column:
            return []

        return self._rows(
            f"""
            SELECT {tracker_column} AS tracker_id,
                   COUNT(*) AS visits
            FROM customers
            WHERE {tracker_column} IS NOT NULL
            GROUP BY {tracker_column}
            HAVING COUNT(*) > 1
            ORDER BY visits DESC, tracker_id ASC
            LIMIT {int(limit)}
            """
        )

    def get_average_visit_duration(self):
        customer_columns = self._columns("customers")
        if not customer_columns:
            return {
                "avg_seconds": 0,
                "avg_minutes": 0.0,
            }

        expire_stale_sessions(self.db, timeout_seconds=SESSION_TIMEOUT_SECONDS)

        avg_seconds = 0
        if {"entry_time", "last_seen"}.issubset(customer_columns):
            avg_seconds = self._scalar(
                """
                SELECT COALESCE(
                    AVG(
                        CASE
                            WHEN visit_duration IS NOT NULL THEN visit_duration
                            WHEN entry_time IS NOT NULL AND COALESCE(exit_time, last_seen) IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (COALESCE(exit_time, last_seen) - entry_time))
                            ELSE NULL
                        END
                    ),
                    0
                )
                FROM customers
                WHERE entry_time IS NOT NULL
                """
            ) or 0
        elif "visit_duration" in customer_columns:
            avg_seconds = self._scalar(
                "SELECT COALESCE(AVG(visit_duration), 0) FROM customers WHERE visit_duration IS NOT NULL"
            ) or 0
        elif "entry_time" in customer_columns and "exit_time" in customer_columns:
            avg_seconds = self._scalar(
                """
                SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (exit_time - entry_time))), 0)
                FROM customers
                WHERE entry_time IS NOT NULL AND exit_time IS NOT NULL
                """
            ) or 0

        return {
            "avg_seconds": round(float(avg_seconds), 2),
            "avg_minutes": round(float(avg_seconds) / 60, 2),
            "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
        }

    def get_recent_logs(self, max_lines: int = 20, log_path: str = "logs/smart_retail.log"):
        path = Path(log_path)
        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            return []

        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = [line.strip() for line in handle.readlines() if line.strip()]

        return lines[-max_lines:]

    def build_live_context(self):
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "customers": self.get_customer_snapshot(),
            "entry_exit": self.get_entry_exit_summary(),
            "zone_traffic": self.get_zone_traffic(),
            "top_products": self.get_top_products(),
            "peak_hours": self.get_peak_hours(),
            "recent_logs": self.get_recent_logs(),
        }

    def build_historical_context(self):
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "customer_trend": self.get_customer_trend(),
            "repeat_customers": self.get_repeat_customers(),
            "average_visit_duration": self.get_average_visit_duration(),
            "entry_exit_summary": self.get_entry_exit_summary(),
            "zone_analytics": self.get_zone_traffic(),
            "top_products_all_time": self.get_top_products(),
            "peak_hours_history": self.get_peak_hours(),
        }

    def get_recommended_actions(self, live_data=None, historical_data=None):
        live_data = live_data or self.build_live_context()
        historical_data = historical_data or self.build_historical_context()

        customers = live_data.get("customers", {})
        top_products = live_data.get("top_products", []) or historical_data.get("top_products_all_time", [])
        repeat_customers = historical_data.get("repeat_customers", [])
        peak_hours = historical_data.get("peak_hours_history", [])
        zone_traffic = live_data.get("zone_traffic", []) or historical_data.get("zone_analytics", [])
        active_customers = customers.get("active_customers", 0)

        actions = []

        if active_customers >= 8:
            actions.append({
                "priority": "high",
                "title": "Increase floor coverage now",
                "details": f"There are {active_customers} active customers, so add staff near busy aisles and checkouts."
            })
        elif active_customers >= 4:
            actions.append({
                "priority": "medium",
                "title": "Monitor live traffic",
                "details": f"There are {active_customers} active shoppers, so keep one staff member ready for support."
            })

        if zone_traffic:
            top_zone = zone_traffic[0].get("zone", "Top zone")
            visits = zone_traffic[0].get("visits", 0)
            actions.append({
                "priority": "medium",
                "title": f"Watch {top_zone}",
                "details": f"{top_zone} is currently the busiest zone with {visits} tracked visits, so place support nearby."
            })

        if top_products:
            top_product = top_products[0].get("product", "Top product")
            actions.append({
                "priority": "medium",
                "title": f"Promote {top_product}",
                "details": f"{top_product} is drawing the most attention; keep it stocked and feature it in promotions."
            })
        else:
            actions.append({
                "priority": "low",
                "title": "Collect more product interaction data",
                "details": "No product hotspots are visible yet, so keep the vision pipeline running longer for stronger trends."
            })

        if repeat_customers:
            actions.append({
                "priority": "medium",
                "title": "Reward returning shoppers",
                "details": f"{len(repeat_customers)} repeat-customer signals were detected; consider a loyalty or upsell offer."
            })

        if peak_hours:
            peak_hour = peak_hours[0].get("hour")
            actions.append({
                "priority": "low",
                "title": "Plan around peak hour",
                "details": f"Historical demand peaks around hour {peak_hour}; schedule staff and replenishment ahead of that time."
            })

        return actions

    def get_live_alerts(self, live_data=None, historical_data=None):
        live_data = live_data or self.build_live_context()
        historical_data = historical_data or self.build_historical_context()

        customers = live_data.get("customers", {})
        entry_exit = live_data.get("entry_exit", {})
        zone_traffic = live_data.get("zone_traffic", []) or historical_data.get("zone_analytics", [])
        top_products = live_data.get("top_products", []) or historical_data.get("top_products_all_time", [])
        average_visit = historical_data.get("average_visit_duration", {})
        recent_logs = live_data.get("recent_logs", [])

        active_customers = int(customers.get("active_customers", 0) or 0)
        entries_today = int(entry_exit.get("entries_today", 0) or 0)
        exits_today = int(entry_exit.get("exits_today", 0) or 0)
        avg_visit_minutes = float(average_visit.get("avg_minutes", 0) or 0)
        timestamp = datetime.utcnow().isoformat() + "Z"
        alerts = []

        def add_alert(code, severity, title, message, action, value=None):
            alerts.append({
                "id": code,
                "severity": severity,
                "title": title,
                "message": message,
                "action": action,
                "value": value,
                "timestamp": timestamp,
            })

        if active_customers >= 1:
            add_alert(
                "traffic-high",
                "high",
                "High in-store traffic",
                f"{active_customers} shoppers are active right now, which is above the congestion threshold.",
                "Open another checkout lane and move staff toward busy aisles.",
                active_customers,
            )
        elif active_customers >= 6:
            add_alert(
                "traffic-medium",
                "medium",
                "Traffic building up",
                f"{active_customers} shoppers are active in store and traffic is trending upward.",
                "Keep one staff member ready near the main floor and checkout.",
                active_customers,
            )

        net_flow = entries_today - exits_today
        if net_flow >= 5:
            add_alert(
                "entry-surge",
                "medium",
                "Entry surge detected",
                f"Entries exceed exits by {net_flow} today, indicating the store is filling faster than it is clearing.",
                "Prepare more floor coverage and checkout support before lines form.",
                net_flow,
            )

        if entries_today and active_customers > entries_today:
            add_alert(
                "tracking-mismatch",
                "medium",
                "Entry / active mismatch",
                f"Entries today ({entries_today}) are lower than active shoppers ({active_customers}), which suggests stale tracking data or a missed exit event.",
                f"The backend timeout cleanup is {SESSION_TIMEOUT_SECONDS:.0f}s; keep the camera feed stable and verify the entry path stays visible.",
                active_customers - entries_today,
            )

        if zone_traffic:
            top_zone = zone_traffic[0]
            zone_visits = int(top_zone.get("visits", 0) or 0)
            if zone_visits >= 3:
                add_alert(
                    f"zone-{str(top_zone.get('zone', 'hotspot')).lower().replace(' ', '-')}",
                    "medium",
                    f"Zone hotspot: {top_zone.get('zone', 'Unknown')}",
                    f"{top_zone.get('zone', 'This zone')} has {zone_visits} recent tracked visits and is currently the busiest area.",
                    "Place staff nearby and check product availability in that zone.",
                    zone_visits,
                )

        if avg_visit_minutes >= 8:
            add_alert(
                "visit-duration-high",
                "medium",
                "Long visit duration detected",
                f"Average visit duration is {avg_visit_minutes:.1f} minutes, which may suggest browsing friction or checkout delays.",
                "Inspect queue times and make sure high-interest products stay easy to access.",
                avg_visit_minutes,
            )

        joined_logs = "\n".join(recent_logs[-10:])
        if "RateLimitError" in joined_logs or "Backend event post failed" in joined_logs:
            add_alert(
                "system-warning",
                "low",
                "System warning detected",
                "Recent backend logs show an AI quota or event-post warning that may limit automated insights.",
                "Review API quota, connectivity, and retry the pipeline if alerts stop updating.",
            )

        if top_products:
            top_product = top_products[0]
            interactions = int(top_product.get("interactions", 0) or 0)
            if interactions >= 3:
                add_alert(
                    f"product-{str(top_product.get('product', 'hotspot')).lower().replace(' ', '-')}",
                    "low",
                    f"Product hotspot: {top_product.get('product', 'Unknown')}",
                    f"{top_product.get('product', 'This product')} is drawing {interactions} tracked interactions.",
                    "Restock and feature the item while customer attention is high.",
                    interactions,
                )

        if not alerts:
            add_alert(
                "all-clear",
                "info",
                "Store operating normally",
                "No urgent traffic, zone, or system issues are active in the latest monitoring cycle.",
                "Keep monitoring the dashboard for new alerts.",
            )

        severity_rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
        alerts.sort(key=lambda item: (severity_rank.get(item.get("severity", "info"), 99), item.get("title", "")))
        return alerts

    def build_dashboard_summary(self):
        live_data = self.build_live_context()
        historical_data = self.build_historical_context()
        customers = live_data.get("customers", {})
        entry_exit = live_data.get("entry_exit", {})
        top_products = live_data.get("top_products", []) or historical_data.get("top_products_all_time", [])
        peak_hours = live_data.get("peak_hours", []) or historical_data.get("peak_hours_history", [])
        zone_traffic = live_data.get("zone_traffic", []) or historical_data.get("zone_analytics", [])
        average_visit_duration = historical_data.get("average_visit_duration", {})
        alerts = self.get_live_alerts(live_data, historical_data)

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "overview": {
                "total_customers": customers.get("total_customers", 0),
                "active_sessions": customers.get("active_customers", 0),
                "entries_today": entry_exit.get("entries_today", 0),
                "exits_today": entry_exit.get("exits_today", 0),
                "avg_visit_minutes": average_visit_duration.get("avg_minutes", 0),
                "top_zone": zone_traffic[0] if zone_traffic else None,
                "top_product": top_products[0] if top_products else None,
                "peak_hour": peak_hours[0] if peak_hours else None,
                "alert_count": len([alert for alert in alerts if alert.get("severity") != "info"]),
            },
            "live_data": live_data,
            "historical_data": historical_data,
            "recommended_actions": self.get_recommended_actions(live_data, historical_data),
            "alerts": alerts,
        }

    def build_ai_context(self):
        summary = self.build_dashboard_summary()
        return {
            "live": summary["live_data"],
            "historical": summary["historical_data"],
            "recommended_actions": summary["recommended_actions"],
        }