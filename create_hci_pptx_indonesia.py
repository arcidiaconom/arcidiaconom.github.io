#!/usr/bin/env python3
"""
Create Indonesia HCI+ PowerPoint with nested bubble/circle charts.
Compares Indonesia vs EAP regional average for HCI+, Health, Education, Employment.
Style: concentric circles — light blue (potential), orange ring (EAP avg), dark blue (Indonesia).
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import math

# ── Colors ───────────────────────────────────────────────────────────────────
PRIMARY       = RGBColor(0x00, 0x2B, 0x49)    # Deep navy (header bg)
IDN_BLUE      = RGBColor(0x00, 0x3F, 0x72)    # Indonesia dark blue (filled circle)
IDN_BLUE_LBL  = RGBColor(0xCC, 0xDD, 0xEE)    # Label on dark circle
EAP_ORANGE    = RGBColor(0xE8, 0x7D, 0x1E)    # EAP average (orange ring)
POTENTIAL_BG  = RGBColor(0xC6, 0xD8, 0xE8)    # Light blue (potential circle)
LIGHT_BG      = RGBColor(0xF7, 0xF8, 0xFA)    # Slide background
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT      = RGBColor(0x1A, 0x1A, 0x2E)
MEDIUM_GRAY   = RGBColor(0x7A, 0x7A, 0x8C)
TEAL          = RGBColor(0x00, 0x88, 0x9E)

# Pillar accent colors for header strips
HEALTH_ACCENT  = RGBColor(0x2B, 0x4C, 0x7E)
EDUC_ACCENT    = RGBColor(0xD4, 0x53, 0x3B)
EMPLOY_ACCENT  = RGBColor(0x4E, 0x9A, 0x51)

# ── Presentation Setup ───────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)


def shape_rect(slide, left, top, width, height, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    return s


def shape_rounded(slide, left, top, width, height, fill):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    return s


def text_box(slide, left, top, width, height, text, size=12,
             color=DARK_TEXT, bold=False, align=PP_ALIGN.LEFT,
             font="Calibri", anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    tf.vertical_anchor = anchor
    return tb


def add_footer(slide, num):
    shape_rect(slide, Inches(0), Inches(7.0), Inches(13.333), Inches(0.5), PRIMARY)
    text_box(slide, Inches(0.6), Inches(7.07), Inches(6), Inches(0.35),
             "Source: World Bank Human Capital Index Plus (HCI+) 2025",
             size=8, color=RGBColor(0xAA, 0xBB, 0xCC), font="Calibri")
    text_box(slide, Inches(10), Inches(7.07), Inches(2.5), Inches(0.35),
             "humancapital.worldbank.org/hciplus", size=8,
             color=TEAL, align=PP_ALIGN.RIGHT)
    text_box(slide, Inches(12.6), Inches(7.07), Inches(0.5), Inches(0.35),
             str(num), size=8, color=WHITE, align=PP_ALIGN.RIGHT)


def draw_nested_bubbles(slide, cx, cy, max_radius, potential_val, eap_val, idn_val,
                         max_score, label_potential="Potential Productivity",
                         label_eap="East Asia & Pacific HCI+",
                         label_idn="Indonesia HCI+"):
    """Draw three concentric circles: potential (light blue), EAP (orange ring), Indonesia (dark blue)."""

    # Radii proportional to value (use sqrt for area-proportional scaling)
    r_potential = max_radius
    r_eap = max_radius * math.sqrt(eap_val / max_score)
    r_idn = max_radius * math.sqrt(idn_val / max_score)

    # 1. Potential circle (light blue filled)
    pot_size = int(2 * r_potential)
    s_pot = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        int(cx - r_potential), int(cy - r_potential),
        pot_size, pot_size
    )
    s_pot.fill.solid()
    s_pot.fill.fore_color.rgb = POTENTIAL_BG
    s_pot.line.fill.background()

    # 2. EAP circle (orange ring — no fill, thick orange border)
    eap_size = int(2 * r_eap)
    s_eap = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        int(cx - r_eap), int(cy - r_eap),
        eap_size, eap_size
    )
    s_eap.fill.background()
    s_eap.line.color.rgb = EAP_ORANGE
    s_eap.line.width = Pt(3)

    # 3. Indonesia circle (dark blue filled)
    idn_size = int(2 * r_idn)
    s_idn = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        int(cx - r_idn), int(cy - r_idn),
        idn_size, idn_size
    )
    s_idn.fill.solid()
    s_idn.fill.fore_color.rgb = IDN_BLUE
    s_idn.line.fill.background()

    # Value labels
    # EAP value — placed just above the EAP ring, top-center
    eap_label_y = int(cy - r_eap) - Inches(0.15)
    text_box(slide, int(cx - Inches(0.5)), eap_label_y, Inches(1.0), Inches(0.3),
             str(int(round(eap_val))), size=18, color=EAP_ORANGE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)

    # Indonesia value — centered inside
    text_box(slide, int(cx - Inches(0.5)), int(cy - Inches(0.2)), Inches(1.0), Inches(0.4),
             str(int(round(idn_val))), size=22, color=IDN_BLUE_LBL, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def draw_bubble_slide(slide, title, subtitle, score_label, accent_color,
                       potential_val, eap_val, idn_val, max_score,
                       idn_detail_label, eap_detail_label,
                       insight_text, slide_num):
    """Create a full slide with nested bubble comparison."""
    shape_rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

    # Header
    shape_rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
    shape_rect(slide, Inches(0), Inches(1.0), Inches(13.333), Pt(4), accent_color)
    text_box(slide, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
             title, size=24, color=WHITE, bold=True,
             font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
    text_box(slide, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
             score_label, size=22, color=accent_color, bold=True,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

    # Subtitle
    text_box(slide, Inches(0.6), Inches(1.35), Inches(8), Inches(0.4),
             subtitle, size=11, color=MEDIUM_GRAY)

    # Left panel — nested circles
    chart_panel = shape_rounded(slide, Inches(0.5), Inches(2.0), Inches(7.5), Inches(4.7), WHITE)

    # Title above bubble
    text_box(slide, Inches(0.8), Inches(2.15), Inches(4), Inches(0.3),
             "INDONESIA vs EAP AVERAGE", size=11, color=MEDIUM_GRAY, bold=True)
    shape_rect(slide, Inches(0.8), Inches(2.45), Inches(2), Pt(3), accent_color)

    # Draw nested circles (centered in left panel)
    bubble_cx = Inches(4.25)
    bubble_cy = Inches(4.5)
    max_r = Inches(1.85)
    draw_nested_bubbles(slide, bubble_cx, bubble_cy, max_r,
                         potential_val, eap_val, idn_val, max_score)

    # Legend (bottom of left panel)
    legend_y = Inches(6.15)
    # EAP orange swatch
    sw1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), legend_y, Inches(0.25), Inches(0.15))
    sw1.fill.solid()
    sw1.fill.fore_color.rgb = EAP_ORANGE
    sw1.line.fill.background()
    text_box(slide, Inches(1.55), legend_y - Inches(0.02), Inches(2.5), Inches(0.2),
             "East Asia & Pacific HCI+", size=8, color=DARK_TEXT)

    # Indonesia blue swatch
    sw2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.0), legend_y, Inches(0.25), Inches(0.15))
    sw2.fill.solid()
    sw2.fill.fore_color.rgb = IDN_BLUE
    sw2.line.fill.background()
    text_box(slide, Inches(4.35), legend_y - Inches(0.02), Inches(2.0), Inches(0.2),
             "Indonesia HCI+", size=8, color=DARK_TEXT)

    # Potential swatch
    sw3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.0), legend_y, Inches(0.25), Inches(0.15))
    sw3.fill.solid()
    sw3.fill.fore_color.rgb = POTENTIAL_BG
    sw3.line.fill.background()
    text_box(slide, Inches(6.35), legend_y - Inches(0.02), Inches(2.0), Inches(0.2),
             "Potential Productivity", size=8, color=DARK_TEXT)

    # Right panel — Details & Insight
    detail_panel = shape_rounded(slide, Inches(8.3), Inches(2.0), Inches(4.5), Inches(4.7), WHITE)
    shape_rect(slide, Inches(8.3), Inches(2.0), Pt(5), Inches(4.7), accent_color)

    text_box(slide, Inches(8.6), Inches(2.2), Inches(4), Inches(0.25),
             "COMPARISON", size=11, color=accent_color, bold=True)

    # Indonesia stats
    stats = [
        ("Indonesia", f"{idn_val:.1f}", IDN_BLUE),
        ("EAP Average", f"{eap_val:.1f}", EAP_ORANGE),
        ("Maximum Potential", f"{max_score:.0f}", MEDIUM_GRAY),
        ("Gap to EAP Avg", f"{eap_val - idn_val:+.1f}", RGBColor(0xC0, 0x39, 0x2B)),
        ("% of Potential", f"{idn_val/max_score*100:.0f}%", DARK_TEXT),
    ]

    for j, (label, value, color) in enumerate(stats):
        sy = Inches(2.6) + Inches(j * 0.55)
        text_box(slide, Inches(8.6), sy, Inches(2.2), Inches(0.22),
                 label, size=10, color=MEDIUM_GRAY)
        text_box(slide, Inches(11.0), sy, Inches(1.5), Inches(0.22),
                 value, size=13, color=color, bold=True, align=PP_ALIGN.RIGHT)
        if j < len(stats) - 1:
            shape_rect(slide, Inches(8.6), sy + Inches(0.35), Inches(3.9), Pt(1),
                       RGBColor(0xEE, 0xEE, 0xEE))

    # Detail labels
    text_box(slide, Inches(8.6), Inches(5.4), Inches(4), Inches(0.25),
             "KEY INSIGHT", size=10, color=accent_color, bold=True)
    text_box(slide, Inches(8.6), Inches(5.7), Inches(3.9), Inches(0.9),
             insight_text, size=9, color=DARK_TEXT)

    add_footer(slide, slide_num)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s1, Inches(0), Inches(0), Inches(13.333), Inches(7.5), PRIMARY)
shape_rect(s1, Inches(0), Inches(6.0), Inches(13.333), Inches(1.5),
           RGBColor(0x00, 0x1F, 0x38))

# Accent line
shape_rect(s1, Inches(1.3), Inches(2.0), Inches(1.8), Pt(4), EAP_ORANGE)

# Title
text_box(s1, Inches(1.3), Inches(2.3), Inches(7), Inches(1.2),
         "Human Capital\nIndex Plus", size=48, color=WHITE, bold=True,
         font="Calibri Light")
text_box(s1, Inches(1.3), Inches(3.9), Inches(4), Inches(0.5),
         "HCI+  |  2025", size=22, color=EAP_ORANGE, bold=True)
text_box(s1, Inches(1.3), Inches(4.7), Inches(4), Inches(0.7),
         "INDONESIA", size=40, color=WHITE, bold=True)
text_box(s1, Inches(1.3), Inches(5.8), Inches(6), Inches(0.7),
         "Comparing Indonesia with East Asia & Pacific regional averages\nacross health, education, and employment dimensions",
         size=13, color=RGBColor(0x88, 0x99, 0xAA))

# Tags
tag_y = Inches(6.6)
t1 = shape_rounded(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32),
         "East Asia & Pacific", size=9, color=EAP_ORANGE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
t2 = shape_rounded(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32),
         "Upper Middle Income", size=9, color=EAP_ORANGE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Right side — Score panel
score_panel = shape_rounded(s1, Inches(8.8), Inches(1.5), Inches(3.8), Inches(5.0),
                            RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(8.8), Inches(1.7), Inches(3.8), Inches(0.35),
         "OVERALL HCI+ SCORE", size=10, color=EAP_ORANGE, bold=True, align=PP_ALIGN.CENTER)
text_box(s1, Inches(8.8), Inches(2.4), Inches(3.8), Inches(1.6),
         "175.4", size=72, color=WHITE, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, font="Calibri Light")
text_box(s1, Inches(8.8), Inches(4.0), Inches(3.8), Inches(0.3),
         "out of 325", size=12, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)

# Component mini-bars
comp_data = [
    ("Health", 40.7, 50, HEALTH_ACCENT),
    ("Education", 96.5, 180, EDUC_ACCENT),
    ("Employment", 38.1, 70, EMPLOY_ACCENT),
]

bar_start_y = Inches(4.6)
for i, (name, val, max_v, color) in enumerate(comp_data):
    y = bar_start_y + Inches(i * 0.55)
    text_box(s1, Inches(9.1), y, Inches(1.2), Inches(0.22),
             name, size=9, color=RGBColor(0xAA, 0xBB, 0xCC))
    text_box(s1, Inches(11.7), y, Inches(0.7), Inches(0.22),
             f"{val:.1f}", size=9, color=color, bold=True, align=PP_ALIGN.RIGHT)
    bar_y = y + Inches(0.22)
    shape_rounded(s1, Inches(9.1), bar_y, Inches(3.2), Inches(0.1), RGBColor(0x00, 0x2B, 0x49))
    fill_w = max(Inches(0.1), int(Inches(3.2) * (val / max_v)))
    shape_rounded(s1, Inches(9.1), bar_y, fill_w, Inches(0.1), color)

text_box(s1, Inches(9.1), Inches(6.05), Inches(3.2), Inches(0.25),
         "Ranked #17 in EAP  |  #93 Globally",
         size=9, color=EAP_ORANGE, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — OVERALL HCI+ (nested bubbles)
# ══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(prs.slide_layouts[6])
draw_bubble_slide(
    slide=s2,
    title="Indonesia  |  Overall HCI+ Score",
    subtitle="Indonesia's overall human capital score compared with the East Asia & Pacific regional average.",
    score_label="175.4 / 325",
    accent_color=IDN_BLUE,
    potential_val=325, eap_val=201.7, idn_val=175.4, max_score=325,
    idn_detail_label="Indonesia HCI+", eap_detail_label="EAP Average",
    insight_text=(
        "Indonesia scores 175.4 on the HCI+, below the EAP regional "
        "average of 201.7 (a gap of 26.3 points). Indonesia realizes "
        "54% of its potential productivity. The largest gap with the "
        "EAP average is in education (21.6 points below), followed by "
        "health (2.1 points) and employment (2.6 points)."
    ),
    slide_num=1,
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — HEALTH COMPONENT (nested bubbles)
# ══════════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(prs.slide_layouts[6])
draw_bubble_slide(
    slide=s3,
    title="Health Component  |  Indonesia vs EAP",
    subtitle="Health captures adult survival (ages 15-60) and freedom from childhood stunting.",
    score_label="40.7 / 50",
    accent_color=HEALTH_ACCENT,
    potential_val=50, eap_val=42.8, idn_val=40.7, max_score=50,
    idn_detail_label="Indonesia Health", eap_detail_label="EAP Health Avg",
    insight_text=(
        "Indonesia's health score of 40.7 is close to the EAP average "
        "of 42.8 (gap of 2.1 points). Adult survival stands at ~81%, "
        "and child stunting (~21.6%) remains a key challenge. "
        "The EAP best performer (Korea) scores 48.8, indicating "
        "room for improvement especially in nutrition outcomes."
    ),
    slide_num=2,
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — EDUCATION COMPONENT (nested bubbles)
# ══════════════════════════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(prs.slide_layouts[6])
draw_bubble_slide(
    slide=s4,
    title="Education Component  |  Indonesia vs EAP",
    subtitle="Education captures learning quality, years of schooling, pre-primary education, and tertiary enrollment.",
    score_label="96.5 / 180",
    accent_color=EDUC_ACCENT,
    potential_val=180, eap_val=118.1, idn_val=96.5, max_score=180,
    idn_detail_label="Indonesia Education", eap_detail_label="EAP Education Avg",
    insight_text=(
        "Education is Indonesia's largest gap with the EAP average — "
        "scoring 96.5 vs the regional average of 118.1 (a gap of 21.6 "
        "points). Indonesia realizes only 54% of education potential. "
        "Key areas for improvement include learning quality (HLO ~392 "
        "vs EAP avg 436) and tertiary enrollment. The EAP best "
        "performer (Singapore) scores 179.4."
    ),
    slide_num=3,
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — EMPLOYMENT COMPONENT (nested bubbles)
# ══════════════════════════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(prs.slide_layouts[6])
draw_bubble_slide(
    slide=s5,
    title="Employment Component  |  Indonesia vs EAP",
    subtitle="Employment captures labor force participation, wage employment, and skill accumulation for youth and working-age populations.",
    score_label="38.1 / 70",
    accent_color=EMPLOY_ACCENT,
    potential_val=70, eap_val=40.7, idn_val=38.1, max_score=70,
    idn_detail_label="Indonesia Employment", eap_detail_label="EAP Employment Avg",
    insight_text=(
        "Indonesia's employment score of 38.1 is close to the EAP "
        "average of 40.7 (gap of 2.6 points). Indonesia has a notable "
        "gender gap in employment (+33.4 favoring males). Youth labor "
        "force participation and wage employment shares offer room for "
        "growth. The EAP best performer (New Zealand) scores 61.5."
    ),
    slide_num=4,
)


# ── Save ─────────────────────────────────────────────────────────────────────
output_path = "/home/user/arcidiaconom.github.io/Indonesia_HCI_Plus_2025.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
