from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Job(BaseModel):
    """Represents an open job/role."""
    id: str
    title: str
    status: str
    department: Optional[str] = None
    location: Optional[str] = None


class Candidate(BaseModel):
    """Represents a candidate in the pipeline."""
    id: str
    name: str
    email: Optional[str] = None
    job_id: str
    job_title: str
    current_stage: str
    stage_entered_at: Optional[datetime] = None
    days_in_stage: int = 0
    is_stuck: bool = False


class PipelineStage(BaseModel):
    """Counts for a single pipeline stage."""
    name: str
    count: int


class RolePipeline(BaseModel):
    """Pipeline summary for a single role."""
    job_id: str
    job_title: str
    priority: int
    stages: list[PipelineStage]
    total_candidates: int
    stuck_candidates: list[Candidate]
    conversion_rates: dict[str, float]  # e.g., "Screen→HM": 0.42
    gap_to_hire: int
    health_status: str  # "red", "yellow", "green"
    bottleneck: Optional[str] = None  # e.g., "Testing→Onsite (0%)"


class PipelineSnapshot(BaseModel):
    """Complete snapshot of all pipelines."""
    generated_at: datetime
    roles: list[RolePipeline]
    sourcing_allocation: dict[str, int]  # role -> number of outreaches
