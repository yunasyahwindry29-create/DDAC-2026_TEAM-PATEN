"""Province map helpers. Primary = choropleth over the committed 34-province
GeoJSON (joined on the `state` property via dim_province.geojson_state).
Falls back to a centroid bubble map if the GeoJSON is unavailable.
"""
from __future__ import annotations

import json

import plotly.express as px
import streamlit as st

from lib.config import GEOJSON_PATH, DIVERGING_SCALE


@st.cache_resource(show_spinner=False)
def load_geojson() -> dict | None:
    try:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def province_map(df, value_col: str, label: str,
                 color_range: tuple[float, float] | None = None,
                 hover_cols: list[str] | None = None):
    """df must contain `geojson_state`, `lat`, `lon`, `province_name`, value_col."""
    gj = load_geojson()
    hover_cols = hover_cols or []
    if gj is not None:
        fig = px.choropleth(
            df, geojson=gj, locations="geojson_state",
            featureidkey="properties.state", color=value_col,
            color_continuous_scale=DIVERGING_SCALE,
            range_color=color_range,
            hover_name="province_name",
            hover_data={c: True for c in hover_cols} | {"geojson_state": False},
            labels={value_col: label},
        )
        fig.update_geos(fitbounds="locations", visible=False)
    else:
        fig = px.scatter_geo(
            df, lat="lat", lon="lon", color=value_col, size="n_satker",
            color_continuous_scale=DIVERGING_SCALE, range_color=color_range,
            hover_name="province_name", hover_data=hover_cols,
            labels={value_col: label}, projection="mercator",
        )
        fig.update_geos(lataxis_range=[-11, 7], lonaxis_range=[94, 142], visible=True,
                        showcountries=True, showcoastlines=True)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=440,
                      coloraxis_colorbar=dict(title=label))
    return fig
