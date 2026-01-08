"""
Daily Activity Recommendation Engine

Generates actionable recommendations based on:
- Ashby pipeline data (stuck candidates, gaps, stages)
- Gem sourcing data (volume, reply rates, trends)
- Historical patterns and goals
"""

from datetime import date, datetime
from typing import Optional
from app.models.recruiting import PipelineSnapshot, RolePipeline
from app.services.database import (
    get_gem_trend_data,
    get_latest_gem_snapshot,
    save_recommendation,
    get_recommendations_for_date,
)


class Recommendation:
    """A single actionable recommendation."""

    def __init__(
        self,
        for_whom: str,  # "drew" or "blessing"
        priority: str,  # "high", "medium", "low"
        category: str,  # "screen", "follow_up", "sourcing", "review", "sync"
        insight: str,   # Why this matters
        action: str,    # Specific action to take
    ):
        self.for_whom = for_whom
        self.priority = priority
        self.category = category
        self.insight = insight
        self.action = action

    def to_dict(self) -> dict:
        return {
            "for_whom": self.for_whom,
            "priority": self.priority,
            "category": self.category,
            "insight": self.insight,
            "action": self.action,
        }


def generate_recommendations(
    pipeline: Optional[PipelineSnapshot] = None,
    gem_data: Optional[dict] = None,
) -> list[Recommendation]:
    """
    Generate daily recommendations based on all available data.

    Returns a list of Recommendation objects sorted by priority.
    """
    recommendations = []

    # ============ ASHBY-BASED RECOMMENDATIONS ============
    if pipeline:
        recommendations.extend(_generate_pipeline_recommendations(pipeline))

    # ============ GEM-BASED RECOMMENDATIONS ============
    if gem_data is None:
        gem_data = get_latest_gem_snapshot()

    if gem_data:
        gem_trends = get_gem_trend_data()
        recommendations.extend(_generate_sourcing_recommendations(gem_data, gem_trends))

    # ============ COMBINED INSIGHTS ============
    if pipeline and gem_data:
        recommendations.extend(_generate_combined_recommendations(pipeline, gem_data))

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

    return recommendations


def _generate_pipeline_recommendations(pipeline: PipelineSnapshot) -> list[Recommendation]:
    """Generate recommendations from Ashby pipeline data."""
    recs = []

    for role in pipeline.roles:
        # HIGH: Stuck candidates need immediate attention
        for candidate in role.stuck_candidates[:3]:  # Top 3 stuck
            recs.append(Recommendation(
                for_whom="drew",
                priority="high",
                category="follow_up",
                insight=f"{candidate.name} has been in {candidate.current_stage} for {candidate.days_in_stage} days",
                action=f"Follow up on {candidate.name} for {role.job_title} — move forward or archive",
            ))

        # HIGH: Candidates in HM Screen need scheduling
        hm_count = next((s.count for s in role.stages if s.name == "HM Screen"), 0)
        if hm_count > 0:
            recs.append(Recommendation(
                for_whom="drew",
                priority="high",
                category="screen",
                insight=f"{hm_count} candidate(s) waiting for HM Screen",
                action=f"Schedule HM screens for {role.job_title} candidates this week",
            ))

        # MEDIUM: Candidates in Onsite need debrief
        onsite_count = next((s.count for s in role.stages if s.name == "Onsite"), 0)
        if onsite_count > 0:
            recs.append(Recommendation(
                for_whom="drew",
                priority="medium",
                category="review",
                insight=f"{onsite_count} candidate(s) at Onsite stage",
                action=f"Schedule debrief for {role.job_title} onsite candidates",
            ))

        # MEDIUM: Low pipeline warning
        recruiter_screen_count = next((s.count for s in role.stages if s.name == "Recruiter Screen"), 0)
        if recruiter_screen_count < 5 and role.priority == 1:
            recs.append(Recommendation(
                for_whom="blessing",
                priority="medium",
                category="sourcing",
                insight=f"{role.job_title} has only {recruiter_screen_count} candidates at top of funnel",
                action=f"Increase sourcing volume for {role.job_title} this week",
            ))

        # LOW: Pipeline health check
        if role.health_status == "red":
            recs.append(Recommendation(
                for_whom="drew",
                priority="medium",
                category="review",
                insight=f"{role.job_title} pipeline is critical (red status)",
                action=f"Review {role.job_title} pipeline strategy — consider expanding criteria",
            ))

    return recs


def _generate_sourcing_recommendations(gem_data: dict, gem_trends: dict) -> list[Recommendation]:
    """Generate recommendations from Gem sourcing data."""
    recs = []

    if not gem_trends.get("has_data"):
        return recs

    # Check overall volume
    this_week = gem_trends.get("this_week", {})
    sent_trend = gem_trends.get("trends", {}).get("sent", {})

    total_sent = this_week.get("sent", 0)
    if total_sent < 100:
        recs.append(Recommendation(
            for_whom="blessing",
            priority="high",
            category="sourcing",
            insight=f"Only {total_sent} outreaches this week (target: 120)",
            action="Increase daily outreach volume to hit 120/week target",
        ))

    # Check reply rate trends
    reply_trend = gem_trends.get("trends", {}).get("reply_rate", {})
    if reply_trend.get("direction") == "down":
        recs.append(Recommendation(
            for_whom="drew",
            priority="medium",
            category="review",
            insight=f"Reply rate dropped from {reply_trend.get('previous', 0):.1f}% to {reply_trend.get('current', 0):.1f}%",
            action="Review recent outreach messaging — consider refreshing templates",
        ))
        recs.append(Recommendation(
            for_whom="blessing",
            priority="medium",
            category="sourcing",
            insight="Reply rate is declining",
            action="Test new subject lines this week",
        ))

    # Check by role
    by_role = this_week.get("by_role", {})
    for role_name, role_stats in by_role.items():
        sent = role_stats.get("sent", 0)
        replied = role_stats.get("replied", 0)
        reply_rate = (replied / sent * 100) if sent > 0 else 0

        # Low volume warning
        if sent < 40:
            recs.append(Recommendation(
                for_whom="blessing",
                priority="medium",
                category="sourcing",
                insight=f"{role_name} only has {sent} outreaches this week",
                action=f"Allocate more outreach volume to {role_name}",
            ))

        # Low reply rate warning
        if reply_rate < 8 and sent > 20:
            recs.append(Recommendation(
                for_whom="drew",
                priority="low",
                category="review",
                insight=f"{role_name} reply rate is only {reply_rate:.1f}%",
                action=f"Review {role_name} targeting — are we reaching the right candidates?",
            ))

    # Check by sender
    by_sender = this_week.get("by_sender", {})
    for sender_name, sender_stats in by_sender.items():
        sent = sender_stats.get("sent", 0)
        replied = sender_stats.get("replied", 0)
        reply_rate = (replied / sent * 100) if sent > 0 else 0

        # Blessing volume check
        if sender_name == "Blessing" and sent < 80:
            recs.append(Recommendation(
                for_whom="blessing",
                priority="medium",
                category="sourcing",
                insight=f"Blessing has sent {sent} outreaches (target: ~100/week)",
                action="Increase daily outreach cadence",
            ))

    # Check for top performing sequences
    by_sequence = this_week.get("by_sequence", {})
    if by_sequence:
        # Find best performer
        best_seq = max(
            by_sequence.items(),
            key=lambda x: x[1].get("reply_rate", 0) if x[1].get("sent", 0) > 10 else 0,
            default=(None, {})
        )
        if best_seq[0] and best_seq[1].get("reply_rate", 0) > 0.15:
            recs.append(Recommendation(
                for_whom="blessing",
                priority="low",
                category="sync",
                insight=f"'{best_seq[0]}' has {best_seq[1].get('reply_rate', 0)*100:.0f}% reply rate",
                action="Clone the messaging approach from this top-performing sequence",
            ))

        # Find underperformers
        for seq_name, seq_stats in by_sequence.items():
            sent = seq_stats.get("sent", 0)
            reply_rate = seq_stats.get("reply_rate", 0)
            if sent > 20 and reply_rate < 0.05:
                recs.append(Recommendation(
                    for_whom="blessing",
                    priority="medium",
                    category="review",
                    insight=f"'{seq_name}' has only {reply_rate*100:.0f}% reply rate",
                    action="Pause or rewrite this underperforming sequence",
                ))

    return recs


def _generate_combined_recommendations(
    pipeline: PipelineSnapshot,
    gem_data: dict
) -> list[Recommendation]:
    """Generate recommendations that combine Ashby + Gem insights."""
    recs = []

    # Connect pipeline gaps to sourcing priorities
    for role in pipeline.roles:
        if role.health_status in ["red", "yellow"]:
            # Map role title to Gem role name
            gem_role = "Full Stack" if "Full Stack" in role.job_title else "AI Engineer"
            by_role = gem_data.get("by_role", {})
            role_stats = by_role.get(gem_role, {})

            sent = role_stats.get("sent", 0)
            replied = role_stats.get("replied", 0)

            if sent < 50:
                recs.append(Recommendation(
                    for_whom="blessing",
                    priority="high",
                    category="sourcing",
                    insight=f"{role.job_title} pipeline is {role.health_status} and sourcing volume is low ({sent}/week)",
                    action=f"Prioritize {role.job_title} sourcing — need {role.gap_to_hire} screens to hire",
                ))

    return recs


def get_daily_activities(
    pipeline: Optional[PipelineSnapshot] = None,
    for_whom: Optional[str] = None,
) -> dict:
    """
    Get formatted daily activities for display.

    Returns a dict with activities grouped by person and priority.
    """
    recommendations = generate_recommendations(pipeline)

    # Filter by person if specified
    if for_whom:
        recommendations = [r for r in recommendations if r.for_whom.lower() == for_whom.lower()]

    # Group by person
    drew_activities = [r for r in recommendations if r.for_whom == "drew"]
    blessing_activities = [r for r in recommendations if r.for_whom == "blessing"]

    # Format for display
    def format_activities(activities: list[Recommendation]) -> list[dict]:
        formatted = []
        for i, rec in enumerate(activities[:5], 1):  # Top 5 per person
            category_icons = {
                "screen": "📞",
                "follow_up": "⚡",
                "sourcing": "🔍",
                "review": "📋",
                "sync": "🤝",
            }
            icon = category_icons.get(rec.category, "📌")

            formatted.append({
                "number": i,
                "icon": icon,
                "category": rec.category.upper(),
                "action": rec.action,
                "insight": rec.insight,
                "priority": rec.priority,
            })
        return formatted

    return {
        "drew": format_activities(drew_activities),
        "blessing": format_activities(blessing_activities),
        "total_recommendations": len(recommendations),
        "generated_at": datetime.now().isoformat(),
    }


def save_daily_recommendations(pipeline: Optional[PipelineSnapshot] = None):
    """Generate and save recommendations for today."""
    today = date.today()
    recommendations = generate_recommendations(pipeline)

    for rec in recommendations:
        save_recommendation(
            recommendation_date=today,
            for_whom=rec.for_whom,
            priority=rec.priority,
            category=rec.category,
            insight=rec.insight,
            action=rec.action,
        )

    return len(recommendations)
