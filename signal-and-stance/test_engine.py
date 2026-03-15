"""Test the content generation engine with all 4 categories."""

import re
import sys
import textwrap

from engine import generate_posts, load_prompt

TEST_CASES = [
    {
        "category": "pattern",
        "raw_input": "Third VP this month with no quantified achievements on their resume despite managing $50M+ budgets",
    },
    {
        "category": "faq",
        "raw_input": "Client asked if they should include a photo on their executive resume",
    },
    {
        "category": "noticed",
        "raw_input": "Seeing a spike in Chief AI Officer job postings this quarter — none of them list specific AI experience requirements",
    },
    {
        "category": "hottake",
        "raw_input": "Cover letters are NOT dead for executive roles despite what LinkedIn influencers claim",
    },
]

SEPARATOR = "=" * 80

ALL_PROMPT_FILES = [
    "prompts/base_system.md",
    "prompts/autopilot.md",
    "prompts/category_pattern.md",
    "prompts/category_faq.md",
    "prompts/category_noticed.md",
    "prompts/category_hottake.md",
    "prompts/url_react.md",
    "prompts/feed_react.md",
    "prompts/carousel_tips.md",
    "prompts/carousel_beforeafter.md",
    "prompts/carousel_mythreality.md",
]


def test_template_substitution():
    """Verify no unresolved {{}} placeholders remain after loading."""
    print(SEPARATOR)
    print("TEMPLATE SUBSTITUTION TEST")
    print(SEPARATOR)

    all_ok = True
    for pf in ALL_PROMPT_FILES:
        content = load_prompt(pf)
        unresolved = re.findall(r"\{\{.+?\}\}", content)
        if unresolved:
            print(f"  FAIL: {pf} has unresolved placeholders: {unresolved}")
            all_ok = False
        else:
            print(f"  OK: {pf}")

    if all_ok:
        print("\nALL TEMPLATES RESOLVED SUCCESSFULLY")
    else:
        print("\nTEMPLATE ERRORS FOUND — fix before proceeding")

    print(SEPARATOR)
    print()
    return all_ok


def count_words(text):
    return len(text.split())


def check_ai_phrases(text):
    """Check for AI-sounding phrases that should be avoided."""
    bad_phrases = [
        "in today's competitive",
        "in today's fast-paced",
        "as a professional",
        "it's important to note",
        "at the end of the day",
        "i'm excited to share",
        "i've been thinking about",
        "happy monday",
        "happy tuesday",
        "happy wednesday",
        "happy thursday",
        "happy friday",
        "you've got this",
        "believe in yourself",
        "keep pushing",
        "remember your worth",
        "as someone who",
    ]
    found = []
    lower = text.lower()
    for phrase in bad_phrases:
        if phrase in lower:
            found.append(phrase)
    return found


def run_tests():
    all_passed = True

    for test in TEST_CASES:
        category = test["category"]
        raw_input = test["raw_input"]

        print(SEPARATOR)
        print(f"CATEGORY: {category.upper()}")
        print(f"INPUT: {raw_input}")
        print(SEPARATOR)

        try:
            drafts = generate_posts(category, raw_input)
        except Exception as e:
            print(f"\nERROR: Generation failed — {e}\n")
            all_passed = False
            continue

        # Check: 3 drafts returned
        if len(drafts) != 3:
            print(f"\nWARNING: Expected 3 drafts, got {len(drafts)}")
            all_passed = False

        for i, draft in enumerate(drafts, start=1):
            content = draft["content"]
            angle = draft["angle"]
            word_count = count_words(content)
            ai_phrases = check_ai_phrases(content)

            print(f"\n--- Draft {i} ---")
            print(f"Angle: {angle}")
            print(f"Word count: {word_count}")
            print()
            print(content)
            print()

            # Quality checks
            issues = []
            if word_count < 100:
                issues.append(f"Too short ({word_count} words, minimum ~150)")
            if word_count > 350:
                issues.append(f"Too long ({word_count} words, maximum ~300)")
            if ai_phrases:
                issues.append(f"AI phrases detected: {', '.join(ai_phrases)}")
            if not angle:
                issues.append("No angle description parsed")

            if issues:
                print("ISSUES:")
                for issue in issues:
                    print(f"  - {issue}")
                all_passed = False
            else:
                print("CHECKS PASSED")

        print()

    print(SEPARATOR)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME ISSUES FOUND — review output above")
    print(SEPARATOR)


if __name__ == "__main__":
    if not test_template_substitution():
        sys.exit(1)
    run_tests()
