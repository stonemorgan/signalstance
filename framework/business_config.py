"""Centralized business configuration loader.

Reads business_config.json from the active tenant directory.
The tenant directory is specified by the SIGNALSTANCE_TENANT_DIR environment variable.
Falls back to looking in the same directory as this file (for backwards compatibility).
"""

import json
import os
import re


class ConfigError(Exception):
    """Raised when a tenant's business_config.json is missing, malformed, or
    incomplete. The message identifies the file and the specific problem so
    operators can fix it without reading a stack trace."""


_VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}

# (path, type) — path is dotted, type is the expected JSON type for that node.
_REQUIRED_KEYS = [
    ("app_name", str),
    ("database_name", str),
    ("owner", dict),
    ("platform", dict),
    ("brand", dict),
    ("content", dict),
    ("schedule", dict),
    ("schedule.days", dict),
    ("schedule.suggested_times", dict),
    ("feeds", dict),
    ("feeds.categories", dict),
    ("scoring", dict),
    ("scoring.scoring_description", str),
    ("scoring.scoring_high", str),
    ("scoring.scoring_low", str),
]


def _lookup(config, dotted_path):
    val = config
    for part in dotted_path.split("."):
        if not isinstance(val, dict) or part not in val:
            return None, False
        val = val[part]
    return val, True


def _validate(config, source_path):
    if not isinstance(config, dict):
        raise ConfigError(
            f"{source_path}: top-level value must be a JSON object, got {type(config).__name__}"
        )

    for path, expected_type in _REQUIRED_KEYS:
        val, found = _lookup(config, path)
        if not found:
            raise ConfigError(f"{source_path}: missing required key '{path}'")
        if not isinstance(val, expected_type):
            raise ConfigError(
                f"{source_path}: key '{path}' must be {expected_type.__name__}, "
                f"got {type(val).__name__}"
            )

    days = config["schedule"]["days"]
    if not days:
        raise ConfigError(f"{source_path}: 'schedule.days' must contain at least one weekday")
    for day, info in days.items():
        if day not in _VALID_DAYS:
            raise ConfigError(
                f"{source_path}: 'schedule.days' has unknown weekday '{day}'. "
                f"Valid: {', '.join(sorted(_VALID_DAYS))}"
            )
        if not isinstance(info, dict):
            raise ConfigError(
                f"{source_path}: 'schedule.days.{day}' must be an object with "
                f"'content_type' and 'suggestion'"
            )
        for sub in ("content_type", "suggestion"):
            if sub not in info:
                raise ConfigError(
                    f"{source_path}: 'schedule.days.{day}' is missing '{sub}'"
                )

    suggested_times = config["schedule"]["suggested_times"]
    for day in days:
        if day not in suggested_times:
            raise ConfigError(
                f"{source_path}: 'schedule.suggested_times' is missing entry for '{day}'"
            )


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

_validate(BUSINESS, _CONFIG_PATH)


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
