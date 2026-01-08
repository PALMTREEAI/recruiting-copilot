from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    ashby_api_key: str = ""
    resend_api_key: str = ""
    anthropic_api_key: str = ""
    gem_api_key: str = ""

    # Email configuration
    email_to: str = "dkoloski@fonzi.ai"

    # Ashby API base URL
    ashby_api_base_url: str = "https://api.ashbyhq.com"

    # Cache settings (in seconds)
    data_cache_ttl: int = 3600  # 1 hour

    # Active roles to track
    active_roles: list[str] = [
        "Senior Full Stack Engineer",
        "Senior AI Engineer",
        "GTM Engineer"
    ]

    # Role priorities (1 = highest priority)
    role_priorities: dict[str, int] = {
        "Senior Full Stack Engineer": 1,
        "Senior AI Engineer": 2,
        "GTM Engineer": 3
    }

    # Stuck candidate thresholds (in days)
    stuck_thresholds: dict[str, int] = {
        "Recruiter Screen": 5,
        "HM Screen": 7,
        "Testing": 10,
        "Onsite": 5,
        "Offer": 3
    }

    # Pipeline stages in order
    pipeline_stages: list[str] = [
        "Recruiter Screen",
        "HM Screen",
        "Testing",
        "Onsite",
        "Offer",
        "Hired"
    ]

    # Blessing's weekly outreach capacity
    weekly_outreach_capacity: int = 120

    # Gem API base URL
    gem_api_base_url: str = "https://api.gem.com/v0"

    # Gem sequence to role mapping
    gem_sequence_roles: dict[str, str] = {
        # Full Stack sequences
        "Fonzi - Sr. Full Stack Engineer - Drew": "Full Stack",
        "Fonzi - Fullstack Engineer - Blessing": "Full Stack",
        "Fonzi - Fullstack Engineer - V3": "Full Stack",
        "Fonzi - Sr. Full Stack Engineer - Blessing (as Drew)": "Full Stack",
        "Fonzi - Sr. Full Stack Engineer - Drew (via Cait)": "Full Stack",
        "Fonzi - Sr. Full Stack Engineer - Drew (via Rachel)": "Full Stack",
        "Fonzi - Sr. Full Stack Engineer - Drew/Yang (via Cait)": "Full Stack",
        "Fonzi - Fullstack Engineer - V4 short (as Drew)": "Full Stack",
        "A/B - Fonzi - Fullstack Engineer - Blessing": "Full Stack",
        # AI Engineer sequences
        "Fonzi - Sr. AI Engineer - Drew": "AI Engineer",
        "Fonzi - Sr. AI Engineer - Blessing (as Drew)": "AI Engineer",
        "Fonzi - Sr. AI Engineer - Drew (SOBO via Rachel)": "AI Engineer",
        "Fonzi - Sr. AI Engineer V2 w/Yang - Drew (SOBO via Rachel)": "AI Engineer",
    }

    # Gem sequence to sender mapping (inferred from sequence name)
    gem_sequence_senders: dict[str, str] = {
        "Fonzi - Sr. Full Stack Engineer - Drew": "Drew",
        "Fonzi - Fullstack Engineer - Blessing": "Blessing",
        "Fonzi - Fullstack Engineer - V3": "Blessing",
        "Fonzi - Sr. Full Stack Engineer - Blessing (as Drew)": "Blessing",
        "Fonzi - Sr. Full Stack Engineer - Drew (via Cait)": "Drew",
        "Fonzi - Sr. Full Stack Engineer - Drew (via Rachel)": "Drew",
        "Fonzi - Sr. Full Stack Engineer - Drew/Yang (via Cait)": "Drew",
        "Fonzi - Fullstack Engineer - V4 short (as Drew)": "Blessing",
        "A/B - Fonzi - Fullstack Engineer - Blessing": "Blessing",
        "Fonzi - Sr. AI Engineer - Drew": "Drew",
        "Fonzi - Sr. AI Engineer - Blessing (as Drew)": "Blessing",
        "Fonzi - Sr. AI Engineer - Drew (SOBO via Rachel)": "Drew",
        "Fonzi - Sr. AI Engineer V2 w/Yang - Drew (SOBO via Rachel)": "Drew",
    }

    # Database path for historical tracking
    database_path: str = "data/recruiting.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
