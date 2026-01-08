"""Test script to send a test digest email."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.analysis import analyze_pipeline
from app.services.email import send_digest_email, format_digest_email, generate_ai_insights
from app.services.recommendations import get_daily_activities


async def test_email():
    print("Generating pipeline analysis...")
    snapshot = await analyze_pipeline()

    print("Generating AI insights (Opus 4.5)...")
    ai_insights = await generate_ai_insights(snapshot)
    activities = get_daily_activities(snapshot)

    print("\n--- AI STRATEGIC INSIGHT ---\n")
    print(ai_insights if ai_insights else "(No AI insights - check API key)")

    print("\n--- TEXT EMAIL PREVIEW ---\n")
    print(format_digest_email(snapshot, activities, ai_insights=ai_insights))

    print("\n--- SENDING EMAIL ---\n")
    try:
        result = await send_digest_email(snapshot)
        print(f"✅ Email sent successfully!")
        print(f"   ID: {result.get('id', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


if __name__ == "__main__":
    asyncio.run(test_email())
