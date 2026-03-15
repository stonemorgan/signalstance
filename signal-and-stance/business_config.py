"""Centralized business configuration loader.

Reads business_config.json once at import time and exposes the config
as a module-level dict. All business-specific identity, brand, domain,
and scheduling values live in that JSON file.
"""

import json
import os
import re

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "business_config.json")

with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    BUSINESS = json.load(_f)


def _resolve(template_str):
    """Replace {section.key} placeholders with values from BUSINESS config.

    Supports one level of nesting: {owner.name}, {platform.name}, etc.
    """
    def _replacer(match):
        path = match.group(1)
        parts = path.split(".")
        val = BUSINESS
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part, match.group(0))
            else:
                return match.group(0)
        return str(val) if not isinstance(val, dict) else match.group(0)

    return re.sub(r"\{(\w+\.\w+)\}", _replacer, template_str)


# Convenience accessors
OWNER = BUSINESS["owner"]
PLATFORM = BUSINESS["platform"]
BRAND_COLORS = BUSINESS["brand"]
CONTENT = BUSINESS["content"]
SCHEDULE = BUSINESS["schedule"]
FEEDS_CONFIG = BUSINESS["feeds"]
SCORING = BUSINESS["scoring"]
APP_NAME = BUSINESS["app_name"]

# Pre-resolved scoring strings
SCORING_DESCRIPTION = _resolve(SCORING["scoring_description"])
SCORING_HIGH = _resolve(SCORING["scoring_high"])
SCORING_LOW = _resolve(SCORING["scoring_low"])
