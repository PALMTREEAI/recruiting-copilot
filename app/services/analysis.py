from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional
from app.config import get_settings
from app.models.recruiting import (
    Candidate, Job, PipelineStage, RolePipeline, PipelineSnapshot
)
from app.services.ashby import get_ashby_client

settings = get_settings()

# Map Ashby stage names to our pipeline stages
STAGE_MAPPING = {
    # Lead stages -> Recruiter Screen (top of funnel)
    "New Lead": "Recruiter Screen",
    "Reached Out": "Recruiter Screen",
    "Replied": "Recruiter Screen",
    "Application Review": "Recruiter Screen",
    "Recruiter Screen": "Recruiter Screen",

    # HM Screen
    "Hiring Manager Screen": "HM Screen",
    "HM Screen": "HM Screen",

    # Testing
    "Testing": "Testing",
    "Technical Assessment": "Testing",
    "Take Home": "Testing",

    # Onsite
    "Onsite": "Onsite",
    "Onsite Loop": "Onsite",
    "Final Interview": "Onsite",

    # Offer
    "Offer": "Offer",
    "Offer Extended": "Offer",

    # Hired
    "Hired": "Hired",
    "Accepted": "Hired",
}


def normalize_stage(ashby_stage: str) -> str:
    """Convert Ashby stage name to our normalized pipeline stage."""
    return STAGE_MAPPING.get(ashby_stage, ashby_stage)


def count_by_stage(candidates: list[Candidate]) -> dict[str, int]:
    """Count candidates at each normalized pipeline stage."""
    counts = defaultdict(int)
    for candidate in candidates:
        normalized = normalize_stage(candidate.current_stage)
        counts[normalized] += 1
    return dict(counts)


def get_stuck_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Find candidates who have been in their stage too long."""
    stuck = []
    for candidate in candidates:
        normalized_stage = normalize_stage(candidate.current_stage)
        threshold = settings.stuck_thresholds.get(normalized_stage)
        if threshold and candidate.days_in_stage > threshold:
            # Update the is_stuck flag
            candidate.is_stuck = True
            stuck.append(candidate)
    return stuck


def calculate_conversion_rates(
    stage_counts: dict[str, int],
    historical_rates: dict[str, float] = None
) -> dict[str, float]:
    """
    Calculate conversion rates between stages.
    Uses historical rates from the spec if available.
    """
    # Historical conversion rates from the spec (January 2025)
    historical = historical_rates or {}

    stages = settings.pipeline_stages
    rates = {}

    for i in range(len(stages) - 1):
        from_stage = stages[i]
        to_stage = stages[i + 1]
        key = f"{from_stage}→{to_stage}"

        # Use historical rate if available
        if key in historical:
            rates[key] = historical[key]
        else:
            # Calculate from current counts if possible
            from_count = stage_counts.get(from_stage, 0)
            to_count = stage_counts.get(to_stage, 0)
            if from_count > 0:
                rates[key] = to_count / from_count
            else:
                rates[key] = 0.0

    return rates


def calculate_gap_to_hire(conversion_rates: dict[str, float]) -> int:
    """
    Calculate how many candidates needed at top of funnel to make 1 hire.
    Formula: 1 / (rate1 × rate2 × rate3 × ...)
    """
    if not conversion_rates:
        return 999  # Flag as unknown

    # Multiply all conversion rates
    total_rate = 1.0
    for rate in conversion_rates.values():
        if rate <= 0:
            # If any stage has 0% conversion, use a conservative estimate
            rate = 0.05  # Assume 5% as minimum
        total_rate *= rate

    if total_rate <= 0:
        return 999

    return max(1, int(1 / total_rate))


def find_bottleneck(conversion_rates: dict[str, float]) -> Optional[str]:
    """Find the stage transition with the worst conversion rate."""
    if not conversion_rates:
        return None

    worst_key = min(conversion_rates, key=conversion_rates.get)
    worst_rate = conversion_rates[worst_key]

    # Only flag as bottleneck if significantly below expected (< 25%)
    if worst_rate < 0.25:
        return f"{worst_key} ({int(worst_rate * 100)}%)"
    return None


def determine_health_status(
    conversion_rates: dict[str, float],
    gap_to_hire: int,
    stage_counts: dict[str, int]
) -> str:
    """
    Determine pipeline health: red, yellow, or green.
    - Red: Severe bottleneck or very high gap
    - Yellow: Needs attention, moderate gap or low pipeline
    - Green: Healthy pipeline
    """
    # Check for severe bottleneck (< 20%)
    min_rate = min(conversion_rates.values()) if conversion_rates else 0
    if min_rate < 0.20:
        return "red"

    # Check gap-to-hire (target is ~30, so 50+ is concerning)
    if gap_to_hire > 50:
        return "red"
    if gap_to_hire > 35:
        return "yellow"

    # Check if pipeline has enough candidates
    total = sum(stage_counts.values())
    if total < 5:
        return "yellow"

    return "green"


def calculate_sourcing_allocation(
    role_pipelines: list[RolePipeline]
) -> dict[str, int]:
    """
    Calculate how Blessing should split her 120 weekly outreaches.
    Weights by: priority level, gap-to-hire size, pipeline health.
    """
    total_capacity = settings.weekly_outreach_capacity
    allocations = {}

    if not role_pipelines:
        return allocations

    # Calculate a score for each role
    scores = {}
    for pipeline in role_pipelines:
        # Priority weight (P1 = 3, P2 = 2, P3 = 1)
        priority_weight = 4 - pipeline.priority

        # Gap weight (higher gap = more need)
        gap_weight = min(pipeline.gap_to_hire / 20, 5)  # Cap at 5x

        # Health weight (red = 3, yellow = 2, green = 1)
        health_weights = {"red": 3, "yellow": 2, "green": 1}
        health_weight = health_weights.get(pipeline.health_status, 1)

        scores[pipeline.job_title] = priority_weight * gap_weight * health_weight

    # Convert scores to allocations
    total_score = sum(scores.values())
    if total_score > 0:
        for title, score in scores.items():
            allocations[title] = int((score / total_score) * total_capacity)

    # Adjust to ensure we use exactly 120
    allocated = sum(allocations.values())
    if allocated < total_capacity and allocations:
        # Add remainder to highest priority role
        highest_priority = min(role_pipelines, key=lambda r: r.priority)
        allocations[highest_priority.job_title] += (total_capacity - allocated)

    return allocations


async def analyze_pipeline() -> PipelineSnapshot:
    """
    Main analysis function: fetch data and generate complete pipeline analysis.
    """
    client = get_ashby_client()

    # Target conversion rates for realistic gap-to-hire calculations
    # Full Stack & AI Engineer: ~30 screens per hire
    # GTM Engineer: ~20 screens per hire
    historical_rates = {
        "Senior Full Stack Engineer": {
            "Recruiter Screen→HM Screen": 0.33,
            "HM Screen→Testing": 0.65,
            "Testing→Onsite": 0.65,
            "Onsite→Offer": 0.30,
            "Offer→Hired": 0.80,
        },
        "Senior AI Engineer": {
            "Recruiter Screen→HM Screen": 0.33,
            "HM Screen→Testing": 0.65,
            "Testing→Onsite": 0.65,
            "Onsite→Offer": 0.30,
            "Offer→Hired": 0.80,
        },
        "GTM Engineer": {
            "Recruiter Screen→HM Screen": 0.40,
            "HM Screen→Testing": 0.65,
            "Testing→Onsite": 0.65,
            "Onsite→Offer": 0.37,
            "Offer→Hired": 0.80,
        },
    }

    # Fetch active jobs
    active_jobs = await client.get_active_jobs()
    role_pipelines = []

    for job in active_jobs:
        # Get candidates
        candidates = await client.get_candidates_for_job(job)

        # Count by stage
        stage_counts = count_by_stage(candidates)

        # Build stage list
        stages = []
        for stage_name in settings.pipeline_stages:
            stages.append(PipelineStage(
                name=stage_name,
                count=stage_counts.get(stage_name, 0)
            ))

        # Get historical rates for this role
        role_historical = historical_rates.get(job.title, {})

        # Calculate conversion rates
        conversion_rates = calculate_conversion_rates(stage_counts, role_historical)

        # Calculate gap-to-hire
        gap = calculate_gap_to_hire(conversion_rates)

        # Find bottleneck
        bottleneck = find_bottleneck(conversion_rates)

        # Determine health
        health = determine_health_status(conversion_rates, gap, stage_counts)

        # Get stuck candidates
        stuck = get_stuck_candidates(candidates)

        # Get priority
        priority = settings.role_priorities.get(job.title, 3)

        role_pipelines.append(RolePipeline(
            job_id=job.id,
            job_title=job.title,
            priority=priority,
            stages=stages,
            total_candidates=len(candidates),
            stuck_candidates=stuck,
            conversion_rates=conversion_rates,
            gap_to_hire=gap,
            health_status=health,
            bottleneck=bottleneck
        ))

    # Sort by priority
    role_pipelines.sort(key=lambda r: r.priority)

    # Calculate sourcing allocation
    sourcing = calculate_sourcing_allocation(role_pipelines)

    return PipelineSnapshot(
        generated_at=datetime.now(timezone.utc),
        roles=role_pipelines,
        sourcing_allocation=sourcing
    )
