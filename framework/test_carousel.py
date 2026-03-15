"""Test carousel content generation and parsing for all 3 templates."""

import json
import sys
import os

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(__file__))

import re

from engine import generate_carousel_content, load_prompt


def print_separator(label):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}\n")


def validate_tips(parsed):
    """Validate tips template output."""
    issues = []
    if "error" in parsed:
        return [f"PARSE ERROR: {parsed['error']}"]

    if not parsed.get("title"):
        issues.append("Missing title")
    elif not any(c.isdigit() for c in parsed["title"]):
        issues.append(f"Title has no number: '{parsed['title']}'")

    slides = parsed.get("slides", [])
    if len(slides) < 5:
        issues.append(f"Too few tips: {len(slides)} (expected 5-7)")
    elif len(slides) > 7:
        issues.append(f"Too many tips: {len(slides)} (expected 5-7)")

    for s in slides:
        headline_words = len(s["headline"].split())
        if headline_words > 6:
            issues.append(f"Tip {s['number']} headline too long ({headline_words} words): '{s['headline']}'")
        body_words = len(s["body"].split())
        if body_words > 30:
            issues.append(f"Tip {s['number']} body too long ({body_words} words)")

    if not parsed.get("cta"):
        issues.append("Missing CTA")

    return issues


def validate_beforeafter(parsed):
    """Validate before/after template output."""
    issues = []
    if "error" in parsed:
        return [f"PARSE ERROR: {parsed['error']}"]

    if not parsed.get("title"):
        issues.append("Missing title")

    slides = parsed.get("slides", [])
    if len(slides) < 4:
        issues.append(f"Too few pairs: {len(slides)} (expected 4-6)")
    elif len(slides) > 6:
        issues.append(f"Too many pairs: {len(slides)} (expected 4-6)")

    for i, s in enumerate(slides, 1):
        if not s.get("before"):
            issues.append(f"Pair {i} missing 'before'")
        if not s.get("after"):
            issues.append(f"Pair {i} missing 'after'")

    if not parsed.get("cta"):
        issues.append("Missing CTA")

    return issues


def validate_mythreality(parsed):
    """Validate myth/reality template output."""
    issues = []
    if "error" in parsed:
        return [f"PARSE ERROR: {parsed['error']}"]

    if not parsed.get("title"):
        issues.append("Missing title")

    slides = parsed.get("slides", [])
    if len(slides) < 4:
        issues.append(f"Too few myths: {len(slides)} (expected 4-6)")
    elif len(slides) > 6:
        issues.append(f"Too many myths: {len(slides)} (expected 4-6)")

    for s in slides:
        if not s.get("myth"):
            issues.append(f"Myth {s.get('number', '?')} missing myth text")
        if not s.get("reality"):
            issues.append(f"Myth {s.get('number', '?')} missing reality text")

    if not parsed.get("cta"):
        issues.append("Missing CTA")

    return issues


def run_test(template_type, input_text, validator):
    print_separator(f"TEST: {template_type.upper()}")
    print(f"Input: \"{input_text}\"\n")

    print("Calling API...")
    result = generate_carousel_content(template_type, input_text)

    # Print raw response
    raw = result.pop("_raw", "(no raw content)")
    print("\n--- RAW API RESPONSE ---")
    print(raw)
    print("--- END RAW ---\n")

    # Print parsed dict
    print("--- PARSED DICT ---")
    print(json.dumps(result, indent=2, default=str))
    print("--- END PARSED ---\n")

    # Validate
    issues = validator(result)
    if issues:
        print("VALIDATION ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("VALIDATION: ALL CHECKS PASSED")

    # Summary
    if "error" not in result:
        print(f"\n  Title: {result.get('title')}")
        print(f"  Subtitle: {result.get('subtitle')}")
        print(f"  Slides: {len(result.get('slides', []))}")
        print(f"  CTA: {result.get('cta')}")

    return "error" not in result and len(issues) == 0


CAROUSEL_PROMPT_FILES = [
    "prompts/carousel_tips.md",
    "prompts/carousel_beforeafter.md",
    "prompts/carousel_mythreality.md",
]


def test_carousel_template_substitution():
    """Verify no unresolved {{}} placeholders in carousel prompts."""
    print_separator("TEMPLATE SUBSTITUTION TEST")

    all_ok = True
    for pf in CAROUSEL_PROMPT_FILES:
        content = load_prompt(pf)
        unresolved = re.findall(r"\{\{.+?\}\}", content)
        if unresolved:
            print(f"  FAIL: {pf} has unresolved placeholders: {unresolved}")
            all_ok = False
        else:
            print(f"  OK: {pf}")

    if all_ok:
        print("\nALL CAROUSEL TEMPLATES RESOLVED SUCCESSFULLY")
    else:
        print("\nTEMPLATE ERRORS FOUND — fix before proceeding")

    return all_ok


if __name__ == "__main__":
    if not test_carousel_template_substitution():
        sys.exit(1)

    results = {}

    # Test 1: Tips template
    results["tips"] = run_test(
        "tips",
        "Executives keep listing responsibilities instead of achievements on their resumes",
        validate_tips,
    )

    # Test 2: Before/After template
    results["beforeafter"] = run_test(
        "beforeafter",
        "The difference between how most VPs describe their experience versus how it should read",
        validate_beforeafter,
    )

    # Test 3: Myth/Reality template
    results["mythreality"] = run_test(
        "mythreality",
        "Common misconceptions about how ATS systems actually process executive resumes",
        validate_mythreality,
    )

    # Final summary
    print_separator("FINAL RESULTS")
    for template, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {template}: {status}")

    all_passed = all(results.values())
    print(f"\n  Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)
