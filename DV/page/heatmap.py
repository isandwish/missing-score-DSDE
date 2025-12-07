import streamlit as st
import pydeck as pdk
import pandas as pd
import leafmap.foliumap as leafmap

MAP_STYLES = {
    'Dark': pdk.map_styles.DARK,
    'Light': pdk.map_styles.LIGHT,
    'Road': pdk.map_styles.ROAD,
    'Satellite': pdk.map_styles.SATELLITE,
}

def render_heat_map(filtered_data, map_style):

    st.header("🔥 Heatmap Only (Hotspot)")

    if filtered_data.empty:
        st.warning("ไม่มีข้อมูล")
        return

    filtered_data["weight"] = filtered_data["rank"].fillna(0)

    heat_color_range = [
        [0, 255, 0],
        [255, 255, 0],
        [255, 128, 0],
        [255, 0, 0],
    ]

    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        filtered_data,
        get_position=["longitude", "latitude"],
        get_weight="weight",
        radiusPixels=70,
        colorRange=heat_color_range,
        intensity=3,
        threshold=0.01,
        opacity=0.6,
    )

    view_state = pdk.ViewState(
        latitude=filtered_data["latitude"].mean(),
        longitude=filtered_data["longitude"].mean(),
        zoom=12
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[heatmap_layer],
            initial_view_state=view_state,
            map_style=MAP_STYLES[map_style]
        ),
        height=650
    )
