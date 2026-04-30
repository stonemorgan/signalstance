"""Pure validator for tenant business_config.json.

This module has no import-time side effects so it can be used by tools
that need to validate a config without triggering the tenant-directory
loading in business_config.py.
"""


class ConfigError(Exception):
    """Raised when a tenant's business_config.json is missing, malformed,
    or incomplete. The message identifies the file and the specific
    problem so operators can fix it without reading a stack trace."""


VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}

# (path, type) — path is dotted, type is the expected JSON type for that node.
REQUIRED_KEYS = [
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


def validate_business_config(config, source_path):
    """Validate a parsed business_config dict. Raises ConfigError on any
    schema violation. source_path is used in error messages so operators
    can locate the offending file."""
    if not isinstance(config, dict):
        raise ConfigError(
            f"{source_path}: top-level value must be a JSON object, got {type(config).__name__}"
        )

    for path, expected_type in REQUIRED_KEYS:
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
        if day not in VALID_DAYS:
            raise ConfigError(
                f"{source_path}: 'schedule.days' has unknown weekday '{day}'. "
                f"Valid: {', '.join(sorted(VALID_DAYS))}"
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
