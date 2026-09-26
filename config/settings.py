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
