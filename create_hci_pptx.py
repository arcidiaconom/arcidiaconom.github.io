#!/usr/bin/env python3
"""
Create a professional 5-slide PowerPoint presentation for Kenya's HCI+ data.
World Bank Human Capital Index Plus (HCI+) 2025.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData
import math

# ── Color Palette ──────────────────────────────────────────────────────────────
# Professional palette inspired by World Bank branding
PRIMARY      = RGBColor(0x00, 0x2B, 0x5C)   # Deep navy
ACCENT_1     = RGBColor(0x00, 0x96, 0xD6)   # Bright blue
ACCENT_2     = RGBColor(0x00, 0xA8, 0x5A)   # Green
ACCENT_3     = RGBColor(0xF2, 0xA9, 0x00)   # Amber/gold
ACCENT_4     = RGBColor(0xE8, 0x4D, 0x3D)   # Coral red
LIGHT_BG     = RGBColor(0xF5, 0xF7, 0xFA)   # Very light blue-gray
MEDIUM_GRAY  = RGBColor(0x8C, 0x8C, 0x8C)   # Medium gray
DARK_TEXT     = RGBColor(0x1A, 0x1A, 0x2E)   # Near-black
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_ACCENT = RGBColor(0xE8, 0xF4, 0xFD)   # Very light blue
DIVIDER      = RGBColor(0xD0, 0xD5, 0xDD)   # Light divider gray

# ── Kenya HCI+ Data ───────────────────────────────────────────────────────────
KENYA = {
    "country": "Kenya",
    "region": "Sub-Saharan Africa",
    "income_group": "Lower Middle Income",
    "hci_plus_total": 170.8,
    "hci_plus_max": 325,
    # Components (Both genders)
    "health": 36.6,
    "education": 109.0,
    "employment": 25.3,
    # Gender breakdown
    "hci_female": 166.3,
    "hci_male": 175.6,
    "health_female": 38.3,
    "health_male": 35.0,
    "education_female": 109.4,
    "education_male": 108.5,
    "employment_female": 18.6,
    "employment_male": 32.1,
    # Subcomponents
    "adult_survival": 0.684,
    "not_stunted": 0.824,
    "learning_outcomes": 418.1,
    "expected_years_school": 11.03,
    "tertiary_enrollment": 0.203,
    "lfp_youth": 0.396,
    "lfp_working_age": 0.780,
    "wage_employment_youth": 0.388,
    "wage_employment_working_age": 0.356,
    "pre_primary_years": 0.616,
}

# ── Presentation Setup ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SLIDE_W = prs.slide_width
SLIDE_H = prs.slide_height


def add_shape(slide, left, top, width, height, fill_color, line_color=None):
    """Add a rectangle shape with fill color."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color):
    """Add a rounded rectangle shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=12,
                 color=DARK_TEXT, bold=False, alignment=PP_ALIGN.LEFT,
                 font_name="Calibri", anchor=MSO_ANCHOR.TOP):
    """Add a text box with formatted text."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    tf.vertical_anchor = anchor
    return txBox


def add_footer(slide):
    """Add consistent footer bar."""
    # Footer bar
    add_shape(slide, Inches(0), Inches(7.0), SLIDE_W, Inches(0.5), PRIMARY)
    add_text_box(slide, Inches(0.5), Inches(7.05), Inches(6), Inches(0.4),
                 "Source: World Bank Human Capital Index Plus (HCI+) 2025",
                 font_size=9, color=WHITE, font_name="Calibri")
    add_text_box(slide, Inches(9), Inches(7.05), Inches(4), Inches(0.4),
                 "humancapital.worldbank.org/hciplus",
                 font_size=9, color=ACCENT_1, alignment=PP_ALIGN.RIGHT, font_name="Calibri")


def add_slide_number(slide, num):
    """Add page number."""
    add_text_box(slide, Inches(12.5), Inches(7.05), Inches(0.7), Inches(0.4),
                 str(num), font_size=9, color=WHITE, alignment=PP_ALIGN.RIGHT)


def add_thin_accent_line(slide, left, top, width, color=ACCENT_1):
    """Add a thin decorative line."""
    shape = add_shape(slide, left, top, width, Pt(3), color)
    return shape


def create_metric_card(slide, left, top, width, height, label, value, color=ACCENT_1):
    """Create a styled metric card with label and value."""
    card = add_rounded_rect(slide, left, top, width, height, WHITE)
    card.shadow.inherit = False

    # Accent bar at top of card
    add_shape(slide, left + Inches(0.05), top + Inches(0.05), width - Inches(0.1), Pt(4), color)

    # Value
    add_text_box(slide, left + Inches(0.15), top + Inches(0.25), width - Inches(0.3), Inches(0.6),
                 str(value), font_size=28, color=color, bold=True,
                 alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Label
    add_text_box(slide, left + Inches(0.15), top + height - Inches(0.55), width - Inches(0.3), Inches(0.45),
                 label, font_size=10, color=MEDIUM_GRAY,
                 alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

# Full-width navy background
add_shape(slide1, Inches(0), Inches(0), SLIDE_W, SLIDE_H, PRIMARY)

# Decorative diagonal accent
points = [
    (Inches(0), Inches(4.5)),
    (Inches(0), SLIDE_H),
    (Inches(6), SLIDE_H),
]
# Use a large accent shape instead
add_shape(slide1, Inches(0), Inches(5.5), Inches(13.333), Inches(2), RGBColor(0x00, 0x1F, 0x45))

# Accent line
add_shape(slide1, Inches(1.5), Inches(2.3), Inches(2), Pt(4), ACCENT_1)

# Title text
add_text_box(slide1, Inches(1.5), Inches(2.6), Inches(10), Inches(1.2),
             "Human Capital Index Plus", font_size=44, color=WHITE, bold=True,
             font_name="Calibri Light")

# HCI+ badge
add_text_box(slide1, Inches(1.5), Inches(3.7), Inches(10), Inches(0.6),
             "HCI+  |  2025", font_size=24, color=ACCENT_1, bold=True,
             font_name="Calibri")

# Country name
add_text_box(slide1, Inches(1.5), Inches(4.5), Inches(10), Inches(0.8),
             "KENYA", font_size=36, color=WHITE, bold=True,
             font_name="Calibri")

# Subtitle
add_text_box(slide1, Inches(1.5), Inches(5.8), Inches(8), Inches(0.8),
             "Measuring human capital from birth through working age\nacross health, education, and employment dimensions",
             font_size=14, color=RGBColor(0xAA, 0xBB, 0xCC), font_name="Calibri")

# Region and income tags
tag_y = Inches(6.7)
tag1 = add_rounded_rect(slide1, Inches(1.5), tag_y, Inches(2.5), Inches(0.35), RGBColor(0x00, 0x3D, 0x6B))
add_text_box(slide1, Inches(1.5), tag_y, Inches(2.5), Inches(0.35),
             "Sub-Saharan Africa", font_size=10, color=ACCENT_1,
             alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

tag2 = add_rounded_rect(slide1, Inches(4.2), tag_y, Inches(2.5), Inches(0.35), RGBColor(0x00, 0x3D, 0x6B))
add_text_box(slide1, Inches(4.2), tag_y, Inches(2.5), Inches(0.35),
             "Lower Middle Income", font_size=10, color=ACCENT_1,
             alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Score highlight on the right
score_bg = add_rounded_rect(slide1, Inches(9.5), Inches(2.5), Inches(2.8), Inches(3.5),
                             RGBColor(0x00, 0x3D, 0x6B))
add_text_box(slide1, Inches(9.5), Inches(2.7), Inches(2.8), Inches(0.4),
             "OVERALL SCORE", font_size=11, color=ACCENT_1, bold=True,
             alignment=PP_ALIGN.CENTER, font_name="Calibri")

add_text_box(slide1, Inches(9.5), Inches(3.2), Inches(2.8), Inches(1.5),
             "170.8", font_size=64, color=WHITE, bold=True,
             alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font_name="Calibri Light")

add_text_box(slide1, Inches(9.5), Inches(4.8), Inches(2.8), Inches(0.4),
             "out of 325", font_size=13, color=MEDIUM_GRAY,
             alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Percentage interpretation
pct = round(KENYA["hci_plus_total"] / KENYA["hci_plus_max"] * 100, 1)
add_text_box(slide1, Inches(9.5), Inches(5.2), Inches(2.8), Inches(0.4),
             f"{pct}% of potential", font_size=12, color=ACCENT_3,
             alignment=PP_ALIGN.CENTER, bold=True, font_name="Calibri")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — OVERALL HCI+ SCORE & COMPONENT BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
slide2 = prs.slides.add_slide(prs.slide_layouts[6])

# Light background
add_shape(slide2, Inches(0), Inches(0), SLIDE_W, SLIDE_H, LIGHT_BG)

# Top header bar
add_shape(slide2, Inches(0), Inches(0), SLIDE_W, Inches(1.1), PRIMARY)
add_text_box(slide2, Inches(0.8), Inches(0.2), Inches(8), Inches(0.7),
             "Kenya  |  HCI+ Score Overview", font_size=26, color=WHITE, bold=True,
             font_name="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
add_text_box(slide2, Inches(9), Inches(0.2), Inches(4), Inches(0.7),
             f"Score: 170.8 / 325", font_size=20, color=ACCENT_1, bold=True,
             alignment=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Overall score section
add_text_box(slide2, Inches(0.8), Inches(1.4), Inches(5), Inches(0.4),
             "OVERALL HCI+ COMPOSITION", font_size=12, color=MEDIUM_GRAY, bold=True)
add_thin_accent_line(slide2, Inches(0.8), Inches(1.8), Inches(4))

# Stacked bar chart for composition
chart_data = CategoryChartData()
chart_data.categories = ['Kenya HCI+']
chart_data.add_series('Health (36.6)', (36.6,))
chart_data.add_series('Education (109.0)', (109.0,))
chart_data.add_series('Employment (25.3)', (25.3,))

chart_frame = slide2.shapes.add_chart(
    XL_CHART_TYPE.BAR_STACKED, Inches(0.8), Inches(2.0), Inches(5.5), Inches(1.5),
    chart_data
)
chart = chart_frame.chart
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False
chart.legend.font.size = Pt(10)
chart.legend.font.name = "Calibri"

# Style the chart
plot = chart.plots[0]
plot.gap_width = 80

colors_chart = [ACCENT_2, ACCENT_1, ACCENT_3]
for i, series in enumerate(plot.series):
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = colors_chart[i]

chart.category_axis.visible = False
chart.value_axis.maximum_scale = 325
chart.value_axis.has_title = False
chart.value_axis.major_gridlines.format.line.color.rgb = DIVIDER
chart.value_axis.format.line.color.rgb = DIVIDER

# Component cards
card_y = Inches(3.8)
card_w = Inches(3.7)
card_h = Inches(1.6)

# Health Card
create_metric_card(slide2, Inches(0.8), card_y, card_w, card_h,
                   "HEALTH COMPONENT", "36.6", ACCENT_2)

# Education Card
create_metric_card(slide2, Inches(4.8), card_y, card_w, card_h,
                   "EDUCATION COMPONENT", "109.0", ACCENT_1)

# Employment Card
create_metric_card(slide2, Inches(8.8), card_y, card_w, card_h,
                   "EMPLOYMENT COMPONENT", "25.3", ACCENT_3)

# Gender comparison section
add_text_box(slide2, Inches(0.8), Inches(5.7), Inches(5), Inches(0.4),
             "GENDER COMPARISON", font_size=12, color=MEDIUM_GRAY, bold=True)
add_thin_accent_line(slide2, Inches(0.8), Inches(6.05), Inches(4))

# Gender chart
gender_data = CategoryChartData()
gender_data.categories = ['Health', 'Education', 'Employment', 'Total HCI+']
gender_data.add_series('Female', (38.3, 109.4, 18.6, 166.3))
gender_data.add_series('Male', (35.0, 108.5, 32.1, 175.6))

gender_chart_frame = slide2.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.8), Inches(6.15), Inches(11.5), Inches(0.7),
    gender_data
)
gc = gender_chart_frame.chart
gc.has_legend = True
gc.legend.position = XL_LEGEND_POSITION.RIGHT
gc.legend.font.size = Pt(9)
gc.legend.font.name = "Calibri"

gplot = gc.plots[0]
gplot.gap_width = 80
gplot.series[0].format.fill.solid()
gplot.series[0].format.fill.fore_color.rgb = ACCENT_4
gplot.series[1].format.fill.solid()
gplot.series[1].format.fill.fore_color.rgb = ACCENT_1

gc.category_axis.tick_labels.font.size = Pt(9)
gc.category_axis.tick_labels.font.name = "Calibri"
gc.value_axis.visible = False
gc.value_axis.has_major_gridlines = False

# Right side panel - Key insight
insight_bg = add_rounded_rect(slide2, Inches(7), Inches(1.4), Inches(5.5), Inches(2.0), WHITE)
add_shape(slide2, Inches(7), Inches(1.4), Pt(5), Inches(2.0), ACCENT_1)

add_text_box(slide2, Inches(7.3), Inches(1.5), Inches(5), Inches(0.3),
             "KEY INSIGHT", font_size=11, color=ACCENT_1, bold=True)

add_text_box(slide2, Inches(7.3), Inches(1.85), Inches(5), Inches(1.4),
             "Kenya scores 170.8 out of 325 on the HCI+, meaning a child "
             "born today can expect to achieve 52.6% of their potential "
             "human capital. Education is the strongest contributor at 109.0 points, "
             "while employment outcomes (25.3) present the greatest opportunity for improvement.",
             font_size=11, color=DARK_TEXT)

add_footer(slide2)
add_slide_number(slide2, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — HEALTH COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_shape(slide3, Inches(0), Inches(0), SLIDE_W, SLIDE_H, LIGHT_BG)

# Header
add_shape(slide3, Inches(0), Inches(0), SLIDE_W, Inches(1.1), PRIMARY)
add_shape(slide3, Inches(0), Inches(1.1), SLIDE_W, Pt(4), ACCENT_2)
add_text_box(slide3, Inches(0.8), Inches(0.2), Inches(10), Inches(0.7),
             "Health Component", font_size=26, color=WHITE, bold=True,
             font_name="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
add_text_box(slide3, Inches(9), Inches(0.2), Inches(4), Inches(0.7),
             "Score: 36.6", font_size=20, color=ACCENT_2, bold=True,
             alignment=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Description
add_text_box(slide3, Inches(0.8), Inches(1.5), Inches(6), Inches(0.6),
             "Health outcomes reflect a population's ability to survive into productive adulthood "
             "and develop without the burden of childhood malnutrition.",
             font_size=11, color=MEDIUM_GRAY)

# Metric cards row
card_row_y = Inches(2.3)

# Adult Survival Rate
surv_card = add_rounded_rect(slide3, Inches(0.8), card_row_y, Inches(5.5), Inches(2.8), WHITE)
add_shape(slide3, Inches(0.8), card_row_y, Inches(5.5), Pt(4), ACCENT_2)

add_text_box(slide3, Inches(1.1), card_row_y + Inches(0.2), Inches(5), Inches(0.3),
             "ADULT SURVIVAL RATE", font_size=12, color=ACCENT_2, bold=True)
add_text_box(slide3, Inches(1.1), card_row_y + Inches(0.55), Inches(5), Inches(0.4),
             "Probability of surviving from age 15 to 60",
             font_size=10, color=MEDIUM_GRAY)

add_text_box(slide3, Inches(1.1), card_row_y + Inches(1.0), Inches(2.5), Inches(0.8),
             "68.4%", font_size=48, color=ACCENT_2, bold=True, font_name="Calibri Light")

# Gender breakdown for survival
add_text_box(slide3, Inches(3.8), card_row_y + Inches(1.0), Inches(2.2), Inches(0.35),
             "Female: 72.5%", font_size=14, color=ACCENT_4, bold=False)
add_text_box(slide3, Inches(3.8), card_row_y + Inches(1.4), Inches(2.2), Inches(0.35),
             "Male: 64.4%", font_size=14, color=ACCENT_1, bold=False)

# Progress bar for survival
bar_y = card_row_y + Inches(2.0)
add_rounded_rect(slide3, Inches(1.1), bar_y, Inches(5), Inches(0.25), RGBColor(0xE0, 0xE0, 0xE0))
add_rounded_rect(slide3, Inches(1.1), bar_y, Inches(5 * 0.684), Inches(0.25), ACCENT_2)
add_text_box(slide3, Inches(1.1), bar_y + Inches(0.3), Inches(5), Inches(0.2),
             "68.4% survival rate (target: 100%)", font_size=9, color=MEDIUM_GRAY)


# Not Stunted Rate
stunt_card = add_rounded_rect(slide3, Inches(7), card_row_y, Inches(5.5), Inches(2.8), WHITE)
add_shape(slide3, Inches(7), card_row_y, Inches(5.5), Pt(4), ACCENT_2)

add_text_box(slide3, Inches(7.3), card_row_y + Inches(0.2), Inches(5), Inches(0.3),
             "NOT STUNTED RATE", font_size=12, color=ACCENT_2, bold=True)
add_text_box(slide3, Inches(7.3), card_row_y + Inches(0.55), Inches(5), Inches(0.4),
             "Share of children under 5 not stunted",
             font_size=10, color=MEDIUM_GRAY)

add_text_box(slide3, Inches(7.3), card_row_y + Inches(1.0), Inches(2.5), Inches(0.8),
             "82.4%", font_size=48, color=ACCENT_2, bold=True, font_name="Calibri Light")

add_text_box(slide3, Inches(10), card_row_y + Inches(1.0), Inches(2.2), Inches(0.35),
             "Female: 84.4%", font_size=14, color=ACCENT_4, bold=False)
add_text_box(slide3, Inches(10), card_row_y + Inches(1.4), Inches(2.2), Inches(0.35),
             "Male: 80.4%", font_size=14, color=ACCENT_1, bold=False)

# Progress bar
bar_y2 = card_row_y + Inches(2.0)
add_rounded_rect(slide3, Inches(7.3), bar_y2, Inches(5), Inches(0.25), RGBColor(0xE0, 0xE0, 0xE0))
add_rounded_rect(slide3, Inches(7.3), bar_y2, Inches(5 * 0.824), Inches(0.25), ACCENT_2)
add_text_box(slide3, Inches(7.3), bar_y2 + Inches(0.3), Inches(5), Inches(0.2),
             "82.4% not stunted (target: 100%)", font_size=9, color=MEDIUM_GRAY)


# Gender comparison chart
add_text_box(slide3, Inches(0.8), Inches(5.5), Inches(5), Inches(0.3),
             "HEALTH COMPONENT BY GENDER", font_size=12, color=MEDIUM_GRAY, bold=True)
add_thin_accent_line(slide3, Inches(0.8), Inches(5.8), Inches(3), ACCENT_2)

health_gender_data = CategoryChartData()
health_gender_data.categories = ['Health Component Score']
health_gender_data.add_series('Female (38.3)', (38.3,))
health_gender_data.add_series('Male (35.0)', (35.0,))

hg_chart_frame = slide3.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.9), Inches(5.5), Inches(0.9),
    health_gender_data
)
hgc = hg_chart_frame.chart
hgc.has_legend = True
hgc.legend.position = XL_LEGEND_POSITION.RIGHT
hgc.legend.font.size = Pt(9)
hgc.legend.font.name = "Calibri"
hgp = hgc.plots[0]
hgp.gap_width = 60
hgp.series[0].format.fill.solid()
hgp.series[0].format.fill.fore_color.rgb = ACCENT_4
hgp.series[1].format.fill.solid()
hgp.series[1].format.fill.fore_color.rgb = ACCENT_1
hgc.category_axis.visible = False
hgc.value_axis.visible = False
hgc.value_axis.has_major_gridlines = False

# Insight panel
insight = add_rounded_rect(slide3, Inches(7), Inches(5.5), Inches(5.5), Inches(1.3), WHITE)
add_shape(slide3, Inches(7), Inches(5.5), Pt(5), Inches(1.3), ACCENT_2)
add_text_box(slide3, Inches(7.3), Inches(5.6), Inches(5), Inches(0.25),
             "KEY TAKEAWAY", font_size=10, color=ACCENT_2, bold=True)
add_text_box(slide3, Inches(7.3), Inches(5.9), Inches(5), Inches(0.8),
             "Kenya's adult survival rate of 68.4% indicates significant room for improvement. "
             "However, the relatively high not-stunted rate of 82.4% suggests progress in "
             "childhood nutrition. Women have better survival and nutrition outcomes than men.",
             font_size=10, color=DARK_TEXT)

add_footer(slide3)
add_slide_number(slide3, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — EDUCATION COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
add_shape(slide4, Inches(0), Inches(0), SLIDE_W, SLIDE_H, LIGHT_BG)

# Header
add_shape(slide4, Inches(0), Inches(0), SLIDE_W, Inches(1.1), PRIMARY)
add_shape(slide4, Inches(0), Inches(1.1), SLIDE_W, Pt(4), ACCENT_1)
add_text_box(slide4, Inches(0.8), Inches(0.2), Inches(10), Inches(0.7),
             "Education Component", font_size=26, color=WHITE, bold=True,
             font_name="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
add_text_box(slide4, Inches(9), Inches(0.2), Inches(4), Inches(0.7),
             "Score: 109.0", font_size=20, color=ACCENT_1, bold=True,
             alignment=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

add_text_box(slide4, Inches(0.8), Inches(1.5), Inches(8), Inches(0.5),
             "Education captures learning outcomes, years of schooling, pre-primary education, "
             "and tertiary enrollment \u2014 the foundation for human capital accumulation.",
             font_size=11, color=MEDIUM_GRAY)

# Four metric cards
card_w = Inches(2.8)
card_h = Inches(2.6)
card_y = Inches(2.3)
spacing = Inches(0.25)

metrics = [
    ("Expected Years\nof Schooling", "11.03", "years", ACCENT_1),
    ("Harmonized Learning\nOutcomes", "418.1", "HLO score", RGBColor(0x00, 0x7A, 0xB8)),
    ("Pre-Primary\nEducation", "0.62", "LAYS", ACCENT_2),
    ("Tertiary\nEnrollment", "20.3%", "gross rate", ACCENT_3),
]

for i, (label, value, unit, color) in enumerate(metrics):
    x = Inches(0.8) + i * (card_w + spacing)
    card = add_rounded_rect(slide4, x, card_y, card_w, card_h, WHITE)
    add_shape(slide4, x, card_y, card_w, Pt(4), color)

    # Icon circle
    circle = slide4.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(1.0), card_y + Inches(0.3),
                                      Inches(0.6), Inches(0.6))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    add_text_box(slide4, x + Inches(1.0), card_y + Inches(0.3), Inches(0.6), Inches(0.6),
                 ["S", "L", "P", "T"][i], font_size=18, color=WHITE, bold=True,
                 alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Value
    add_text_box(slide4, x + Inches(0.1), card_y + Inches(1.1), card_w - Inches(0.2), Inches(0.6),
                 value, font_size=32, color=color, bold=True,
                 alignment=PP_ALIGN.CENTER, font_name="Calibri Light")

    # Unit
    add_text_box(slide4, x + Inches(0.1), card_y + Inches(1.65), card_w - Inches(0.2), Inches(0.3),
                 unit, font_size=10, color=MEDIUM_GRAY, alignment=PP_ALIGN.CENTER)

    # Label
    txBox = slide4.shapes.add_textbox(x + Inches(0.1), card_y + Inches(2.0), card_w - Inches(0.2), Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(10)
    p.font.color.rgb = DARK_TEXT
    p.font.bold = True
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER


# Education breakdown chart
add_text_box(slide4, Inches(0.8), Inches(5.2), Inches(5), Inches(0.3),
             "EDUCATION COMPONENT BY GENDER", font_size=12, color=MEDIUM_GRAY, bold=True)
add_thin_accent_line(slide4, Inches(0.8), Inches(5.5), Inches(3), ACCENT_1)

edu_gender_data = CategoryChartData()
edu_gender_data.categories = ['Education Component']
edu_gender_data.add_series('Female (109.4)', (109.4,))
edu_gender_data.add_series('Male (108.5)', (108.5,))

eg_frame = slide4.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.6), Inches(5.5), Inches(0.9),
    edu_gender_data
)
egc = eg_frame.chart
egc.has_legend = True
egc.legend.position = XL_LEGEND_POSITION.RIGHT
egc.legend.font.size = Pt(9)
egp = egc.plots[0]
egp.gap_width = 60
egp.series[0].format.fill.solid()
egp.series[0].format.fill.fore_color.rgb = ACCENT_4
egp.series[1].format.fill.solid()
egp.series[1].format.fill.fore_color.rgb = ACCENT_1
egc.category_axis.visible = False
egc.value_axis.visible = False
egc.value_axis.has_major_gridlines = False

# Insight
insight = add_rounded_rect(slide4, Inches(7), Inches(5.2), Inches(5.5), Inches(1.5), WHITE)
add_shape(slide4, Inches(7), Inches(5.2), Pt(5), Inches(1.5), ACCENT_1)
add_text_box(slide4, Inches(7.3), Inches(5.3), Inches(5), Inches(0.25),
             "KEY TAKEAWAY", font_size=10, color=ACCENT_1, bold=True)
add_text_box(slide4, Inches(7.3), Inches(5.6), Inches(5), Inches(1.0),
             "Education is Kenya's strongest HCI+ pillar at 109.0 points. With 11.03 expected years "
             "of schooling and an HLO score of 418.1, Kenya demonstrates solid educational foundations. "
             "Tertiary enrollment at 20.3% presents an area for growth. Gender parity in education "
             "is nearly achieved, with minimal gaps between male and female scores.",
             font_size=10, color=DARK_TEXT)

add_footer(slide4)
add_slide_number(slide4, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — EMPLOYMENT / ON-THE-JOB LEARNING COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
add_shape(slide5, Inches(0), Inches(0), SLIDE_W, SLIDE_H, LIGHT_BG)

# Header
add_shape(slide5, Inches(0), Inches(0), SLIDE_W, Inches(1.1), PRIMARY)
add_shape(slide5, Inches(0), Inches(1.1), SLIDE_W, Pt(4), ACCENT_3)
add_text_box(slide5, Inches(0.8), Inches(0.2), Inches(10), Inches(0.7),
             "Employment & On-the-Job Learning", font_size=26, color=WHITE, bold=True,
             font_name="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
add_text_box(slide5, Inches(9), Inches(0.2), Inches(4), Inches(0.7),
             "Score: 25.3", font_size=20, color=ACCENT_3, bold=True,
             alignment=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

add_text_box(slide5, Inches(0.8), Inches(1.5), Inches(8), Inches(0.5),
             "Employment outcomes capture labor force participation, wage employment, "
             "and unemployment rates for both youth and working-age populations.",
             font_size=11, color=MEDIUM_GRAY)

# Youth vs Working Age comparison table
# Section: Youth (15-24)
add_text_box(slide5, Inches(0.8), Inches(2.2), Inches(5.5), Inches(0.35),
             "YOUTH (15\u201324)", font_size=13, color=ACCENT_3, bold=True)
add_thin_accent_line(slide5, Inches(0.8), Inches(2.55), Inches(2), ACCENT_3)

youth_card = add_rounded_rect(slide5, Inches(0.8), Inches(2.7), Inches(5.5), Inches(2.0), WHITE)

# Youth metrics table
youth_metrics = [
    ("Labor Force Participation", "39.6%", "42.4%", "37.2%"),
    ("Wage Employment Share", "38.8%", "43.9%", "32.9%"),
]

table_y = Inches(2.85)
# Header row
add_text_box(slide5, Inches(1.0), table_y, Inches(2), Inches(0.3),
             "Indicator", font_size=10, color=MEDIUM_GRAY, bold=True)
add_text_box(slide5, Inches(3.0), table_y, Inches(1), Inches(0.3),
             "Both", font_size=10, color=MEDIUM_GRAY, bold=True, alignment=PP_ALIGN.CENTER)
add_text_box(slide5, Inches(4.0), table_y, Inches(1), Inches(0.3),
             "Male", font_size=10, color=ACCENT_1, bold=True, alignment=PP_ALIGN.CENTER)
add_text_box(slide5, Inches(5.0), table_y, Inches(1), Inches(0.3),
             "Female", font_size=10, color=ACCENT_4, bold=True, alignment=PP_ALIGN.CENTER)

# Divider
add_shape(slide5, Inches(1.0), table_y + Inches(0.3), Inches(5), Pt(1), DIVIDER)

for j, (indicator, both, male, female) in enumerate(youth_metrics):
    row_y = table_y + Inches(0.4 + j * 0.55)
    add_text_box(slide5, Inches(1.0), row_y, Inches(2), Inches(0.3),
                 indicator, font_size=10, color=DARK_TEXT)
    add_text_box(slide5, Inches(3.0), row_y, Inches(1), Inches(0.3),
                 both, font_size=12, color=DARK_TEXT, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide5, Inches(4.0), row_y, Inches(1), Inches(0.3),
                 male, font_size=12, color=ACCENT_1, bold=False, alignment=PP_ALIGN.CENTER)
    add_text_box(slide5, Inches(5.0), row_y, Inches(1), Inches(0.3),
                 female, font_size=12, color=ACCENT_4, bold=False, alignment=PP_ALIGN.CENTER)
    if j < len(youth_metrics) - 1:
        add_shape(slide5, Inches(1.0), row_y + Inches(0.35), Inches(5), Pt(1), RGBColor(0xEE, 0xEE, 0xEE))


# Section: Working Age (25-65)
add_text_box(slide5, Inches(7), Inches(2.2), Inches(5.5), Inches(0.35),
             "WORKING AGE (25\u201365)", font_size=13, color=ACCENT_3, bold=True)
add_thin_accent_line(slide5, Inches(7), Inches(2.55), Inches(2), ACCENT_3)

wa_card = add_rounded_rect(slide5, Inches(7), Inches(2.7), Inches(5.5), Inches(2.0), WHITE)

wa_metrics = [
    ("Labor Force Participation", "78.0%", "85.2%", "71.0%"),
    ("Wage Employment Share", "35.6%", "44.2%", "25.4%"),
]

table_y2 = Inches(2.85)
add_text_box(slide5, Inches(7.2), table_y2, Inches(2), Inches(0.3),
             "Indicator", font_size=10, color=MEDIUM_GRAY, bold=True)
add_text_box(slide5, Inches(9.2), table_y2, Inches(1), Inches(0.3),
             "Both", font_size=10, color=MEDIUM_GRAY, bold=True, alignment=PP_ALIGN.CENTER)
add_text_box(slide5, Inches(10.2), table_y2, Inches(1), Inches(0.3),
             "Male", font_size=10, color=ACCENT_1, bold=True, alignment=PP_ALIGN.CENTER)
add_text_box(slide5, Inches(11.2), table_y2, Inches(1), Inches(0.3),
             "Female", font_size=10, color=ACCENT_4, bold=True, alignment=PP_ALIGN.CENTER)

add_shape(slide5, Inches(7.2), table_y2 + Inches(0.3), Inches(5), Pt(1), DIVIDER)

for j, (indicator, both, male, female) in enumerate(wa_metrics):
    row_y = table_y2 + Inches(0.4 + j * 0.55)
    add_text_box(slide5, Inches(7.2), row_y, Inches(2), Inches(0.3),
                 indicator, font_size=10, color=DARK_TEXT)
    add_text_box(slide5, Inches(9.2), row_y, Inches(1), Inches(0.3),
                 both, font_size=12, color=DARK_TEXT, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide5, Inches(10.2), row_y, Inches(1), Inches(0.3),
                 male, font_size=12, color=ACCENT_1, bold=False, alignment=PP_ALIGN.CENTER)
    add_text_box(slide5, Inches(11.2), row_y, Inches(1), Inches(0.3),
                 female, font_size=12, color=ACCENT_4, bold=False, alignment=PP_ALIGN.CENTER)
    if j < len(wa_metrics) - 1:
        add_shape(slide5, Inches(7.2), row_y + Inches(0.35), Inches(5), Pt(1), RGBColor(0xEE, 0xEE, 0xEE))


# Employment chart
add_text_box(slide5, Inches(0.8), Inches(5.0), Inches(5), Inches(0.3),
             "EMPLOYMENT COMPONENT BY GENDER", font_size=12, color=MEDIUM_GRAY, bold=True)
add_thin_accent_line(slide5, Inches(0.8), Inches(5.3), Inches(3), ACCENT_3)

emp_data = CategoryChartData()
emp_data.categories = ['LFP Youth', 'Wage Emp Youth', 'LFP Working Age', 'Wage Emp Working Age']
emp_data.add_series('Female', (37.2, 32.9, 71.0, 25.4))
emp_data.add_series('Male', (42.4, 43.9, 85.2, 44.2))

emp_frame = slide5.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.8), Inches(5.4), Inches(5.5), Inches(1.4),
    emp_data
)
emc = emp_frame.chart
emc.has_legend = True
emc.legend.position = XL_LEGEND_POSITION.BOTTOM
emc.legend.font.size = Pt(9)
emc.legend.font.name = "Calibri"
emp_plot = emc.plots[0]
emp_plot.gap_width = 80
emp_plot.series[0].format.fill.solid()
emp_plot.series[0].format.fill.fore_color.rgb = ACCENT_4
emp_plot.series[1].format.fill.solid()
emp_plot.series[1].format.fill.fore_color.rgb = ACCENT_1
emc.category_axis.tick_labels.font.size = Pt(8)
emc.category_axis.tick_labels.font.name = "Calibri"
emc.value_axis.visible = False
emc.value_axis.has_major_gridlines = False

# Insight panel
insight5 = add_rounded_rect(slide5, Inches(7), Inches(5.0), Inches(5.5), Inches(1.8), WHITE)
add_shape(slide5, Inches(7), Inches(5.0), Pt(5), Inches(1.8), ACCENT_3)
add_text_box(slide5, Inches(7.3), Inches(5.1), Inches(5), Inches(0.25),
             "KEY TAKEAWAY", font_size=10, color=ACCENT_3, bold=True)
add_text_box(slide5, Inches(7.3), Inches(5.4), Inches(5), Inches(1.3),
             "Employment is Kenya's weakest HCI+ component at 25.3 points. "
             "While working-age labor force participation is relatively strong at 78.0%, "
             "youth employment (39.6% LFP) and wage employment shares remain low. "
             "Significant gender gaps exist: women's wage employment (25.4%) is nearly "
             "half that of men (44.2%), presenting a major opportunity for improvement.",
             font_size=10, color=DARK_TEXT)

add_footer(slide5)
add_slide_number(slide5, 4)


# ── Save ──────────────────────────────────────────────────────────────────────
output_path = "/home/user/arcidiaconom.github.io/Kenya_HCI_Plus_2025.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Slides: {len(prs.slides)}")
