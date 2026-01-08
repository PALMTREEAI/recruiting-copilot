import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict
from app.config import get_settings

settings = get_settings()


class GemClient:
    """Client for interacting with the Gem API."""

    def __init__(self):
        self.base_url = settings.gem_api_base_url
        self.api_key = settings.gem_api_key
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to the Gem API."""
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def _get_all_pages(self, endpoint: str, params: dict = None) -> list:
        """Fetch all pages from a paginated endpoint."""
        all_results = []
        params = params or {}

        while True:
            result = await self._get(endpoint, params)

            # Handle different response structures
            if isinstance(result, list):
                all_results.extend(result)
                break
            elif "data" in result:
                all_results.extend(result.get("data", []))
            elif "results" in result:
                all_results.extend(result.get("results", []))
            else:
                all_results.append(result)
                break

            # Check for pagination
            next_cursor = result.get("next_cursor") or result.get("nextCursor")
            if next_cursor:
                params["cursor"] = next_cursor
            else:
                break

        return all_results

    async def get_sequences(self) -> list[dict]:
        """Fetch all sequences."""
        return await self._get_all_pages("sequences")

    async def get_sequence_stats(self, sequence_id: str) -> dict:
        """Get stats for a specific sequence."""
        return await self._get(f"sequences/{sequence_id}/stats")

    async def get_candidate_events(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> list[dict]:
        """Fetch candidate events (outreach activities)."""
        params = {}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()

        return await self._get_all_pages("candidates/events", params)

    async def get_outreach_stats(self, days: int = 7) -> dict:
        """
        Get outreach statistics for the past N days.
        Aggregates data by sequence, role, and sender.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all sequences first
        sequences = await self.get_sequences()

        # Build stats structure
        stats = {
            "period_days": days,
            "since": since.isoformat(),
            "by_sequence": {},
            "by_role": defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}),
            "by_sender": defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}),
            "totals": {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}
        }

        # Process each sequence
        for seq in sequences:
            seq_name = seq.get("name", "Unknown")
            seq_id = seq.get("id")

            # Skip sequences not in our target list
            if seq_name not in settings.gem_sequence_roles:
                continue

            # Get role and sender for this sequence
            role = settings.gem_sequence_roles.get(seq_name, "Unknown")
            sender = settings.gem_sequence_senders.get(seq_name, "Unknown")

            # Try to get sequence-level stats
            try:
                seq_stats = await self.get_sequence_stats(seq_id)
                sent = seq_stats.get("sent", 0) or seq_stats.get("emails_sent", 0) or 0
                opened = seq_stats.get("opened", 0) or seq_stats.get("emails_opened", 0) or 0
                replied = seq_stats.get("replied", 0) or seq_stats.get("replies", 0) or 0
                bounced = seq_stats.get("bounced", 0) or seq_stats.get("bounces", 0) or 0
            except Exception:
                # If stats endpoint doesn't exist, use sequence metadata
                sent = seq.get("stats", {}).get("sent", 0)
                opened = seq.get("stats", {}).get("opened", 0)
                replied = seq.get("stats", {}).get("replied", 0)
                bounced = seq.get("stats", {}).get("bounced", 0)

            # Store sequence stats
            stats["by_sequence"][seq_name] = {
                "id": seq_id,
                "sent": sent,
                "opened": opened,
                "replied": replied,
                "bounced": bounced,
                "reply_rate": replied / sent if sent > 0 else 0,
                "role": role,
                "sender": sender
            }

            # Aggregate by role
            stats["by_role"][role]["sent"] += sent
            stats["by_role"][role]["opened"] += opened
            stats["by_role"][role]["replied"] += replied
            stats["by_role"][role]["bounced"] += bounced

            # Aggregate by sender
            stats["by_sender"][sender]["sent"] += sent
            stats["by_sender"][sender]["opened"] += opened
            stats["by_sender"][sender]["replied"] += replied
            stats["by_sender"][sender]["bounced"] += bounced

            # Totals
            stats["totals"]["sent"] += sent
            stats["totals"]["opened"] += opened
            stats["totals"]["replied"] += replied
            stats["totals"]["bounced"] += bounced

        # Calculate reply rates
        for role_stats in stats["by_role"].values():
            role_stats["reply_rate"] = (
                role_stats["replied"] / role_stats["sent"]
                if role_stats["sent"] > 0 else 0
            )

        for sender_stats in stats["by_sender"].values():
            sender_stats["reply_rate"] = (
                sender_stats["replied"] / sender_stats["sent"]
                if sender_stats["sent"] > 0 else 0
            )

        stats["totals"]["reply_rate"] = (
            stats["totals"]["replied"] / stats["totals"]["sent"]
            if stats["totals"]["sent"] > 0 else 0
        )

        # Convert defaultdicts to regular dicts
        stats["by_role"] = dict(stats["by_role"])
        stats["by_sender"] = dict(stats["by_sender"])

        return stats


# Singleton instance
_client: Optional[GemClient] = None


def get_gem_client() -> GemClient:
    """Get or create the Gem client singleton."""
    global _client
    if _client is None:
        _client = GemClient()
    return _client
