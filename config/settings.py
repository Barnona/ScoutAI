import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-4-31b-it")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

MAX_SEARCHES = int(os.getenv("MAX_SEARCHES", "5"))
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "12"))
MAX_VERIFICATION_ROUNDS = int(os.getenv("MAX_VERIFICATION_ROUNDS", "2"))
MAX_FOLLOWUP_SEARCHES = int(os.getenv("MAX_FOLLOWUP_SEARCHES", "4"))

RESEARCH_PROFILES = {
    "quick": {"searches": 3, "sources": 7, "rounds": 1, "followups": 2},
    "standard": {"searches": MAX_SEARCHES, "sources": MAX_SOURCES, "rounds": MAX_VERIFICATION_ROUNDS, "followups": MAX_FOLLOWUP_SEARCHES},
    "deep": {"searches": 7, "sources": 18, "rounds": 3, "followups": 5},
    "investigative": {"searches": 9, "sources": 24, "rounds": 4, "followups": 7},
}


def get_research_profile(depth: str) -> dict[str, int]:
    return RESEARCH_PROFILES.get(depth, RESEARCH_PROFILES["standard"])


def validate_environment() -> None:
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not SERPAPI_API_KEY:
        missing.append("SERPAPI_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )
