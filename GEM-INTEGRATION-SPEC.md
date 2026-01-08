# Gem API Integration — Recruiting Co-Pilot

## Overview

Add Gem sourcing data to the recruiting co-pilot with **historical tracking** and **intelligent recommendations**. This isn't just a report — it's a daily coach that tells you what's working, what's stalling, and exactly what to do next.

---

## Core Philosophy

The daily digest should answer:
1. **What happened?** — Activity and results from sourcing
2. **Is it working?** — Trends compared to last week, reply rates, momentum
3. **What do I do now?** — Specific actions for Drew and Blessing based on the data

Every insight should connect to an action. No data without direction.

---

## Target Sequences

**Full Stack Engineer:**
- Fonzi - Sr. Full Stack Engineer - Drew
- Fonzi - Fullstack Engineer - Blessing
- Fonzi - Fullstack Engineer - V3
- Fonzi - Sr. Full Stack Engineer - Blessing (as Drew)
- Fonzi - Sr. Full Stack Engineer - Drew (via Cait)
- Fonzi - Sr. Full Stack Engineer - Drew (via Rachel)
- Fonzi - Sr. Full Stack Engineer - Drew/Yang (via Cait)
- Fonzi - Fullstack Engineer - V4 short (as Drew)
- A/B - Fonzi - Fullstack Engineer - Blessing

**AI Engineer:**
- Fonzi - Sr. AI Engineer - Drew
- Fonzi - Sr. AI Engineer - Blessing (as Drew)
- Fonzi - Sr. AI Engineer - Drew (SOBO via Rachel)
- Fonzi - Sr. AI Engineer V2 w/Yang - Drew (SOBO via Rachel)

---

## Historical Tracking

### What to Store (Daily Snapshot)

Every day at 6am, before sending the digest, store:

```python
{
    "date": "2025-01-06",
    "by_sequence": {
        "Fonzi - Sr. Full Stack Engineer - Drew": {
            "sent": 12,
            "opened": 9,
            "replied": 2,
            "bounced": 1
        },
        # ... all sequences
    },
    "by_role": {
        "Full Stack": {"sent": 78, "replied": 9},
        "AI Engineer": {"sent": 49, "replied": 5}
    },
    "by_sender": {
        "Blessing": {"sent": 95, "replied": 11},
        "Drew": {"sent": 32, "replied": 3}
    },
    "totals": {
        "sent": 127,
        "opened": 89,
        "replied": 14,
        "bounced": 3
    }
}
```

### Database

Use SQLite (simple, no setup) or Render's PostgreSQL.

Tables:
- `daily_snapshots` — One row per day with JSON blob of all metrics
- `sequence_daily` — One row per sequence per day (for granular queries)

This lets you query:
- "What was our reply rate 2 weeks ago?"
- "Which sequence improved most over time?"
- "Is Blessing's volume trending up or down?"

---

## Intelligent Daily Digest

### New Email Format

```
📊 RECRUITING CO-PILOT — Monday, Jan 6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 PIPELINE HEALTH

[Existing Ashby section — pipeline counts, gaps, stuck candidates]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 SOURCING MOMENTUM

This week vs last week:

             This Week    Last Week    Trend
Sent         127          98           ↑ 30% 🟢
Replies      14           9            ↑ 56% 🟢
Reply Rate   11%          9%           ↑ 2pts 🟢

BLESSING: 95 sent (↑ from 72) • 12% reply rate (steady)
DREW: 32 sent (↑ from 26) • 9% reply rate (↓ from 12%)

BY ROLE:
• Full Stack: 78 sent, 9 replies (12%) — ↑ volume, steady conversion
• AI Engineer: 49 sent, 5 replies (10%) — needs more volume

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 WHAT'S WORKING

✓ "Fonzi - Sr. Full Stack Engineer - Drew (via Rachel)"
  → 18% reply rate (best performer)
  → ACTION: Have Blessing clone this messaging for her sequences

✓ Full Stack volume is up 30%
  → Keep this momentum going

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ WHAT NEEDS ATTENTION

✗ AI Engineer sourcing volume too low
  → At current pace: 49/week × 10% reply = ~5 replies/week
  → You need ~25 screens to fill top of funnel. That's 5 weeks just to fill top of funnel.
  → ACTION: Blessing should shift 20 outreaches/week from Full Stack to AI Engineer

✗ Drew's reply rate dropped (12% → 9%)
  → Possible causes: messaging fatigue, wrong audience, timing
  → ACTION: Review last 10 non-replies. Are they the right profiles?

✗ "Fonzi - Fullstack Engineer - V3" underperforming
  → 3% reply rate (vs 12% average)
  → ACTION: Pause this sequence or rewrite messaging

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 TODAY'S ACTIONS

DREW:
1. [SCREEN] 3 Full Stack candidates responded — schedule screens today
2. [REVIEW] Check Drew's last 10 AI Engineer outreaches — why no replies?
3. [SYNC] Share "via Rachel" messaging with Blessing

BLESSING:
1. [SHIFT] Move 20 outreaches this week from Full Stack → AI Engineer
2. [PAUSE] Stop using "Fullstack Engineer - V3" sequence
3. [COPY] Adapt "via Rachel" subject lines to her sequences

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 THIS WEEK'S GOAL

Get 8+ replies for AI Engineer (currently trending toward 5)
→ Requires: More volume + better targeting
→ If you hit this, you'll have enough pipeline to stay on track for March hire

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Recommendation Logic

### Momentum Indicators

Calculate for each metric:
```python
def get_trend(this_week, last_week):
    if last_week == 0:
        return "new"

    change = (this_week - last_week) / last_week

    if change >= 0.15:
        return "↑ strong"   # 🟢
    elif change >= 0.05:
        return "↑ growing"  # 🟢
    elif change >= -0.05:
        return "→ steady"   # 🟡
    elif change >= -0.15:
        return "↓ slipping" # 🟠
    else:
        return "↓ falling"  # 🔴
```

### Automatic Recommendations

Build a rules engine that generates actions based on data:

```python
RECOMMENDATION_RULES = [
    {
        "condition": lambda data: data["by_role"]["AI Engineer"]["sent"] < 60,
        "insight": "AI Engineer sourcing volume too low",
        "action_drew": "Review AI Engineer candidate pool — are we targeting right profiles?",
        "action_blessing": "Shift 20 outreaches/week to AI Engineer",
        "priority": "high"
    },
    {
        "condition": lambda data: get_best_sequence(data)["reply_rate"] > 0.15,
        "insight": f"'{get_best_sequence(data)['name']}' is outperforming",
        "action_drew": "Share this messaging approach with Blessing",
        "action_blessing": "Clone the subject line and opening from top sequence",
        "priority": "medium"
    },
    {
        "condition": lambda data: any(s["reply_rate"] < 0.05 and s["sent"] > 20 for s in data["sequences"]),
        "insight": "Underperforming sequence detected",
        "action_blessing": "Pause or rewrite the underperforming sequence",
        "priority": "high"
    },
    {
        "condition": lambda data: data["trend"]["reply_rate"] == "down",
        "insight": "Overall reply rate is declining",
        "action_drew": "Review recent non-replies — are we hitting the right people?",
        "action_blessing": "Test new subject lines this week",
        "priority": "high"
    },
    {
        "condition": lambda data: data["by_sender"]["Blessing"]["sent"] < 100,
        "insight": "Blessing's volume below target (120/week)",
        "action_blessing": "Increase daily outreach to hit 120/week target",
        "priority": "medium"
    },
    # Connect to Ashby data
    {
        "condition": lambda data: data["ashby"]["gap_to_hire"]["Full Stack"] > 50,
        "insight": "Full Stack pipeline gap is critical",
        "action_blessing": "Prioritize Full Stack sourcing this week",
        "priority": "high"
    },
]
```

### Weekly Goal Generation

Each Monday, set a specific goal based on:
- Current pipeline gaps (from Ashby)
- Current reply rates (from Gem)
- Historical trends

Example logic:
```python
def generate_weekly_goal(ashby_data, gem_data):
    # Find the role with biggest gap
    biggest_gap_role = max(ashby_data["gaps"], key=lambda r: r["candidates_needed"])

    # Calculate realistic target based on current reply rate
    current_reply_rate = gem_data["by_role"][biggest_gap_role]["reply_rate"]
    replies_needed = ashby_data["gaps"][biggest_gap_role]["screens_needed"]

    # What's achievable with 20% improvement?
    projected_replies = gem_data["by_role"][biggest_gap_role]["sent"] * 1.2 * current_reply_rate

    return {
        "role": biggest_gap_role,
        "metric": "replies",
        "target": min(replies_needed, int(projected_replies * 1.3)),  # Stretch but achievable
        "current_trajectory": int(projected_replies),
        "why": f"You need {replies_needed} screens to hit your {biggest_gap_role} hire target"
    }
```

---

## Chat Interface Capabilities

Enable these conversations:

**Status questions:**
- "How's sourcing going?" → Summary with trends
- "What's Blessing's reply rate?" → Current + trend
- "Which sequence is working best?" → Top performer + why

**Diagnostic questions:**
- "Why is AI Engineer sourcing slow?" → Volume analysis + recommendations
- "What's wrong with the V3 sequence?" → Performance breakdown
- "Are we on track for our Full Stack hire?" → Pipeline math + sourcing projection

**Action questions:**
- "What should Blessing focus on today?" → Top 3 priorities from recommendations
- "What can I do to improve reply rates?" → Specific tactics based on data
- "Should we pause any sequences?" → Underperformers flagged

**Trend questions:**
- "How did we do compared to last week?" → Week-over-week comparison
- "Is our reply rate getting better?" → Trend analysis
- "What's changed in the last month?" → Longer-term view

---

## Database Schema

```sql
-- Daily snapshots for trend analysis
CREATE TABLE sourcing_snapshots (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    data JSON NOT NULL,  -- Full snapshot blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Granular sequence data for detailed queries
CREATE TABLE sequence_daily (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    sequence_name TEXT NOT NULL,
    role TEXT NOT NULL,
    sender TEXT NOT NULL,
    sent INTEGER DEFAULT 0,
    opened INTEGER DEFAULT 0,
    clicked INTEGER DEFAULT 0,
    replied INTEGER DEFAULT 0,
    bounced INTEGER DEFAULT 0,
    UNIQUE(date, sequence_name)
);

-- Generated recommendations (for tracking what was suggested)
CREATE TABLE daily_recommendations (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    for_whom TEXT NOT NULL,  -- 'drew' or 'blessing'
    priority TEXT NOT NULL,
    insight TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weekly goals
CREATE TABLE weekly_goals (
    id INTEGER PRIMARY KEY,
    week_start DATE NOT NULL,
    role TEXT NOT NULL,
    metric TEXT NOT NULL,
    target INTEGER NOT NULL,
    actual INTEGER,  -- Filled in at end of week
    hit BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Order

1. **Basic Gem pull** — Connect to API, fetch sequence data
2. **Daily snapshot storage** — Save data to SQLite each morning
3. **Week-over-week comparison** — Calculate trends
4. **Recommendation engine** — Generate actions from rules
5. **Updated digest format** — New email template with coaching
6. **Chat integration** — Add Gem context to Claude queries
7. **Weekly goals** — Auto-generate Monday goals

---

## Credentials Needed

- **Gem API Key:** Get from Gem Team Settings → API Keys
- Add to `.env` as `GEM_API_KEY`
