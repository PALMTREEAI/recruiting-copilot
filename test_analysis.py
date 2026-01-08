"""Test script to verify pipeline analysis."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.analysis import analyze_pipeline


async def test_analysis():
    print("Running pipeline analysis...\n")

    snapshot = await analyze_pipeline()

    print(f"Generated at: {snapshot.generated_at}\n")

    for role in snapshot.roles:
        health_emoji = {"red": "🔴", "yellow": "🟡", "green": "🟢"}
        emoji = health_emoji.get(role.health_status, "⚪")

        print(f"{'='*50}")
        print(f"{role.job_title} (P{role.priority}) {emoji}")
        print(f"{'='*50}")

        # Pipeline counts
        print("\nPipeline:")
        stage_counts = " → ".join([f"{s.count}" for s in role.stages])
        stage_names = " → ".join([s.name[:6] for s in role.stages])
        print(f"  {stage_names}")
        print(f"  {stage_counts}")
        print(f"  Total active: {role.total_candidates}")

        # Gap to hire
        print(f"\nGap to hire: ~{role.gap_to_hire} candidates needed at top of funnel")

        # Bottleneck
        if role.bottleneck:
            print(f"Bottleneck: {role.bottleneck}")

        # Conversion rates
        print("\nConversion rates:")
        for transition, rate in role.conversion_rates.items():
            print(f"  {transition}: {int(rate * 100)}%")

        # Stuck candidates
        if role.stuck_candidates:
            print(f"\n⚠️ Stuck candidates ({len(role.stuck_candidates)}):")
            for c in role.stuck_candidates[:5]:
                print(f"  - {c.name}: {c.current_stage} for {c.days_in_stage} days")
        else:
            print("\n✅ No stuck candidates")

        print()

    # Sourcing allocation
    print("="*50)
    print("SOURCING ALLOCATION (120 total)")
    print("="*50)
    for title, count in snapshot.sourcing_allocation.items():
        pct = int((count / 120) * 100)
        print(f"  • {title}: {count} ({pct}%)")


if __name__ == "__main__":
    asyncio.run(test_analysis())
