"""API routes for the Recruiting Co-Pilot."""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.analysis import analyze_pipeline
from app.services.database import (
    save_gem_snapshot,
    save_gem_sequence_stats,
    get_gem_trend_data,
    get_latest_gem_snapshot,
    get_gem_snapshots_range,
)
from app.services.recommendations import get_daily_activities, generate_recommendations
from app.services.email import send_digest_email
from app.services.chat import chat as chat_service
from app.config import get_settings

settings = get_settings()
router = APIRouter()


# ============ REQUEST/RESPONSE MODELS ============

class GemSequenceInput(BaseModel):
    """Input for a single sequence's stats."""
    sequence_name: str
    role: str  # "Full Stack" or "AI Engineer"
    sender: str  # "Drew" or "Blessing"
    sent: int = 0
    opened: int = 0
    replied: int = 0
    bounced: int = 0


class GemSnapshotInput(BaseModel):
    """Input for a complete Gem data snapshot."""
    snapshot_date: Optional[str] = None  # ISO format, defaults to today
    sequences: list[GemSequenceInput]
    notes: Optional[str] = None


class ChatMessage(BaseModel):
    """A chat message from the user."""
    message: str


# ============ GEM DATA ENDPOINTS ============

@router.post("/api/gem/snapshot")
async def save_gem_data(data: GemSnapshotInput):
    """
    Save a Gem data snapshot.

    This endpoint accepts sequence-level stats and aggregates them
    into role/sender summaries automatically.
    """
    # Parse date
    if data.snapshot_date:
        try:
            snapshot_date = date.fromisoformat(data.snapshot_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        snapshot_date = date.today()

    # Aggregate data
    by_sequence = {}
    by_role = {}
    by_sender = {}
    totals = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}

    for seq in data.sequences:
        # Store sequence stats
        save_gem_sequence_stats(
            snapshot_date=snapshot_date,
            sequence_name=seq.sequence_name,
            role=seq.role,
            sender=seq.sender,
            sent=seq.sent,
            opened=seq.opened,
            replied=seq.replied,
            bounced=seq.bounced,
        )

        # Build aggregates
        reply_rate = seq.replied / seq.sent if seq.sent > 0 else 0
        by_sequence[seq.sequence_name] = {
            "sent": seq.sent,
            "opened": seq.opened,
            "replied": seq.replied,
            "bounced": seq.bounced,
            "reply_rate": reply_rate,
            "role": seq.role,
            "sender": seq.sender,
        }

        # Aggregate by role
        if seq.role not in by_role:
            by_role[seq.role] = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}
        by_role[seq.role]["sent"] += seq.sent
        by_role[seq.role]["opened"] += seq.opened
        by_role[seq.role]["replied"] += seq.replied
        by_role[seq.role]["bounced"] += seq.bounced

        # Aggregate by sender
        if seq.sender not in by_sender:
            by_sender[seq.sender] = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}
        by_sender[seq.sender]["sent"] += seq.sent
        by_sender[seq.sender]["opened"] += seq.opened
        by_sender[seq.sender]["replied"] += seq.replied
        by_sender[seq.sender]["bounced"] += seq.bounced

        # Totals
        totals["sent"] += seq.sent
        totals["opened"] += seq.opened
        totals["replied"] += seq.replied
        totals["bounced"] += seq.bounced

    # Calculate reply rates
    for role_stats in by_role.values():
        role_stats["reply_rate"] = (
            role_stats["replied"] / role_stats["sent"]
            if role_stats["sent"] > 0 else 0
        )
    for sender_stats in by_sender.values():
        sender_stats["reply_rate"] = (
            sender_stats["replied"] / sender_stats["sent"]
            if sender_stats["sent"] > 0 else 0
        )
    totals["reply_rate"] = totals["replied"] / totals["sent"] if totals["sent"] > 0 else 0

    # Save complete snapshot
    snapshot_data = {
        "by_sequence": by_sequence,
        "by_role": by_role,
        "by_sender": by_sender,
        "totals": totals,
        "notes": data.notes,
    }
    snapshot_id = save_gem_snapshot(snapshot_date, snapshot_data)

    return {
        "status": "success",
        "snapshot_id": snapshot_id,
        "snapshot_date": snapshot_date.isoformat(),
        "totals": totals,
        "sequences_saved": len(data.sequences),
    }


@router.get("/api/gem/latest")
async def get_latest_gem():
    """Get the most recent Gem snapshot."""
    snapshot = get_latest_gem_snapshot()
    if not snapshot:
        return {"status": "no_data", "message": "No Gem data has been entered yet"}
    return {"status": "success", "data": snapshot}


@router.get("/api/gem/trends")
async def get_gem_trends():
    """Get Gem trend data (this week vs last week)."""
    trends = get_gem_trend_data()
    return {"status": "success", "data": trends}


# ============ PIPELINE & ANALYSIS ENDPOINTS ============

@router.get("/api/pipeline")
async def get_pipeline():
    """Get current pipeline analysis from Ashby."""
    try:
        snapshot = await analyze_pipeline()
        return {
            "status": "success",
            "data": {
                "generated_at": snapshot.generated_at.isoformat(),
                "roles": [
                    {
                        "job_title": role.job_title,
                        "priority": role.priority,
                        "health_status": role.health_status,
                        "total_candidates": role.total_candidates,
                        "gap_to_hire": role.gap_to_hire,
                        "bottleneck": role.bottleneck,
                        "stages": [{"name": s.name, "count": s.count} for s in role.stages],
                        "stuck_candidates": [
                            {
                                "name": c.name,
                                "current_stage": c.current_stage,
                                "days_in_stage": c.days_in_stage,
                            }
                            for c in role.stuck_candidates
                        ],
                    }
                    for role in snapshot.roles
                ],
                "sourcing_allocation": snapshot.sourcing_allocation,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pipeline: {str(e)}")


@router.post("/api/refresh")
async def refresh_data():
    """Refresh all data from Ashby."""
    try:
        snapshot = await analyze_pipeline()
        return {
            "status": "success",
            "message": "Data refreshed",
            "generated_at": snapshot.generated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh: {str(e)}")


# ============ RECOMMENDATIONS ENDPOINTS ============

@router.get("/api/activities")
async def get_activities(for_whom: Optional[str] = None):
    """
    Get daily activity recommendations.

    Optional query param: for_whom=drew or for_whom=blessing
    """
    try:
        # Get fresh pipeline data
        pipeline = await analyze_pipeline()
        activities = get_daily_activities(pipeline, for_whom)
        return {"status": "success", "data": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")


# ============ EMAIL DIGEST ENDPOINT ============

@router.post("/api/digest/send")
async def send_digest():
    """Manually trigger sending the daily digest email."""
    try:
        snapshot = await analyze_pipeline()
        result = await send_digest_email(snapshot)
        return {
            "status": "success",
            "message": "Digest email sent",
            "email_id": result.get("id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send digest: {str(e)}")


# ============ CHAT ENDPOINT ============

@router.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """
    Chat with the recruiting co-pilot.

    Send a message and get an AI-powered response based on
    current pipeline data and recommendations.
    """
    try:
        response = await chat_service(message.message)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "response": f"Sorry, I encountered an error: {str(e)}"}
