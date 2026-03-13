"""PDF carousel renderer for Signal & Stance.

Generates branded 1080x1080 carousel PDFs from structured content
produced by engine.generate_carousel_content().
"""

import os
import time
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph

from brand import BRAND

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
W = BRAND["slide_width"]
H = BRAND["slide_height"]
MARGIN = 80
CONTENT_WIDTH = W - 2 * MARGIN
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_carousels")

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def hex_to_color(hex_str):
    """Convert a hex color string to a ReportLab Color."""
    return HexColor(hex_str)


def _alpha(hex_str, opacity):
    """Return a Color from hex with the given opacity (0-1)."""
    c = HexColor(hex_str)
    return Color(c.red, c.green, c.blue, opacity)


# Precomputed brand colors
C_PRIMARY = hex_to_color(BRAND["primary"])
C_SECONDARY = hex_to_color(BRAND["secondary"])
C_ACCENT = hex_to_color(BRAND["accent"])
C_BG = hex_to_color(BRAND["background"])
C_BG_ALT = hex_to_color(BRAND["background_alt"])
C_TEXT_DARK = hex_to_color(BRAND["text_dark"])
C_TEXT_LIGHT = hex_to_color(BRAND["text_light"])
C_TEXT_MUTED = hex_to_color(BRAND["text_muted"])
C_DIVIDER = hex_to_color(BRAND["divider"])
C_NEGATIVE = hex_to_color(BRAND["negative"])
C_POSITIVE = hex_to_color(BRAND["positive"])

# Light tinted backgrounds for before/after boxes
C_LIGHT_RED = Color(0.753, 0.224, 0.169, 0.10)   # C_NEGATIVE at 10%
C_LIGHT_GREEN = Color(0.153, 0.682, 0.376, 0.10)  # C_POSITIVE at 10%

# ---------------------------------------------------------------------------
# Text rendering helpers
# ---------------------------------------------------------------------------

_ALIGNMENT_MAP = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "right": TA_RIGHT,
}


def draw_wrapped_text(c, text, x, y, width, height, font, size, color,
                      alignment="center", leading=None):
    """Draw text wrapped inside a frame region using Paragraph/Frame.

    Args:
        c: ReportLab canvas
        text: plain text string (will be XML-escaped)
        x, y: bottom-left corner of the frame
        width, height: frame dimensions
        font: font name
        size: font size in points
        color: ReportLab Color object
        alignment: "left", "center", or "right"
        leading: line spacing (defaults to size * 1.3)
    """
    if not text:
        return
    if leading is None:
        leading = size * 1.3

    style = ParagraphStyle(
        "wrapped",
        fontName=font,
        fontSize=size,
        leading=leading,
        textColor=color,
        alignment=_ALIGNMENT_MAP.get(alignment, TA_CENTER),
    )
    para = Paragraph(xml_escape(text), style)
    frame = Frame(x, y, width, height, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, showBoundary=0)
    frame.addFromList([para], c)


# ---------------------------------------------------------------------------
# Common drawing helpers
# ---------------------------------------------------------------------------

def draw_accent_line(c, y, width_fraction=0.6):
    """Draw a centered horizontal divider line."""
    line_w = W * width_fraction
    x_start = (W - line_w) / 2
    c.setStrokeColor(C_DIVIDER)
    c.setLineWidth(1.5)
    c.line(x_start, y, x_start + line_w, y)


def draw_footer(c):
    """Draw the branded footer: accent line + author name."""
    draw_accent_line(c, 75, 0.6)
    draw_wrapped_text(
        c,
        f"{BRAND['author_name']}  \u00b7  {BRAND['author_business']}",
        MARGIN, 30, CONTENT_WIDTH, 36,
        BRAND["font_body"], 18, C_TEXT_MUTED, "center",
    )


def _fill_bg(c, color):
    """Fill the entire slide with a background color."""
    c.setFillColor(color)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _draw_round_rect(c, x, y, w, h, r, fill_color, stroke=0):
    """Draw a rounded rectangle."""
    c.setFillColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=stroke)


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def render_cover_slide(c, title, subtitle):
    """Navy background cover slide with gold accent bar."""
    _fill_bg(c, C_PRIMARY)

    # Gold accent bar at top
    c.setFillColor(C_ACCENT)
    c.rect(0, H - 40, W, 40, fill=1, stroke=0)

    # Secondary color thin line just below
    c.setFillColor(C_SECONDARY)
    c.rect(0, H - 44, W, 4, fill=1, stroke=0)

    # Title — centered in upper region
    draw_wrapped_text(
        c, title,
        MARGIN, 350, CONTENT_WIDTH, 400,
        BRAND["font_heading"], 64, C_TEXT_LIGHT, "center", leading=74,
    )

    # Subtitle — gold, below title
    if subtitle:
        draw_wrapped_text(
            c, subtitle,
            MARGIN, 250, CONTENT_WIDTH, 100,
            BRAND["font_body"], 28, C_ACCENT, "center",
        )

    # Author footer — white on navy
    draw_wrapped_text(
        c,
        f"{BRAND['author_name']}  \u00b7  {BRAND['author_business']}",
        MARGIN, 50, CONTENT_WIDTH, 40,
        BRAND["font_body"], 16, Color(1, 1, 1, 0.7), "center",
    )

    c.showPage()


def render_cta_slide(c, cta_text):
    """Call-to-action closing slide with navy background."""
    _fill_bg(c, C_PRIMARY)

    # Gold accent bar at top
    c.setFillColor(C_ACCENT)
    c.rect(0, H - 40, W, 40, fill=1, stroke=0)

    # Secondary thin line
    c.setFillColor(C_SECONDARY)
    c.rect(0, H - 44, W, 4, fill=1, stroke=0)

    # Author name — large
    draw_wrapped_text(
        c, BRAND["author_name"],
        MARGIN, 700, CONTENT_WIDTH, 60,
        BRAND["font_heading"], 48, C_TEXT_LIGHT, "center",
    )

    # CPRW title — gold
    draw_wrapped_text(
        c, BRAND["author_title"],
        MARGIN, 645, CONTENT_WIDTH, 40,
        BRAND["font_body"], 24, C_ACCENT, "center",
    )

    # Business name
    draw_wrapped_text(
        c, BRAND["author_business"],
        MARGIN, 595, CONTENT_WIDTH, 35,
        BRAND["font_body"], 22, C_TEXT_LIGHT, "center",
    )

    # URL — teal
    draw_wrapped_text(
        c, BRAND["author_url"],
        MARGIN, 550, CONTENT_WIDTH, 35,
        BRAND["font_body"], 20, C_SECONDARY, "center",
    )

    # Divider
    draw_accent_line(c, 500, 0.5)

    # CTA box — secondary color rounded rectangle
    box_x, box_y, box_w, box_h = 120, 280, 840, 180
    _draw_round_rect(c, box_x, box_y, box_w, box_h, 20, C_SECONDARY)

    # CTA text inside box
    draw_wrapped_text(
        c, cta_text,
        box_x + 30, box_y + 20, box_w - 60, box_h - 40,
        BRAND["font_heading"], 28, C_TEXT_LIGHT, "center",
    )

    c.showPage()


def render_tip_slide(c, number, headline, body, total_tips):
    """Single tip slide with large watermark number."""
    # Alternating background
    bg = C_BG if number % 2 == 1 else C_BG_ALT
    _fill_bg(c, bg)

    # Large watermark number — teal at 15% opacity
    c.saveState()
    c.setFillColor(_alpha(BRAND["secondary"], 0.15))
    c.setFont(BRAND["font_heading"], 120)
    num_text = str(number)
    num_w = c.stringWidth(num_text, BRAND["font_heading"], 120)
    c.drawString((W - num_w) / 2, 730, num_text)
    c.restoreState()

    # "of N" label below number
    c.saveState()
    c.setFillColor(_alpha(BRAND["text_muted"], 0.30))
    c.setFont(BRAND["font_body"], 24)
    of_text = f"of {total_tips}"
    of_w = c.stringWidth(of_text, BRAND["font_body"], 24)
    c.drawString((W - of_w) / 2, 700, of_text)
    c.restoreState()

    # Headline — dark, centered
    draw_wrapped_text(
        c, headline,
        MARGIN, 560, CONTENT_WIDTH, 110,
        BRAND["font_heading"], 38, C_TEXT_DARK, "center",
    )

    # Body — muted, centered
    draw_wrapped_text(
        c, body,
        MARGIN, 300, CONTENT_WIDTH, 220,
        BRAND["font_body"], 26, C_TEXT_MUTED, "center", leading=36,
    )

    draw_footer(c)
    c.showPage()


def render_beforeafter_slide(c, before_text, after_text, note=None):
    """Before/After comparison slide."""
    _fill_bg(c, C_BG)

    # --- BEFORE section ---
    # Label with X marker
    try:
        before_label = "\u2717 BEFORE"
    except Exception:
        before_label = "X BEFORE"

    draw_wrapped_text(
        c, before_label,
        MARGIN, 910, CONTENT_WIDTH, 30,
        BRAND["font_heading"], 22, C_NEGATIVE, "left",
    )

    # Light-red rounded box
    box_x, box_w, box_h, box_r = MARGIN, CONTENT_WIDTH, 210, 16
    before_box_y = 690
    _draw_round_rect(c, box_x, before_box_y, box_w, box_h, box_r, C_LIGHT_RED)

    # Before text inside box
    draw_wrapped_text(
        c, before_text,
        box_x + 20, before_box_y + 20, box_w - 40, box_h - 40,
        BRAND["font_body"], 24, C_TEXT_DARK, "left", leading=34,
    )

    # Divider between sections
    draw_accent_line(c, 650, 0.4)

    # --- AFTER section ---
    try:
        after_label = "\u2713 AFTER"
    except Exception:
        after_label = "> AFTER"

    draw_wrapped_text(
        c, after_label,
        MARGIN, 600, CONTENT_WIDTH, 30,
        BRAND["font_heading"], 22, C_POSITIVE, "left",
    )

    # Light-green rounded box
    after_box_y = 380
    _draw_round_rect(c, box_x, after_box_y, box_w, box_h, box_r, C_LIGHT_GREEN)

    # After text inside box
    draw_wrapped_text(
        c, after_text,
        box_x + 20, after_box_y + 20, box_w - 40, box_h - 40,
        BRAND["font_body"], 24, C_TEXT_DARK, "left", leading=34,
    )

    # Optional note
    if note:
        draw_wrapped_text(
            c, note,
            MARGIN, 280, CONTENT_WIDTH, 60,
            BRAND["font_accent"], 20, C_TEXT_MUTED, "center",
        )

    draw_footer(c)
    c.showPage()


def render_myth_slide(c, number, myth_text, reality_text):
    """Myth vs Reality slide with pill divider."""
    # Alternating background
    bg = C_BG if number % 2 == 1 else C_BG_ALT
    _fill_bg(c, bg)

    # "MYTH #N" header — red, centered
    draw_wrapped_text(
        c, f"MYTH #{number}",
        MARGIN, 890, CONTENT_WIDTH, 35,
        BRAND["font_heading"], 22, C_NEGATIVE, "center",
    )

    # Myth text in curly quotes, italic
    quoted_myth = f"\u201c{myth_text}\u201d"
    draw_wrapped_text(
        c, quoted_myth,
        MARGIN, 660, CONTENT_WIDTH, 210,
        BRAND["font_accent"], 28, C_TEXT_DARK, "center", leading=38,
    )

    # Divider line at y=620
    draw_accent_line(c, 620, 0.5)

    # "REALITY" pill label — green rounded rect with white text
    pill_text = "REALITY"
    pill_font = BRAND["font_heading"]
    pill_size = 18
    c.saveState()
    pill_w = c.stringWidth(pill_text, pill_font, pill_size) + 30
    pill_h = 30
    pill_x = (W - pill_w) / 2
    pill_y = 608
    _draw_round_rect(c, pill_x, pill_y, pill_w, pill_h, pill_h / 2, C_POSITIVE)
    c.setFillColor(C_TEXT_LIGHT)
    c.setFont(pill_font, pill_size)
    text_x = pill_x + 15
    text_y = pill_y + 8
    c.drawString(text_x, text_y, pill_text)
    c.restoreState()

    # Reality text
    draw_wrapped_text(
        c, reality_text,
        MARGIN, 370, CONTENT_WIDTH, 210,
        BRAND["font_body"], 24, C_TEXT_DARK, "center", leading=34,
    )

    draw_footer(c)
    c.showPage()


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def render_carousel(parsed_content, template_type, output_path=None):
    """Render a full carousel PDF from parsed content.

    Args:
        parsed_content: dict from engine.parse_carousel_content()
            Must contain: title, slides, cta
            Optional: subtitle
        template_type: "tips", "beforeafter", or "mythreality"
        output_path: optional path for the PDF; auto-generated if None

    Returns:
        dict with success, path, file_size, page_count
    """
    # Validate input
    if "error" in parsed_content:
        return {"success": False, "error": parsed_content["error"]}

    title = parsed_content.get("title")
    subtitle = parsed_content.get("subtitle")
    slides = parsed_content.get("slides", [])
    cta = parsed_content.get("cta", "Follow for more career strategy")

    if not title or not slides:
        return {"success": False, "error": "Missing title or slides in content"}

    if template_type not in ("tips", "beforeafter", "mythreality"):
        return {"success": False, "error": f"Unknown template_type: {template_type}"}

    # Determine output path
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = int(time.time())
        filename = f"carousel_{template_type}_{timestamp}.pdf"
        output_path = os.path.join(OUTPUT_DIR, filename)

    # Create canvas
    pdf = canvas.Canvas(output_path, pagesize=(W, H))
    pdf.setTitle(title)

    # Cover slide
    render_cover_slide(pdf, title, subtitle)

    # Content slides
    if template_type == "tips":
        total = len(slides)
        for slide in slides:
            render_tip_slide(
                pdf,
                slide["number"],
                slide["headline"],
                slide["body"],
                total,
            )
    elif template_type == "beforeafter":
        for slide in slides:
            render_beforeafter_slide(
                pdf,
                slide["before"],
                slide["after"],
                slide.get("note"),
            )
    elif template_type == "mythreality":
        for slide in slides:
            render_myth_slide(
                pdf,
                slide["number"],
                slide["myth"],
                slide["reality"],
            )

    # CTA slide
    render_cta_slide(pdf, cta)

    # Save
    pdf.save()

    file_size = os.path.getsize(output_path)
    # page_count = cover + content slides + CTA
    page_count = 1 + len(slides) + 1

    return {
        "success": True,
        "path": output_path,
        "file_size": file_size,
        "page_count": page_count,
    }
