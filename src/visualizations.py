import json
from collections import OrderedDict
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, dcc, html

import math
import random

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "data" / "processed_data" / "year-end_top20_songs_predictions.json"
WEIGHTS_PATH = BASE_DIR / "data" / "processed_data" / "word_weights.json"
POLITICAL_LABEL = "political"   # exact value of "prediction" that gets the blue bars
COLOR_POLITICAL = "#2563EB"     # blue
COLOR_NON_POLITICAL = "#FACC15" # yellow

BAR_SLOT_PX = 40        # horizontal space per bar; keeps vertical titles from touching
GROUP_GAP = 1.0         # empty bar-widths between two years
FIG_HEIGHT_PX = 700
MARGIN = dict(l=70, r=30, t=70, b=70)
FONT_SIZE = 11
CHAR_WIDTH_FACTOR = 0.6  # average character width as a fraction of font size (estimate)
COUNT_AXIS_MAX = 20 

WORD_COUNT = 80          # how many words appear in EACH cloud
MAX_FONT_SIZE = 64       # px, size of the biggest word in either cloud
MIN_FONT_SIZE = 12       # px, size of the smallest word in the rank-based (yellow) cloud
CLOUD_WIDTH = 1000       # px
CLOUD_HEIGHT = 520       # px
CLOUD_BG = "#0F172A"     # dark background so the yellow words stay readable
CLOUD_CHAR_WIDTH = 0.55  # average character width as a fraction of font size (estimate)
CLOUD_PADDING = 6  

def load_songs(path=JSON_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data

def group_by_year(songs):
    """Years in order of first appearance; songs keep file order within each year."""
    groups = OrderedDict()
    for s in songs:
        groups.setdefault(str(s["year"]), []).append(s)
    return groups

def truncate(title, prob):
    """Shorten a title so it (roughly) fits inside a bar of height `prob` percent.
    The fit is an estimate based on font size, so tune CHAR_WIDTH_FACTOR if needed."""
    plot_h = FIG_HEIGHT_PX - MARGIN["t"] - MARGIN["b"]
    fit = int(prob / 100 * plot_h / (FONT_SIZE * CHAR_WIDTH_FACTOR))
    if len(title) <= fit:
        return title
    if fit < 1:
        return ""
    return title[: fit - 1].rstrip() + "…"

def build_figure(songs):
    groups = group_by_year(songs)

    # Bars sit at numeric x positions so years can have a gap between them and
    # duplicate titles never collide. Year labels go at each group's centre.
    rows, tickvals, ticktext = [], [], []
    cursor = 0.0
    for year, items in groups.items():
        xs = [cursor + i for i in range(len(items))]
        rows += [(x, s) for x, s in zip(xs, items)]
        tickvals.append(sum(xs) / len(xs))
        ticktext.append(year)
        cursor = xs[-1] + 1 + GROUP_GAP

    fig = go.Figure()
    for is_political, name, color, text_color in (
        (True, "Political", COLOR_POLITICAL, "white"),
        (False, "Non-political", COLOR_NON_POLITICAL, "#1F2937"),
    ):
        subset = [(x, s) for x, s in rows
                  if (s["prediction"] == POLITICAL_LABEL) == is_political]
        fig.add_trace(go.Bar(
            name=name,
            x=[x for x, _ in subset],
            y=[float(s["political_probability"]) for _, s in subset],
            marker_color=color,
            width=0.85,
            text=[truncate(s["song"], float(s["political_probability"])) for _, s in subset],
            textposition="inside",
            insidetextanchor="start",   # text starts at the base of the bar
            textangle=-90,              # vertical
            constraintext="none",       # don't let Plotly shrink/rotate the text
            textfont=dict(size=FONT_SIZE, color=text_color),
            customdata=[[s["song"], s["artist"], str(s["year"]),
                         float(s["political_probability"]),
                         float(s["non_political_probability"])] for _, s in subset],
            hovertemplate=("<b>%{customdata[0]}</b><br>"
                           "Artist: %{customdata[1]}<br>"
                           "Year: %{customdata[2]}<br>"
                           "Political: %{customdata[3]:.2f}%<br>"
                           "Non-political: %{customdata[4]:.2f}%"
                           "<extra></extra>"),
        ))

    fig.add_hline(y=50, line_dash="dash", line_color="#6B7280", line_width=1)

    fig.update_layout(
        width=int(cursor * BAR_SLOT_PX + MARGIN["l"] + MARGIN["r"]),
        height=FIG_HEIGHT_PX,
        margin=MARGIN,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13),
        legend=dict(orientation="h", x=0, y=1.08, xanchor="left"),
        xaxis=dict(tickmode="array", tickvals=tickvals, ticktext=ticktext,
                   range=[-0.7, cursor - GROUP_GAP - 0.3],
                   title="Year", showgrid=False, ticks=""),
        yaxis=dict(range=[0, 100], title="Political probability (%)",
                   gridcolor="#E5E7EB", zeroline=False),
    )
    return fig

def build_count_figure(songs):
    """Number of songs predicted political in each year (same year order as above)."""
    groups = group_by_year(songs)
    years = list(groups)
    totals = [len(items) for items in groups.values()]
    counts = [sum(s["prediction"] == POLITICAL_LABEL for s in items)
              for items in groups.values()]
 
    fig = go.Figure(go.Bar(
        x=years,
        y=counts,
        marker_color=COLOR_POLITICAL,
        width=0.6,
        customdata=totals,
        hovertemplate=("<b>%{x}</b><br>"
                       "Political songs: %{y} of %{customdata}"
                       "<extra></extra>"),
    ))
    fig.update_layout(
        height=450,
        margin=dict(l=70, r=30, t=30, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13),
        xaxis=dict(type="category", title="Year", showgrid=False, ticks=""),
        yaxis=dict(range=[0, COUNT_AXIS_MAX], dtick=2,
                   title="Songs predicted political", gridcolor="#E5E7EB",
                   zeroline=False),
    )
    return fig
 

def load_weights(path=WEIGHTS_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
 
 
def select_cloud_words(weights, n, highest):
    """Pick the n words for one cloud and give each a font size.
 
    highest=True  -> the n highest weights; size is proportional to the weight
                     (the top word gets MAX_FONT_SIZE). Words with weight <= 0 are
                     dropped, because proportional sizing is undefined for them.
    highest=False -> the n lowest weights; size is proportional to the NEGATIVE of the
                     weight, so the most negative word gets MAX_FONT_SIZE. Words with
                     weight >= 0 are dropped for the same reason.
    """
    ordered = sorted(weights, key=lambda d: float(d["weight"]), reverse=highest)
    ordered = [d for d in ordered if (float(d["weight"]) > 0) == highest and float(d["weight"]) != 0]
    ordered = ordered[:n]
    items = []
    for i, d in enumerate(ordered):
        w = float(d["weight"])
        size = MAX_FONT_SIZE * w / float(ordered[0]["weight"])  # same sign, so positive
        items.append({"word": d["word"], "weight": w, "rank": i + 1, "size": size, "total": len(ordered)})
    return items
 
 
def layout_words(items, width, height, seed=0):
    """Place words (largest first) along a spiral from the centre, skipping overlaps.
    Word widths are estimated from font size, so tune CLOUD_CHAR_WIDTH / CLOUD_PADDING
    if words touch or the spacing looks too loose. Returns (placed, omitted)."""
    rng = random.Random(seed)
    cx, cy, stretch = width / 2, height / 2, width / height
    boxes, placed, omitted = [], [], []
    for it in sorted(items, key=lambda d: -d["size"]):
        tw = len(it["word"]) * it["size"] * CLOUD_CHAR_WIDTH
        th = it["size"]
        bw, bh = tw + 2 * CLOUD_PADDING, th + 2 * CLOUD_PADDING
        a0 = rng.uniform(0, 2 * math.pi)
        for step in range(4000):
            t = step * 0.1
            x = cx + 2.0 * t * math.cos(t + a0) * stretch
            y = cy + 2.0 * t * math.sin(t + a0)
            x0, x1, y0, y1 = x - bw / 2, x + bw / 2, y - bh / 2, y + bh / 2
            if x0 < 0 or x1 > width or y0 < 0 or y1 > height:
                continue
            if any(x0 < b[1] and x1 > b[0] and y0 < b[3] and y1 > b[2] for b in boxes):
                continue
            boxes.append((x0, x1, y0, y1))
            placed.append({**it, "x": x, "y": y, "tw": tw})
            break
        else:
            omitted.append(it["word"])
    return placed, omitted
 
 
def build_cloud_figure(items, color):
    placed, omitted = layout_words(items, CLOUD_WIDTH, CLOUD_HEIGHT)
    font = "system-ui, -apple-system, Segoe UI, sans-serif"
    fig = go.Figure()
 
    # Visible words
    fig.add_trace(go.Scatter(
        x=[p["x"] for p in placed], y=[p["y"] for p in placed],
        mode="text", text=[p["word"] for p in placed],
        textposition="middle center",
        textfont=dict(size=[p["size"] for p in placed], color=color, family=font),
        hoverinfo="skip", showlegend=False,
    ))
 
    # Invisible hover targets: Plotly only detects hover near a point, so each word
    # gets several transparent markers spread along its width.
    hx, hy, hs, hdata = [], [], [], []
    for p in placed:
        n = max(1, int(p["tw"] / (p["size"] * 0.5)))
        for j in range(n):
            hx.append(p["x"] - p["tw"] / 2 + (j + 0.5) * p["tw"] / n)
            hy.append(p["y"])
            hs.append(p["size"])
            hdata.append([p["word"], p["weight"], p["rank"], p["total"]])
    fig.add_trace(go.Scatter(
        x=hx, y=hy, mode="markers",
        marker=dict(size=hs, opacity=0, color=color),
        customdata=hdata, showlegend=False,
        hovertemplate=("<b>%{customdata[0]}</b><br>"
                       "Weight: %{customdata[1]:.4f}<br>"
                       "Rank: %{customdata[2]} of %{customdata[3]}"
                       "<extra></extra>"),
        hoverlabel=dict(bgcolor="white", font=dict(color="#111827", family=font)),
    ))
 
    axis = dict(visible=False, fixedrange=True)
    fig.update_layout(
        width=CLOUD_WIDTH, height=CLOUD_HEIGHT, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=CLOUD_BG, plot_bgcolor=CLOUD_BG, hovermode="closest",
        xaxis=dict(range=[0, CLOUD_WIDTH], **axis),
        yaxis=dict(range=[CLOUD_HEIGHT, 0], **axis),  # reversed so y grows downward
    )
    return fig, omitted
 
 
def cloud_section(title, items, color):
    fig, omitted = build_cloud_figure(items, color)
    children = [
        html.H2(title),
        html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}),
                 style={"overflowX": "auto"}),
    ]
    if omitted:
        children.append(html.P(f"{len(omitted)} word(s) did not fit and were left out: "
                               + ", ".join(omitted)))
    return children
 

def make_app(songs, weights):
    fig = build_figure(songs)
    count_fig = build_count_figure(songs)
    high = select_cloud_words(weights, WORD_COUNT, highest=True)
    low = select_cloud_words(weights, WORD_COUNT, highest=False)
    app = Dash(__name__)
    app.layout = html.Div(
        style={"fontFamily": "system-ui, sans-serif", "padding": "16px"},
        children=[
            html.H2("Political songs per year"),
            dcc.Graph(figure=count_fig, config={"displayModeBar": False}),
            html.H2("Political probability of songs by year"),
            # The graph has a fixed pixel width; this wrapper scrolls sideways.
            html.Div(dcc.Graph(figure=fig, config={"displayModeBar": False}),
                     style={"overflowX": "auto"}),
            *cloud_section("Words with the highest weights (size proportional to weight)",
                           high, COLOR_POLITICAL),
            *cloud_section("Words with the lowest weights (size proportional to how negative the weight is)",
                           low, COLOR_NON_POLITICAL),
        ],
    )
    return app
 
 
if __name__ == "__main__":
    songs = load_songs()
    found = sorted({s["prediction"] for s in songs})
    print(f"Loaded {len(songs)} songs. Distinct 'prediction' values: {found}")
    make_app(songs, load_weights()).run(debug=True)
