"""Reusable Plotly chart builders with a consistent theme.

Chart-per-question discipline: line=trend, box=distribution, scatter=positioning,
choropleth=geography (in geo.py), heatmap=two categoricals, diverging bar=gap.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from lib.config import (
    COLOR_PRIMARY, COLOR_GOOD, COLOR_BAD, COLOR_WARN,
    DIVERGING_SCALE, HEALTHY_THRESHOLD,
)
from lib.data import QUADRANT_COLORS, QUADRANT_LABELS

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=420,
               plot_bgcolor="white", font=dict(size=13))


def _apply(fig, height=None):
    fig.update_layout(**{**_LAYOUT, **({"height": height} if height else {})})
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F6")
    return fig


def national_trend(nat: pd.DataFrame):  # noqa: F821
    fig = px.line(nat, x="year", y="avg_nilai_akhir", markers=True,
                  labels={"year": "Tahun", "avg_nilai_akhir": "IKPA rata-rata"})
    fig.update_traces(line=dict(color=COLOR_PRIMARY, width=3), marker=dict(size=9))
    fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color=COLOR_WARN,
                  annotation_text="Batas sehat (89)", annotation_position="bottom right")
    for _, r in nat.iterrows():
        fig.add_annotation(x=r["year"], y=r["avg_nilai_akhir"],
                           text=f"{r['avg_nilai_akhir']:.1f}", showarrow=False, yshift=14)
    fig.update_yaxes(range=[min(85, nat["avg_nilai_akhir"].min() - 2), 100])
    return _apply(fig, 360)


def monthly_buildup(mon: pd.DataFrame):  # noqa: F821
    fig = px.line(mon, x="periode", y="avg_nilai_akhir", color="year", markers=True,
                  labels={"periode": "Bulan (kumulatif)", "avg_nilai_akhir": "IKPA rata-rata",
                          "year": "Tahun"})
    fig.update_xaxes(dtick=1)
    return _apply(fig, 360)


def distribution_by_year(df: pd.DataFrame, value="avg_nilai_akhir"):  # noqa: F821
    """Box/strip of an entity-level distribution per year (spread reveal)."""
    fig = px.box(df, x="year", y=value, points="all",
                 labels={"year": "Tahun", value: "IKPA"}, color_discrete_sequence=[COLOR_PRIMARY])
    fig.update_traces(marker=dict(size=4, opacity=0.45), jitter=0.4)
    fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color=COLOR_WARN)
    return _apply(fig, 400)


def quadrant_scatter(q: pd.DataFrame, name_col: str, title_label="entitas"):  # noqa: F821
    label_colors = {QUADRANT_LABELS[k]: QUADRANT_COLORS[k] for k in QUADRANT_LABELS}
    fig = px.scatter(
        q, x="level", y="slope", color="quadrant_label", size="n_satker",
        color_discrete_map=label_colors, hover_name=name_col,
        category_orders={"quadrant_label": list(label_colors.keys())},
        labels={"level": "Kinerja terkini (IKPA)", "slope": "Tren per tahun (+ membaik)",
                "quadrant_label": "Kuadran"},
        custom_data=["quadrant_label"],
    )
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>IKPA: %{x:.1f}"
                      "<br>Tren: %{y:+.2f}/th<br>%{customdata[0]}<extra></extra>")
    div = q["divider_level"].iloc[0] if len(q) else HEALTHY_THRESHOLD
    fig.add_vline(x=div, line_dash="dot", line_color="#888")
    fig.add_hline(y=0, line_dash="dot", line_color="#888")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return _apply(fig, 480)


def diverging_gap(gap: pd.DataFrame):  # noqa: F821
    g = gap.sort_values("weighted_gap")
    colors = [COLOR_BAD if v > 0 else COLOR_GOOD for v in g["weighted_gap"]]
    fig = go.Figure(go.Bar(
        x=g["weighted_gap"], y=g["label"], orientation="h", marker_color=colors,
        hovertemplate="%{y}<br>Kontribusi gap: %{x:+.2f} poin<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#444")
    fig.update_layout(xaxis_title="Kontribusi terhadap selisih vs nasional (poin tertimbang)",
                      yaxis_title="")
    return _apply(fig, 380)


def matrix_heatmap(piv, zmin=80, zmax=100):
    fig = px.imshow(piv, color_continuous_scale=DIVERGING_SCALE, zmin=zmin, zmax=zmax,
                    aspect="auto", labels=dict(x="Provinsi", y="K/L", color="IKPA"))
    fig.update_xaxes(side="top", tickangle=45, title_text="")
    fig.update_yaxes(title_text="")
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=620,
                      coloraxis_colorbar=dict(title="IKPA"))
    return fig


def component_small_multiples(df, facet_col="label"):
    fig = px.line(df, x="year", y="avg_nilai", facet_col=facet_col, facet_col_wrap=4,
                  markers=True, labels={"year": "", "avg_nilai": ""})
    fig.update_traces(line=dict(color=COLOR_PRIMARY, width=2))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=11)))
    fig.update_yaxes(range=[60, 102])
    fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color=COLOR_WARN)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=460, plot_bgcolor="white")
    return fig


def cohort_bars(df):
    fig = px.bar(df, x="avg_nilai", y="label", color="kohort", barmode="group",
                 orientation="h", color_discrete_sequence=[COLOR_BAD, COLOR_PRIMARY],
                 labels={"avg_nilai": "Nilai komponen rata-rata", "label": "", "kohort": ""})
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return _apply(fig, 460)


def region_bar(df, x, y, color_col=None):
    fig = px.bar(df, x=x, y=y, color=color_col, color_continuous_scale=DIVERGING_SCALE,
                 range_color=(88, 97))
    fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color=COLOR_WARN)
    return _apply(fig, 360)
