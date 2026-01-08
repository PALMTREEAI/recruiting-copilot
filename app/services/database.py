import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import Optional
from contextlib import contextmanager
from app.config import get_settings

settings = get_settings()


def get_db_path() -> str:
    """Get the database file path."""
    return settings.database_path


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database with all required tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Gem sourcing snapshots - stores daily stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL UNIQUE,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Gem sequence daily stats - granular data for each sequence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_sequence_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL,
                sequence_name TEXT NOT NULL,
                role TEXT NOT NULL,
                sender TEXT NOT NULL,
                sent INTEGER DEFAULT 0,
                opened INTEGER DEFAULT 0,
                replied INTEGER DEFAULT 0,
                bounced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(snapshot_date, sequence_name)
            )
        """)

        # Daily recommendations - track what was suggested
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_date DATE NOT NULL,
                for_whom TEXT NOT NULL,
                priority TEXT NOT NULL,
                category TEXT NOT NULL,
                insight TEXT NOT NULL,
                action TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Weekly goals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start DATE NOT NULL,
                role TEXT NOT NULL,
                metric TEXT NOT NULL,
                target INTEGER NOT NULL,
                actual INTEGER,
                hit BOOLEAN,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


# ============ GEM DATA FUNCTIONS ============

def save_gem_snapshot(snapshot_date: date, data: dict) -> int:
    """Save or update a Gem data snapshot for a specific date."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if exists
        cursor.execute(
            "SELECT id FROM gem_snapshots WHERE snapshot_date = ?",
            (snapshot_date.isoformat(),)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE gem_snapshots
                SET data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_date = ?
            """, (json.dumps(data), snapshot_date.isoformat()))
            return existing["id"]
        else:
            cursor.execute("""
                INSERT INTO gem_snapshots (snapshot_date, data)
                VALUES (?, ?)
            """, (snapshot_date.isoformat(), json.dumps(data)))
            return cursor.lastrowid


def save_gem_sequence_stats(
    snapshot_date: date,
    sequence_name: str,
    role: str,
    sender: str,
    sent: int = 0,
    opened: int = 0,
    replied: int = 0,
    bounced: int = 0
) -> int:
    """Save stats for a specific sequence on a specific date."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO gem_sequence_stats
            (snapshot_date, sequence_name, role, sender, sent, opened, replied, bounced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (snapshot_date.isoformat(), sequence_name, role, sender, sent, opened, replied, bounced))

        return cursor.lastrowid


def get_gem_snapshot(snapshot_date: date) -> Optional[dict]:
    """Get Gem snapshot for a specific date."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data FROM gem_snapshots WHERE snapshot_date = ?",
            (snapshot_date.isoformat(),)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row["data"])
        return None


def get_gem_snapshots_range(start_date: date, end_date: date) -> list[dict]:
    """Get all Gem snapshots within a date range."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT snapshot_date, data FROM gem_snapshots
            WHERE snapshot_date BETWEEN ? AND ?
            ORDER BY snapshot_date ASC
        """, (start_date.isoformat(), end_date.isoformat()))

        results = []
        for row in cursor.fetchall():
            data = json.loads(row["data"])
            data["snapshot_date"] = row["snapshot_date"]
            results.append(data)
        return results


def get_latest_gem_snapshot() -> Optional[dict]:
    """Get the most recent Gem snapshot."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT snapshot_date, data FROM gem_snapshots
            ORDER BY snapshot_date DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            data = json.loads(row["data"])
            data["snapshot_date"] = row["snapshot_date"]
            return data
        return None


def get_gem_trend_data(days: int = 14) -> dict:
    """
    Get trend data comparing this week vs last week.
    Returns aggregated stats and calculated trends.
    """
    today = date.today()
    this_week_start = today - timedelta(days=6)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)

    this_week_data = get_gem_snapshots_range(this_week_start, today)
    last_week_data = get_gem_snapshots_range(last_week_start, last_week_end)

    def aggregate_snapshots(snapshots: list[dict]) -> dict:
        """Aggregate multiple snapshots into totals."""
        if not snapshots:
            return {"sent": 0, "opened": 0, "replied": 0, "bounced": 0, "by_role": {}, "by_sender": {}}

        # Use the latest snapshot's totals (they're cumulative)
        latest = snapshots[-1] if snapshots else {}
        return {
            "sent": latest.get("totals", {}).get("sent", 0),
            "opened": latest.get("totals", {}).get("opened", 0),
            "replied": latest.get("totals", {}).get("replied", 0),
            "bounced": latest.get("totals", {}).get("bounced", 0),
            "by_role": latest.get("by_role", {}),
            "by_sender": latest.get("by_sender", {}),
            "by_sequence": latest.get("by_sequence", {}),
        }

    this_week = aggregate_snapshots(this_week_data)
    last_week = aggregate_snapshots(last_week_data)

    def calc_trend(current: int, previous: int) -> dict:
        """Calculate trend between two values."""
        if previous == 0:
            change_pct = 100 if current > 0 else 0
            direction = "up" if current > 0 else "steady"
        else:
            change_pct = ((current - previous) / previous) * 100
            if change_pct >= 15:
                direction = "up"
            elif change_pct <= -15:
                direction = "down"
            else:
                direction = "steady"

        return {
            "current": current,
            "previous": previous,
            "change_pct": round(change_pct, 1),
            "direction": direction
        }

    return {
        "this_week": this_week,
        "last_week": last_week,
        "trends": {
            "sent": calc_trend(this_week["sent"], last_week["sent"]),
            "replied": calc_trend(this_week["replied"], last_week["replied"]),
            "reply_rate": calc_trend(
                (this_week["replied"] / this_week["sent"] * 100) if this_week["sent"] > 0 else 0,
                (last_week["replied"] / last_week["sent"] * 100) if last_week["sent"] > 0 else 0
            ),
        },
        "has_data": len(this_week_data) > 0,
        "data_points": len(this_week_data),
    }


# ============ RECOMMENDATION FUNCTIONS ============

def save_recommendation(
    recommendation_date: date,
    for_whom: str,
    priority: str,
    category: str,
    insight: str,
    action: str
) -> int:
    """Save a daily recommendation."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_recommendations
            (recommendation_date, for_whom, priority, category, insight, action)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recommendation_date.isoformat(), for_whom, priority, category, insight, action))
        return cursor.lastrowid


def get_recommendations_for_date(target_date: date) -> list[dict]:
    """Get all recommendations for a specific date."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_recommendations
            WHERE recommendation_date = ?
            ORDER BY
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                id
        """, (target_date.isoformat(),))

        return [dict(row) for row in cursor.fetchall()]


def mark_recommendation_completed(recommendation_id: int):
    """Mark a recommendation as completed."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily_recommendations
            SET completed = TRUE
            WHERE id = ?
        """, (recommendation_id,))


# ============ WEEKLY GOALS FUNCTIONS ============

def save_weekly_goal(
    week_start: date,
    role: str,
    metric: str,
    target: int,
    notes: str = None
) -> int:
    """Save a weekly goal."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weekly_goals (week_start, role, metric, target, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (week_start.isoformat(), role, metric, target, notes))
        return cursor.lastrowid


def get_current_weekly_goal() -> Optional[dict]:
    """Get the current week's goal."""
    today = date.today()
    # Get Monday of current week
    monday = today - timedelta(days=today.weekday())

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM weekly_goals
            WHERE week_start = ?
            ORDER BY id DESC LIMIT 1
        """, (monday.isoformat(),))

        row = cursor.fetchone()
        return dict(row) if row else None


# Initialize database on module import
init_database()
