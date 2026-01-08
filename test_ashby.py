"""Test script to verify Ashby API connection."""
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.ashby import get_ashby_client


async def test_connection():
    print("Testing Ashby API connection...\n")

    client = get_ashby_client()

    # Test 1: Fetch all jobs
    print("1. Fetching all open jobs...")
    try:
        jobs = await client.get_jobs()
        print(f"   Found {len(jobs)} open jobs:")
        for job in jobs:
            print(f"   - {job.title} ({job.status})")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Test 2: Fetch active jobs (filtered)
    print("\n2. Filtering to active roles...")
    try:
        active_jobs = await client.get_active_jobs()
        print(f"   Found {len(active_jobs)} active roles:")
        for job in active_jobs:
            print(f"   - {job.title}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Test 3: Fetch candidates for first active job
    if active_jobs:
        print(f"\n3. Fetching candidates for '{active_jobs[0].title}'...")
        try:
            candidates = await client.get_candidates_for_job(active_jobs[0])
            print(f"   Found {len(candidates)} candidates:")
            for c in candidates[:5]:  # Show first 5
                stuck_flag = " [STUCK]" if c.is_stuck else ""
                print(f"   - {c.name}: {c.current_stage} ({c.days_in_stage} days){stuck_flag}")
            if len(candidates) > 5:
                print(f"   ... and {len(candidates) - 5} more")
        except Exception as e:
            print(f"   ERROR: {e}")
            return

    print("\n✅ Ashby API connection successful!")


if __name__ == "__main__":
    asyncio.run(test_connection())
