#!/usr/bin/env python3
"""
Create a professional 6-slide PowerPoint for East Asia & Pacific HCI+ data.
Regional focus with comparisons to other regions and world averages.
Bubble chart highlights EAP countries, all others transparent/faded.
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
TEAL          = RGBColor(0x00, 0x88, 0x9E)
BLUE          = RGBColor(0x00, 0x6E, 0xAF)
ORANGE        = RGBColor(0xE8, 0x7D, 0x1E)
CORAL         = RGBColor(0xE0, 0x5A, 0x4F)
DARK_BLUE     = RGBColor(0x1B, 0x3A, 0x5C)
LIGHT_BG      = RGBColor(0xF7, 0xF8, 0xFA)
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT      = RGBColor(0x1A, 0x1A, 0x2E)
MEDIUM_GRAY   = RGBColor(0x7A, 0x7A, 0x8C)
LIGHT_GRAY    = RGBColor(0xE0, 0xE2, 0xE6)
DIVIDER       = RGBColor(0xD0, 0xD5, 0xDD)
GREEN_POS     = RGBColor(0x2E, 0xA0, 0x6A)
LIGHT_TEAL    = RGBColor(0xE0, 0xF5, 0xF5)
BENCHMARK_GRAY = RGBColor(0xBB, 0xBB, 0xCC)
# Faded gray for non-EAP bubbles
FADED_GRAY    = RGBColor(0xCC, 0xCC, 0xCC)

# EAP accent - bright blue
EAP_ACCENT    = RGBColor(0x00, 0x6E, 0xAF)

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
         size=9, color=ORANGE, bold=True, align=PP_ALIGN.CENTER)


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

# Bubble chart data — EAP countries colored, all others faded gray
bubble_data = BubbleChartData()

# Series 1: Non-EAP countries (gray/transparent)
non_eap_countries = [
    # SSA
    ('Nigeria', 8.64, 130.7, 5), ('South Africa', 9.52, 132.1, 5),
    ('Kenya', 8.67, 170.8, 5), ('Ethiopia', 7.97, 123.4, 5),
    ('Ghana', 8.86, 152.9, 3), ('Rwanda', 8.09, 156.9, 3),
    ('Uganda', 7.97, 145.2, 3), ('Tanzania', 8.22, 132.6, 3),
    ('Mauritius', 10.22, 201.0, 3), ('Senegal', 8.41, 109.4, 3),
    ('Botswana', 9.80, 156.9, 3),
    # Europe & Central Asia
    ('Germany', 11.05, 256.5, 5), ('France', 10.91, 251.2, 5),
    ('Sweden', 11.05, 269.3, 3), ('Poland', 10.72, 259.5, 3),
    ('Netherlands', 11.17, 269.7, 3), ('Turkiye', 10.32, 210.5, 5),
    ('Albania', 9.85, 203.5, 3), ('Kyrgyz Republic', 8.86, 197.5, 3),
    ('Romania', 10.40, 221.3, 3), ('Georgia', 9.73, 204.7, 3),
    # Latin America
    ('Chile', 10.32, 226.2, 3), ('Brazil', 9.89, 202.9, 8),
    ('Mexico', 10.00, 193.5, 5), ('Colombia', 9.83, 197.6, 5),
    ('Argentina', 10.10, 205.3, 5), ('Jamaica', 9.24, 200.1, 3),
    ('Nicaragua', 8.94, 178.1, 3),
    # South Asia & MENA
    ('India', 9.19, 158.8, 10), ('Bangladesh', 9.05, 146.7, 5),
    ('Sri Lanka', 9.73, 182.6, 3), ('Pakistan', 8.47, 99.3, 5),
    ('Jordan', 9.16, 170.2, 3), ('Egypt', 9.73, 161.2, 5),
    ('Morocco', 9.11, 147.1, 3), ('Iran', 10.17, 196.3, 5),
    # North America
    ('United States', 11.20, 251.2, 8), ('Canada', 10.98, 257.3, 5),
]

# Series 2: EAP countries (colored)
eap_countries = [
    ('Japan', 10.74, 284.3, 8),
    ('Singapore', 11.79, 282.4, 3),
    ('Korea, Rep.', 10.83, 266.9, 5),
    ('Australia', 11.00, 270.0, 5),
    ('New Zealand', 10.78, 263.1, 3),
    ('Hong Kong', 11.10, 258.4, 3),
    ('Macao', 11.63, 255.9, 3),
    ('China', 10.08, 219.8, 12),
    ('Vietnam', 9.58, 215.8, 5),
    ('Mongolia', 9.73, 209.5, 3),
    ('Brunei', 11.28, 207.6, 3),
    ('Thailand', 9.99, 202.3, 5),
    ('Malaysia', 10.44, 201.3, 5),
    ('Fiji', 9.55, 192.8, 3),
    ('Indonesia', 9.58, 175.4, 10),
    ('Philippines', 9.25, 175.4, 5),
    ('Tonga', 8.86, 175.8, 3),
    ('Tuvalu', 8.67, 166.1, 3),
    ('Kiribati', 8.09, 161.9, 3),
    ('Myanmar', 8.57, 149.2, 5),
    ('Cambodia', 8.86, 138.9, 5),
    ('Lao PDR', 9.06, 135.6, 3),
    ('Vanuatu', 8.06, 136.4, 3),
]

# Add non-EAP as first series (will be gray)
s_non_eap = bubble_data.add_series('Other Regions')
for name, gdp, score, size in non_eap_countries:
    s_non_eap.add_data_point(gdp, score, size)

# Add EAP as second series (will be blue)
s_eap = bubble_data.add_series('East Asia & Pacific')
for name, gdp, score, size in eap_countries:
    s_eap.add_data_point(gdp, score, size)

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
bc.value_axis.minimum_scale = 80
bc.value_axis.maximum_scale = 300
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
    ("World Average", "188.5", MEDIUM_GRAY),
    ("Economies", "27", DARK_TEXT),
    ("Top Performer", "Japan (284.3)", TEAL),
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

add_footer(s2, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — SCORE DECOMPOSITION & REGIONAL BENCHMARKING
# ══════════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s3, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "East Asia & Pacific  |  Score Decomposition", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s3, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "201.7 / 325", size=22, color=EAP_ACCENT, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# LEFT — Regional composition stacked bar
left_panel = shape_rounded(s3, Inches(0.5), Inches(1.3), Inches(6.0), Inches(5.4), WHITE)

text_box(s3, Inches(0.8), Inches(1.5), Inches(5), Inches(0.3),
         "COMPONENT DECOMPOSITION BY REGION", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s3, Inches(0.8), Inches(1.85), Inches(2), Pt(3), EAP_ACCENT)

chart_data = CategoryChartData()
chart_data.categories = [
    'Sub-Saharan\nAfrica', 'South\nAsia', 'Latin America\n& Caribbean',
    'MENA+', 'East Asia\n& Pacific', 'Europe &\nCentral Asia', 'World'
]
chart_data.add_series('Health',     (37.3, 41.0, 43.4, 44.9, 42.8, 45.9, 42.6))
chart_data.add_series('Education',  (64.1, 83.0, 98.3, 105.8, 118.1, 140.8, 107.4))
chart_data.add_series('Employment', (26.9, 23.4, 41.5, 35.0, 40.7, 46.6, 37.2))

cf = s3.shapes.add_chart(
    XL_CHART_TYPE.BAR_STACKED, Inches(0.8), Inches(2.0), Inches(5.5), Inches(2.8),
    chart_data
)
ch = cf.chart
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(9)
ch.legend.font.name = "Calibri"

plot = ch.plots[0]
plot.gap_width = 50
colors = [TEAL, BLUE, ORANGE]
for i, series in enumerate(plot.series):
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = colors[i]

ch.category_axis.tick_labels.font.size = Pt(9)
ch.category_axis.tick_labels.font.name = "Calibri"
ch.value_axis.maximum_scale = 280
ch.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
ch.value_axis.format.line.color.rgb = DIVIDER
ch.value_axis.tick_labels.font.size = Pt(8)

# EAP vs World dot comparisons
text_box(s3, Inches(0.8), Inches(5.0), Inches(5), Inches(0.3),
         "EAP vs WORLD AVERAGE (Filled = EAP, Hollow = World)", size=10, color=MEDIUM_GRAY, bold=True)
shape_rect(s3, Inches(0.8), Inches(5.35), Inches(2), Pt(2), EAP_ACCENT)

benchmarks = {
    "Health": (42.8, 42.6, 50),
    "Education": (118.1, 107.4, 180),
    "Employment": (40.7, 37.2, 70),
}

dot_y = Inches(5.55)
for i, (comp, (actual, bench, max_v)) in enumerate(benchmarks.items()):
    y = dot_y + Inches(i * 0.5)
    color = [TEAL, BLUE, ORANGE][i]
    draw_dot_comparison(s3, Inches(0.8), y, Inches(5.5), comp, actual, bench, max_v, color)


# RIGHT — Top EAP economies bar chart
right_panel = shape_rounded(s3, Inches(6.8), Inches(1.3), Inches(6.0), Inches(5.4), WHITE)

text_box(s3, Inches(7.1), Inches(1.5), Inches(5), Inches(0.3),
         "TOP EAP ECONOMIES BY HCI+ SCORE", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s3, Inches(7.1), Inches(1.85), Inches(2), Pt(3), EAP_ACCENT)

eap_rank_data = CategoryChartData()
eap_rank_data.categories = [
    'Lao PDR', 'Vanuatu', 'Cambodia', 'Myanmar', 'Indonesia',
    'Philippines', 'Fiji', 'Thailand', 'Malaysia', 'Mongolia',
    'Vietnam', 'China', 'Palau', 'Macao', 'Hong Kong',
    'New Zealand', 'Korea, Rep.', 'Australia', 'Singapore', 'Japan'
]
eap_rank_data.add_series('HCI+ Score', (
    135.6, 136.4, 138.9, 149.2, 175.4,
    175.4, 192.8, 202.3, 201.3, 209.5,
    215.8, 219.8, 228.6, 255.9, 258.4,
    263.1, 266.9, 270.0, 282.4, 284.3
))

rcf = s3.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.1), Inches(2.0), Inches(5.4), Inches(3.5),
    eap_rank_data
)
rc = rcf.chart
rc.has_legend = False
rplot = rc.plots[0]
rplot.gap_width = 30

series = rplot.series[0]
series.format.fill.solid()
series.format.fill.fore_color.rgb = EAP_ACCENT

# World avg line would be at 188.5 — highlight countries above/below
# Color bottom 6 (below world avg) differently
for idx in range(6):  # Lao, Vanuatu, Cambodia, Myanmar, Indonesia, Philippines
    series.points[idx].format.fill.solid()
    series.points[idx].format.fill.fore_color.rgb = CORAL

rc.category_axis.tick_labels.font.size = Pt(8)
rc.category_axis.tick_labels.font.name = "Calibri"
rc.value_axis.maximum_scale = 300
rc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
rc.value_axis.format.line.color.rgb = DIVIDER
rc.value_axis.tick_labels.font.size = Pt(8)

series.has_data_labels = True
series.data_labels.font.size = Pt(7)
series.data_labels.font.name = "Calibri"
series.data_labels.font.bold = True
series.data_labels.number_format = '0.0'

# Legend
shape_rect(s3, Inches(7.1), Inches(5.65), Inches(0.25), Inches(0.12), EAP_ACCENT)
text_box(s3, Inches(7.45), Inches(5.6), Inches(1.5), Inches(0.2),
         "Above world avg", size=8, color=DARK_TEXT)
shape_rect(s3, Inches(9.0), Inches(5.65), Inches(0.25), Inches(0.12), CORAL)
text_box(s3, Inches(9.35), Inches(5.6), Inches(1.5), Inches(0.2),
         "Below world avg", size=8, color=DARK_TEXT)

# Insight
text_box(s3, Inches(7.1), Inches(5.9), Inches(5.5), Inches(0.8),
         "KEY INSIGHT: EAP outperforms the world average in all three components. "
         "Education is the strongest pillar (118.1 vs world 107.4). "
         "However, a 2:1 gap exists between top (Japan, 284.3) and bottom performers "
         "(Lao PDR, 135.6), reflecting wide income and development disparities.",
         size=10, color=DARK_TEXT)

add_footer(s3, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — HEALTH COMPONENT
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
shape_rect(s4, world_surv_x, Inches(3.55), Pt(2), Inches(0.38), ORANGE)
text_box(s4, world_surv_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "World", size=7, color=ORANGE, align=PP_ALIGN.CENTER)

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
shape_rect(s4, world_ns_x, Inches(3.55), Pt(2), Inches(0.38), ORANGE)
text_box(s4, world_ns_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "World", size=7, color=ORANGE, align=PP_ALIGN.CENTER)

# BOTTOM — Regional health comparison
bottom_panel = shape_rounded(s4, Inches(0.5), Inches(4.7), Inches(12.3), Inches(2.1), WHITE)

text_box(s4, Inches(0.8), Inches(4.85), Inches(5), Inches(0.3),
         "HEALTH COMPONENT: REGIONAL COMPARISON", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s4, Inches(0.8), Inches(5.15), Inches(2), Pt(2), TEAL)

reg_health_data = CategoryChartData()
reg_health_data.categories = [
    'Sub-Saharan\nAfrica', 'South\nAsia', 'East Asia\n& Pacific',
    'Latin America\n& Caribbean', 'MENA+',
    'Europe &\nCentral Asia', 'World'
]
reg_health_data.add_series('Health Score', (37.3, 41.0, 42.8, 43.4, 44.9, 45.9, 42.6))

hcf = s4.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.25), Inches(11.8), Inches(1.35),
    reg_health_data
)
hc = hcf.chart
hc.has_legend = False
hp = hc.plots[0]
hp.gap_width = 50
hseries = hp.series[0]
hseries.format.fill.solid()
hseries.format.fill.fore_color.rgb = TEAL

# Highlight EAP
hseries.points[2].format.fill.solid()
hseries.points[2].format.fill.fore_color.rgb = EAP_ACCENT
# World bar different
hseries.points[6].format.fill.solid()
hseries.points[6].format.fill.fore_color.rgb = MEDIUM_GRAY

hseries.has_data_labels = True
hseries.data_labels.font.size = Pt(9)
hseries.data_labels.font.bold = True
hseries.data_labels.number_format = '0.0'

hc.category_axis.tick_labels.font.size = Pt(9)
hc.category_axis.tick_labels.font.name = "Calibri"
hc.value_axis.visible = False
hc.value_axis.has_major_gridlines = False

add_footer(s4, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — EDUCATION COMPONENT
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

# Four metric cards
metrics = [
    ("Expected Years\nof Schooling", "10.8", "years (EAP avg)", 10.8, 14, BLUE),
    ("Harmonized Learning\nOutcomes", "436", "HLO score (out of 625)", 436, 625, RGBColor(0x00, 0x5A, 0x9E)),
    ("Pre-Primary\nEducation", "0.59", "learning-adj. years", 0.59, 1.0, TEAL),
    ("Tertiary\nEnrollment", "37.4%", "gross enrollment rate", 37.4, 100, ORANGE),
]

for i, (label, value, unit, num_val, max_val, color) in enumerate(metrics):
    x = Inches(0.5) + i * Inches(3.15)
    card = shape_rounded(s5, x, Inches(2.0), Inches(2.95), Inches(2.5), WHITE)
    shape_rect(s5, x, Inches(2.0), Inches(2.95), Pt(4), color)

    text_box(s5, x + Inches(0.15), Inches(2.2), Inches(2.65), Inches(0.5),
             label, size=11, color=DARK_TEXT, bold=True)

    text_box(s5, x + Inches(0.15), Inches(2.8), Inches(2.65), Inches(0.7),
             value, size=36, color=color, bold=True, font="Calibri Light")

    text_box(s5, x + Inches(0.15), Inches(3.5), Inches(2.65), Inches(0.25),
             unit, size=9, color=MEDIUM_GRAY)

    draw_horizontal_bar(s5, x + Inches(0.15), Inches(3.85), Inches(2.65), Inches(0.12),
                       num_val, max_val, color)

    pct = num_val / max_val * 100
    text_box(s5, x + Inches(0.15), Inches(4.05), Inches(2.65), Inches(0.2),
             f"{pct:.0f}% of maximum", size=8, color=MEDIUM_GRAY)

# Bottom — Regional education comparison
bottom = shape_rounded(s5, Inches(0.5), Inches(4.75), Inches(7.5), Inches(2.0), WHITE)

text_box(s5, Inches(0.8), Inches(4.9), Inches(5), Inches(0.3),
         "EDUCATION COMPONENT: REGIONAL COMPARISON", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s5, Inches(0.8), Inches(5.2), Inches(2), Pt(2), BLUE)

edu_comp_data = CategoryChartData()
edu_comp_data.categories = [
    'Sub-Saharan\nAfrica', 'South\nAsia', 'Latin America\n& Caribbean',
    'MENA+', 'East Asia\n& Pacific',
    'Europe &\nCentral Asia', 'World'
]
edu_comp_data.add_series('Education Score', (64.1, 83.0, 98.3, 105.8, 118.1, 140.8, 107.4))

ecf = s5.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.3), Inches(7.0), Inches(1.3),
    edu_comp_data
)
ec = ecf.chart
ec.has_legend = False
ep = ec.plots[0]
ep.gap_width = 50
eseries = ep.series[0]
eseries.format.fill.solid()
eseries.format.fill.fore_color.rgb = BLUE
eseries.points[4].format.fill.solid()
eseries.points[4].format.fill.fore_color.rgb = EAP_ACCENT
eseries.points[6].format.fill.solid()
eseries.points[6].format.fill.fore_color.rgb = MEDIUM_GRAY

eseries.has_data_labels = True
eseries.data_labels.font.size = Pt(9)
eseries.data_labels.font.bold = True
eseries.data_labels.number_format = '0.0'

ec.category_axis.tick_labels.font.size = Pt(9)
ec.value_axis.visible = False
ec.value_axis.has_major_gridlines = False

# Insight
insight = shape_rounded(s5, Inches(8.3), Inches(4.75), Inches(4.5), Inches(2.0), WHITE)
shape_rect(s5, Inches(8.3), Inches(4.75), Pt(5), Inches(2.0), BLUE)

text_box(s5, Inches(8.6), Inches(4.9), Inches(4), Inches(0.25),
         "KEY INSIGHT", size=10, color=BLUE, bold=True)
text_box(s5, Inches(8.6), Inches(5.2), Inches(4), Inches(1.4),
         "Education is EAP's strongest component, scoring 118.1 \u2014 "
         "well above the world average (107.4) and second only to Europe & "
         "Central Asia (140.8). Singapore leads globally with an HLO of 594. "
         "EAP averages 10.8 expected years of schooling. "
         "Tertiary enrollment (37.4%) and pre-primary (0.59 years) "
         "remain areas for growth across the region.",
         size=10, color=DARK_TEXT)

add_footer(s5, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — EMPLOYMENT + GENDER GAP
# ══════════════════════════════════════════════════════════════════════════════
s6 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s6, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

shape_rect(s6, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s6, Inches(0), Inches(1.0), Inches(13.333), Pt(4), ORANGE)
text_box(s6, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Employment & Gender Gap  |  East Asia & Pacific", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s6, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Avg: 40.7 / 70", size=22, color=ORANGE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s6, Inches(0.6), Inches(1.35), Inches(10), Inches(0.4),
         "Employment captures labor force participation, wage employment, and skill accumulation for youth (15\u201324) and working-age (25\u201365).",
         size=11, color=MEDIUM_GRAY)

# LEFT — Employment indicators table
left = shape_rounded(s6, Inches(0.5), Inches(2.0), Inches(6.0), Inches(3.0), WHITE)
shape_rect(s6, Inches(0.5), Inches(2.0), Inches(6.0), Pt(4), ORANGE)

text_box(s6, Inches(0.8), Inches(2.2), Inches(3), Inches(0.25),
         "EAP EMPLOYMENT INDICATORS (AVG)", size=11, color=ORANGE, bold=True)

headers = [("", 2.0), ("EAP", 0.8), ("World", 0.8), ("Europe", 0.8)]
hx = Inches(0.8)
for label, w in headers:
    color = MEDIUM_GRAY if label == "" else (EAP_ACCENT if label == "EAP" else MEDIUM_GRAY)
    text_box(s6, hx, Inches(2.6), Inches(w), Inches(0.25),
             label, size=10, color=color, bold=True,
             align=PP_ALIGN.CENTER if label else PP_ALIGN.LEFT)
    hx += Inches(w)

shape_rect(s6, Inches(0.8), Inches(2.85), Inches(4.4), Pt(1), DIVIDER)

rows_data = [
    ("LFP Youth (15\u201324)",    "60.0%", "48.2%", "46.7%"),
    ("Wage Emp. Youth",          "75.2%", "55.1%", "80.3%"),
    ("LFP Working Age (25\u201365)", "75.3%", "72.6%", "78.2%"),
    ("Wage Emp. Working Age",    "71.0%", "59.8%", "82.1%"),
]

for j, (ind, eap_v, world_v, eur_v) in enumerate(rows_data):
    ry = Inches(2.95 + j * 0.45)
    bg_color = WHITE if j % 2 == 0 else RGBColor(0xF9, 0xFA, 0xFB)
    shape_rect(s6, Inches(0.8), ry, Inches(4.4), Inches(0.4), bg_color)

    rx = Inches(0.8)
    vals = [(ind, 2.0, DARK_TEXT, False), (eap_v, 0.8, EAP_ACCENT, True),
            (world_v, 0.8, MEDIUM_GRAY, False), (eur_v, 0.8, MEDIUM_GRAY, False)]
    for val, w, col, bld in vals:
        text_box(s6, rx, ry + Inches(0.05), Inches(w), Inches(0.3),
                 val, size=10, color=col, bold=bld,
                 align=PP_ALIGN.CENTER if w == 0.8 else PP_ALIGN.LEFT)
        rx += Inches(w)


# RIGHT — Gender gap by region
right = shape_rounded(s6, Inches(6.8), Inches(2.0), Inches(6.0), Inches(3.0), WHITE)
shape_rect(s6, Inches(6.8), Inches(2.0), Inches(6.0), Pt(4), ORANGE)

text_box(s6, Inches(7.1), Inches(2.15), Inches(5), Inches(0.3),
         "GENDER GAP BY REGION (Male \u2212 Female HCI+)", size=11, color=ORANGE, bold=True)
text_box(s6, Inches(7.1), Inches(2.4), Inches(5.5), Inches(0.25),
         "Positive = men outperform; Negative = women outperform",
         size=9, color=MEDIUM_GRAY)

gender_gap_data = CategoryChartData()
gender_gap_data.categories = [
    'Sub-Saharan\nAfrica', 'South\nAsia', 'MENA+',
    'Latin America\n& Caribbean', 'East Asia\n& Pacific',
    'Europe &\nCentral Asia'
]
# Approximate regional gender gaps (Male - Female HCI+)
gender_gap_data.add_series('Gender Gap', (5.2, 15.8, 18.3, 4.1, 5.7, -1.2))

ggf = s6.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.1), Inches(2.7), Inches(5.4), Inches(2.1),
    gender_gap_data
)
gg = ggf.chart
gg.has_legend = False
ggp = gg.plots[0]
ggp.gap_width = 60

ggseries = ggp.series[0]
ggseries.format.fill.solid()
ggseries.format.fill.fore_color.rgb = DARK_BLUE

# EAP bar highlighted
ggseries.points[4].format.fill.solid()
ggseries.points[4].format.fill.fore_color.rgb = EAP_ACCENT

# Negative (women outperform) in coral
for idx, val in enumerate([5.2, 15.8, 18.3, 4.1, 5.7, -1.2]):
    if val < 0:
        ggseries.points[idx].format.fill.solid()
        ggseries.points[idx].format.fill.fore_color.rgb = CORAL

ggseries.has_data_labels = True
ggseries.data_labels.font.size = Pt(9)
ggseries.data_labels.font.bold = True
ggseries.data_labels.number_format = '+0.0;-0.0'

gg.category_axis.tick_labels.font.size = Pt(9)
gg.category_axis.tick_labels.font.name = "Calibri"
gg.value_axis.has_major_gridlines = True
gg.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
gg.value_axis.tick_labels.font.size = Pt(8)

# Legend
shape_rect(s6, Inches(9.0), Inches(4.7), Inches(0.3), Inches(0.15), DARK_BLUE)
text_box(s6, Inches(9.4), Inches(4.65), Inches(1.5), Inches(0.2),
         "Men outperform", size=8, color=DARK_TEXT)
shape_rect(s6, Inches(10.8), Inches(4.7), Inches(0.3), Inches(0.15), CORAL)
text_box(s6, Inches(11.2), Inches(4.65), Inches(1.5), Inches(0.2),
         "Women outperform", size=8, color=DARK_TEXT)

# Bottom — EAP employment ranking + insight
bottom_left = shape_rounded(s6, Inches(0.5), Inches(5.2), Inches(7.5), Inches(1.6), WHITE)

text_box(s6, Inches(0.8), Inches(5.3), Inches(5), Inches(0.25),
         "EMPLOYMENT COMPONENT: REGIONAL COMPARISON", size=10, color=MEDIUM_GRAY, bold=True)
shape_rect(s6, Inches(0.8), Inches(5.55), Inches(1.5), Pt(2), ORANGE)

emp_reg_data = CategoryChartData()
emp_reg_data.categories = [
    'South\nAsia', 'Sub-Saharan\nAfrica', 'MENA+',
    'World', 'East Asia\n& Pacific',
    'Latin America\n& Caribbean', 'Europe &\nCentral Asia'
]
emp_reg_data.add_series('Employment Score', (23.4, 26.9, 35.0, 37.2, 40.7, 41.5, 46.6))

emcf = s6.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.6), Inches(7.0), Inches(1.1),
    emp_reg_data
)
emc = emcf.chart
emc.has_legend = False
emp = emc.plots[0]
emp.gap_width = 50
emseries = emp.series[0]
emseries.format.fill.solid()
emseries.format.fill.fore_color.rgb = ORANGE
emseries.points[4].format.fill.solid()
emseries.points[4].format.fill.fore_color.rgb = EAP_ACCENT
emseries.points[3].format.fill.solid()
emseries.points[3].format.fill.fore_color.rgb = MEDIUM_GRAY

emseries.has_data_labels = True
emseries.data_labels.font.size = Pt(9)
emseries.data_labels.font.bold = True
emseries.data_labels.number_format = '0.0'

emc.category_axis.tick_labels.font.size = Pt(9)
emc.value_axis.visible = False
emc.value_axis.has_major_gridlines = False

# Insight
insight6 = shape_rounded(s6, Inches(8.3), Inches(5.2), Inches(4.5), Inches(1.6), WHITE)
shape_rect(s6, Inches(8.3), Inches(5.2), Pt(5), Inches(1.6), ORANGE)
text_box(s6, Inches(8.6), Inches(5.3), Inches(4), Inches(0.25),
         "KEY TAKEAWAY", size=10, color=ORANGE, bold=True)
text_box(s6, Inches(8.6), Inches(5.6), Inches(4), Inches(1.1),
         "EAP's employment score (40.7) ranks 3rd among regions and exceeds "
         "the world average (37.2). Youth LFP (60.0%) is notably high. "
         "The EAP gender gap (+5.7) is moderate \u2014 better than South Asia "
         "(+15.8) and MENA (+18.3), but wider than Europe (\u22121.2). "
         "Countries like Indonesia (+22.6) and Fiji (+25.2) drive the gap, "
         "while Cambodia (\u221214.2) and Thailand (\u22128.1) favor women.",
         size=10, color=DARK_TEXT)

add_footer(s6, 5)


# ── Save ──────────────────────────────────────────────────────────────────────
output_path = "/home/user/arcidiaconom.github.io/EAP_HCI_Plus_2025.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
