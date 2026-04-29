"""Tests for business_config.py validation.

Each test stages a tenant directory with a specific defect, points
SIGNALSTANCE_TENANT_DIR at it, and asserts that importing business_config
raises ConfigError with a message that names the file and the defect.
"""

import copy
import importlib
import json
import os
import sys

import pytest


_AFFECTED_MODULES = ("business_config", "config", "feeds", "database", "engine", "app")


@pytest.fixture(autouse=True)
def _isolate_module_cache():
    """Each test in this file reloads business_config under a different
    tenant. Drop any cached copy of business_config and its downstream
    importers before AND after the test so neither this test nor any later
    test sees stale module-level state."""
    for name in _AFFECTED_MODULES:
        sys.modules.pop(name, None)
    yield
    for name in _AFFECTED_MODULES:
        sys.modules.pop(name, None)


_VALID_CONFIG = {
    "app_name": "Test App",
    "database_name": "test.db",
    "owner": {"name": "Test"},
    "platform": {"name": "LinkedIn"},
    "brand": {"primary": "#000000"},
    "content": {"categories": {}},
    "schedule": {
        "days": {
            "Monday": {"content_type": "x", "suggestion": "y"},
            "Tuesday": {"content_type": "x", "suggestion": "y"},
            "Wednesday": {"content_type": "x", "suggestion": "y"},
            "Thursday": {"content_type": "x", "suggestion": "y"},
            "Friday": {"content_type": "x", "suggestion": "y"},
        },
        "suggested_times": {
            "Monday": "8:00 AM",
            "Tuesday": "8:00 AM",
            "Wednesday": "8:00 AM",
            "Thursday": "8:00 AM",
            "Friday": "8:00 AM",
        },
    },
    "feeds": {"categories": {}},
    "scoring": {
        "scoring_description": "desc",
        "scoring_high": "high",
        "scoring_low": "low",
    },
}


def _stage_tenant(tmp_path, config=None, raw_text=None, write_config=True):
    """Write a tenant dir at tmp_path. If raw_text is given, write that
    verbatim (used to test malformed JSON). Otherwise json-dump `config`.
    Set write_config=False to skip writing the file entirely."""
    if write_config:
        config_path = tmp_path / "business_config.json"
        if raw_text is not None:
            config_path.write_text(raw_text, encoding="utf-8")
        else:
            config_path.write_text(json.dumps(config), encoding="utf-8")
    return str(tmp_path)


def _import_fresh(tenant_dir, monkeypatch):
    """Force a fresh import of business_config under the given tenant dir.
    Returns the imported module."""
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant_dir)
    # Drop any previously-imported copy so the module-level code re-runs.
    sys.modules.pop("business_config", None)
    return importlib.import_module("business_config")


def test_valid_config_imports_cleanly(tmp_path, monkeypatch):
    tenant = _stage_tenant(tmp_path, copy.deepcopy(_VALID_CONFIG))
    mod = _import_fresh(tenant, monkeypatch)
    assert mod.BUSINESS["app_name"] == "Test App"
    assert mod.APP_NAME == "Test App"


def test_missing_file_raises(tmp_path, monkeypatch):
    tenant = _stage_tenant(tmp_path, write_config=False)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "business_config.json not found" in str(exc.value)
    assert type(exc.value).__name__ == "ConfigError"


def test_malformed_json_raises(tmp_path, monkeypatch):
    tenant = _stage_tenant(tmp_path, raw_text="{ not valid json")
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    msg = str(exc.value)
    assert "invalid JSON" in msg
    assert "line" in msg and "column" in msg


def test_missing_top_level_key_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    del bad["scoring"]
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "missing required key 'scoring'" in str(exc.value)


def test_missing_nested_key_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    del bad["scoring"]["scoring_high"]
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "missing required key 'scoring.scoring_high'" in str(exc.value)


def test_wrong_type_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    bad["app_name"] = 123  # should be string
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "app_name" in str(exc.value)
    assert "must be str" in str(exc.value)


def test_unknown_weekday_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    bad["schedule"]["days"]["Saturday"] = {"content_type": "x", "suggestion": "y"}
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "unknown weekday 'Saturday'" in str(exc.value)


def test_day_missing_subkey_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    del bad["schedule"]["days"]["Monday"]["suggestion"]
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "schedule.days.Monday" in str(exc.value)
    assert "suggestion" in str(exc.value)


def test_missing_suggested_time_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    del bad["schedule"]["suggested_times"]["Wednesday"]
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "suggested_times" in str(exc.value)
    assert "Wednesday" in str(exc.value)


def test_empty_days_raises(tmp_path, monkeypatch):
    bad = copy.deepcopy(_VALID_CONFIG)
    bad["schedule"]["days"] = {}
    tenant = _stage_tenant(tmp_path, bad)
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "must contain at least one weekday" in str(exc.value)


def test_top_level_not_object_raises(tmp_path, monkeypatch):
    tenant = _stage_tenant(tmp_path, raw_text='["array", "not", "object"]')
    sys.modules.pop("business_config", None)
    monkeypatch.setenv("SIGNALSTANCE_TENANT_DIR", tenant)
    with pytest.raises(Exception) as exc:
        importlib.import_module("business_config")
    assert "must be a JSON object" in str(exc.value)
