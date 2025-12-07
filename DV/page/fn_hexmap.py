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

def render_fn_hex_map(filtered_data, map_style):

    st.header("🗄️ Hexagon final_hybrid_score")

    if filtered_data.empty:
        st.warning("ไม่มีข้อมูล")
        return
    
    map_data = filtered_data[[
        "longitude",
        "latitude",
        "final_hybrid_score",
    ]].copy()

    map_data["weight"] = map_data["final_hybrid_score"].fillna(0)

    hex_color_range = [
        [0, 255, 0],
        [255, 255, 0],
        [255, 128, 0],
        [255, 0, 0],
    ]

    hex_layer = pdk.Layer(
        "HexagonLayer",
        map_data,
        get_position=['longitude', 'latitude'],
        radius=1500,
        pickable=True,
        opacity=0.5,
    )

    view_state = pdk.ViewState(
        latitude=filtered_data["latitude"].mean(),
        longitude=filtered_data["longitude"].mean(),
        zoom=10
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[hex_layer],
            initial_view_state=view_state,
            map_style=MAP_STYLES[map_style]
        ),
        height=650
    )
