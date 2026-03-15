"""Brand configuration for carousel rendering.

Reads visual identity and author metadata from business_config.json.
"""

from business_config import BRAND_COLORS, OWNER, PLATFORM

BRAND = {
    # Colors
    "primary": BRAND_COLORS["primary"],
    "secondary": BRAND_COLORS["secondary"],
    "accent": BRAND_COLORS["accent"],
    "background": BRAND_COLORS["background"],
    "background_alt": BRAND_COLORS["background_alt"],
    "text_dark": BRAND_COLORS["text_dark"],
    "text_light": BRAND_COLORS["text_light"],
    "text_muted": BRAND_COLORS["text_muted"],
    "divider": BRAND_COLORS["divider"],
    "negative": BRAND_COLORS["negative"],
    "positive": BRAND_COLORS["positive"],
    # Typography
    "font_heading": BRAND_COLORS["font_heading"],
    "font_body": BRAND_COLORS["font_body"],
    "font_accent": BRAND_COLORS["font_accent"],
    # Slide dimensions
    "slide_width": PLATFORM["carousel_dimensions"][0],
    "slide_height": PLATFORM["carousel_dimensions"][1],
    # Author
    "author_name": OWNER["name"],
    "author_title": OWNER["title"],
    "author_business": OWNER["business"],
    "author_url": OWNER["url"],
}
