#!/usr/bin/env python3
"""
Create a professional 5-slide PowerPoint for Kenya HCI+ data.
Version 2: Charts styled to match the HCI+ webpage visualizations.
- Semicircle gauge for overall score
- Horizontal decomposition waterfall bars
- Filled vs hollow circle comparisons (actual vs benchmark)
- Diverging gender gap bars
- Scatter/bubble context chart
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData, XyChartData, BubbleChartData
import math

# ── Color Palette (matching HCI+ website style) ──────────────────────────────
# The HCI+ site uses a teal/dark blue primary with orange for highlights
PRIMARY       = RGBColor(0x00, 0x2244 >> 8, 0x44)  # Deep teal-navy
PRIMARY       = RGBColor(0x00, 0x2B, 0x49)
TEAL          = RGBColor(0x00, 0x88, 0x9E)   # Teal (health)
BLUE          = RGBColor(0x00, 0x6E, 0xAF)   # Blue (education)
ORANGE        = RGBColor(0xE8, 0x7D, 0x1E)   # Orange (employment / highlight)
CORAL         = RGBColor(0xE0, 0x5A, 0x4F)   # Coral (female)
DARK_BLUE     = RGBColor(0x1B, 0x3A, 0x5C)   # Dark blue (male)
LIGHT_BG      = RGBColor(0xF7, 0xF8, 0xFA)   # Near-white background
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT      = RGBColor(0x1A, 0x1A, 0x2E)
MEDIUM_GRAY   = RGBColor(0x7A, 0x7A, 0x8C)
LIGHT_GRAY    = RGBColor(0xE0, 0xE2, 0xE6)
DIVIDER       = RGBColor(0xD0, 0xD5, 0xDD)
GREEN_POS     = RGBColor(0x2E, 0xA0, 0x6A)   # Positive change
LIGHT_TEAL    = RGBColor(0xE0, 0xF5, 0xF5)
BENCHMARK_GRAY = RGBColor(0xBB, 0xBB, 0xCC)  # Hollow circle / benchmark

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
    """Draw a circle centered at (cx, cy)."""
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
             f"humancapital.worldbank.org/hciplus", size=8,
             color=TEAL, align=PP_ALIGN.RIGHT)
    text_box(slide, Inches(12.6), Inches(7.07), Inches(0.5), Inches(0.35),
             str(num), size=8, color=WHITE, align=PP_ALIGN.RIGHT)


def draw_semicircle_gauge(slide, cx, cy, outer_r, inner_r, value, max_val,
                          track_color, fill_color, label_text=""):
    """Draw a semicircle gauge using arc segments made of thin pie slices."""
    # Background track (full semicircle)
    segments = 36
    angle_span = math.pi
    for i in range(segments):
        a1 = math.pi + (i / segments) * angle_span
        a2 = math.pi + ((i + 1) / segments) * angle_span
        filled_fraction = value / max_val
        seg_fraction = (i + 0.5) / segments
        color = fill_color if seg_fraction <= filled_fraction else track_color

        # Draw as small rectangles approximating the arc
        mid_a = (a1 + a2) / 2
        mid_r = (outer_r + inner_r) / 2
        x = cx + int(mid_r * math.cos(mid_a))
        y = cy + int(mid_r * math.sin(mid_a))
        thickness = outer_r - inner_r
        seg_w = int(2 * math.pi * mid_r / segments) + Pt(2)

        s = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            int(x - seg_w // 2), int(y - thickness // 2),
            seg_w, thickness
        )
        s.fill.solid()
        s.fill.fore_color.rgb = color
        s.line.fill.background()
        s.rotation = -math.degrees(mid_a) + 90


def draw_horizontal_bar(slide, left, top, width, height, value, max_val, fill_color, track_color=LIGHT_GRAY):
    """Draw a horizontal progress bar."""
    # Track
    shape_rounded(slide, left, top, width, height, track_color)
    # Fill
    fill_w = max(Inches(0.1), int(width * (value / max_val)))
    shape_rounded(slide, left, top, fill_w, height, fill_color)


def draw_dot_comparison(slide, left, top, width, label, actual, benchmark, max_val, color, bench_label="Top Performer"):
    """Draw filled dot (actual) and hollow dot (benchmark) on a horizontal scale."""
    # Label
    text_box(slide, left, top, Inches(2.2), Inches(0.3), label, size=10, color=DARK_TEXT, bold=True)

    bar_left = left + Inches(2.3)
    bar_width = width - Inches(2.3)
    bar_y = top + Inches(0.12)

    # Scale line
    shape_rect(slide, bar_left, bar_y + Inches(0.04), bar_width, Pt(2), LIGHT_GRAY)

    # Benchmark (hollow circle)
    bench_x = bar_left + int(bar_width * (benchmark / max_val))
    shape_circle(slide, bench_x, bar_y + Inches(0.05), Inches(0.12), None,
                 line_color=BENCHMARK_GRAY, line_width=2.5)

    # Actual (filled circle)
    actual_x = bar_left + int(bar_width * (actual / max_val))
    shape_circle(slide, actual_x, bar_y + Inches(0.05), Inches(0.12), color)

    # Value labels
    text_box(slide, actual_x - Inches(0.3), top + Inches(0.25), Inches(0.6), Inches(0.2),
             f"{actual:.1f}", size=9, color=color, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE (clean, modern)
# ══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(prs.slide_layouts[6])

# Full dark background
shape_rect(s1, Inches(0), Inches(0), Inches(13.333), Inches(7.5), PRIMARY)

# Subtle bottom accent
shape_rect(s1, Inches(0), Inches(6.0), Inches(13.333), Inches(1.5),
           RGBColor(0x00, 0x1F, 0x38))

# Thin teal accent line
shape_rect(s1, Inches(1.3), Inches(2.0), Inches(1.8), Pt(4), TEAL)

# Main title
text_box(s1, Inches(1.3), Inches(2.3), Inches(7), Inches(1.2),
         "Human Capital\nIndex Plus", size=48, color=WHITE, bold=True,
         font="Calibri Light")

# HCI+ | 2025
text_box(s1, Inches(1.3), Inches(3.9), Inches(4), Inches(0.5),
         "HCI+  |  2025", size=22, color=TEAL, bold=True)

# Country
text_box(s1, Inches(1.3), Inches(4.7), Inches(4), Inches(0.7),
         "KENYA", size=40, color=WHITE, bold=True)

# Subtitle
text_box(s1, Inches(1.3), Inches(5.8), Inches(6), Inches(0.7),
         "Measuring human capital from birth through working age across\nhealth, education, and employment dimensions",
         size=13, color=RGBColor(0x88, 0x99, 0xAA))

# Tags
tag_y = Inches(6.6)
t1 = shape_rounded(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(1.3), tag_y, Inches(2.2), Inches(0.32),
         "Sub-Saharan Africa", size=9, color=TEAL, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
t2 = shape_rounded(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32), RGBColor(0x00, 0x3A, 0x5C))
text_box(s1, Inches(3.7), tag_y, Inches(2.2), Inches(0.32),
         "Lower Middle Income", size=9, color=TEAL, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Right side — Large score display with gauge-like ring
score_panel = shape_rounded(s1, Inches(8.8), Inches(1.5), Inches(3.8), Inches(5.0),
                            RGBColor(0x00, 0x3A, 0x5C))

text_box(s1, Inches(8.8), Inches(1.7), Inches(3.8), Inches(0.35),
         "OVERALL HCI+ SCORE", size=10, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

# Score value
text_box(s1, Inches(8.8), Inches(2.4), Inches(3.8), Inches(1.6),
         "170.8", size=72, color=WHITE, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, font="Calibri Light")

text_box(s1, Inches(8.8), Inches(4.0), Inches(3.8), Inches(0.3),
         "out of 325", size=12, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)

# Component mini-bars
comp_data = [
    ("Health", 36.6, 50, TEAL),
    ("Education", 109.0, 180, BLUE),
    ("Employment", 25.3, 70, ORANGE),
]

bar_start_y = Inches(4.6)
for i, (name, val, max_v, color) in enumerate(comp_data):
    y = bar_start_y + Inches(i * 0.55)
    text_box(s1, Inches(9.1), y, Inches(1.2), Inches(0.22),
             name, size=9, color=RGBColor(0xAA, 0xBB, 0xCC))
    text_box(s1, Inches(11.7), y, Inches(0.7), Inches(0.22),
             f"{val:.1f}", size=9, color=color, bold=True, align=PP_ALIGN.RIGHT)
    # Mini bar
    bar_y = y + Inches(0.22)
    shape_rounded(s1, Inches(9.1), bar_y, Inches(3.2), Inches(0.1), RGBColor(0x00, 0x2B, 0x49))
    fill_w = max(Inches(0.1), int(Inches(3.2) * (val / max_v)))
    shape_rounded(s1, Inches(9.1), bar_y, fill_w, Inches(0.1), color)

# Rankings
text_box(s1, Inches(9.1), Inches(6.05), Inches(3.2), Inches(0.25),
         "Ranked #3 in Sub-Saharan Africa  |  #96 Globally",
         size=9, color=ORANGE, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — BUBBLE CHART: HCI+ vs GDP per capita
# ══════════════════════════════════════════════════════════════════════════════
s2_bubble = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2_bubble, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

# Header
shape_rect(s2_bubble, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s2_bubble, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Kenya in Global Context  |  HCI+ vs GDP per Capita", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2_bubble, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "170.8 / 325", size=22, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Main panel
bubble_panel = shape_rounded(s2_bubble, Inches(0.5), Inches(1.3), Inches(8.8), Inches(5.4), WHITE)

text_box(s2_bubble, Inches(0.8), Inches(1.5), Inches(7), Inches(0.3),
         "HCI+ SCORE vs LOG GDP PER CAPITA (PPP)", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s2_bubble, Inches(0.8), Inches(1.85), Inches(2.5), Pt(3), TEAL)
text_box(s2_bubble, Inches(0.8), Inches(1.95), Inches(7), Inches(0.25),
         "Each bubble represents a country. Kenya (orange) outperforms many countries at similar income levels.",
         size=9, color=MEDIUM_GRAY)

# Bubble chart — HCI+ (Y) vs GDP per capita log (X)
# Group countries by region for color coding
# We'll use separate series per region for color control

bubble_data = BubbleChartData()

# Define country data by region
regions_data = {
    'Sub-Saharan Africa': [
        ('Kenya', 8.67, 170.8, 15),       # larger bubble for Kenya
        ('Rwanda', 8.09, 156.9, 5),
        ('Ghana', 8.86, 152.9, 5),
        ('Uganda', 7.97, 145.2, 5),
        ('Nigeria', 8.64, 130.7, 5),
        ('Ethiopia', 7.97, 123.4, 5),
        ('South Africa', 9.52, 132.1, 5),
        ('Mauritius', 10.22, 201.0, 3),
        ('Botswana', 9.80, 156.9, 3),
        ('Tanzania', 8.22, 132.6, 5),
        ('Senegal', 8.41, 109.4, 3),
    ],
    'East Asia & Pacific': [
        ('Japan', 10.74, 284.3, 5),
        ('Singapore', 11.79, 282.4, 3),
        ('Korea, Rep.', 10.83, 266.9, 5),
        ('China', 10.08, 219.8, 10),
        ('Vietnam', 9.25, 206.8, 5),
        ('Thailand', 9.99, 202.3, 5),
        ('Indonesia', 9.58, 175.4, 8),
        ('Philippines', 9.25, 175.4, 5),
        ('Australia', 11.00, 270.0, 3),
    ],
    'Europe & Central Asia': [
        ('Germany', 11.05, 256.5, 5),
        ('France', 10.91, 251.2, 5),
        ('Sweden', 11.05, 269.3, 3),
        ('Poland', 10.72, 259.5, 3),
        ('Turkiye', 10.32, 210.5, 5),
        ('Albania', 9.85, 203.5, 3),
        ('Kyrgyz Republic', 8.86, 197.5, 3),
    ],
    'Latin America & Caribbean': [
        ('Chile', 10.32, 226.2, 3),
        ('Brazil', 9.89, 202.9, 8),
        ('Mexico', 10.00, 193.5, 5),
        ('Colombia', 9.83, 197.6, 5),
        ('Jamaica', 9.24, 200.1, 3),
        ('Nicaragua', 8.94, 178.1, 3),
    ],
    'South Asia & MENA': [
        ('India', 9.19, 158.8, 10),
        ('Bangladesh', 9.05, 146.7, 5),
        ('Sri Lanka', 9.73, 182.6, 3),
        ('Jordan', 9.16, 170.2, 3),
        ('Egypt', 9.73, 161.2, 5),
        ('Morocco', 9.11, 147.1, 3),
    ],
}

region_colors = {
    'Sub-Saharan Africa': TEAL,
    'East Asia & Pacific': BLUE,
    'Europe & Central Asia': RGBColor(0x6B, 0x5B, 0x95),  # Purple
    'Latin America & Caribbean': RGBColor(0x2E, 0xA0, 0x6A),  # Green
    'South Asia & MENA': RGBColor(0x99, 0x66, 0x33),  # Brown
}

for region, countries_list in regions_data.items():
    series = bubble_data.add_series(region)
    for name, gdp, score, size in countries_list:
        series.add_data_point(gdp, score, size)

bcf = s2_bubble.shapes.add_chart(
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

# Color each series by region
for i, (region, color) in enumerate(region_colors.items()):
    plot_series = bc.series[i]
    plot_series.format.fill.solid()
    plot_series.format.fill.fore_color.rgb = color

# Highlight Kenya bubble (first point in SSA series) with orange
bc.series[0].points[0].format.fill.solid()
bc.series[0].points[0].format.fill.fore_color.rgb = ORANGE

# RIGHT PANEL — Key context & annotations
right_ctx = shape_rounded(s2_bubble, Inches(9.6), Inches(1.3), Inches(3.3), Inches(5.4), WHITE)
shape_rect(s2_bubble, Inches(9.6), Inches(1.3), Pt(5), Inches(5.4), TEAL)

text_box(s2_bubble, Inches(9.9), Inches(1.5), Inches(2.9), Inches(0.25),
         "KENYA IN CONTEXT", size=11, color=TEAL, bold=True)

# Kenya stats
stats = [
    ("HCI+ Score", "170.8", TEAL),
    ("Global Rank", "#96 / 161", DARK_TEXT),
    ("SSA Rank", "#3 / 39", ORANGE),
    ("SSA Average", "128.4", MEDIUM_GRAY),
    ("Global Average", "188.5", MEDIUM_GRAY),
    ("LMI 75th Pctile", "160.1", MEDIUM_GRAY),
]

for j, (label, value, color) in enumerate(stats):
    sy = Inches(1.9) + Inches(j * 0.55)
    text_box(s2_bubble, Inches(9.9), sy, Inches(1.8), Inches(0.22),
             label, size=9, color=MEDIUM_GRAY)
    text_box(s2_bubble, Inches(11.5), sy, Inches(1.2), Inches(0.22),
             value, size=11, color=color, bold=True, align=PP_ALIGN.RIGHT)
    if j < len(stats) - 1:
        shape_rect(s2_bubble, Inches(9.9), sy + Inches(0.35), Inches(2.8), Pt(1),
                   RGBColor(0xEE, 0xEE, 0xEE))

# Insight text
text_box(s2_bubble, Inches(9.9), Inches(5.3), Inches(2.9), Inches(0.25),
         "KEY INSIGHT", size=10, color=TEAL, bold=True)
text_box(s2_bubble, Inches(9.9), Inches(5.6), Inches(2.9), Inches(0.95),
         "Kenya (orange) scores well above the SSA average and "
         "outperforms many countries at similar GDP levels. "
         "The World Bank identifies Kenya as a top performer "
         "relative to its income, alongside Jamaica, Kyrgyz Republic, and Vietnam.",
         size=9, color=DARK_TEXT)

add_footer(s2_bubble, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — SCORE DECOMPOSITION & BENCHMARKING
# ══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s2, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

# Header
shape_rect(s2, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
text_box(s2, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Kenya  |  HCI+ Score Decomposition", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s2, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "170.8 / 325", size=22, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# LEFT PANEL — Waterfall/decomposition stacked bar
left_panel = shape_rounded(s2, Inches(0.5), Inches(1.3), Inches(6.0), Inches(5.4), WHITE)

text_box(s2, Inches(0.8), Inches(1.5), Inches(5), Inches(0.3),
         "COMPONENT DECOMPOSITION", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s2, Inches(0.8), Inches(1.85), Inches(2), Pt(3), TEAL)

# Stacked horizontal bar — HCI+ composition
chart_data = CategoryChartData()
chart_data.categories = ['Kenya HCI+\n(170.8 / 325)']
chart_data.add_series('Health (36.6)', (36.6,))
chart_data.add_series('Education (109.0)', (109.0,))
chart_data.add_series('Employment (25.3)', (25.3,))

cf = s2.shapes.add_chart(
    XL_CHART_TYPE.BAR_STACKED, Inches(0.8), Inches(2.1), Inches(5.5), Inches(1.2),
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
ch.value_axis.maximum_scale = 325
ch.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
ch.value_axis.format.line.color.rgb = DIVIDER
ch.value_axis.tick_labels.font.size = Pt(8)

# Component comparison: Kenya vs Benchmarks (filled vs hollow style)
text_box(s2, Inches(0.8), Inches(3.5), Inches(5), Inches(0.3),
         "KENYA vs BENCHMARKS (Filled = Kenya, Hollow = Top Performer*)", size=10, color=MEDIUM_GRAY, bold=True)
shape_rect(s2, Inches(0.8), Inches(3.85), Inches(2), Pt(2), TEAL)

text_box(s2, Inches(0.8), Inches(3.95), Inches(5.5), Inches(0.25),
         "*Top performer = 75th percentile among lower-middle-income countries",
         size=8, color=MEDIUM_GRAY)

# Dot comparisons with scale lines
# Kenya vs top LMI performer benchmark (approximated from 75th pctile)
benchmarks = {
    "Health": (36.6, 45.3, 50),
    "Education": (109.0, 86.6, 180),  # Kenya actually beats benchmark here
    "Employment": (25.3, 28.3, 70),
}

dot_y = Inches(4.35)
for i, (comp, (actual, bench, max_v)) in enumerate(benchmarks.items()):
    y = dot_y + Inches(i * 0.55)
    color = [TEAL, BLUE, ORANGE][i]
    draw_dot_comparison(s2, Inches(0.8), y, Inches(5.5), comp, actual, bench, max_v, color)

# Legend for dots
shape_circle(s2, Inches(1.2), Inches(6.15), Inches(0.08), TEAL)
text_box(s2, Inches(1.35), Inches(6.05), Inches(1), Inches(0.2),
         "Kenya", size=8, color=DARK_TEXT)
shape_circle(s2, Inches(2.5), Inches(6.15), Inches(0.08), None,
             line_color=BENCHMARK_GRAY, line_width=2)
text_box(s2, Inches(2.65), Inches(6.05), Inches(2), Inches(0.2),
         "LMI 75th Percentile", size=8, color=DARK_TEXT)


# RIGHT PANEL — Regional comparison bar chart
right_panel = shape_rounded(s2, Inches(6.8), Inches(1.3), Inches(6.0), Inches(5.4), WHITE)

text_box(s2, Inches(7.1), Inches(1.5), Inches(5), Inches(0.3),
         "REGIONAL COMPARISON", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s2, Inches(7.1), Inches(1.85), Inches(2), Pt(3), BLUE)

reg_data = CategoryChartData()
reg_data.categories = [
    'Sub-Saharan\nAfrica', 'South\nAsia', 'Latin America\n& Caribbean',
    'MENA+', 'East Asia\n& Pacific', 'Europe &\nCentral Asia',
    'Kenya'
]
reg_data.add_series('HCI+ Score', (128.4, 147.5, 183.2, 185.7, 201.7, 233.3, 170.8))

rcf = s2.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.1), Inches(2.0), Inches(5.4), Inches(3.2),
    reg_data
)
rc = rcf.chart
rc.has_legend = False
rplot = rc.plots[0]
rplot.gap_width = 60

# Color Kenya's bar differently
series = rplot.series[0]
series.format.fill.solid()
series.format.fill.fore_color.rgb = BLUE

# Make Kenya bar orange
from pptx.oxml.ns import qn
point = series.points[6]
point.format.fill.solid()
point.format.fill.fore_color.rgb = ORANGE

rc.category_axis.tick_labels.font.size = Pt(9)
rc.category_axis.tick_labels.font.name = "Calibri"
rc.value_axis.maximum_scale = 280
rc.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
rc.value_axis.format.line.color.rgb = DIVIDER
rc.value_axis.tick_labels.font.size = Pt(8)

# Add data labels
series.has_data_labels = True
series.data_labels.font.size = Pt(8)
series.data_labels.font.name = "Calibri"
series.data_labels.font.bold = True
series.data_labels.number_format = '0.0'

# Key insight box
text_box(s2, Inches(7.1), Inches(5.4), Inches(5.5), Inches(0.3),
         "KEY INSIGHT", size=10, color=TEAL, bold=True)
text_box(s2, Inches(7.1), Inches(5.7), Inches(5.4), Inches(0.85),
         "Kenya ranks #3 in Sub-Saharan Africa and outperforms the SSA average "
         "by 42.4 points. Education (109.0) is Kenya's strongest component, "
         "actually exceeding the LMI 75th percentile benchmark (86.6). "
         "Kenya is identified as a top performer relative to its income level.",
         size=10, color=DARK_TEXT)

add_footer(s2, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — HEALTH COMPONENT (filled/hollow dots + progress bars)
# ══════════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

# Header with teal accent
shape_rect(s3, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s3, Inches(0), Inches(1.0), Inches(13.333), Pt(4), TEAL)
text_box(s3, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Health Component", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s3, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Score: 36.6", size=22, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# Description
text_box(s3, Inches(0.6), Inches(1.35), Inches(8), Inches(0.4),
         "Health outcomes reflect survival into productive adulthood and freedom from childhood malnutrition.",
         size=11, color=MEDIUM_GRAY)

# LEFT — Adult Survival Rate card
card1 = shape_rounded(s3, Inches(0.5), Inches(2.0), Inches(6.0), Inches(2.4), WHITE)
shape_rect(s3, Inches(0.5), Inches(2.0), Inches(6.0), Pt(4), TEAL)

text_box(s3, Inches(0.8), Inches(2.2), Inches(3), Inches(0.25),
         "ADULT SURVIVAL RATE", size=12, color=TEAL, bold=True)
text_box(s3, Inches(0.8), Inches(2.5), Inches(5), Inches(0.25),
         "Probability of surviving from age 15 to 60", size=10, color=MEDIUM_GRAY)

# Big number
text_box(s3, Inches(0.8), Inches(2.85), Inches(2.5), Inches(0.7),
         "68.4%", size=44, color=TEAL, bold=True, font="Calibri Light")

# Progress bar
draw_horizontal_bar(s3, Inches(0.8), Inches(3.65), Inches(5.4), Inches(0.18), 68.4, 100, TEAL)

# Gender dots
text_box(s3, Inches(3.5), Inches(2.9), Inches(2.5), Inches(0.25),
         "Female: 72.5%", size=12, color=CORAL)
text_box(s3, Inches(3.5), Inches(3.2), Inches(2.5), Inches(0.25),
         "Male: 64.4%", size=12, color=DARK_BLUE)

# SSA comparison line on progress bar
ssa_surv = 0.65  # approximate SSA avg
ssa_x = Inches(0.8) + int(Inches(5.4) * ssa_surv)
shape_rect(s3, ssa_x, Inches(3.55), Pt(2), Inches(0.38), ORANGE)
text_box(s3, ssa_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "SSA Avg", size=7, color=ORANGE, align=PP_ALIGN.CENTER)

# RIGHT — Not Stunted Rate card
card2 = shape_rounded(s3, Inches(6.8), Inches(2.0), Inches(6.0), Inches(2.4), WHITE)
shape_rect(s3, Inches(6.8), Inches(2.0), Inches(6.0), Pt(4), TEAL)

text_box(s3, Inches(7.1), Inches(2.2), Inches(3), Inches(0.25),
         "NOT STUNTED RATE", size=12, color=TEAL, bold=True)
text_box(s3, Inches(7.1), Inches(2.5), Inches(5), Inches(0.25),
         "Share of children under 5 not stunted", size=10, color=MEDIUM_GRAY)

text_box(s3, Inches(7.1), Inches(2.85), Inches(2.5), Inches(0.7),
         "82.4%", size=44, color=TEAL, bold=True, font="Calibri Light")

draw_horizontal_bar(s3, Inches(7.1), Inches(3.65), Inches(5.4), Inches(0.18), 82.4, 100, TEAL)

text_box(s3, Inches(9.8), Inches(2.9), Inches(2.5), Inches(0.25),
         "Female: 84.4%", size=12, color=CORAL)
text_box(s3, Inches(9.8), Inches(3.2), Inches(2.5), Inches(0.25),
         "Male: 80.4%", size=12, color=DARK_BLUE)

# SSA avg marker
ssa_stunt_x = Inches(7.1) + int(Inches(5.4) * 0.67)  # SSA avg ~67% not stunted
shape_rect(s3, ssa_stunt_x, Inches(3.55), Pt(2), Inches(0.38), ORANGE)
text_box(s3, ssa_stunt_x - Inches(0.3), Inches(3.9), Inches(1.2), Inches(0.2),
         "SSA Avg", size=7, color=ORANGE, align=PP_ALIGN.CENTER)

# BOTTOM — SSA peer comparison chart (horizontal bars)
bottom_panel = shape_rounded(s3, Inches(0.5), Inches(4.7), Inches(12.3), Inches(2.1), WHITE)

text_box(s3, Inches(0.8), Inches(4.85), Inches(5), Inches(0.3),
         "HEALTH COMPONENT: SSA TOP PERFORMERS", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s3, Inches(0.8), Inches(5.15), Inches(2), Pt(2), TEAL)

ssa_health_data = CategoryChartData()
ssa_health_data.categories = ['Seychelles', 'Mauritius', 'Botswana', 'Ghana', 'Namibia',
                               'Rwanda', 'Uganda', 'Togo', 'Kenya']
ssa_health_data.add_series('Health Score',
                           (44.0, 43.9, 40.2, 39.4, 39.4, 38.0, 38.2, 37.8, 36.6))

hcf = s3.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.25), Inches(11.8), Inches(1.35),
    ssa_health_data
)
hc = hcf.chart
hc.has_legend = False
hp = hc.plots[0]
hp.gap_width = 40
hseries = hp.series[0]
hseries.format.fill.solid()
hseries.format.fill.fore_color.rgb = TEAL

# Highlight Kenya bar
hseries.points[8].format.fill.solid()
hseries.points[8].format.fill.fore_color.rgb = ORANGE

hseries.has_data_labels = True
hseries.data_labels.font.size = Pt(8)
hseries.data_labels.font.bold = True
hseries.data_labels.number_format = '0.0'

hc.category_axis.tick_labels.font.size = Pt(8)
hc.category_axis.tick_labels.font.name = "Calibri"
hc.value_axis.visible = False
hc.value_axis.has_major_gridlines = False

add_footer(s3, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — EDUCATION COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s4, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

# Header
shape_rect(s4, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s4, Inches(0), Inches(1.0), Inches(13.333), Pt(4), BLUE)
text_box(s4, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Education Component", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s4, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Score: 109.0", size=22, color=BLUE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s4, Inches(0.6), Inches(1.35), Inches(8), Inches(0.4),
         "Education captures learning quality, years of schooling, pre-primary education, and tertiary enrollment.",
         size=11, color=MEDIUM_GRAY)

# Four metric cards with progress bars
metrics = [
    ("Expected Years of Schooling", "11.03", "years", 11.03, 14, BLUE),
    ("Harmonized Learning Outcomes", "418.1", "HLO score (out of 625)", 418.1, 625, RGBColor(0x00, 0x5A, 0x9E)),
    ("Pre-Primary Education", "0.62", "learning-adj. years", 0.62, 1.0, TEAL),
    ("Tertiary Enrollment", "20.3%", "gross enrollment rate", 20.3, 100, ORANGE),
]

for i, (label, value, unit, num_val, max_val, color) in enumerate(metrics):
    x = Inches(0.5) + i * Inches(3.15)
    card = shape_rounded(s4, x, Inches(2.0), Inches(2.95), Inches(2.5), WHITE)
    shape_rect(s4, x, Inches(2.0), Inches(2.95), Pt(4), color)

    text_box(s4, x + Inches(0.15), Inches(2.2), Inches(2.65), Inches(0.5),
             label, size=11, color=DARK_TEXT, bold=True)

    text_box(s4, x + Inches(0.15), Inches(2.8), Inches(2.65), Inches(0.7),
             value, size=36, color=color, bold=True, font="Calibri Light")

    text_box(s4, x + Inches(0.15), Inches(3.5), Inches(2.65), Inches(0.25),
             unit, size=9, color=MEDIUM_GRAY)

    # Progress bar
    draw_horizontal_bar(s4, x + Inches(0.15), Inches(3.85), Inches(2.65), Inches(0.12),
                       num_val, max_val, color)

    # Percentage label
    pct = num_val / max_val * 100
    text_box(s4, x + Inches(0.15), Inches(4.05), Inches(2.65), Inches(0.2),
             f"{pct:.0f}% of maximum", size=8, color=MEDIUM_GRAY)


# Bottom panel — SSA education comparison
bottom = shape_rounded(s4, Inches(0.5), Inches(4.75), Inches(7.5), Inches(2.0), WHITE)

text_box(s4, Inches(0.8), Inches(4.9), Inches(5), Inches(0.3),
         "EDUCATION COMPONENT: SSA TOP PERFORMERS", size=11, color=MEDIUM_GRAY, bold=True)
shape_rect(s4, Inches(0.8), Inches(5.2), Inches(2), Pt(2), BLUE)

edu_comp_data = CategoryChartData()
edu_comp_data.categories = ['Seychelles', 'Mauritius', 'Kenya', 'Botswana', 'Rwanda',
                             'Ghana', 'Zimbabwe', 'Namibia']
edu_comp_data.add_series('Education Score', (126.4, 113.8, 109.0, 86.1, 83.9, 80.5, 78.7, 78.1))

ecf = s4.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.3), Inches(7.0), Inches(1.3),
    edu_comp_data
)
ec = ecf.chart
ec.has_legend = False
ep = ec.plots[0]
ep.gap_width = 40
eseries = ep.series[0]
eseries.format.fill.solid()
eseries.format.fill.fore_color.rgb = BLUE
eseries.points[2].format.fill.solid()
eseries.points[2].format.fill.fore_color.rgb = ORANGE

eseries.has_data_labels = True
eseries.data_labels.font.size = Pt(8)
eseries.data_labels.font.bold = True
eseries.data_labels.number_format = '0.0'

ec.category_axis.tick_labels.font.size = Pt(8)
ec.value_axis.visible = False
ec.value_axis.has_major_gridlines = False

# Right insight panel
insight = shape_rounded(s4, Inches(8.3), Inches(4.75), Inches(4.5), Inches(2.0), WHITE)
shape_rect(s4, Inches(8.3), Inches(4.75), Pt(5), Inches(2.0), BLUE)

text_box(s4, Inches(8.6), Inches(4.9), Inches(4), Inches(0.25),
         "KEY INSIGHT", size=10, color=BLUE, bold=True)
text_box(s4, Inches(8.6), Inches(5.2), Inches(4), Inches(1.4),
         "Education is Kenya's strongest HCI+ pillar, scoring 109.0 \u2014 "
         "ranking #3 in SSA and exceeding the lower-middle-income 75th "
         "percentile benchmark (86.6). With 11.03 expected years of schooling "
         "and an HLO of 418.1, Kenya demonstrates strong educational foundations. "
         "Gender parity is nearly achieved. Tertiary enrollment (20.3%) "
         "offers room for growth.",
         size=10, color=DARK_TEXT)

add_footer(s4, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — EMPLOYMENT + GENDER GAP (diverging bars)
# ══════════════════════════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(prs.slide_layouts[6])
shape_rect(s5, Inches(0), Inches(0), Inches(13.333), Inches(7.5), LIGHT_BG)

# Header
shape_rect(s5, Inches(0), Inches(0), Inches(13.333), Inches(1.0), PRIMARY)
shape_rect(s5, Inches(0), Inches(1.0), Inches(13.333), Pt(4), ORANGE)
text_box(s5, Inches(0.6), Inches(0.15), Inches(8), Inches(0.7),
         "Employment & Gender Gap Analysis", size=24, color=WHITE, bold=True,
         font="Calibri Light", anchor=MSO_ANCHOR.MIDDLE)
text_box(s5, Inches(9.5), Inches(0.15), Inches(3.5), Inches(0.7),
         "Score: 25.3", size=22, color=ORANGE, bold=True,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

text_box(s5, Inches(0.6), Inches(1.35), Inches(10), Inches(0.4),
         "Employment captures labor force participation, wage employment, and skill accumulation for youth (15\u201324) and working-age (25\u201365) populations.",
         size=11, color=MEDIUM_GRAY)

# LEFT — Employment metrics table-style
left = shape_rounded(s5, Inches(0.5), Inches(2.0), Inches(6.0), Inches(3.0), WHITE)
shape_rect(s5, Inches(0.5), Inches(2.0), Inches(6.0), Pt(4), ORANGE)

text_box(s5, Inches(0.8), Inches(2.2), Inches(3), Inches(0.25),
         "EMPLOYMENT INDICATORS", size=11, color=ORANGE, bold=True)

# Table headers
headers = [("", 2.0), ("Both", 0.8), ("Male", 0.8), ("Female", 0.8)]
hx = Inches(0.8)
for label, w in headers:
    color = MEDIUM_GRAY if label == "" else (DARK_BLUE if label == "Male" else (CORAL if label == "Female" else DARK_TEXT))
    text_box(s5, hx, Inches(2.6), Inches(w), Inches(0.25),
             label, size=10, color=color, bold=True,
             align=PP_ALIGN.CENTER if label else PP_ALIGN.LEFT)
    hx += Inches(w)

shape_rect(s5, Inches(0.8), Inches(2.85), Inches(4.4), Pt(1), DIVIDER)

rows = [
    ("LFP Youth (15\u201324)", "39.6%", "42.4%", "37.2%"),
    ("Wage Emp. Youth", "38.8%", "43.9%", "32.9%"),
    ("LFP Working Age (25\u201365)", "78.0%", "85.2%", "71.0%"),
    ("Wage Emp. Working Age", "35.6%", "44.2%", "25.4%"),
]

for j, (ind, both, male, female) in enumerate(rows):
    ry = Inches(2.95 + j * 0.45)
    bg_color = WHITE if j % 2 == 0 else RGBColor(0xF9, 0xFA, 0xFB)
    shape_rect(s5, Inches(0.8), ry, Inches(4.4), Inches(0.4), bg_color)

    rx = Inches(0.8)
    vals = [(ind, 2.0, DARK_TEXT, False), (both, 0.8, DARK_TEXT, True),
            (male, 0.8, DARK_BLUE, False), (female, 0.8, CORAL, False)]
    for val, w, col, bld in vals:
        text_box(s5, rx, ry + Inches(0.05), Inches(w), Inches(0.3),
                 val, size=10, color=col, bold=bld,
                 align=PP_ALIGN.CENTER if w == 0.8 else PP_ALIGN.LEFT)
        rx += Inches(w)


# RIGHT — Gender gap diverging bar chart
right = shape_rounded(s5, Inches(6.8), Inches(2.0), Inches(6.0), Inches(3.0), WHITE)
shape_rect(s5, Inches(6.8), Inches(2.0), Inches(6.0), Pt(4), ORANGE)

text_box(s5, Inches(7.1), Inches(2.15), Inches(5), Inches(0.3),
         "GENDER GAP (Male \u2212 Female)", size=11, color=ORANGE, bold=True)
text_box(s5, Inches(7.1), Inches(2.4), Inches(5.5), Inches(0.25),
         "Bars show points by which male scores exceed female scores",
         size=9, color=MEDIUM_GRAY)

# Diverging horizontal bar chart
gender_gap_data = CategoryChartData()
gender_gap_data.categories = ['Health\nComponent', 'Education\nComponent', 'Employment\nComponent', 'Overall\nHCI+']
# Male minus Female gaps
gender_gap_data.add_series('Gender Gap (Male - Female)',
                           (35.0 - 38.3, 108.5 - 109.4, 32.1 - 18.6, 175.6 - 166.3))

ggf = s5.shapes.add_chart(
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

# Color negative bars (where women outperform)
for idx, val in enumerate([-3.3, -0.9, 13.5, 9.3]):
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

# Legend explanation
shape_rect(s5, Inches(9.0), Inches(4.7), Inches(0.3), Inches(0.15), DARK_BLUE)
text_box(s5, Inches(9.4), Inches(4.65), Inches(1.5), Inches(0.2),
         "Men outperform", size=8, color=DARK_TEXT)
shape_rect(s5, Inches(10.8), Inches(4.7), Inches(0.3), Inches(0.15), CORAL)
text_box(s5, Inches(11.2), Inches(4.65), Inches(1.5), Inches(0.2),
         "Women outperform", size=8, color=DARK_TEXT)

# Bottom — SSA employment comparison + insight
bottom_left = shape_rounded(s5, Inches(0.5), Inches(5.2), Inches(7.5), Inches(1.6), WHITE)

text_box(s5, Inches(0.8), Inches(5.3), Inches(5), Inches(0.25),
         "EMPLOYMENT COMPONENT: SSA COMPARISON", size=10, color=MEDIUM_GRAY, bold=True)
shape_rect(s5, Inches(0.8), Inches(5.55), Inches(1.5), Pt(2), ORANGE)

emp_ssa_data = CategoryChartData()
emp_ssa_data.categories = ['Uganda', 'Rwanda', 'Togo', 'Ghana', 'Botswana',
                            'Kenya', 'Zimbabwe', 'Namibia']
emp_ssa_data.add_series('Employment Score', (39.2, 35.1, 35.3, 32.9, 30.6, 25.3, 25.2, 23.3))

emcf = s5.shapes.add_chart(
    XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.8), Inches(5.6), Inches(7.0), Inches(1.1),
    emp_ssa_data
)
emc = emcf.chart
emc.has_legend = False
emp = emc.plots[0]
emp.gap_width = 40
emseries = emp.series[0]
emseries.format.fill.solid()
emseries.format.fill.fore_color.rgb = ORANGE
emseries.points[5].format.fill.solid()
emseries.points[5].format.fill.fore_color.rgb = RGBColor(0xC0, 0x5A, 0x00)

emseries.has_data_labels = True
emseries.data_labels.font.size = Pt(8)
emseries.data_labels.font.bold = True
emseries.data_labels.number_format = '0.0'

emc.category_axis.tick_labels.font.size = Pt(8)
emc.value_axis.visible = False
emc.value_axis.has_major_gridlines = False

# Insight
insight5 = shape_rounded(s5, Inches(8.3), Inches(5.2), Inches(4.5), Inches(1.6), WHITE)
shape_rect(s5, Inches(8.3), Inches(5.2), Pt(5), Inches(1.6), ORANGE)
text_box(s5, Inches(8.6), Inches(5.3), Inches(4), Inches(0.25),
         "KEY TAKEAWAY", size=10, color=ORANGE, bold=True)
text_box(s5, Inches(8.6), Inches(5.6), Inches(4), Inches(1.1),
         "Employment is Kenya's weakest component (25.3). The largest gender gap "
         "is in employment (+13.5 for men), driven by disparities in wage employment "
         "(men 44.2% vs women 25.4%). Women outperform men in health (\u22123.3) and "
         "education (\u22120.9). Closing the employment gender gap could significantly "
         "boost Kenya's overall HCI+ score.",
         size=10, color=DARK_TEXT)

add_footer(s5, 5)


# ── Save ──────────────────────────────────────────────────────────────────────
output_path = "/home/user/arcidiaconom.github.io/Kenya_HCI_Plus_2025_v3.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
