"""Tests for pure parsing functions in framework/engine.py.

These tests exercise parse_drafts(), extract_source_info(), _extract_field(),
_parse_tips(), _parse_beforeafter(), and _parse_mythreality() WITHOUT making
any API calls.
"""

import os
import sys

import pytest

_framework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _framework_dir not in sys.path:
    sys.path.insert(0, _framework_dir)

from engine import (
    _extract_field,
    _parse_beforeafter,
    _parse_mythreality,
    _parse_tips,
    extract_source_info,
    parse_drafts,
)


# ---------------------------------------------------------------------------
# parse_drafts()
# ---------------------------------------------------------------------------

class TestParseDrafts:
    def test_well_formed_3_drafts(self):
        """Parse well-formed input with 3 drafts and angle descriptions."""
        text = (
            "Draft 1:\n"
            "Here is the first draft about resumes.\n"
            "[Personal story angle]\n\n"
            "Draft 2:\n"
            "Second draft with tactical advice.\n"
            "[Tactical tip angle]\n\n"
            "Draft 3:\n"
            "Third draft, a hot take.\n"
            "[Contrarian angle]\n"
        )
        drafts = parse_drafts(text)
        assert len(drafts) == 3
        assert "first draft" in drafts[0]["content"]
        assert drafts[0]["angle"] == "Personal story angle"
        assert "Second draft" in drafts[1]["content"]
        assert drafts[1]["angle"] == "Tactical tip angle"
        assert "Third draft" in drafts[2]["content"]
        assert drafts[2]["angle"] == "Contrarian angle"

    def test_malformed_no_separators(self):
        """When there are no Draft N: markers, return entire text as one draft."""
        text = "Just some random text without draft markers."
        drafts = parse_drafts(text)
        assert len(drafts) == 1
        assert drafts[0]["content"] == text
        assert drafts[0]["angle"] == ""

    def test_single_draft(self):
        """Input with only one Draft marker should return 1 draft."""
        text = "Draft 1:\nThis is the only draft.\n[Solo angle]"
        drafts = parse_drafts(text)
        assert len(drafts) == 1
        assert "only draft" in drafts[0]["content"]
        assert drafts[0]["angle"] == "Solo angle"

    def test_two_drafts(self):
        """Two drafts should return exactly 2."""
        text = (
            "Draft 1:\nFirst one.\n[Angle A]\n\n"
            "Draft 2:\nSecond one.\n[Angle B]\n"
        )
        drafts = parse_drafts(text)
        assert len(drafts) == 2

    def test_drafts_without_angles(self):
        """Drafts without bracket angles should have empty angle string."""
        text = (
            "Draft 1:\nNo angle here.\n\n"
            "Draft 2:\nAlso no angle.\n\n"
            "Draft 3:\nStill none.\n"
        )
        drafts = parse_drafts(text)
        assert len(drafts) == 3
        for d in drafts:
            assert d["angle"] == ""

    def test_preamble_before_first_draft(self):
        """Text before 'Draft 1:' should be ignored."""
        text = (
            "Here is some preamble text.\n\n"
            "Draft 1:\nActual draft content.\n[Real angle]\n"
        )
        drafts = parse_drafts(text)
        assert len(drafts) == 1
        assert "preamble" not in drafts[0]["content"]
        assert "Actual draft content" in drafts[0]["content"]

    def test_empty_input(self):
        """Empty string should still return at least one draft."""
        drafts = parse_drafts("")
        assert len(drafts) == 1

    def test_draft_numbering_flexible(self):
        """Draft markers with varying spacing should still parse."""
        text = (
            "Draft  1 :\nFirst.\n[A]\n\n"
            "Draft  2 :\nSecond.\n[B]\n"
        )
        drafts = parse_drafts(text)
        assert len(drafts) == 2


# ---------------------------------------------------------------------------
# extract_source_info()
# ---------------------------------------------------------------------------

class TestExtractSourceInfo:
    def test_full_extraction(self):
        """Extract all fields from a well-formed response."""
        text = (
            "SOURCE_SUMMARY: Article about AI in recruiting\n"
            "SOURCE_URL: https://example.com/article\n"
            "CATEGORY: noticed\n"
            "INSIGHT: AI is changing how resumes are screened\n"
        )
        info = extract_source_info(text)
        assert info["source_summary"] == "Article about AI in recruiting"
        assert info["source_url"] == "https://example.com/article"
        assert info["category"] == "noticed"
        assert info["insight"] == "AI is changing how resumes are screened"

    def test_missing_fields(self):
        """Missing fields should be None or empty string."""
        text = "SOURCE_SUMMARY: Just a summary\n"
        info = extract_source_info(text)
        assert info["source_summary"] == "Just a summary"
        assert info["source_url"] is None
        assert info["category"] is None
        assert info["insight"] is None

    def test_empty_input(self):
        """Empty input should return default dict."""
        info = extract_source_info("")
        assert info["source_summary"] == ""
        assert info["source_url"] is None

    def test_reaction_type_extraction(self):
        """REACTION_TYPE should be extracted when present."""
        text = (
            "SOURCE_SUMMARY: Test\n"
            "REACTION_TYPE: agree_amplify\n"
        )
        info = extract_source_info(text)
        assert info["reaction_type"] == "agree_amplify"

    def test_url_with_query_params(self):
        """URLs with query parameters should be extracted correctly."""
        text = "SOURCE_URL: https://example.com/article?id=123&ref=social\n"
        info = extract_source_info(text)
        assert info["source_url"] == "https://example.com/article?id=123&ref=social"


# ---------------------------------------------------------------------------
# _extract_field()
# ---------------------------------------------------------------------------

class TestExtractField:
    def test_simple_extraction(self):
        text = "TITLE: My Great Title\nSUBTITLE: A subtitle"
        assert _extract_field(text, "TITLE:") == "My Great Title"
        assert _extract_field(text, "SUBTITLE:") == "A subtitle"

    def test_missing_field(self):
        text = "TITLE: Some title"
        assert _extract_field(text, "MISSING:") is None

    def test_field_with_extra_spaces(self):
        text = "TITLE:   Spaced Out Title  \n"
        assert _extract_field(text, "TITLE:") == "Spaced Out Title"

    def test_multiline_text(self):
        text = "LINE1: First\nLINE2: Second\nLINE3: Third"
        assert _extract_field(text, "LINE2:") == "Second"


# ---------------------------------------------------------------------------
# _parse_tips()
# ---------------------------------------------------------------------------

class TestParseTips:
    def test_valid_tips(self):
        text = (
            "TITLE: 5 Resume Tips\n"
            "SUBTITLE: For executives\n"
            "TIP 1 HEADLINE: Use metrics\n"
            "TIP 1 BODY: Always quantify your achievements.\n"
            "TIP 2 HEADLINE: Keep it concise\n"
            "TIP 2 BODY: Two pages max for most executives.\n"
            "CTA: Follow for more resume advice\n"
        )
        result = _parse_tips(text)
        assert "error" not in result
        assert result["title"] == "5 Resume Tips"
        assert result["subtitle"] == "For executives"
        assert len(result["slides"]) == 2
        assert result["slides"][0]["headline"] == "Use metrics"
        assert result["slides"][0]["body"] == "Always quantify your achievements."
        assert result["cta"] == "Follow for more resume advice"

    def test_missing_title_returns_error(self):
        text = "TIP 1 HEADLINE: No title\nTIP 1 BODY: body"
        result = _parse_tips(text)
        assert "error" in result

    def test_headline_without_body(self):
        """A tip with headline but no body should still be included."""
        text = (
            "TITLE: Tips\n"
            "TIP 1 HEADLINE: Solo headline\n"
        )
        result = _parse_tips(text)
        assert len(result["slides"]) == 1
        assert result["slides"][0]["body"] == ""

    def test_no_tips_returns_error(self):
        text = "TITLE: A Title\n"
        result = _parse_tips(text)
        assert "error" in result


# ---------------------------------------------------------------------------
# _parse_beforeafter()
# ---------------------------------------------------------------------------

class TestParseBeforeAfter:
    def test_valid_pairs(self):
        text = (
            "TITLE: Resume Transformations\n"
            "SUBTITLE: Real examples\n"
            "PAIR 1 BEFORE: Responsible for sales\n"
            "PAIR 1 AFTER: Grew territory revenue 43% YoY\n"
            "PAIR 1 NOTE: Always quantify impact\n"
            "PAIR 2 BEFORE: Managed a team\n"
            "PAIR 2 AFTER: Led 12-person cross-functional team\n"
            "CTA: Save this for your next resume update\n"
        )
        result = _parse_beforeafter(text)
        assert "error" not in result
        assert result["title"] == "Resume Transformations"
        assert len(result["slides"]) == 2
        assert result["slides"][0]["before"] == "Responsible for sales"
        assert result["slides"][0]["after"] == "Grew territory revenue 43% YoY"
        assert result["slides"][0]["note"] == "Always quantify impact"
        # Second pair has no NOTE, so it should be None
        assert result["slides"][1]["note"] is None

    def test_missing_title_returns_error(self):
        text = "PAIR 1 BEFORE: X\nPAIR 1 AFTER: Y\n"
        result = _parse_beforeafter(text)
        assert "error" in result

    def test_no_pairs_returns_error(self):
        text = "TITLE: No Pairs Here\n"
        result = _parse_beforeafter(text)
        assert "error" in result

    def test_incomplete_pair_stops_parsing(self):
        """If BEFORE exists but AFTER is missing, stop at that pair."""
        text = (
            "TITLE: Test\n"
            "PAIR 1 BEFORE: Before text\n"
            "PAIR 1 AFTER: After text\n"
            "PAIR 2 BEFORE: Only before\n"
        )
        result = _parse_beforeafter(text)
        assert len(result["slides"]) == 1


# ---------------------------------------------------------------------------
# _parse_mythreality()
# ---------------------------------------------------------------------------

class TestParseMythReality:
    def test_valid_myths(self):
        text = (
            "TITLE: Resume Myths Debunked\n"
            "SUBTITLE: What you think you know\n"
            "MYTH 1: One-page resumes are always better\n"
            "REALITY 1: Executives should use 2 pages to show scope\n"
            "MYTH 2: Include every job you ever had\n"
            "REALITY 2: Focus on the last 15 years\n"
            "CTA: Follow for myth-busting career advice\n"
        )
        result = _parse_mythreality(text)
        assert "error" not in result
        assert result["title"] == "Resume Myths Debunked"
        assert len(result["slides"]) == 2
        assert result["slides"][0]["myth"] == "One-page resumes are always better"
        assert result["slides"][0]["reality"] == "Executives should use 2 pages to show scope"
        assert result["slides"][0]["number"] == 1

    def test_missing_title_returns_error(self):
        text = "MYTH 1: X\nREALITY 1: Y\n"
        result = _parse_mythreality(text)
        assert "error" in result

    def test_no_myths_returns_error(self):
        text = "TITLE: Title Only\n"
        result = _parse_mythreality(text)
        assert "error" in result

    def test_incomplete_myth_stops_parsing(self):
        """MYTH without REALITY stops parsing."""
        text = (
            "TITLE: Test\n"
            "MYTH 1: First myth\n"
            "REALITY 1: First reality\n"
            "MYTH 2: Orphan myth\n"
        )
        result = _parse_mythreality(text)
        assert len(result["slides"]) == 1
