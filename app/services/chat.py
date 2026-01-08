"""
Chat service powered by Claude API.

Provides intelligent responses about pipeline data, candidates,
and recruiting recommendations.
"""

import anthropic
from datetime import datetime
from app.config import get_settings
from app.services.analysis import analyze_pipeline
from app.services.database import get_gem_trend_data, get_latest_gem_snapshot
from app.services.recommendations import get_daily_activities

settings = get_settings()


def get_system_prompt(pipeline_data: dict, gem_data: dict, activities: dict) -> str:
    """Build the system prompt with current data context."""

    # Format pipeline data
    pipeline_summary = ""
    if pipeline_data:
        for role in pipeline_data.get("roles", []):
            stages = " → ".join([str(s["count"]) for s in role["stages"]])
            stuck_names = ", ".join([c["name"] for c in role.get("stuck_candidates", [])[:3]])

            pipeline_summary += f"""
**{role['job_title']}** (P{role['priority']}) - {role['health_status'].upper()}
- Pipeline: {stages}
- Active candidates: {role['total_candidates']}
- Gap to hire: ~{role['gap_to_hire']} screens needed
- Stuck candidates: {stuck_names if stuck_names else 'None'}
"""

    # Format Gem data
    gem_summary = ""
    if gem_data:
        totals = gem_data.get("totals", {})
        gem_summary = f"""
**This Week's Sourcing:**
- Total sent: {totals.get('sent', 0)}
- Total replies: {totals.get('replied', 0)}
- Reply rate: {totals.get('reply_rate', 0) * 100:.1f}%
"""
        by_role = gem_data.get("by_role", {})
        for role_name, stats in by_role.items():
            gem_summary += f"- {role_name}: {stats.get('sent', 0)} sent, {stats.get('replied', 0)} replies\n"

    # Format activities
    activities_summary = ""
    if activities:
        drew_tasks = activities.get("drew", [])[:3]
        blessing_tasks = activities.get("blessing", [])[:3]

        if drew_tasks:
            activities_summary += "\n**Drew's Top Priorities:**\n"
            for task in drew_tasks:
                activities_summary += f"- [{task['category']}] {task['action']}\n"

        if blessing_tasks:
            activities_summary += "\n**Blessing's Top Priorities:**\n"
            for task in blessing_tasks:
                activities_summary += f"- [{task['category']}] {task['action']}\n"

    return f"""You are a recruiting co-pilot assistant for Drew, an internal recruiter at an AI startup called Fonzi.

Your role is to:
1. Answer questions about the recruiting pipeline
2. Provide actionable recommendations
3. Help Drew and Blessing (the sourcer) stay focused on high-leverage work
4. Flag issues and stuck candidates

**Current Date:** {datetime.now().strftime("%A, %B %d, %Y")}

**CURRENT PIPELINE DATA:**
{pipeline_summary if pipeline_summary else "No pipeline data available."}

**SOURCING DATA (from Gem):**
{gem_summary if gem_summary else "No sourcing data available yet. Drew can add Gem stats in the 'Add Gem Data' tab."}

**TODAY'S RECOMMENDED ACTIVITIES:**
{activities_summary if activities_summary else "No specific activities generated."}

**CONTEXT:**
- Drew manages screens and moves candidates through the pipeline
- Blessing handles sourcing via LinkedIn + Gem (~120 outreaches/week)
- Pipeline stages: Recruiter Screen → HM Screen → Testing → Onsite → Offer → Hired
- A candidate is "stuck" if they've been in a stage longer than the threshold (e.g., >5 days in Recruiter Screen)

**GUIDELINES:**
- Be concise and actionable
- Always connect insights to specific actions
- Use the actual data provided above
- If asked about something not in the data, say so clearly
- Format responses with bullet points for readability
- When recommending who to screen, prioritize by days waiting and stage
"""


async def chat(message: str) -> str:
    """
    Process a chat message and return a response.

    Fetches current pipeline data and uses Claude to generate a response.
    """
    # Check if API key is configured
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_anthropic_api_key_here":
        return "⚠️ Claude API key not configured. Please add your Anthropic API key to the .env file to enable chat."

    try:
        # Fetch current data
        pipeline_snapshot = await analyze_pipeline()
        pipeline_data = {
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
                        {"name": c.name, "current_stage": c.current_stage, "days_in_stage": c.days_in_stage}
                        for c in role.stuck_candidates
                    ],
                }
                for role in pipeline_snapshot.roles
            ]
        }

        # Get Gem data
        gem_data = get_latest_gem_snapshot()

        # Get activities
        activities = get_daily_activities(pipeline_snapshot)

        # Build system prompt with data
        system_prompt = get_system_prompt(pipeline_data, gem_data, activities)

        # Call Claude API
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )

        return response.content[0].text

    except anthropic.APIError as e:
        return f"⚠️ Error communicating with Claude: {str(e)}"
    except Exception as e:
        return f"⚠️ An error occurred: {str(e)}"
