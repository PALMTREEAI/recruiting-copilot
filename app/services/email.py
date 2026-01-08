import resend
import httpx
from datetime import datetime
from typing import List, Dict
from app.config import get_settings
from app.models.recruiting import PipelineSnapshot, RolePipeline
from app.services.recommendations import get_daily_activities

settings = get_settings()

# AI Recruiting news sources - curated list of high-quality sources
AI_RECRUITING_SOURCES = [
    {
        "title": "How AI is Transforming Technical Recruiting",
        "url": "https://www.linkedin.com/pulse/ai-recruiting-trends/",
        "category": "AI Recruiting Trends"
    },
    {
        "title": "The Future of AI-Powered Candidate Sourcing",
        "url": "https://www.shrm.org/topics-tools/news/technology",
        "category": "Sourcing Tech"
    },
    {
        "title": "Building Diverse Engineering Teams with AI Tools",
        "url": "https://www.ere.net/",
        "category": "DEI in Tech Hiring"
    },
    {
        "title": "Recruiter Productivity: AI Tools That Actually Work",
        "url": "https://www.recruitingdaily.com/",
        "category": "Recruiter Tools"
    },
    {
        "title": "2025 Tech Hiring Market Analysis",
        "url": "https://www.hired.com/state-of-tech-salaries",
        "category": "Market Data"
    },
]

# Daily sourcing action templates
SOURCING_ACTION_TEMPLATES = [
    {"action": "Search LinkedIn for {role} candidates with specific tech stack keywords", "icon": "🔍", "category": "SOURCING"},
    {"action": "Refresh Boolean search strings for {role} on LinkedIn Recruiter", "icon": "🔄", "category": "SOURCING"},
    {"action": "Review and respond to any inbound applications in Ashby", "icon": "📬", "category": "INBOUND"},
    {"action": "Post engaging content about Fonzi's engineering culture", "icon": "📢", "category": "EMPLOYER BRAND"},
    {"action": "Reach out to 5 passive candidates from previous searches", "icon": "✉️", "category": "OUTREACH"},
    {"action": "Update job descriptions with latest tech stack requirements", "icon": "📝", "category": "JOB POSTING"},
    {"action": "Network with referral sources and past candidates", "icon": "🤝", "category": "NETWORKING"},
    {"action": "Research competitors hiring for similar roles", "icon": "🔬", "category": "MARKET INTEL"},
    {"action": "Review Gem sequence performance and A/B test messaging", "icon": "📊", "category": "OPTIMIZATION"},
    {"action": "Attend or plan virtual tech meetup for talent pipeline", "icon": "🎤", "category": "EVENTS"},
]


async def fetch_ai_recruiting_news() -> List[Dict]:
    """
    Fetch AI recruiting news and trends.

    Returns a curated list of relevant articles for recruiters.
    In production, this could integrate with RSS feeds or news APIs.
    """
    # For now, return curated high-value resources
    # These rotate based on the day of week to keep content fresh
    day_of_week = datetime.now().weekday()

    # Rotate through different content each day
    news_items = [
        # Monday - Focus on AI tools
        [
            {"title": "Top AI Recruiting Tools for 2025", "url": "https://www.g2.com/categories/recruiting-automation", "category": "🤖 AI Tools"},
            {"title": "ChatGPT Prompts for Recruiters", "url": "https://www.linkedin.com/pulse/chatgpt-recruiting/", "category": "🤖 AI Tools"},
            {"title": "How to Use AI for Boolean Searches", "url": "https://www.sourcecon.com/", "category": "🔍 Sourcing"},
            {"title": "AI Writing Tools for Outreach Messages", "url": "https://www.jasper.ai/", "category": "✍️ Outreach"},
            {"title": "Candidate Matching AI Platforms Compared", "url": "https://www.capterra.com/recruiting-software/", "category": "🎯 Matching"},
        ],
        # Tuesday - Market trends
        [
            {"title": "Tech Hiring Trends: What's Hot in 2025", "url": "https://www.hired.com/blog/", "category": "📈 Market Trends"},
            {"title": "AI Engineer Salary Benchmarks", "url": "https://www.levels.fyi/", "category": "💰 Compensation"},
            {"title": "Remote vs Hybrid: What Candidates Want", "url": "https://www.flexjobs.com/blog/", "category": "🏠 Remote Work"},
            {"title": "Full Stack Developer Market Analysis", "url": "https://stackoverflow.blog/", "category": "📊 Market Data"},
            {"title": "Startup Hiring Playbook", "url": "https://www.ycombinator.com/library/", "category": "🚀 Startup Hiring"},
        ],
        # Wednesday - Candidate experience
        [
            {"title": "Improving Candidate Experience with AI", "url": "https://www.talentboard.org/", "category": "😊 Candidate Experience"},
            {"title": "Speed to Hire: Why Every Day Matters", "url": "https://www.shrm.org/", "category": "⏱️ Process"},
            {"title": "Interview Scheduling Best Practices", "url": "https://www.greenhouse.io/blog", "category": "📅 Scheduling"},
            {"title": "Rejection Emails That Keep Doors Open", "url": "https://www.ere.net/", "category": "📧 Communication"},
            {"title": "Building a Talent Community", "url": "https://www.beamery.com/resources/", "category": "👥 Talent Pools"},
        ],
        # Thursday - Sourcing techniques
        [
            {"title": "Advanced LinkedIn Recruiter Techniques", "url": "https://business.linkedin.com/talent-solutions/blog", "category": "🔍 LinkedIn"},
            {"title": "GitHub Sourcing for Engineers", "url": "https://www.sourcecon.com/", "category": "💻 GitHub"},
            {"title": "X-Ray Search Mastery Guide", "url": "https://recruitingbrainfood.com/", "category": "🔬 Boolean"},
            {"title": "Diversity Sourcing Strategies", "url": "https://www.hiretechladies.com/", "category": "🌈 DEI"},
            {"title": "Building Your Sourcing Tech Stack", "url": "https://www.gem.com/blog/", "category": "🛠️ Tools"},
        ],
        # Friday - Industry insights
        [
            {"title": "AI Industry Hiring Trends", "url": "https://www.aijobbulletin.com/", "category": "🤖 AI Industry"},
            {"title": "What Top Engineers Look for in Jobs", "url": "https://www.teamblind.com/", "category": "💡 Candidate Intel"},
            {"title": "Competing for AI Talent", "url": "https://hbr.org/", "category": "🏆 Competition"},
            {"title": "The Future of Technical Recruiting", "url": "https://www.recruiter.com/", "category": "🔮 Future"},
            {"title": "Building Engineering Culture", "url": "https://www.infoq.com/", "category": "🏗️ Culture"},
        ],
        # Saturday - Deep dives
        [
            {"title": "Recruiter Productivity Hacks", "url": "https://www.recruitingdaily.com/", "category": "⚡ Productivity"},
            {"title": "Understanding Technical Skills", "url": "https://roadmap.sh/", "category": "📚 Technical Knowledge"},
            {"title": "Psychology of Candidate Decisions", "url": "https://www.linkedin.com/learning/", "category": "🧠 Psychology"},
            {"title": "Recruiter Personal Branding", "url": "https://www.linkedin.com/pulse/", "category": "📣 Personal Brand"},
            {"title": "Negotiation Strategies for Offers", "url": "https://www.levels.fyi/blog/", "category": "🤝 Negotiation"},
        ],
        # Sunday - Planning
        [
            {"title": "Weekly Recruiting Planning Guide", "url": "https://www.notion.so/templates/", "category": "📋 Planning"},
            {"title": "Recruiting Metrics That Matter", "url": "https://www.greenhouse.io/blog", "category": "📊 Metrics"},
            {"title": "Setting Hiring Goals", "url": "https://www.ashbyhq.com/blog", "category": "🎯 Goals"},
            {"title": "Pipeline Health Indicators", "url": "https://www.lever.co/blog/", "category": "🏥 Pipeline Health"},
            {"title": "Recruiter Wellness and Burnout Prevention", "url": "https://www.headspace.com/", "category": "🧘 Wellness"},
        ],
    ]

    return news_items[day_of_week]


def get_sourcing_actions(snapshot: PipelineSnapshot) -> List[Dict]:
    """Generate 5 specific sourcing actions based on pipeline state."""
    actions = []

    # Find the highest priority role with biggest gap
    priority_role = None
    max_gap = 0
    for role in snapshot.roles:
        if role.gap_to_hire > max_gap:
            max_gap = role.gap_to_hire
            priority_role = role.job_title

    if not priority_role:
        priority_role = "Senior Full Stack Engineer"

    # Generate 5 targeted sourcing actions
    actions = [
        {
            "number": 1,
            "action": f"Send 20 personalized outreach messages to {priority_role} candidates on LinkedIn",
            "icon": "✉️",
            "category": "OUTREACH"
        },
        {
            "number": 2,
            "action": "Review and respond to all new inbound applications (aim for <24hr response time)",
            "icon": "📬",
            "category": "INBOUND"
        },
        {
            "number": 3,
            "action": f"Refresh your Boolean search on LinkedIn for {priority_role} with new keywords",
            "icon": "🔍",
            "category": "SOURCING"
        },
        {
            "number": 4,
            "action": "Post an engaging update about Fonzi's engineering culture or recent wins",
            "icon": "📢",
            "category": "EMPLOYER BRAND"
        },
        {
            "number": 5,
            "action": "Reach out to 3 past silver-medalist candidates to re-engage them",
            "icon": "🔄",
            "category": "RE-ENGAGEMENT"
        },
    ]

    return actions

# Initialize Resend
resend.api_key = settings.resend_api_key


def format_digest_email(
    snapshot: PipelineSnapshot,
    activities: dict = None,
    sourcing_actions: list = None,
    news_items: list = None
) -> str:
    """Format the daily digest email content."""
    date_str = snapshot.generated_at.strftime("%B %d, %Y")
    day_name = snapshot.generated_at.strftime("%A")

    lines = []
    lines.append(f"📊 RECRUITING DAILY BRIEF — {day_name}, {date_str}")
    lines.append("")
    lines.append("Good morning! Here's your recruiting dashboard for today.")
    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("🎯 FULL PIPELINE REPORT")
    lines.append("")

    # Pipeline health for each role
    total_candidates = 0
    total_gap = 0
    for role in snapshot.roles:
        health_emoji = {"red": "🔴", "yellow": "🟡", "green": "🟢"}
        emoji = health_emoji.get(role.health_status, "⚪")

        lines.append(f"▸ {role.job_title} (P{role.priority}) {emoji}")

        # Pipeline counts as arrow flow with stage names
        stage_flow = []
        for s in role.stages:
            stage_flow.append(f"{s.name}: {s.count}")
        lines.append(f"  {' → '.join(stage_flow)}")

        # Gap to hire
        lines.append(f"  Gap to Hire: ~{role.gap_to_hire} more screens needed")

        # Bottleneck
        if role.bottleneck:
            lines.append(f"  ⚠️ Bottleneck: {role.bottleneck}")

        total_candidates += role.total_candidates
        total_gap += role.gap_to_hire
        lines.append("")

    lines.append(f"📈 SUMMARY: {total_candidates} active candidates | ~{total_gap} total screens needed")
    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("👤 DREW'S PRIORITIES TODAY (Candidate Experience)")
    lines.append("")
    lines.append("Focus on these to keep candidates moving and happy:")
    lines.append("")

    # Use smart recommendations if available, fallback to simple priorities
    if activities and activities.get("drew"):
        for item in activities["drew"][:5]:
            lines.append(f"{item['number']}. {item['icon']} [{item['category']}] {item['action']}")
    else:
        priorities = generate_priorities(snapshot)
        for i, priority in enumerate(priorities[:5], 1):
            lines.append(f"{i}. {priority}")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("🔍 5 SOURCING ACTIONS FOR TODAY")
    lines.append("")
    lines.append("Build the pipeline with these daily actions:")
    lines.append("")

    if sourcing_actions:
        for action in sourcing_actions:
            lines.append(f"{action['number']}. {action['icon']} [{action['category']}] {action['action']}")
    else:
        lines.append("1. ✉️ [OUTREACH] Send 20 personalized messages to priority role candidates")
        lines.append("2. 📬 [INBOUND] Review and respond to new applications")
        lines.append("3. 🔍 [SOURCING] Refresh Boolean searches with new keywords")
        lines.append("4. 📢 [EMPLOYER BRAND] Post about Fonzi's engineering culture")
        lines.append("5. 🔄 [RE-ENGAGE] Reach out to past silver-medalist candidates")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("📋 BLESSING'S PRIORITIES TODAY")
    lines.append("")

    if activities and activities.get("blessing"):
        for item in activities["blessing"][:5]:
            lines.append(f"{item['number']}. {item['icon']} [{item['category']}] {item['action']}")
    else:
        lines.append("1. 🔍 [SOURCING] Focus outreach on priority roles")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("🎯 SOURCING ALLOCATION THIS WEEK")
    lines.append("")
    lines.append("Recommended outreach split (120 total):")

    for role in snapshot.roles:
        count = snapshot.sourcing_allocation.get(role.job_title, 0)
        pct = int((count / 120) * 100) if count else 0
        reason = get_sourcing_reason(role)
        lines.append(f"  • {role.job_title}: {count} ({pct}%) — {reason}")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("⚠️ STUCK CANDIDATES (action needed)")
    lines.append("")

    # Collect all stuck candidates
    stuck_count = 0
    for role in snapshot.roles:
        for candidate in role.stuck_candidates:
            lines.append(
                f"• {role.job_title}: {candidate.name} — "
                f"{candidate.current_stage} for {candidate.days_in_stage} days"
            )
            stuck_count += 1

    if stuck_count == 0:
        lines.append("✅ No stuck candidates — pipeline is moving!")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("📚 AI RECRUITING TRENDS & READING")
    lines.append("")
    lines.append("Stay sharp with today's curated resources:")
    lines.append("")

    if news_items:
        for i, item in enumerate(news_items, 1):
            lines.append(f"{i}. [{item['category']}] {item['title']}")
            lines.append(f"   {item['url']}")
    else:
        lines.append("1. [🤖 AI Tools] Top AI Recruiting Tools for 2025")
        lines.append("2. [📈 Trends] Tech Hiring Market Analysis")
        lines.append("3. [🔍 Sourcing] Advanced LinkedIn Techniques")
        lines.append("4. [💡 Insights] What Engineers Look for in Jobs")
        lines.append("5. [🚀 Strategy] Startup Recruiting Playbook")

    lines.append("")
    lines.append("━" * 50)
    lines.append("")
    lines.append("Have a great day! 🚀")
    lines.append("")
    lines.append("— Your Recruiting Co-Pilot")

    return "\n".join(lines)


def generate_priorities(snapshot: PipelineSnapshot) -> list[str]:
    """Generate today's priority actions based on pipeline analysis."""
    priorities = []

    for role in snapshot.roles:
        # Check for stuck candidates
        if role.stuck_candidates:
            for candidate in role.stuck_candidates[:2]:
                priorities.append(
                    f"[FOLLOW UP] {candidate.name} stuck in {candidate.current_stage} "
                    f"for {candidate.days_in_stage} days ({role.job_title})"
                )

        # Check for bottlenecks
        if role.bottleneck and role.health_status == "red":
            priorities.append(
                f"[REVIEW] {role.job_title} has critical bottleneck: {role.bottleneck}"
            )

        # Check for candidates in HM Screen (need to schedule)
        hm_count = next(
            (s.count for s in role.stages if s.name == "HM Screen"), 0
        )
        if hm_count > 0:
            priorities.append(
                f"[SCHEDULE] {hm_count} candidate(s) in HM Screen for {role.job_title}"
            )

        # Check for candidates in Onsite
        onsite_count = next(
            (s.count for s in role.stages if s.name == "Onsite"), 0
        )
        if onsite_count > 0:
            priorities.append(
                f"[DEBRIEF] {onsite_count} candidate(s) completed Onsite for {role.job_title}"
            )

    # Add general priorities if list is short
    if len(priorities) < 3:
        priorities.append("[SOURCING] Review Blessing's outreach targets for the week")

    return priorities


def get_sourcing_reason(role: RolePipeline) -> str:
    """Get a short reason for the sourcing allocation."""
    if role.health_status == "red":
        if role.bottleneck:
            return f"Critical — {role.bottleneck.split('(')[0].strip()}"
        return "Critical pipeline gap"
    elif role.health_status == "yellow":
        return "Moderate gap, needs attention"
    else:
        return "Healthy, maintain flow"


def format_html_digest(
    snapshot: PipelineSnapshot,
    activities: dict = None,
    sourcing_actions: list = None,
    news_items: list = None
) -> str:
    """Format the daily digest as HTML email."""
    date_str = snapshot.generated_at.strftime("%B %d, %Y")
    day_name = snapshot.generated_at.strftime("%A")

    # Calculate totals
    total_candidates = sum(role.total_candidates for role in snapshot.roles)
    total_gap = sum(role.gap_to_hire for role in snapshot.roles)

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 650px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            h1 {{ color: #1a1a1a; border-bottom: 3px solid #4F46E5; padding-bottom: 15px; margin-bottom: 10px; }}
            .greeting {{ color: #666; margin-bottom: 25px; }}
            h2 {{ color: #374151; margin-top: 30px; font-size: 18px; }}
            .section {{ background: #f9fafb; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4F46E5; }}
            .section-alt {{ background: #fef3c7; border-left-color: #f59e0b; }}
            .section-green {{ background: #d1fae5; border-left-color: #10b981; }}
            .section-blue {{ background: #dbeafe; border-left-color: #3b82f6; }}
            .role {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #e5e7eb; }}
            .role:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
            .role-header {{ font-weight: bold; font-size: 16px; margin-bottom: 8px; }}
            .pipeline {{ font-family: 'SF Mono', Monaco, monospace; color: #6b7280; margin: 8px 0; font-size: 13px; background: #f3f4f6; padding: 8px 12px; border-radius: 4px; }}
            .red {{ color: #dc2626; }}
            .yellow {{ color: #d97706; }}
            .green {{ color: #059669; }}
            .summary {{ background: #4F46E5; color: white; padding: 15px 20px; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
            .stuck {{ background: #fef3c7; padding: 12px 15px; border-radius: 6px; margin: 8px 0; border-left: 3px solid #f59e0b; }}
            .news-item {{ padding: 12px 0; border-bottom: 1px solid #e5e7eb; }}
            .news-item:last-child {{ border-bottom: none; }}
            .news-category {{ display: inline-block; background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 8px; }}
            .news-link {{ color: #4F46E5; text-decoration: none; }}
            .news-link:hover {{ text-decoration: underline; }}
            ul {{ padding-left: 0; list-style: none; }}
            li {{ margin: 10px 0; padding-left: 25px; position: relative; }}
            li:before {{ content: ""; position: absolute; left: 0; top: 8px; width: 8px; height: 8px; background: #4F46E5; border-radius: 50%; }}
            ol {{ padding-left: 25px; }}
            ol li {{ padding-left: 10px; }}
            ol li:before {{ display: none; }}
            .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Recruiting Daily Brief — {day_name}, {date_str}</h1>
            <p class="greeting">Good morning! Here's your recruiting dashboard for today.</p>

            <h2>🎯 Full Pipeline Report</h2>
            <div class="section">
    """

    # Pipeline health for each role
    for role in snapshot.roles:
        health_class = role.health_status
        health_emoji = {"red": "🔴", "yellow": "🟡", "green": "🟢"}.get(role.health_status, "⚪")

        stage_flow = " → ".join([f"{s.name}: {s.count}" for s in role.stages])

        html += f"""
                <div class="role">
                    <div class="role-header">{role.job_title} (P{role.priority}) <span class="{health_class}">{health_emoji}</span></div>
                    <div class="pipeline">{stage_flow}</div>
                    <div>Gap to Hire: ~{role.gap_to_hire} more screens needed</div>
        """
        if role.bottleneck:
            html += f'<div class="red">⚠️ Bottleneck: {role.bottleneck}</div>'
        html += "</div>"

    html += f"""
            </div>

            <div class="summary">
                📈 SUMMARY: {total_candidates} active candidates | ~{total_gap} total screens needed
            </div>

            <h2>👤 Drew's Priorities Today (Candidate Experience)</h2>
            <p style="color: #6b7280; margin-bottom: 10px;">Focus on these to keep candidates moving and happy:</p>
            <div class="section section-green">
                <ol>
    """

    if activities and activities.get("drew"):
        for item in activities["drew"][:5]:
            html += f"<li><strong>[{item['category']}]</strong> {item['action']}</li>"
    else:
        priorities = generate_priorities(snapshot)
        for priority in priorities[:5]:
            html += f"<li>{priority}</li>"

    html += """
                </ol>
            </div>

            <h2>🔍 5 Sourcing Actions for Today</h2>
            <p style="color: #6b7280; margin-bottom: 10px;">Build the pipeline with these daily actions:</p>
            <div class="section section-blue">
                <ol>
    """

    if sourcing_actions:
        for action in sourcing_actions:
            html += f"<li><strong>[{action['category']}]</strong> {action['action']}</li>"
    else:
        html += """
                    <li><strong>[OUTREACH]</strong> Send 20 personalized messages to priority role candidates</li>
                    <li><strong>[INBOUND]</strong> Review and respond to new applications</li>
                    <li><strong>[SOURCING]</strong> Refresh Boolean searches with new keywords</li>
                    <li><strong>[EMPLOYER BRAND]</strong> Post about Fonzi's engineering culture</li>
                    <li><strong>[RE-ENGAGE]</strong> Reach out to past silver-medalist candidates</li>
        """

    html += """
                </ol>
            </div>

            <h2>📋 Blessing's Priorities Today</h2>
            <div class="section">
                <ol>
    """

    if activities and activities.get("blessing"):
        for item in activities["blessing"][:5]:
            html += f"<li><strong>[{item['category']}]</strong> {item['action']}</li>"
    else:
        html += "<li><strong>[SOURCING]</strong> Focus outreach on priority roles</li>"

    html += """
                </ol>
            </div>

            <h2>🎯 Sourcing Allocation This Week</h2>
            <div class="section">
                <p><strong>Recommended outreach split (120 total):</strong></p>
                <ul>
    """

    for role in snapshot.roles:
        count = snapshot.sourcing_allocation.get(role.job_title, 0)
        pct = int((count / 120) * 100) if count else 0
        reason = get_sourcing_reason(role)
        html += f"<li><strong>{role.job_title}:</strong> {count} ({pct}%) — {reason}</li>"

    html += """
                </ul>
            </div>

            <h2>⚠️ Stuck Candidates (Action Needed)</h2>
            <div class="section section-alt">
    """

    stuck_count = 0
    for role in snapshot.roles:
        for candidate in role.stuck_candidates:
            html += f"""
                <div class="stuck">
                    <strong>{role.job_title}:</strong> {candidate.name} —
                    {candidate.current_stage} for {candidate.days_in_stage} days
                </div>
            """
            stuck_count += 1

    if stuck_count == 0:
        html += "<p>✅ No stuck candidates — pipeline is moving!</p>"

    html += """
            </div>

            <h2>📚 AI Recruiting Trends & Reading</h2>
            <p style="color: #6b7280; margin-bottom: 10px;">Stay sharp with today's curated resources:</p>
            <div class="section">
    """

    if news_items:
        for item in news_items:
            html += f"""
                <div class="news-item">
                    <span class="news-category">{item['category']}</span>
                    <a href="{item['url']}" class="news-link" target="_blank">{item['title']}</a>
                </div>
            """
    else:
        html += """
                <div class="news-item"><span class="news-category">🤖 AI Tools</span> <a href="#" class="news-link">Top AI Recruiting Tools for 2025</a></div>
                <div class="news-item"><span class="news-category">📈 Trends</span> <a href="#" class="news-link">Tech Hiring Market Analysis</a></div>
                <div class="news-item"><span class="news-category">🔍 Sourcing</span> <a href="#" class="news-link">Advanced LinkedIn Techniques</a></div>
                <div class="news-item"><span class="news-category">💡 Insights</span> <a href="#" class="news-link">What Engineers Look for in Jobs</a></div>
                <div class="news-item"><span class="news-category">🚀 Strategy</span> <a href="#" class="news-link">Startup Recruiting Playbook</a></div>
        """

    html += """
            </div>

            <div class="footer">
                <p>Have a great day! 🚀</p>
                <p>— Your Recruiting Co-Pilot</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


async def send_digest_email(snapshot: PipelineSnapshot) -> dict:
    """Send the daily digest email via Resend."""
    date_str = snapshot.generated_at.strftime("%B %d, %Y")
    day_name = snapshot.generated_at.strftime("%A")

    # Generate smart activity recommendations
    activities = get_daily_activities(snapshot)

    # Generate sourcing actions
    sourcing_actions = get_sourcing_actions(snapshot)

    # Fetch AI recruiting news/trends
    news_items = await fetch_ai_recruiting_news()

    # Format email content with all data
    text_content = format_digest_email(snapshot, activities, sourcing_actions, news_items)
    html_content = format_html_digest(snapshot, activities, sourcing_actions, news_items)

    # Send via Resend
    result = resend.Emails.send({
        "from": "Recruiting Co-Pilot <onboarding@resend.dev>",
        "to": [settings.email_to],
        "subject": f"📊 Recruiting Daily Brief — {day_name}, {date_str}",
        "text": text_content,
        "html": html_content,
    })

    return result
