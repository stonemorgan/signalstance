import os

from dotenv import load_dotenv

# Load .env from this directory first, then from parent (root) for run.py usage
_this_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(_this_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(_this_dir), ".env"))

from business_config import BUSINESS, SCHEDULE, TENANT_DIR

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DATABASE_PATH = os.path.join(TENANT_DIR, BUSINESS["database_name"])

_DAY_TO_INT = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}

# Weekly content schedule — read from business config
CONTENT_SCHEDULE = {}
for day, info in SCHEDULE["days"].items():
    CONTENT_SCHEDULE[_DAY_TO_INT[day]] = {
        "type": info["content_type"],
        "suggestion": info["suggestion"],
    }

# Suggested posting times
SUGGESTED_TIMES = {}
for day, time_str in SCHEDULE["suggested_times"].items():
    SUGGESTED_TIMES[_DAY_TO_INT[day]] = time_str
