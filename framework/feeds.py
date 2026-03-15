import json
import os

from business_config import FEEDS_CONFIG, TENANT_DIR

FEED_CATEGORIES = FEEDS_CONFIG["categories"]

# Load default feeds from tenant directory
_FEEDS_PATH = os.path.join(TENANT_DIR, "feeds.json")
if os.path.exists(_FEEDS_PATH):
    with open(_FEEDS_PATH, "r", encoding="utf-8") as f:
        DEFAULT_FEEDS = json.load(f)
else:
    DEFAULT_FEEDS = []
