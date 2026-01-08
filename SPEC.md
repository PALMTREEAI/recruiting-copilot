# Recruiting Co-Pilot: Full Build Spec for Claude Code

## What I Need You to Build

A **Recruiting Co-Pilot** with two interfaces:
1. **Daily email digest** — sent at 6am via Resend
2. **Web chat interface** — a simple web app where I can ask questions about my pipeline anytime

I am not an engineer. Walk me through every step. Ask me for credentials when you need them and tell me to store them as environment variables.

---

## Part 1: Who I Am (Context for the Assistant)

I'm Drew, an internal recruiter at an AI startup. I have ADHD and need help staying focused on high-leverage work.

**My roles:**
- **Internal Recruiter** — Own multiple open roles, run screens, manage pipelines, close candidates
- **Product SME** — Give feedback on our recruiting product from a user perspective

**My sourcer:** Blessing handles sourcing via LinkedIn + Gem. She does ~120 outreaches per week. I screen candidates and manage them after they respond.

**What I need from this system:**
- Tell me which roles need attention and why
- Calculate how many more candidates we need at top of funnel
- Tell Blessing where to focus her sourcing
- Flag stuck candidates
- Let me ask questions like "What's the status on GTM Engineer?" or "Who should I screen today?"

---

## Part 2: Current Recruiting Data

### Active Roles (Priority Order)

| Priority | Role | Status | Key Issue |
|----------|------|--------|-----------|
| 🥇 P1 | GTM Engineer | Critical | Funnel broken — 0% Testing→Onsite conversion |
| 🥇 P1 | Senior Full Stack Engineer | Critical | Low Testing→Onsite conversion (14%) |
| 🥈 P2 | Senior AI Engineer | Active | Healthier pipeline, 3 at Onsite, watch for decisions |

### Recently Closed
- ✅ **Head of Engineering** — Offer accepted (remove from active tracking)

### Conversion Rates (from Ashby, January 2025)

| Role | Screen→HM | HM→Testing | Testing→Onsite | Onsite→Offer |
|------|-----------|------------|----------------|--------------|
| GTM Engineer | 20% | 50% | 0% | — |
| Senior Full Stack | 42% | 50% | 14% | 0% |
| Senior AI Engineer | 50% | 42% | 60% | 0% |

### Pipeline Stages (in order)
1. Recruiter Screen
2. HM Screen
3. Testing
4. Onsite
5. Offer
6. Hired

### Stuck Candidate Thresholds
Flag a candidate as "stuck" if they've been in a stage longer than:
- Recruiter Screen: > 5 days
- HM Screen: > 7 days
- Testing: > 10 days
- Onsite: > 5 days
- Offer: > 3 days

---

## Part 3: What to Build

### Component 1: Ashby Data Layer

**Purpose:** Pull live data from Ashby API

**What to fetch:**
- All open jobs (filter to active roles: GTM Engineer, Senior Full Stack Engineer, Senior AI Engineer)
- All candidates for those jobs
- Current stage for each candidate
- Date entered current stage
- Activity/update timestamps

**Credentials:**
- I have an Ashby API key — ask me for it when you need it
- Store as environment variable: `ASHBY_API_KEY`

**Ashby API docs:** https://developers.ashbyhq.com/reference

### Component 2: Analysis Layer

**Purpose:** Turn raw data into actionable insights

**Calculate for each role:**
1. **Pipeline counts** — How many candidates at each stage
2. **Conversion rates** — What % move from each stage to the next
3. **Gap-to-hire** — Based on conversion rates, how many candidates do we need at top of funnel to make 1 hire
4. **Stuck candidates** — Anyone past the threshold for their current stage
5. **Sourcing allocation** — How should Blessing split her 120 weekly outreaches across roles

**Gap-to-hire formula:**
```
candidates_needed = 1 / (screen_to_hm × hm_to_testing × testing_to_onsite × onsite_to_offer × offer_to_hire)
```
Use historical conversion rates. If a stage has 0% conversion, flag it as "bottleneck" and estimate conservatively.

**Sourcing allocation logic:**
- Weight by: (1) priority level, (2) gap-to-hire size, (3) pipeline health
- P1 roles get more allocation than P2
- Roles with bigger gaps get more allocation
- Output a specific number for each role that sums to 120

### Component 3: Daily Email Digest

**Purpose:** Send me a morning brief at 6am

**Delivery:** Resend API
- I have a Resend API key — ask me for it when you need it
- Store as environment variable: `RESEND_API_KEY`
- Send to: dkoloski@fonzi.ai

**Email format:**

```
📊 RECRUITING DAILY BRIEF — [Date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 PIPELINE HEALTH

[Role Name] ([Priority]) [🔴/🟡/🟢]
  Pipeline: [count by stage, e.g., 10 → 2 → 1 → 0 → 0]
  Gap: Need ~[X] more screens to hire 1
  Bottleneck: [Stage] → [Stage] ([X]% conversion)
  
[Repeat for each active role]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 YOUR PRIORITIES TODAY

1. [ACTION TYPE] [Specific task]
2. [ACTION TYPE] [Specific task]
3. [ACTION TYPE] [Specific task]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 BLESSING'S SOURCING PRIORITIES THIS WEEK

Recommended outreach split (120 total):
  • [Role]: [X] ([Y]%) — [reason]
  • [Role]: [X] ([Y]%) — [reason]
  • [Role]: [X] ([Y]%) — [reason]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ STUCK CANDIDATES (action needed)

• [Role] [Name] — [Stage] for [X] days
• [Role] [Name] — [Stage] for [X] days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Health indicators:**
- 🔴 Red: Conversion bottleneck (0-15%), or critical gap
- 🟡 Yellow: Needs attention, moderate gap
- 🟢 Green: Healthy pipeline

### Component 4: Web Chat Interface

**Purpose:** Let me ask questions about my pipeline anytime

**Tech stack (keep it simple):**
- Frontend: Simple HTML/CSS/JS (or React if easier for you)
- Backend: Python (FastAPI or Flask)
- AI: Claude API for answering questions
- Host everything on Render.com

**How it works:**
1. I open the web app
2. I see a chat interface (text input + message history)
3. I type a question like "What's the status on GTM Engineer?"
4. Backend fetches current Ashby data (or uses cached data < 1 hour old)
5. Backend sends my question + pipeline data to Claude API
6. Claude responds with an answer
7. Answer appears in the chat

**Example questions I might ask:**
- "What's the status on GTM Engineer?"
- "Who should I screen today?"
- "Which candidates are stuck?"
- "Where should Blessing focus this week?"
- "What's our biggest bottleneck right now?"
- "How many candidates do we need for Full Stack?"

**UI requirements:**
- Simple, clean, works on desktop
- Shows conversation history for the session
- Has a "Refresh data" button to pull latest from Ashby

**Credentials:**
- Claude API key — I'll provide when you ask
- Store as environment variable: `ANTHROPIC_API_KEY`

---

## Part 4: Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     WEB CHAT INTERFACE                       │
│  • Chat input                                                │
│  • Message history                                           │
│  • "Refresh data" button                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (Python)                      │
│  • /chat endpoint — handles questions                        │
│  • /refresh endpoint — pulls fresh Ashby data                │
│  • /digest endpoint — generates daily brief                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   ASHBY API     │ │   CLAUDE API    │ │   RESEND API    │
│  (pipeline data)│ │  (chat answers) │ │  (send email)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Scheduled job:**
- Run daily at 6am: fetch Ashby data → generate digest → send via Resend

---

## Part 5: Deployment

**Platform:** Render.com (free tier)

**What to deploy:**
1. Web service (backend API + frontend)
2. Cron job (daily email at 6am)

**Environment variables to configure on Render:**
- `ASHBY_API_KEY`
- `RESEND_API_KEY`
- `ANTHROPIC_API_KEY`
- `EMAIL_TO=dkoloski@fonzi.ai`

---

## Part 6: Build Order

Please build in this order:

1. **Project setup** — Create folder structure, requirements.txt, basic files
2. **Ashby integration** — Connect to API, fetch jobs and candidates
3. **Analysis functions** — Pipeline counts, conversion rates, gap-to-hire, stuck candidates
4. **Email digest** — Format the daily brief, send via Resend
5. **Web backend** — FastAPI/Flask with /chat and /refresh endpoints
6. **Claude integration** — Connect to Claude API for answering questions
7. **Web frontend** — Simple chat interface
8. **Deployment** — Push to Render, configure env vars, set up cron

Test each component as we go. Show me the output at each step so I can verify it looks right.

---

## Part 7: Credentials I Have Ready

When you need them, I have:
- ✅ Ashby API key (new one, old one was revoked)
- ✅ Resend API key
- ⬜ Anthropic/Claude API key (I'll get this when we need it)

**DO NOT ask me to paste credentials in this chat. Tell me to store them as environment variables or paste them when Claude Code asks directly.**

---

## Start Now

Begin with Step 1: Project setup. Create the folder structure and tell me what you're creating. Walk me through every step — I'm not an engineer.
