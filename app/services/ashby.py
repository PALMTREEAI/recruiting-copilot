import httpx
import base64
from datetime import datetime, timezone
from typing import Optional
from app.config import get_settings
from app.models.recruiting import Job, Candidate

settings = get_settings()


class AshbyClient:
    """Client for interacting with the Ashby API."""

    def __init__(self):
        self.base_url = settings.ashby_api_base_url
        self.api_key = settings.ashby_api_key
        # Ashby uses basic auth with API key as username, empty password
        credentials = base64.b64encode(f"{self.api_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }

    async def _post(self, endpoint: str, data: dict = None) -> dict:
        """Make a POST request to the Ashby API."""
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=data or {},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_jobs(self) -> list[Job]:
        """Fetch all open jobs from Ashby, handling pagination."""
        jobs = []
        cursor = None

        while True:
            data = {}
            if cursor:
                data["cursor"] = cursor

            result = await self._post("job.list", data)

            for job_data in result.get("results", []):
                # Only include open jobs
                if job_data.get("status") == "Open":
                    jobs.append(Job(
                        id=job_data.get("id"),
                        title=job_data.get("title", "Unknown"),
                        status=job_data.get("status", "Unknown"),
                        department=job_data.get("departmentName"),
                        location=job_data.get("locationName")
                    ))

            # Check for more pages
            if result.get("moreDataAvailable") and result.get("nextCursor"):
                cursor = result["nextCursor"]
            else:
                break

        return jobs

    async def get_active_jobs(self) -> list[Job]:
        """Get only the jobs we're actively tracking."""
        all_jobs = await self.get_jobs()
        active_titles = settings.active_roles

        # Match jobs by title (case-insensitive partial match)
        active_jobs = []
        for job in all_jobs:
            for active_title in active_titles:
                if active_title.lower() in job.title.lower():
                    active_jobs.append(job)
                    break

        return active_jobs

    async def get_applications(self, job_id: Optional[str] = None) -> list[dict]:
        """Fetch all applications, handling pagination."""
        all_results = []
        cursor = None

        while True:
            data = {}
            if job_id:
                data["jobId"] = job_id
            if cursor:
                data["cursor"] = cursor

            result = await self._post("application.list", data)
            all_results.extend(result.get("results", []))

            # Check for more pages
            if result.get("moreDataAvailable") and result.get("nextCursor"):
                cursor = result["nextCursor"]
            else:
                break

        return all_results

    async def get_candidates_for_job(self, job: Job, include_archived: bool = False) -> list[Candidate]:
        """Get all candidates for a specific job with their current stage."""
        applications = await self.get_applications(job.id)
        candidates = []

        for app in applications:
            # Skip archived candidates unless explicitly requested
            app_status = app.get("status", "")
            stage_type = app.get("currentInterviewStage", {}).get("type", "")
            if not include_archived and app_status == "Archived":
                continue
            # Extract candidate info
            candidate_data = app.get("candidate", {})
            current_stage = app.get("currentInterviewStage", {})
            stage_name = current_stage.get("title", "Unknown")

            # Calculate days in stage
            # Try multiple possible field names for stage start date
            stage_entered_str = (
                app.get("currentInterviewStageStartedAt") or
                app.get("statusChangedAt") or
                app.get("updatedAt")
            )
            stage_entered_at = None
            days_in_stage = 0

            if stage_entered_str:
                try:
                    stage_entered_at = datetime.fromisoformat(
                        stage_entered_str.replace("Z", "+00:00")
                    )
                    now = datetime.now(timezone.utc)
                    days_in_stage = (now - stage_entered_at).days
                except (ValueError, TypeError):
                    pass

            # Check if stuck based on thresholds
            is_stuck = False
            threshold = settings.stuck_thresholds.get(stage_name)
            if threshold and days_in_stage > threshold:
                is_stuck = True

            # Get candidate name
            name = candidate_data.get("name", "Unknown")
            if not name or name == "Unknown":
                # Try to build name from first/last
                first = candidate_data.get("firstName", "")
                last = candidate_data.get("lastName", "")
                name = f"{first} {last}".strip() or "Unknown"

            candidates.append(Candidate(
                id=candidate_data.get("id", app.get("id", "")),
                name=name,
                email=candidate_data.get("primaryEmailAddress", {}).get("value"),
                job_id=job.id,
                job_title=job.title,
                current_stage=stage_name,
                stage_entered_at=stage_entered_at,
                days_in_stage=days_in_stage,
                is_stuck=is_stuck
            ))

        return candidates

    async def get_all_pipeline_data(self) -> dict[str, list[Candidate]]:
        """
        Get all candidates for all active jobs.
        Returns a dict mapping job title -> list of candidates.
        """
        active_jobs = await self.get_active_jobs()
        pipeline_data = {}

        for job in active_jobs:
            candidates = await self.get_candidates_for_job(job)
            pipeline_data[job.title] = candidates

        return pipeline_data


# Singleton instance
_client: Optional[AshbyClient] = None


def get_ashby_client() -> AshbyClient:
    """Get or create the Ashby client singleton."""
    global _client
    if _client is None:
        _client = AshbyClient()
    return _client
