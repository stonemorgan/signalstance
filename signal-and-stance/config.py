import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
FLASK_PORT = 5000
DATABASE_PATH = "signal_stance.db"

# Weekly content schedule (0=Monday, 4=Friday)
CONTENT_SCHEDULE = {
    0: {
        "type": "Educational / Pattern",
        "suggestion": "Share a pattern or recurring mistake you see in your work"
    },
    1: {
        "type": "Tactical Tip",
        "suggestion": "Share a specific, actionable tip about resumes, LinkedIn, or job search"
    },
    2: {
        "type": "Deep Dive / Story",
        "suggestion": "Tell a story or go deeper on a topic with a client example"
    },
    3: {
        "type": "Thought Leadership / Hot Take",
        "suggestion": "Share a contrarian opinion or professional stance"
    },
    4: {
        "type": "Quick Win / Encouragement",
        "suggestion": "Share a quick tip or insight that builds confidence"
    },
}

# Suggested posting times (EST) for each day
# These are LinkedIn engagement sweet spots for professional audiences
# Dana uses these as guidance when scheduling on LinkedIn
SUGGESTED_TIMES = {
    0: "8:30 AM",   # Monday
    1: "9:00 AM",   # Tuesday
    2: "8:30 AM",   # Wednesday
    3: "9:00 AM",   # Thursday
    4: "10:00 AM",  # Friday
}
