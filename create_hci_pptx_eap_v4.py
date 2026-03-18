#!/usr/bin/env python3
"""
Create EAP HCI+ PowerPoint v4.
v4: Distinct pillar colors (navy, orange-red, green), region-aware highlighting
(EAP=blue, World=cranberry, others=gray).
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData, BubbleChartData
from pptx.oxml.ns import qn
import math

# ── Color Palette ────────────────────────────────────────────────────────────
PRIMARY       = RGBColor(0x00, 0x2B, 0x49)
DARK_BLUE     = RGBColor(0x1B, 0x3A, 0x5C)
LIGHT_BG      = RGBColor(0xF7, 0xF8, 0xFA)
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT      = RGBColor(0x1A, 0x1A, 0x2E)
MEDIUM_GRAY   = RGBColor(0x7A, 0x7A, 0x8C)
LIGHT_GRAY    = RGBColor(0xE0, 0xE2, 0xE6)
DIVIDER       = RGBColor(0xD0, 0xD5, 0xDD)
GREEN_POS     = RGBColor(0x2E, 0xA0, 0x6A)
BENCHMARK_GRAY = RGBColor(0xBB, 0xBB, 0xCC)
FADED_GRAY    = RGBColor(0xCC, 0xCC, 0xCC)

# ── Three Pillar Colors (consistent throughout) ─────────────────────────────
# Health = navy at 75%  |  Education = orange-red at 55%  |  Employment = green at 55%
HEALTH_CLR    = RGBColor(0x2B, 0x4C, 0x7E)   # navy 75%
EDUC_CLR      = RGBColor(0xD4, 0x53, 0x3B)   # orange-red 55%
EMPLOY_CLR    = RGBColor(0x4E, 0x9A, 0x51)   # green 55%

# Legacy aliases (used in a few non-pillar spots — kept for readability)
TEAL          = HEALTH_CLR
BLUE          = EDUC_CLR
ORANGE        = EMPLOY_CLR
CORAL         = RGBColor(0xC0, 0x39, 0x2B)   # darker variant for "below avg"
LIGHT_TEAL    = RGBColor(0xE0, 0xE8, 0xF0)   # light navy tint

# ── Region Highlight Colors ─────────────────────────────────────────────────
EAP_ACCENT    = RGBColor(0x21, 0x71, 0xB5)   # EAP blue
WORLD_CLR     = RGBColor(0x9E, 0x1B, 0x34)   # cranberry for World
REGION_GRAY   = RGBColor(0x9E, 0x9E, 0x9E)   # gray for other regions

# ── Presentation Setup ────────────────────────────────────────────────────────
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


def shape_circle(slide, cx, cy, radius, fill, line_color=None, line_width=None):
    s = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        int(cx - radius), int(cy - radius),
        int(2 * radius), int(2 * radius)
    )
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    else:
        s.fill.background()
    if line_color:
        s.line.color.rgb = line_color
        s.line.width = Pt(line_width or 2)
    else:
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
             "Source: World Bank Human Capital Index Plus (HCI+) 2025  |  github.com/worldbank/HCI-Plus",
             size=8, color=RGBColor(0xAA, 0xBB, 0xCC), font="Calibri")
    text_box(slide, Inches(10), Inches(7.07), Inches(2.5), Inches(0.35),
             "humancapital.worldbank.org/hciplus", size=8,
             color=TEAL, align=PP_ALIGN.RIGHT)
    text_box(slide, Inches(12.6), Inches(7.07), Inches(0.5), Inches(0.35),
             str(num), size=8, color=WHITE, align=PP_ALIGN.RIGHT)


def draw_horizontal_bar(slide, left, top, width, height, value, max_val, fill_color, track_color=LIGHT_GRAY):
    shape_rounded(slide, left, top, width, height, track_color)
    fill_w = max(Inches(0.1), int(width * (value / max_val)))
    shape_rounded(slide, left, top, fill_w, height, fill_color)


def draw_dot_comparison(slide, left, top, width, label, actual, benchmark, max_val, color, bench_label="Top Performer"):
    text_box(slide, left, top, Inches(2.2), Inches(0.3), label, size=10, color=DARK_TEXT, bold=True)
    bar_left = left + Inches(2.3)
    bar_width = width - Inches(2.3)
    bar_y = top + Inches(0.12)
    shape_rect(slide, bar_left, bar_y + Inches(0.04), bar_width, Pt(2), LIGHT_GRAY)
    bench_x = bar_left + int(bar_width * (benchmark / max_val))
    shape_circle(slide, bench_x, bar_y + Inches(0.05), Inches(0.12), None,
                 line_color=BENCHMARK_GRAY, line_width=2.5)
    actual_x = bar_left + int(bar_width * (actual / max_val))
    shape_circle(slide, actual_x, bar_y + Inches(0.05), Inches(0.12), color)
    text_box(slide, actual_x - Inches(0.3), top + Inches(0.25), Inches(0.6), Inches(0.2),
             f"{actual:.1f}", size=9, color=color, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s1, Inches(0), Inches(0), Inches(13.333), Inches(7.5), PRIMARY)
shape_rect(s1, Inches(0), Inches(6.0), Inches(13.333), Inches(1.5),
           RGBColor(0x00, 0x1F, 0x38))

# Accent line
shape_rect(s1, Inches(1.3), Inches(2.0), Inches(1.8), Pt(4), EAP_ACCENT)

# Title
text_box(s1, Inches(1.3), Inches(2.3), Inches(7), Inches(1.2),
         "Human Capital\nIndex Plus", size=48, color=WHITE, bold=True,
         font="Calibri Light")

text_box(s1, Inches(1.3), Inches(3.9), Inches(4), Inches(0.5),
         "HCI+  |  2025", size=22, color=EAP_ACCENT, bold=True)

# Region name
text_box(s1, Inches(1.3), Inches(4.7), Inches(8), Inches(0.7),
         "EAST ASIA & PACIFIC", size=40, color=WHITE, bold=True)

text_box(s1, Inches(1.3), Inches(5.8), Inches(6), Inches(0.7),
         "Regional overview across 27 economies spanning health,\neducation, and employment dimensions of human capital",
         size=13, color=RGBColor(0x88, 0x99, 0xAA))

# Tags
tag_y = Inches(6.6)
t1 = shape_rounded(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32),
         "27 Economies", size=9, color=EAP_ACCENT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
t2 = shape_rounded(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32),
         "All Income Levels", size=9, color=EAP_ACCENT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Right panel — Score display
score_panel = shape_rounded(s1, Inches(8.8), Inches(1.5), Inches(3.8), Inches(5.0),
                            RGBColor(0x00, 0x3A, 0x5C))

text_box(s1, Inches(8.8), Inches(1.7), Inches(3.8), Inches(0.35),
         "REGIONAL HCI+ AVERAGE", size=10, color=EAP_ACCENT, bold=True, align=PP_ALIGN.CENTER)

text_box(s1, Inches(8.8), Inches(2.4), Inches(3.8), Inches(1.6),
         "201.7", size=72, color=WHITE, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, font="Calibri Light")

text_box(s1, Inches(8.8), Inches(4.0), Inches(3.8), Inches(0.3),
         "out of 325  |  World avg: 188.5", size=12, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)

# Component mini-bars
comp_data = [
    ("Health", 42.8, 50, TEAL),
    ("Education", 118.1, 180, BLUE),
    ("Employment", 40.7, 70, ORANGE),
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
         "Ranked #3 among 7 World Bank regions",
         size=9, color=EAP_ACCENT, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — BUBBLE CHART: HCI+ vs GDP (EAP colored, rest transparent)
# ══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s2, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s2, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  HCI+ vs GDP per Capita", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "201.7 / 325", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

bubble_panel = shape_rounded(s2, Inches(0.5), Inches(1.3), Inches(8.8), Inches(5.4), WHITE)

text_box(s2, Inches(0.8), Inches(1.5), Inches(7), Inches(0.3),
         "HCI+ SCORE vs LOG GDP PER CAPITA (PPP)", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s2, Inches(0.8), Inches(1.85), Inches(2.5), Pt(3), EAP_ACCENT)
text_box(s2, Inches(0.8), Inches(1.95), Inches(7), Inches(0.25),
         "EAP countries in blue. All other regions shown in light gray for context.",
         size=9, color=MEDIUM_GRAY)

# ISO3 code mappings for all countries
ISO3_CODES = {
    'Nigeria': 'NGA', 'South Africa': 'ZAF', 'Kenya': 'KEN', 'Ethiopia': 'ETH',
    'Ghana': 'GHA', 'Rwanda': 'RWA', 'Uganda': 'UGA', 'Tanzania': 'TZA',
    'Mauritius': 'MUS', 'Senegal': 'SEN', 'Botswana': 'BWA',
    'Germany': 'DEU', 'France': 'FRA', 'Sweden': 'SWE', 'Poland': 'POL',
    'Netherlands': 'NLD', 'Turkiye': 'TUR', 'Albania': 'ALB',
    'Kyrgyz Republic': 'KGZ', 'Romania': 'ROU', 'Georgia': 'GEO',
    'Chile': 'CHL', 'Brazil': 'BRA', 'Mexico': 'MEX', 'Colombia': 'COL',
    'Argentina': 'ARG', 'Jamaica': 'JAM', 'Nicaragua': 'NIC',
    'India': 'IND', 'Bangladesh': 'BGD', 'Sri Lanka': 'LKA', 'Pakistan': 'PAK',
    'Jordan': 'JOR', 'Egypt': 'EGY', 'Morocco': 'MAR', 'Iran': 'IRN',
    'United States': 'USA', 'Canada': 'CAN',
    'Japan': 'JPN', 'Singapore': 'SGP', 'Korea, Rep.': 'KOR',
    'Australia': 'AUS', 'New Zealand': 'NZL', 'Hong Kong': 'HKG',
    'Macao': 'MAC', 'China': 'CHN', 'Vietnam': 'VNM',
    'Mongolia': 'MNG', 'Brunei': 'BRN', 'Thailand': 'THA',
    'Malaysia': 'MYS', 'Fiji': 'FJI', 'Indonesia': 'IDN',
    'Philippines': 'PHL', 'Tonga': 'TON', 'Tuvalu': 'TUV',
    'Kiribati': 'KIR', 'Myanmar': 'MMR', 'Cambodia': 'KHM',
    'Lao PDR': 'LAO', 'Vanuatu': 'VUT',
}

# Bubble chart data — EAP countries colored, all others faded gray
bubble_data = BubbleChartData()

# Uniform bubble size for all countries
BSIZE = 0.3

# Series 1: Non-EAP countries (gray/transparent)
non_eap_countries = [
    # SSA
    ('Nigeria', 8.64, 130.7), ('South Africa', 9.52, 132.1),
    ('Kenya', 8.67, 170.8), ('Ethiopia', 7.97, 123.4),
    ('Ghana', 8.86, 152.9), ('Rwanda', 8.09, 156.9),
    ('Uganda', 7.97, 145.2), ('Tanzania', 8.22, 132.6),
    ('Mauritius', 10.22, 201.0), ('Senegal', 8.41, 109.4),
    ('Botswana', 9.80, 156.9),
    # Europe & Central Asia
    ('Germany', 11.05, 256.5), ('France', 10.91, 251.2),
    ('Sweden', 11.05, 269.3), ('Poland', 10.72, 259.5),
    ('Netherlands', 11.17, 269.7), ('Turkiye', 10.32, 210.5),
    ('Albania', 9.85, 203.5), ('Kyrgyz Republic', 8.86, 197.5),
    ('Romania', 10.40, 221.3), ('Georgia', 9.73, 204.7),
    # Latin America
    ('Chile', 10.32, 226.2), ('Brazil', 9.89, 202.9),
    ('Mexico', 10.00, 193.5), ('Colombia', 9.83, 197.6),
    ('Argentina', 10.10, 205.3), ('Jamaica', 9.24, 200.1),
    ('Nicaragua', 8.94, 178.1),
    # South Asia & MENA
    ('India', 9.19, 158.8), ('Bangladesh', 9.05, 146.7),
    ('Sri Lanka', 9.73, 182.6), ('Pakistan', 8.47, 99.3),
    ('Jordan', 9.16, 170.2), ('Egypt', 9.73, 161.2),
    ('Morocco', 9.11, 147.1), ('Iran', 10.17, 196.3),
    # North America
    ('United States', 11.20, 251.2), ('Canada', 10.98, 257.3),
]

# Series 2: EAP countries (colored)
eap_countries = [
    ('Japan', 10.74, 284.3),
    ('Singapore', 11.79, 282.4),
    ('Korea, Rep.', 10.83, 266.9),
    ('Australia', 11.00, 270.0),
    ('New Zealand', 10.78, 263.1),
    ('Hong Kong', 11.10, 258.4),
    ('Macao', 11.63, 255.9),
    ('China', 10.08, 219.8),
    ('Vietnam', 9.58, 215.8),
    ('Mongolia', 9.73, 209.5),
    ('Brunei', 11.28, 207.6),
    ('Thailand', 9.99, 202.3),
    ('Malaysia', 10.44, 201.3),
    ('Fiji', 9.55, 192.8),
    ('Indonesia', 9.58, 175.4),
    ('Philippines', 9.25, 175.4),
    ('Tonga', 8.86, 175.8),
    ('Tuvalu', 8.67, 166.1),
    ('Kiribati', 8.09, 161.9),
    ('Myanmar', 8.57, 149.2),
    ('Cambodia', 8.86, 138.9),
    ('Lao PDR', 9.06, 135.6),
    ('Vanuatu', 8.06, 136.4),
]

# Add non-EAP as first series (will be gray)
s_non_eap = bubble_data.add_series('Other Regions')
for name, gdp, score in non_eap_countries:
    s_non_eap.add_data_point(gdp, score, BSIZE)

# Add EAP as second series (will be blue)
s_eap = bubble_data.add_series('East Asia & Pacific')
for name, gdp, score in eap_countries:
    s_eap.add_data_point(gdp, score, BSIZE)

bcf = s2.shapes.add_chart(
    XL_CHART_TYPE.BUBBLE, Inches(0.8), Inches(2.2), Inches(8.2), Inches(4.2),
    bubble_data
)
bc = bcf.chart
bc.has_legend = True
bc.legend.position = XL_LEGEND_POSITION.BOTTOM
bc.legend.include_in_layout = False
bc.legend.font.size = Pt(9)
bc.legend.font.name = "Calibri"

# Style axes
bc.value_axis.has_title = True
bc.value_axis.axis_title.text_frame.paragraphs[0].text = "HCI+ Score"
bc.value_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(10)
bc.value_axis.axis_title.text_frame.paragraphs[0].font.name = "Calibri"
bc.value_axis.minimum_scale = 60
bc.value_axis.maximum_scale = 310

# Reduce bubble scale to make bubbles much smaller
from lxml import etree as _etree
bubble_chart_el = bc.plots[0]._element
bubble_scale_el = bubble_chart_el.find(qn('c:bubbleScale'))
if bubble_scale_el is None:
    bubble_scale_el = _etree.SubElement(bubble_chart_el, qn('c:bubbleScale'))
bubble_scale_el.set('val', '15')
bc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
bc.value_axis.tick_labels.font.size = Pt(9)

bc.category_axis.has_title = True
bc.category_axis.axis_title.text_frame.paragraphs[0].text = "Log GDP per Capita (PPP)"
bc.category_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(10)
bc.category_axis.axis_title.text_frame.paragraphs[0].font.name = "Calibri"
bc.category_axis.minimum_scale = 7.5
bc.category_axis.maximum_scale = 12.0
bc.category_axis.tick_labels.font.size = Pt(9)

# Non-EAP series: light gray with transparency
non_eap_series = bc.series[0]
non_eap_series.format.fill.solid()
non_eap_series.format.fill.fore_color.rgb = FADED_GRAY
# Set transparency to 60% on non-EAP bubbles via XML
spPr = non_eap_series._element
solidFill_el = spPr.find('.//' + qn('a:solidFill'))
if solidFill_el is not None:
    srgbClr = solidFill_el.find(qn('a:srgbClr'))
    if srgbClr is not None:
        alpha = srgbClr.makeelement(qn('a:alpha'), {'val': '40000'})
        srgbClr.append(alpha)

# EAP series: blue
eap_series = bc.series[1]
eap_series.format.fill.solid()
eap_series.format.fill.fore_color.rgb = EAP_ACCENT

# RIGHT PANEL — EAP context
right_ctx = shape_rounded(s2, Inches(9.6), Inches(1.3), Inches(3.3), Inches(5.4), WHITE)
shape_rect(s2, Inches(9.6), Inches(1.3), Pt(5), Inches(5.4), EAP_ACCENT)

text_box(s2, Inches(9.9), Inches(1.5), Inches(2.9), Inches(0.25),
         "EAP IN CONTEXT", size=11, color=EAP_ACCENT, bold=True)

stats = [
    ("Regional Average", "201.7", EAP_ACCENT),
    ("World Average", "188.5", WORLD_CLR),
    ("Economies", "27", DARK_TEXT),
    ("Top Performer", "Japan (284.3)", EAP_ACCENT),
    ("Lowest in EAP", "Lao PDR (135.6)", CORAL),
    ("vs Europe/C. Asia", "233.3", MEDIUM_GRAY),
    ("vs Latin America", "183.2", MEDIUM_GRAY),
    ("vs Sub-Saharan Africa", "128.4", MEDIUM_GRAY),
]

for j, (label, value, color) in enumerate(stats):
    sy = Inches(1.9) + Inches(j * 0.5)
    text_box(s2, Inches(9.9), sy, Inches(1.8), Inches(0.22),
             label, size=9, color=MEDIUM_GRAY)
    text_box(s2, Inches(11.5), sy, Inches(1.2), Inches(0.22),
             value, size=10, color=color, bold=True, align=PP_ALIGN.RIGHT)
    if j < len(stats) - 1:
        shape_rect(s2, Inches(9.9), sy + Inches(0.32), Inches(2.8), Pt(1),
                   RGBColor(0xEE, 0xEE, 0xEE))

# Insight text
text_box(s2, Inches(9.9), Inches(5.3), Inches(2.9), Inches(0.25),
         "KEY INSIGHT", size=10, color=EAP_ACCENT, bold=True)
text_box(s2, Inches(9.9), Inches(5.6), Inches(2.9), Inches(0.95),
         "EAP (avg 201.7) ranks 3rd among WB regions, exceeding "
         "the global average by 13 points. The region shows enormous "
         "variation: Japan (284.3) leads globally, while Lao PDR "
         "(135.6) trails. High-income EAP economies rival Europe.",
         size=9, color=DARK_TEXT)

# ── Add ISO3 labels on bubbles ────────────────────────────────────────────────
# Chart area: left=0.8", top=2.2", width=8.2", height=4.2"
# Axes: x = 7.5–12.0 (log GDP), y = 60–310 (HCI+)
b_chart_left = Inches(0.8)
b_chart_top = Inches(2.2)
b_chart_w = Inches(8.2)
b_chart_h = Inches(4.2)
# Approximate plot area within chart (axes/labels offset)
b_plot_left = b_chart_left + Inches(0.55)
b_plot_top = b_chart_top + Inches(0.1)
b_plot_w = b_chart_w - Inches(0.9)
b_plot_h = b_chart_h - Inches(0.65)
b_x_min, b_x_max = 7.5, 12.0
b_y_min, b_y_max = 60, 310


def bubble_to_pos(gdp_val, hci_val):
    px = b_plot_left + int(b_plot_w * (gdp_val - b_x_min) / (b_x_max - b_x_min))
    py = b_plot_top + int(b_plot_h * (1 - (hci_val - b_y_min) / (b_y_max - b_y_min)))
    return px, py


# Non-EAP labels (small, gray)
for name, gdp, score in non_eap_countries:
    code = ISO3_CODES.get(name, name[:3].upper())
    px, py = bubble_to_pos(gdp, score)
    text_box(s2, px - Inches(0.2), py - Inches(0.18), Inches(0.5), Inches(0.18),
             code, size=5, color=FADED_GRAY, bold=False, align=PP_ALIGN.CENTER)

# EAP labels (small, blue, bold)
for name, gdp, score in eap_countries:
    code = ISO3_CODES.get(name, name[:3].upper())
    px, py = bubble_to_pos(gdp, score)
    text_box(s2, px - Inches(0.2), py - Inches(0.18), Inches(0.5), Inches(0.18),
             code, size=6, color=EAP_ACCENT, bold=True, align=PP_ALIGN.CENTER)

add_footer(s2, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2b — COMPONENT DECOMPOSITION BY REGION (full slide)
# ══════════════════════════════════════════════════════════════════════════════
s2b = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2b, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s2b, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s2b, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  Component Decomposition by Region", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2b, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "201.7 / 325", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Stacked bar — regional composition
reg_stacked = CategoryChartData()
reg_stacked.categories = ['SSA', 'SAR', 'LAC', 'MENA+', 'EAP', 'ECA', 'World']
reg_stacked.add_series('Health',     (37.3, 41.0, 43.4, 44.9, 42.8, 45.9, 42.6))
reg_stacked.add_series('Education',  (64.1, 83.0, 98.3, 105.8, 118.1, 140.8, 107.4))
reg_stacked.add_series('Employment', (26.9, 23.4, 41.5, 35.0, 40.7, 46.6, 37.2))

rcf2b = s2b.shapes.add_chart(
    XL_CHART_TYPE.BAR_STACKED, Inches(0.6), Inches(1.2), Inches(7.5), Inches(5.5),
    reg_stacked
)
rch2b = rcf2b.chart
rch2b.has_legend = True
rch2b.legend.position = XL_LEGEND_POSITION.BOTTOM
rch2b.legend.include_in_layout = False
rch2b.legend.font.size = Pt(11)
rch2b.legend.font.name = "Calibri"

rplot2b = rch2b.plots[0]
rplot2b.gap_width = 60
rcolors2b = [TEAL, BLUE, ORANGE]
for i, ser in enumerate(rplot2b.series):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rcolors2b[i]
    ser.has_data_labels = True
    ser.data_labels.font.size = Pt(9)
    ser.data_labels.font.bold = True
    ser.data_labels.font.name = "Calibri"
    ser.data_labels.number_format = '0.0'

rch2b.category_axis.tick_labels.font.size = Pt(11)
rch2b.category_axis.tick_labels.font.name = "Calibri"
rch2b.value_axis.maximum_scale = 280
rch2b.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
rch2b.value_axis.format.line.color.rgb = DIVIDER
rch2b.value_axis.tick_labels.font.size = Pt(9)

# EAP vs World dot comparisons
text_box(s2b, Inches(8.5), Inches(1.3), Inches(4.5), Inches(0.3),
         "EAP vs WORLD AVERAGE", size=12, color=EAP_ACCENT, bold=True)
text_box(s2b, Inches(8.5), Inches(1.65), Inches(4.5), Inches(0.25),
         "Filled = EAP  |  Hollow = World", size=10, color=MEDIUM_GRAY)
shape_rect(s2b, Inches(8.5), Inches(1.95), Inches(2), Pt(3), EAP_ACCENT)

benchmarks_2b = {
    "Health": (42.8, 42.6, 50),
    "Education": (118.1, 107.4, 180),
    "Employment": (40.7, 37.2, 70),
}

dot_y_2b = Inches(2.2)
for i, (comp, (actual, bench, max_v)) in enumerate(benchmarks_2b.items()):
    y = dot_y_2b + Inches(i * 0.6)
    color = [TEAL, BLUE, ORANGE][i]
    draw_dot_comparison(s2b, Inches(8.5), y, Inches(4.2), comp, actual, bench, max_v, color)

# Summary stats
text_box(s2b, Inches(8.5), Inches(4.2), Inches(4.5), Inches(0.3),
         "REGIONAL AVERAGES", size=12, color=EAP_ACCENT, bold=True)
shape_rect(s2b, Inches(8.5), Inches(4.55), Inches(2), Pt(3), EAP_ACCENT)

reg_stats = [
    ("Sub-Saharan Africa", "128.4"),
    ("South Asia", "147.5"),
    ("Latin America & Carib.", "183.2"),
    ("MENA+", "185.7"),
    ("East Asia & Pacific", "201.7"),
    ("Europe & Central Asia", "233.3"),
    ("World", "188.5"),
]
for j, (rname, rval) in enumerate(reg_stats):
    ry = Inches(4.75) + Inches(j * 0.32)
    text_box(s2b, Inches(8.5), ry, Inches(3), Inches(0.25),
             rname, size=10, color=MEDIUM_GRAY)
    val_color = EAP_ACCENT if "East Asia" in rname else (WORLD_CLR if rname == "World" else DARK_TEXT)
    text_box(s2b, Inches(11.5), ry, Inches(1.5), Inches(0.25),
             rval, size=10, color=val_color, bold=True, align=PP_ALIGN.RIGHT)

add_footer(s2b, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2c — HEALTH COMPONENT: REGIONAL COMPARISON (full slide)
# ══════════════════════════════════════════════════════════════════════════════
s2c = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2c, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s2c, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s2c, Inches(0), Inches(1.0), Inches(13.333), Pt(4), TEAL)
text_box(s2c, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Health Component  |  Regional Comparison", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2c, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "EAP Avg: 42.8 / 50", size=22, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

rh_data = CategoryChartData()
rh_data.categories = ['SSA', 'SAR', 'EAP', 'LAC', 'MENA+', 'ECA', 'World']
rh_data.add_series('Health Score', (37.3, 41.0, 42.8, 43.4, 44.9, 45.9, 42.6))

rhcf = s2c.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.3), Inches(12.2), Inches(5.5),
    rh_data
)
rhc = rhcf.chart
rhc.has_legend = False
rhp = rhc.plots[0]
rhp.gap_width = 80
rhs = rhp.series[0]
rhs.format.fill.solid()
rhs.format.fill.fore_color.rgb = REGION_GRAY
rhs.points[2].format.fill.solid()
rhs.points[2].format.fill.fore_color.rgb = EAP_ACCENT
rhs.points[6].format.fill.solid()
rhs.points[6].format.fill.fore_color.rgb = WORLD_CLR

rhs.has_data_labels = True
rhs.data_labels.font.size = Pt(14)
rhs.data_labels.font.bold = True
rhs.data_labels.font.name = "Calibri"
rhs.data_labels.number_format = '0.0'

rhc.category_axis.tick_labels.font.size = Pt(13)
rhc.category_axis.tick_labels.font.name = "Calibri"
rhc.value_axis.visible = False
rhc.value_axis.has_major_gridlines = False

add_footer(s2c, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2d — EDUCATION COMPONENT: REGIONAL COMPARISON (full slide)
# ══════════════════════════════════════════════════════════════════════════════
s2d = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2d, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s2d, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s2d, Inches(0), Inches(1.0), Inches(13.333), Pt(4), BLUE)
text_box(s2d, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Education Component  |  Regional Comparison", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2d, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "EAP Avg: 118.1 / 180", size=22, color=BLUE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

re_data = CategoryChartData()
re_data.categories = ['SSA', 'SAR', 'LAC', 'MENA+', 'EAP', 'ECA', 'World']
re_data.add_series('Education Score', (64.1, 83.0, 98.3, 105.8, 118.1, 140.8, 107.4))

recf = s2d.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.3), Inches(12.2), Inches(5.5),
    re_data
)
rec = recf.chart
rec.has_legend = False
rep = rec.plots[0]
rep.gap_width = 80
res = rep.series[0]
res.format.fill.solid()
res.format.fill.fore_color.rgb = REGION_GRAY
res.points[4].format.fill.solid()
res.points[4].format.fill.fore_color.rgb = EAP_ACCENT
res.points[6].format.fill.solid()
res.points[6].format.fill.fore_color.rgb = WORLD_CLR

res.has_data_labels = True
res.data_labels.font.size = Pt(14)
res.data_labels.font.bold = True
res.data_labels.font.name = "Calibri"
res.data_labels.number_format = '0.0'

rec.category_axis.tick_labels.font.size = Pt(13)
rec.category_axis.tick_labels.font.name = "Calibri"
rec.value_axis.visible = False
rec.value_axis.has_major_gridlines = False

add_footer(s2d, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2e — EMPLOYMENT COMPONENT: REGIONAL COMPARISON (full slide)
# ══════════════════════════════════════════════════════════════════════════════
s2e = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2e, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s2e, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s2e, Inches(0), Inches(1.0), Inches(13.333), Pt(4), ORANGE)
text_box(s2e, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Employment Component  |  Regional Comparison", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2e, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "EAP Avg: 40.7 / 70", size=22, color=ORANGE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

remp_data = CategoryChartData()
remp_data.categories = ['SAR', 'SSA', 'MENA+', 'World', 'EAP', 'LAC', 'ECA']
remp_data.add_series('Employment Score', (23.4, 26.9, 35.0, 37.2, 40.7, 41.5, 46.6))

remcf = s2e.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.3), Inches(12.2), Inches(5.5),
    remp_data
)
remc = remcf.chart
remc.has_legend = False
remp = remc.plots[0]
remp.gap_width = 80
rems = remp.series[0]
rems.format.fill.solid()
rems.format.fill.fore_color.rgb = REGION_GRAY
rems.points[4].format.fill.solid()
rems.points[4].format.fill.fore_color.rgb = EAP_ACCENT
rems.points[3].format.fill.solid()
rems.points[3].format.fill.fore_color.rgb = WORLD_CLR

rems.has_data_labels = True
rems.data_labels.font.size = Pt(14)
rems.data_labels.font.bold = True
rems.data_labels.font.name = "Calibri"
rems.data_labels.number_format = '0.0'

remc.category_axis.tick_labels.font.size = Pt(13)
remc.category_axis.tick_labels.font.name = "Calibri"
remc.value_axis.visible = False
remc.value_axis.has_major_gridlines = False

add_footer(s2e, 5)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — ALL EAP ECONOMIES RANKING
# ══════════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s3, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  All Economies Ranking", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s3, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "201.7 / 325", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Full-width EAP economies bar chart
main_panel = shape_rounded(s3, Inches(0.5), Inches(1.3), Inches(12.3), Inches(5.4), WHITE)

text_box(s3, Inches(0.8), Inches(1.5), Inches(8), Inches(0.3),
         "ALL EAP ECONOMIES BY HCI+ SCORE", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s3, Inches(0.8), Inches(1.85), Inches(2), Pt(3), EAP_ACCENT)

# All 27 EAP economies sorted ascending (ISO3 codes)
eap_rank_data = CategoryChartData()
eap_rank_data.categories = [
    'LAO', 'VUT', 'KHM', 'MHL', 'MMR',
    'NRU', 'KIR', 'WSM', 'TUV', 'TON',
    'IDN', 'PHL', 'FJI', 'MYS', 'THA',
    'BRN', 'MNG', 'VNM', 'CHN', 'PLW',
    'MAC', 'HKG', 'NZL', 'KOR',
    'AUS', 'SGP', 'JPN'
]
eap_rank_data.add_series('HCI+ Score', (
    135.6, 136.4, 138.9, 145.2, 149.2,
    161.6, 161.9, 164.4, 166.1, 175.8,
    175.4, 175.4, 192.8, 201.3, 202.3,
    207.6, 209.5, 215.8, 219.8, 228.6,
    255.9, 258.4, 263.1, 266.9,
    270.0, 282.4, 284.3
))

rcf = s3.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(2.0), Inches(11.8), Inches(4.2),
    eap_rank_data
)
rc = rcf.chart
rc.has_legend = False
rplot = rc.plots[0]
rplot.gap_width = 20

series = rplot.series[0]
series.format.fill.solid()
series.format.fill.fore_color.rgb = EAP_ACCENT

# Color countries below world avg (188.5) differently — first 12
for idx in range(12):  # Lao through Philippines
    series.points[idx].format.fill.solid()
    series.points[idx].format.fill.fore_color.rgb = CORAL

rc.category_axis.tick_labels.font.size = Pt(7)
rc.category_axis.tick_labels.font.name = "Calibri"
rc.value_axis.maximum_scale = 300
rc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
rc.value_axis.format.line.color.rgb = DIVIDER
rc.value_axis.tick_labels.font.size = Pt(7)

series.has_data_labels = True
series.data_labels.font.size = Pt(6)
series.data_labels.font.name = "Calibri"
series.data_labels.font.bold = True
series.data_labels.number_format = '0.0'

# Legend
shape_rect(s3, Inches(0.8), Inches(6.3), Inches(0.25), Inches(0.12), EAP_ACCENT)
text_box(s3, Inches(1.15), Inches(6.25), Inches(1.8), Inches(0.2),
         "Above world avg (188.5)", size=9, color=DARK_TEXT)
shape_rect(s3, Inches(3.2), Inches(6.3), Inches(0.25), Inches(0.12), CORAL)
text_box(s3, Inches(3.55), Inches(6.25), Inches(1.5), Inches(0.2),
         "Below world avg", size=9, color=DARK_TEXT)

add_footer(s3, 6)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — COUNTRY-BY-COUNTRY COMPONENT DECOMPOSITION
# ══════════════════════════════════════════════════════════════════════════════
s3b = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s3b, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s3b, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s3b, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  Country Decomposition", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s3b, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Health + Education + Employment", size=16, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

main_panel = shape_rounded(s3b, Inches(0.5), Inches(1.2), Inches(12.3), Inches(5.5), WHITE)

text_box(s3b, Inches(0.8), Inches(1.35), Inches(8), Inches(0.3),
         "COMPONENT DECOMPOSITION BY ECONOMY (sorted by total HCI+)", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s3b, Inches(0.8), Inches(1.65), Inches(2.5), Pt(3), EAP_ACCENT)

# All 27 EAP countries sorted ascending by HCI+ total (ISO3 codes)
decomp_data = CategoryChartData()
decomp_data.categories = [
    'LAO', 'VUT', 'KHM', 'MHL', 'MMR',
    'NRU', 'KIR', 'WSM', 'TUV', 'TON',
    'IDN', 'PHL', 'FJI', 'MYS', 'THA',
    'BRN', 'MNG', 'VNM', 'CHN', 'PLW',
    'MAC', 'HKG', 'NZL', 'KOR',
    'AUS', 'SGP', 'JPN'
]
# Health component
decomp_data.add_series('Health', (
    38.8, 39.3, 40.6, 36.4, 38.5,
    35.9, 41.0, 43.3, 40.7, 44.4,
    40.7, 40.0, 41.7, 42.4, 42.5,
    44.4, 42.5, 42.5, 46.5, 41.0,
    47.9, 47.4, 46.6, 48.8,
    48.0, 47.7, 47.5
))
# Education component
decomp_data.add_series('Education', (
    66.5, 84.2, 69.9, 88.8, 76.3,
    82.2, 96.7, 102.8, 102.5, 100.4,
    96.5, 98.4, 120.3, 111.1, 114.3,
    117.4, 128.1, 123.8, 127.5, 132.6,
    147.9, 162.5, 155.0, 170.8,
    160.8, 179.4, 172.5
))
# Employment component
decomp_data.add_series('Employment', (
    30.3, 13.0, 28.4, 20.0, 34.3,
    43.5, 24.2, 18.3, 23.0, 31.0,
    38.1, 37.1, 30.8, 47.8, 45.5,
    45.8, 38.9, 49.5, 45.8, 55.0,
    60.1, 48.5, 61.5, 47.4,
    61.2, 55.3, 64.4
))

dcf = s3b.shapes.add_chart(
    XL_CHART_TYPE.BAR_STACKED, Inches(0.8), Inches(1.8), Inches(11.8), Inches(4.7),
    decomp_data
)
dc = dcf.chart
dc.has_legend = True
dc.legend.position = XL_LEGEND_POSITION.BOTTOM
dc.legend.include_in_layout = False
dc.legend.font.size = Pt(9)
dc.legend.font.name = "Calibri"

dplot = dc.plots[0]
dplot.gap_width = 20
dcolors = [TEAL, BLUE, ORANGE]
for i, ds in enumerate(dplot.series):
    ds.format.fill.solid()
    ds.format.fill.fore_color.rgb = dcolors[i]

dc.category_axis.tick_labels.font.size = Pt(7)
dc.category_axis.tick_labels.font.name = "Calibri"
dc.value_axis.maximum_scale = 300
dc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
dc.value_axis.format.line.color.rgb = DIVIDER
dc.value_axis.tick_labels.font.size = Pt(8)

add_footer(s3b, 7)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — HEALTH COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s4, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s4, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s4, Inches(0), Inches(1.0), Inches(13.333), Pt(4), TEAL)
text_box(s4, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Health Component  |  East Asia & Pacific", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s4, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Avg: 42.8 / 50", size=22, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s4, Inches(0.6), Inches(1.35), Inches(8), Inches(0.4),
         "Health outcomes reflect adult survival (ages 15-60) and freedom from childhood stunting.",
         size=11, color=MEDIUM_GRAY)

# LEFT — Adult Survival Rate
card1 = shape_rounded(s4, Inches(0.5), Inches(2.0), Inches(6.0), Inches(2.4), WHITE)
shape_rect(s4, Inches(0.5), Inches(2.0), Inches(6.0), Pt(4), TEAL)

text_box(s4, Inches(0.8), Inches(2.2), Inches(3), Inches(0.25),
         "ADULT SURVIVAL RATE (EAP AVG)", size=12, color=TEAL, bold=True)
text_box(s4, Inches(0.8), Inches(2.5), Inches(5), Inches(0.25),
         "Probability of surviving from age 15 to 60", size=10, color=MEDIUM_GRAY)

text_box(s4, Inches(0.8), Inches(2.85), Inches(2.5), Inches(0.7),
         "85.3%", size=44, color=TEAL, bold=True, font="Calibri Light")

draw_horizontal_bar(s4, Inches(0.8), Inches(3.65), Inches(5.4), Inches(0.18), 85.3, 100, TEAL)

text_box(s4, Inches(3.5), Inches(2.9), Inches(2.5), Inches(0.25),
         "World avg: 81.5%", size=12, color=MEDIUM_GRAY)
text_box(s4, Inches(3.5), Inches(3.2), Inches(2.5), Inches(0.25),
         "Best: Korea 96.7%", size=12, color=EAP_ACCENT)

# World avg marker
world_surv_x = Inches(0.8) + int(Inches(5.4) * 0.815)
shape_rect(s4, world_surv_x, Inches(3.55), Pt(2), Inches(0.38), WORLD_CLR)
text_box(s4, world_surv_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "World", size=7, color=WORLD_CLR, align=PP_ALIGN.CENTER)

# RIGHT — Not Stunted
card2 = shape_rounded(s4, Inches(6.8), Inches(2.0), Inches(6.0), Inches(2.4), WHITE)
shape_rect(s4, Inches(6.8), Inches(2.0), Inches(6.0), Pt(4), TEAL)

text_box(s4, Inches(7.1), Inches(2.2), Inches(3), Inches(0.25),
         "NOT STUNTED RATE (EAP AVG)", size=12, color=TEAL, bold=True)
text_box(s4, Inches(7.1), Inches(2.5), Inches(5), Inches(0.25),
         "Share of children under 5 not stunted", size=10, color=MEDIUM_GRAY)

text_box(s4, Inches(7.1), Inches(2.85), Inches(2.5), Inches(0.7),
         "86.6%", size=44, color=TEAL, bold=True, font="Calibri Light")

draw_horizontal_bar(s4, Inches(7.1), Inches(3.65), Inches(5.4), Inches(0.18), 86.6, 100, TEAL)

text_box(s4, Inches(9.8), Inches(2.9), Inches(2.5), Inches(0.25),
         "World avg: 77.1%", size=12, color=MEDIUM_GRAY)
text_box(s4, Inches(9.8), Inches(3.2), Inches(2.5), Inches(0.25),
         "Best: Korea 99.1%", size=12, color=EAP_ACCENT)

# World avg marker
world_ns_x = Inches(7.1) + int(Inches(5.4) * 0.771)
shape_rect(s4, world_ns_x, Inches(3.55), Pt(2), Inches(0.38), WORLD_CLR)
text_box(s4, world_ns_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "World", size=7, color=WORLD_CLR, align=PP_ALIGN.CENTER)

add_footer(s4, 8)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — EDUCATION COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s5, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s5, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s5, Inches(0), Inches(1.0), Inches(13.333), Pt(4), BLUE)
text_box(s5, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Education Component  |  East Asia & Pacific", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s5, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Avg: 118.1 / 180", size=22, color=BLUE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s5, Inches(0.6), Inches(1.35), Inches(8), Inches(0.4),
         "Education captures learning quality, years of schooling, pre-primary education, and tertiary enrollment.",
         size=11, color=MEDIUM_GRAY)

# Four metric cards with world avg and best EAP
# Format: (label, value, unit, num_val, max_val, color, world_avg, best_eap_label, best_eap_val, world_num_val)
metrics = [
    ("Expected Years\nof Schooling", "10.8", "years (EAP avg)", 10.8, 14, EDUC_CLR,
     "World: 10.1 yrs", "Best: Japan 12.0", 10.1),
    ("Harmonized Learning\nOutcomes", "436", "HLO score (out of 625)", 436, 625, EDUC_CLR,
     "World: 411", "Best: Singapore 594", 411),
    ("Pre-Primary\nEducation", "0.59", "learning-adj. years", 0.59, 1.0, EDUC_CLR,
     "World: 0.46 yrs", "Best: Singapore 0.91", 0.46),
    ("Tertiary\nEnrollment", "37.4%", "gross enrollment rate", 37.4, 100, EDUC_CLR,
     "World: 32.6%", "Best: Korea 76.9%", 32.6),
]

for i, (label, value, unit, num_val, max_val, color, world_lbl, best_lbl, world_num) in enumerate(metrics):
    x = Inches(0.5) + i * Inches(3.15)
    card = shape_rounded(s5, x, Inches(2.0), Inches(2.95), Inches(2.9), WHITE)
    shape_rect(s5, x, Inches(2.0), Inches(2.95), Pt(4), color)

    text_box(s5, x + Inches(0.15), Inches(2.2), Inches(2.65), Inches(0.5),
             label, size=11, color=DARK_TEXT, bold=True)

    text_box(s5, x + Inches(0.15), Inches(2.8), Inches(2.65), Inches(0.7),
             value, size=36, color=color, bold=True, font="Calibri Light")

    text_box(s5, x + Inches(0.15), Inches(3.5), Inches(2.65), Inches(0.25),
             unit, size=9, color=MEDIUM_GRAY)

    bar_left_pos = x + Inches(0.15)
    bar_width_pos = Inches(2.65)
    draw_horizontal_bar(s5, bar_left_pos, Inches(3.85), bar_width_pos, Inches(0.12),
                       num_val, max_val, color)

    # World avg cranberry dash marker on the bar
    world_x = bar_left_pos + int(bar_width_pos * (world_num / max_val))
    shape_rect(s5, world_x, Inches(3.75), Pt(2), Inches(0.32), WORLD_CLR)
    text_box(s5, world_x - Inches(0.25), Inches(4.05), Inches(0.6), Inches(0.15),
             "World", size=6, color=WORLD_CLR, align=PP_ALIGN.CENTER)

    # World average and best EAP
    text_box(s5, x + Inches(0.15), Inches(4.2), Inches(2.65), Inches(0.2),
             world_lbl, size=8, color=MEDIUM_GRAY)
    text_box(s5, x + Inches(0.15), Inches(4.4), Inches(2.65), Inches(0.2),
             best_lbl, size=8, color=EAP_ACCENT, bold=True)

# Insight panel (full width, no regional comparison — moved to dedicated slide)
insight = shape_rounded(s5, Inches(0.5), Inches(5.15), Inches(12.3), Inches(1.6), WHITE)
shape_rect(s5, Inches(0.5), Inches(5.15), Pt(5), Inches(1.6), BLUE)

text_box(s5, Inches(0.8), Inches(5.25), Inches(4), Inches(0.25),
         "KEY INSIGHT", size=10, color=BLUE, bold=True)
text_box(s5, Inches(0.8), Inches(5.5), Inches(11.5), Inches(1.1),
         "Education is EAP's strongest component, scoring 118.1 \u2014 "
         "well above the world average (107.4) and second only to Europe & "
         "Central Asia (140.8). Singapore leads globally with an HLO of 594. "
         "EAP averages 10.8 expected years of schooling. "
         "Tertiary enrollment (37.4%) and pre-primary (0.59 years) "
         "remain areas for growth across the region.",
         size=10, color=DARK_TEXT)

add_footer(s5, 9)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — EMPLOYMENT COMPONENT (styled like slides 5 & 6)
# ══════════════════════════════════════════════════════════════════════════════
s6 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s6, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s6, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s6, Inches(0), Inches(1.0), Inches(13.333), Pt(4), ORANGE)
text_box(s6, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Employment Component  |  East Asia & Pacific", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s6, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Avg: 40.7 / 70", size=22, color=ORANGE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s6, Inches(0.6), Inches(1.35), Inches(10), Inches(0.4),
         "Employment captures labor force participation, wage employment, and skill accumulation for youth (15\u201324) and working-age (25\u201365).",
         size=11, color=MEDIUM_GRAY)

# Six metric cards — 3 per row (Youth top, Working Age bottom)
# Format: (label, value, unit, num_val, max_val, color, world_lbl, best_lbl, world_num)

# Row 1: Youth (15-24) indicators
emp_row1 = [
    ("LFP Youth\n(15\u201324)", "60.0%", "EAP average", 60.0, 100, EMPLOY_CLR,
     "World: 48.2%", "Best: Nauru 79.7%", 48.2),
    ("Emp. Rate Youth\n(15\u201324)", "53.0%", "EAP average", 53.0, 100, EMPLOY_CLR,
     "World: 39.6%", "Best: Cambodia 68.5%", 39.6),
    ("Wage Emp.\nYouth", "75.2%", "wage share of employment", 75.2, 100, EMPLOY_CLR,
     "World: 55.1%", "Best: Japan 93.8%", 55.1),
]

# Row 2: Working Age (25-65) indicators
emp_row2 = [
    ("LFP Working Age\n(25\u201365)", "75.3%", "EAP average", 75.3, 100, EMPLOY_CLR,
     "World: 72.6%", "Best: Palau 87.8%", 72.6),
    ("Emp. Rate Working Age\n(25\u201365)", "72.5%", "EAP average", 72.5, 100, EMPLOY_CLR,
     "World: 68.8%", "Best: Palau 85.2%", 68.8),
    ("Wage Emp.\nWorking Age", "71.0%", "wage share of employment", 71.0, 100, EMPLOY_CLR,
     "World: 59.8%", "Best: Japan 92.4%", 59.8),
]

# Row label
text_box(s6, Inches(0.5), Inches(1.7), Inches(3), Inches(0.25),
         "YOUTH (15\u201324)", size=10, color=EMPLOY_CLR, bold=True)

card_w = Inches(3.85)
card_h = Inches(1.75)
gap_x = Inches(0.25)

for i, (label, value, unit, num_val, max_val, color, world_lbl, best_lbl, world_num) in enumerate(emp_row1):
    x = Inches(0.5) + i * (card_w + gap_x)
    y_top = Inches(1.95)
    card = shape_rounded(s6, x, y_top, card_w, card_h, WHITE)
    shape_rect(s6, x, y_top, card_w, Pt(3), color)

    text_box(s6, x + Inches(0.1), y_top + Inches(0.1), card_w - Inches(0.2), Inches(0.4),
             label, size=9, color=DARK_TEXT, bold=True)
    text_box(s6, x + Inches(0.1), y_top + Inches(0.45), Inches(1.5), Inches(0.4),
             value, size=26, color=color, bold=True, font="Calibri Light")
    text_box(s6, x + Inches(1.6), y_top + Inches(0.5), card_w - Inches(1.7), Inches(0.2),
             unit, size=7, color=MEDIUM_GRAY)

    bar_l = x + Inches(0.1)
    bar_w = card_w - Inches(0.2)
    draw_horizontal_bar(s6, bar_l, y_top + Inches(0.95), bar_w, Inches(0.1), num_val, max_val, color)

    # World avg cranberry dash
    w_x = bar_l + int(bar_w * (world_num / max_val))
    shape_rect(s6, w_x, y_top + Inches(0.88), Pt(2), Inches(0.25), WORLD_CLR)
    text_box(s6, w_x - Inches(0.2), y_top + Inches(1.12), Inches(0.5), Inches(0.12),
             "World", size=5, color=WORLD_CLR, align=PP_ALIGN.CENTER)

    text_box(s6, x + Inches(0.1), y_top + Inches(1.25), card_w - Inches(0.2), Inches(0.18),
             world_lbl, size=7, color=MEDIUM_GRAY)
    text_box(s6, x + Inches(0.1), y_top + Inches(1.43), card_w - Inches(0.2), Inches(0.18),
             best_lbl, size=7, color=EAP_ACCENT, bold=True)

# Row 2 label
text_box(s6, Inches(0.5), Inches(3.85), Inches(3), Inches(0.25),
         "WORKING AGE (25\u201365)", size=10, color=EMPLOY_CLR, bold=True)

for i, (label, value, unit, num_val, max_val, color, world_lbl, best_lbl, world_num) in enumerate(emp_row2):
    x = Inches(0.5) + i * (card_w + gap_x)
    y_top = Inches(4.1)
    card = shape_rounded(s6, x, y_top, card_w, card_h, WHITE)
    shape_rect(s6, x, y_top, card_w, Pt(3), color)

    text_box(s6, x + Inches(0.1), y_top + Inches(0.1), card_w - Inches(0.2), Inches(0.4),
             label, size=9, color=DARK_TEXT, bold=True)
    text_box(s6, x + Inches(0.1), y_top + Inches(0.45), Inches(1.5), Inches(0.4),
             value, size=26, color=color, bold=True, font="Calibri Light")
    text_box(s6, x + Inches(1.6), y_top + Inches(0.5), card_w - Inches(1.7), Inches(0.2),
             unit, size=7, color=MEDIUM_GRAY)

    bar_l = x + Inches(0.1)
    bar_w = card_w - Inches(0.2)
    draw_horizontal_bar(s6, bar_l, y_top + Inches(0.95), bar_w, Inches(0.1), num_val, max_val, color)

    # World avg cranberry dash
    w_x = bar_l + int(bar_w * (world_num / max_val))
    shape_rect(s6, w_x, y_top + Inches(0.88), Pt(2), Inches(0.25), WORLD_CLR)
    text_box(s6, w_x - Inches(0.2), y_top + Inches(1.12), Inches(0.5), Inches(0.12),
             "World", size=5, color=WORLD_CLR, align=PP_ALIGN.CENTER)

    text_box(s6, x + Inches(0.1), y_top + Inches(1.25), card_w - Inches(0.2), Inches(0.18),
             world_lbl, size=7, color=MEDIUM_GRAY)
    text_box(s6, x + Inches(0.1), y_top + Inches(1.43), card_w - Inches(0.2), Inches(0.18),
             best_lbl, size=7, color=EAP_ACCENT, bold=True)

# Insight panel (full width, no regional comparison — moved to dedicated slide)
insight6 = shape_rounded(s6, Inches(0.5), Inches(5.95), Inches(12.3), Inches(0.85), WHITE)
shape_rect(s6, Inches(0.5), Inches(5.95), Pt(4), Inches(0.85), ORANGE)
text_box(s6, Inches(0.8), Inches(5.98), Inches(4.6), Inches(0.2),
         "KEY INSIGHT", size=9, color=ORANGE, bold=True)
text_box(s6, Inches(0.8), Inches(6.18), Inches(11.5), Inches(0.55),
         "EAP employment (40.7) ranks 3rd among regions, above world avg (37.2). "
         "Youth LFP (60.0%) far exceeds global avg (48.2%). Japan leads wage employment; "
         "Palau and Nauru post strong LFP rates.",
         size=8, color=DARK_TEXT)

add_footer(s6, 10)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — GENDER SCATTER: Male HCI+ vs Female HCI+
# ══════════════════════════════════════════════════════════════════════════════
from pptx.chart.data import XyChartData

# Colors inspired by the bar chart reference (steel blue & salmon/coral)
SCATTER_BLUE = RGBColor(0x6B, 0x8C, 0xA3)   # steel blue — Male > Female
SCATTER_RED  = RGBColor(0xE0, 0x7B, 0x73)    # salmon/coral — Female > Male

s7 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s7, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s7, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s7, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Gender Analysis  |  Male vs Female HCI+", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s7, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "East Asia & Pacific", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Main chart panel
chart_panel = shape_rounded(s7, Inches(0.5), Inches(1.3), Inches(9.0), Inches(5.8), WHITE)

text_box(s7, Inches(0.8), Inches(1.5), Inches(7), Inches(0.3),
         "MALE HCI+ vs FEMALE HCI+ BY ECONOMY", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s7, Inches(0.8), Inches(1.85), Inches(2.5), Pt(3), EAP_ACCENT)
text_box(s7, Inches(0.8), Inches(1.95), Inches(7), Inches(0.25),
         "Countries above the 45\u00b0 line: Male HCI+ > Female HCI+. Below: Female HCI+ > Male HCI+.",
         size=9, color=MEDIUM_GRAY)

# Male vs Female HCI+ data for EAP countries
# (country, female_hci_plus, male_hci_plus)
gender_data = [
    ('Japan',         277.5, 290.8),
    ('Singapore',     284.1, 280.6),
    ('Korea, Rep.',   258.9, 274.9),
    ('Australia',     264.8, 275.2),
    ('New Zealand',   262.7, 263.5),
    ('Hong Kong',     253.8, 263.0),
    ('Macao',         260.2, 251.6),
    ('China',         225.4, 214.2),
    ('Vietnam',       220.8, 210.8),
    ('Mongolia',      214.2, 204.8),
    ('Brunei',        211.0, 204.2),
    ('Thailand',      210.5, 194.1),
    ('Malaysia',      196.3, 206.3),
    ('Fiji',          177.2, 208.4),
    ('Indonesia',     158.7, 192.1),
    ('Philippines',   171.8, 179.0),
    ('Tonga',         175.2, 176.4),
    ('Tuvalu',        173.4, 158.8),
    ('Samoa',         164.2, 164.6),
    ('Kiribati',      163.5, 160.3),
    ('Myanmar',       140.3, 158.1),
    ('Marshall Is.',  139.5, 150.9),
    ('Cambodia',      150.0, 127.8),
    ('Lao PDR',       130.5, 140.7),
    ('Vanuatu',       128.0, 144.8),
]

# Split into two series: Male > Female (blue) and Female > Male (red)
male_gt = [(n, f, m) for n, f, m in gender_data if m > f]
female_gt = [(n, f, m) for n, f, m in gender_data if f >= m]

xy_data = XyChartData()

# Series 1: Male HCI+ > Female HCI+ (blue diamonds)
s_male_gt = xy_data.add_series('Male HCI+ > Female HCI+')
for name, female, male in male_gt:
    s_male_gt.add_data_point(female, male)

# Series 2: Female HCI+ > Male HCI+ (red diamonds)
s_female_gt = xy_data.add_series('Female HCI+ \u2265 Male HCI+')
for name, female, male in female_gt:
    s_female_gt.add_data_point(female, male)

scf = s7.shapes.add_chart(
    XL_CHART_TYPE.XY_SCATTER, Inches(0.8), Inches(2.2), Inches(8.4), Inches(4.6),
    xy_data
)
sc = scf.chart
sc.has_legend = True
sc.legend.position = XL_LEGEND_POSITION.BOTTOM
sc.legend.include_in_layout = False
sc.legend.font.size = Pt(9)
sc.legend.font.name = "Calibri"

# Style axes
sc.value_axis.has_title = True
sc.value_axis.axis_title.text_frame.paragraphs[0].text = "Male HCI+"
sc.value_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(11)
sc.value_axis.axis_title.text_frame.paragraphs[0].font.name = "Calibri"
sc.value_axis.axis_title.text_frame.paragraphs[0].font.bold = True
sc.value_axis.minimum_scale = 120
sc.value_axis.maximum_scale = 300
sc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xE8, 0xE8, 0xE8)
sc.value_axis.major_gridlines.format.line.dash_style = 4  # dash
sc.value_axis.tick_labels.font.size = Pt(9)

sc.category_axis.has_title = True
sc.category_axis.axis_title.text_frame.paragraphs[0].text = "Female HCI+"
sc.category_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(11)
sc.category_axis.axis_title.text_frame.paragraphs[0].font.name = "Calibri"
sc.category_axis.axis_title.text_frame.paragraphs[0].font.bold = True
sc.category_axis.minimum_scale = 120
sc.category_axis.maximum_scale = 300
sc.category_axis.major_gridlines.format.line.color.rgb = RGBColor(0xE8, 0xE8, 0xE8)
sc.category_axis.major_gridlines.format.line.dash_style = 4  # dash
sc.category_axis.tick_labels.font.size = Pt(9)

# Color series — markers only, no connecting lines
series_blue = sc.series[0]
series_blue.format.line.fill.background()  # no line connecting dots
series_blue.marker.style = 8  # diamond
series_blue.marker.size = 8
series_blue.marker.format.fill.solid()
series_blue.marker.format.fill.fore_color.rgb = SCATTER_BLUE
series_blue.marker.format.line.color.rgb = SCATTER_BLUE

series_red = sc.series[1]
series_red.format.line.fill.background()  # no line connecting dots
series_red.marker.style = 8  # diamond
series_red.marker.size = 8
series_red.marker.format.fill.solid()
series_red.marker.format.fill.fore_color.rgb = SCATTER_RED
series_red.marker.format.line.color.rgb = SCATTER_RED

# Add 45-degree reference line as a third series (light gray)
diag_series_data = XyChartData()
# Re-add existing series data (required by python-pptx)
# We'll add the diagonal line using XML manipulation instead
# Draw a thin light gray 45° line from (120,120) to (300,300) using shapes
# Since chart coordinates don't map easily, we add a line series via XML

# Add diagonal line via a third invisible series
from lxml import etree

# Access the chart XML to add a reference line series
chart_part = sc.part
chart_xml = chart_part._element

# Find the scatterChart element
ns = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
ns_a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
scatter_chart = chart_xml.find('.//' + qn('c:scatterChart'))

if scatter_chart is not None:
    # Create a new series for the 45-degree line
    new_ser = etree.SubElement(scatter_chart, qn('c:ser'))

    idx_el = etree.SubElement(new_ser, qn('c:idx'))
    idx_el.set('val', '2')
    order_el = etree.SubElement(new_ser, qn('c:order'))
    order_el.set('val', '2')

    # Series name
    tx = etree.SubElement(new_ser, qn('c:tx'))
    str_ref = etree.SubElement(tx, qn('c:strRef'))
    f_el = etree.SubElement(str_ref, qn('c:f'))
    f_el.text = ''
    str_cache = etree.SubElement(str_ref, qn('c:strCache'))
    pt_count = etree.SubElement(str_cache, qn('c:ptCount'))
    pt_count.set('val', '1')
    pt = etree.SubElement(str_cache, qn('c:pt'))
    pt.set('idx', '0')
    v_el = etree.SubElement(pt, qn('c:v'))
    v_el.text = '45\u00b0 line'

    # Series formatting: light gray line, no markers
    spPr = etree.SubElement(new_ser, qn('c:spPr'))
    ln = etree.SubElement(spPr, qn('a:ln'))
    ln.set('w', '12700')  # 1pt line
    solidFill = etree.SubElement(ln, qn('a:solidFill'))
    srgbClr = etree.SubElement(solidFill, qn('a:srgbClr'))
    srgbClr.set('val', 'CCCCCC')

    # No markers
    marker = etree.SubElement(new_ser, qn('c:marker'))
    symbol = etree.SubElement(marker, qn('c:symbol'))
    symbol.set('val', 'none')

    # X values
    xVal = etree.SubElement(new_ser, qn('c:xVal'))
    numRef = etree.SubElement(xVal, qn('c:numRef'))
    f_x = etree.SubElement(numRef, qn('c:f'))
    f_x.text = ''
    numCache_x = etree.SubElement(numRef, qn('c:numCache'))
    ptCount_x = etree.SubElement(numCache_x, qn('c:ptCount'))
    ptCount_x.set('val', '2')
    for i, val in enumerate([120, 300]):
        pt_x = etree.SubElement(numCache_x, qn('c:pt'))
        pt_x.set('idx', str(i))
        v_x = etree.SubElement(pt_x, qn('c:v'))
        v_x.text = str(val)

    # Y values
    yVal = etree.SubElement(new_ser, qn('c:yVal'))
    numRef_y = etree.SubElement(yVal, qn('c:numRef'))
    f_y = etree.SubElement(numRef_y, qn('c:f'))
    f_y.text = ''
    numCache_y = etree.SubElement(numRef_y, qn('c:numCache'))
    ptCount_y = etree.SubElement(numCache_y, qn('c:ptCount'))
    ptCount_y.set('val', '2')
    for i, val in enumerate([120, 300]):
        pt_y = etree.SubElement(numCache_y, qn('c:pt'))
        pt_y.set('idx', str(i))
        v_y = etree.SubElement(pt_y, qn('c:v'))
        v_y.text = str(val)

    # Smooth line
    smooth = etree.SubElement(new_ser, qn('c:smooth'))
    smooth.set('val', '0')

# Add country labels as text boxes overlaid on chart area
# Chart area: left=0.8", top=2.2", width=8.4", height=4.6"
# Data range: x (Female) 120-300, y (Male) 120-300
chart_left = Inches(0.8)
chart_top = Inches(2.2)
chart_w = Inches(8.4)
chart_h = Inches(4.6)
# Approximate plot area within chart (accounting for axes/labels)
plot_left = chart_left + Inches(0.6)
plot_top = chart_top + Inches(0.15)
plot_w = chart_w - Inches(1.0)
plot_h = chart_h - Inches(0.7)
data_min = 120
data_max = 300

def data_to_pos(female_val, male_val):
    px = plot_left + int(plot_w * (female_val - data_min) / (data_max - data_min))
    py = plot_top + int(plot_h * (1 - (male_val - data_min) / (data_max - data_min)))
    return px, py

# Add country code labels
country_codes = {
    'Japan': 'JPN', 'Singapore': 'SGP', 'Korea, Rep.': 'KOR',
    'Australia': 'AUS', 'New Zealand': 'NZL', 'Hong Kong': 'HKG',
    'Macao': 'MAC', 'China': 'CHN', 'Vietnam': 'VNM',
    'Mongolia': 'MNG', 'Brunei': 'BRN', 'Thailand': 'THA',
    'Malaysia': 'MYS', 'Fiji': 'FJI', 'Indonesia': 'IDN',
    'Philippines': 'PHL', 'Tonga': 'TON', 'Tuvalu': 'TUV',
    'Samoa': 'WSM', 'Kiribati': 'KIR', 'Myanmar': 'MMR',
    'Marshall Is.': 'MHL', 'Cambodia': 'KHM', 'Lao PDR': 'LAO',
    'Vanuatu': 'VUT',
}

for name, female, male in gender_data:
    code = country_codes.get(name, name[:3].upper())
    px, py = data_to_pos(female, male)
    lbl_color = SCATTER_RED if female >= male else SCATTER_BLUE
    text_box(s7, px - Inches(0.2), py - Inches(0.22), Inches(0.6), Inches(0.2),
             code, size=7, color=lbl_color, bold=True, align=PP_ALIGN.CENTER)


# RIGHT — Insight panel
right_panel = shape_rounded(s7, Inches(9.8), Inches(1.3), Inches(3.1), Inches(5.8), WHITE)
shape_rect(s7, Inches(9.8), Inches(1.3), Pt(5), Inches(5.8), EAP_ACCENT)

text_box(s7, Inches(10.1), Inches(1.5), Inches(2.7), Inches(0.25),
         "GENDER ANALYSIS", size=11, color=EAP_ACCENT, bold=True)

# Legend items
shape_rect(s7, Inches(10.1), Inches(1.9), Inches(0.25), Inches(0.15), SCATTER_BLUE)
text_box(s7, Inches(10.45), Inches(1.87), Inches(2.3), Inches(0.2),
         "Male HCI+ > Female HCI+", size=8, color=DARK_TEXT)
shape_rect(s7, Inches(10.1), Inches(2.15), Inches(0.25), Inches(0.15), SCATTER_RED)
text_box(s7, Inches(10.45), Inches(2.12), Inches(2.3), Inches(0.2),
         "Female HCI+ \u2265 Male HCI+", size=8, color=DARK_TEXT)

shape_rect(s7, Inches(10.1), Inches(2.45), Inches(2.7), Pt(1), DIVIDER)

text_box(s7, Inches(10.1), Inches(2.6), Inches(2.7), Inches(0.25),
         "KEY FINDINGS", size=10, color=EAP_ACCENT, bold=True)

findings = [
    ("Above 45\u00b0 line", f"{len(male_gt)} economies", "Male HCI+ exceeds Female"),
    ("Below 45\u00b0 line", f"{len(female_gt)} economies", "Female HCI+ exceeds Male"),
    ("Largest male\nadvantage", "Indonesia (+33.4)\nFiji (+31.2)", ""),
    ("Largest female\nadvantage", "Cambodia (\u221222.2)\nThailand (\u221216.4)", ""),
]

fy = Inches(2.9)
for title, value, sub in findings:
    text_box(s7, Inches(10.1), fy, Inches(2.7), Inches(0.3),
             title, size=9, color=MEDIUM_GRAY)
    text_box(s7, Inches(10.1), fy + Inches(0.25), Inches(2.7), Inches(0.35),
             value, size=10, color=DARK_TEXT, bold=True)
    if sub:
        text_box(s7, Inches(10.1), fy + Inches(0.55), Inches(2.7), Inches(0.2),
                 sub, size=8, color=MEDIUM_GRAY)
    fy += Inches(0.75)

shape_rect(s7, Inches(10.1), fy, Inches(2.7), Pt(1), DIVIDER)
fy += Inches(0.15)

text_box(s7, Inches(10.1), fy, Inches(2.7), Inches(0.25),
         "KEY INSIGHT", size=10, color=EAP_ACCENT, bold=True)
text_box(s7, Inches(10.1), fy + Inches(0.3), Inches(2.7), Inches(1.5),
         "Most EAP economies show higher male HCI+, "
         "driven largely by employment gaps. However, "
         "several countries \u2014 notably Cambodia, Thailand, "
         "China, and Vietnam \u2014 show female advantage, "
         "reflecting higher female education outcomes "
         "and labor force participation in these economies.",
         size=9, color=DARK_TEXT)

add_footer(s7, 11)


# ══════════════════════════════════════════════════════════════════════════════
# GENERATE EAP CHOROPLETH MAP IMAGE
# ══════════════════════════════════════════════════════════════════════════════
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
import numpy as np

# HCI+ data for EAP countries (ISO A3 codes → HCI+ score)
eap_hci_data = {
    'JPN': 284.3, 'SGP': 282.4, 'KOR': 266.9, 'AUS': 270.0,
    'NZL': 263.1, 'HKG': 258.4, 'MAC': 255.9, 'CHN': 219.8,
    'VNM': 215.8, 'MNG': 209.5, 'BRN': 207.6, 'THA': 202.3,
    'MYS': 201.3, 'FJI': 192.8, 'IDN': 175.4, 'PHL': 175.4,
    'TON': 175.8, 'TUV': 166.1, 'KIR': 161.9, 'WSM': 164.4,
    'MMR': 149.2, 'KHM': 138.9, 'LAO': 135.6, 'VUT': 136.4,
    'MHL': 145.2, 'NRU': 161.6, 'PLW': 228.6,
}

# All EAP ISO codes (including those without data)
eap_isos = set(eap_hci_data.keys()) | {'PRK', 'TLS', 'PNG', 'SLB', 'FSM'}

def get_color_category(score):
    if score is None:
        return '#666666'  # NA - dark gray
    elif score >= 250:
        return '#6BAED6'  # Between 250 and 325 - blue
    elif score >= 200:
        return '#BDD7E7'  # Between 200 and 250 - light blue
    elif score >= 150:
        return '#FDD835'  # Between 150 and 200 - yellow
    elif score >= 100:
        return '#FFAB91'  # Between 100 and 150 - salmon/orange
    else:
        return '#E53935'  # Below 100 - red

# Load world shapefile from pyogrio test fixtures
world = gpd.read_file('/usr/local/lib/python3.11/dist-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp')

# Fix ISO codes for some countries
world.loc[world['name'] == 'China', 'iso_a3'] = 'CHN'
world.loc[world['name'] == 'France', 'iso_a3'] = 'FRA'
world.loc[world['name'] == 'Norway', 'iso_a3'] = 'NOR'

# Assign colors
def assign_color(row):
    iso = row['iso_a3']
    if iso in eap_hci_data:
        return get_color_category(eap_hci_data[iso])
    elif iso in eap_isos:
        return '#666666'  # EAP country without data
    else:
        return '#E8E8E8'  # Non-EAP (very light gray, not shown prominently)

world['color'] = world.apply(assign_color, axis=1)

# Create the map figure - focus on EAP region
fig, ax = plt.subplots(1, 1, figsize=(16, 9), facecolor='#F0F0F0')
ax.set_facecolor('#F0F0F0')

# Plot all countries (non-EAP in very light gray for context)
non_eap = world[~world['iso_a3'].isin(eap_isos)]
non_eap.plot(ax=ax, color='#E0E0E0', edgecolor='white', linewidth=0.5)

# Plot EAP countries with colors
eap_world = world[world['iso_a3'].isin(eap_isos)]
eap_world.plot(ax=ax, color=eap_world['color'], edgecolor='white', linewidth=0.8)

# Focus on EAP region
ax.set_xlim(60, 190)
ax.set_ylim(-50, 55)
ax.axis('off')

# Title - two parts with different colors
ax.set_title('', pad=20)  # clear default title
fig.text(0.39, 0.94, 'HCI+ 2025 in ', fontsize=28, fontweight='bold',
         color='#002B49', ha='right', va='center', fontfamily='sans-serif',
         transform=fig.transFigure)
fig.text(0.39, 0.94, '                    East Asia & Pacific', fontsize=28, fontweight='bold',
         color='#006EAF', ha='left', va='center', fontfamily='sans-serif',
         transform=fig.transFigure)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor='#6BAED6', edgecolor='white', label='Between 250 and 325'),
    mpatches.Patch(facecolor='#BDD7E7', edgecolor='white', label='Between 200 and 250'),
    mpatches.Patch(facecolor='#FDD835', edgecolor='white', label='Between 150 and 200'),
    mpatches.Patch(facecolor='#FFAB91', edgecolor='white', label='Between 100 and 150'),
    mpatches.Patch(facecolor='#E53935', edgecolor='white', label='Below 100'),
    mpatches.Patch(facecolor='#666666', edgecolor='white', label='NA'),
]

legend = ax.legend(handles=legend_elements, loc='lower left', fontsize=11,
                   title='The HCI+ 2025:', title_fontsize=12,
                   frameon=True, facecolor='#F0F0F0', edgecolor='none',
                   bbox_to_anchor=(0.01, 0.02))
legend.get_title().set_fontweight('bold')

# Bottom bar with branding
fig.patches.append(plt.Rectangle((0, 0), 1, 0.04, transform=fig.transFigure,
                                  facecolor='#E0E0E0', zorder=10))
fig.text(0.95, 0.02, 'HCI+ 2025', fontsize=14, fontweight='bold',
         color='#006EAF', ha='right', va='center', transform=fig.transFigure)

# Accent line under title
ax_pos = ax.get_position()
fig.patches.append(plt.Rectangle((0.08, 0.88), 0.15, 0.004,
                                  transform=fig.transFigure,
                                  facecolor='#002B49', zorder=10))

map_path = '/home/user/arcidiaconom.github.io/eap_hci_map.png'
plt.savefig(map_path, dpi=200, bbox_inches='tight', facecolor='#F0F0F0',
            edgecolor='none', pad_inches=0.2)
plt.close()
print(f"Map saved: {map_path}")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — EAP CHOROPLETH MAP
# ══════════════════════════════════════════════════════════════════════════════
s8 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s8, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s8, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s8, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  HCI+ Map", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s8, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "2025", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Insert map image
s8.shapes.add_picture(map_path, Inches(0.3), Inches(1.1), Inches(12.7), Inches(5.8))

add_footer(s8, 12)


# ── Save ──────────────────────────────────────────────────────────────────────
output_path = "/home/user/arcidiaconom.github.io/EAP_HCI_Plus_2025_v4.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
