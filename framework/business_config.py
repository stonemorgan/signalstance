"""Centralized business configuration loader.

Reads business_config.json from the active tenant directory.
The tenant directory is specified by the SIGNALSTANCE_TENANT_DIR environment variable.
Falls back to looking in the same directory as this file (for backwards compatibility).
"""

import json
import os
import re

from validate import ConfigError, validate_business_config


# Determine tenant directory
TENANT_DIR = os.environ.get("SIGNALSTANCE_TENANT_DIR")
if not TENANT_DIR:
    # Backwards compatibility: look in same directory as this file
    TENANT_DIR = os.path.dirname(__file__)

_CONFIG_PATH = os.path.join(TENANT_DIR, "business_config.json")

if not os.path.exists(_CONFIG_PATH):
    raise ConfigError(
        f"business_config.json not found at {_CONFIG_PATH}. "
        f"Set SIGNALSTANCE_TENANT_DIR to the tenant directory."
    )

try:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
        BUSINESS = json.load(_f)
except json.JSONDecodeError as e:
    raise ConfigError(
        f"{_CONFIG_PATH}: invalid JSON at line {e.lineno} column {e.colno}: {e.msg}"
    ) from e

validate_business_config(BUSINESS, _CONFIG_PATH)


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
