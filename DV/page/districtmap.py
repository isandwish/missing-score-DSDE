# districtmap.py (ปรับปรุงใหม่)

import streamlit as st
import pydeck as pdk
import pandas as pd

MAP_STYLES = {
    'Dark': pdk.map_styles.DARK,
    'Light': pdk.map_styles.LIGHT,
    'Road': pdk.map_styles.ROAD,
    'Satellite': pdk.map_styles.SATELLITE,
}

# -----------------------------
# 🟢 District Map
# -----------------------------
def render_district_map(filtered_data, map_style):

    st.header("📍 ตำแหน่งการแจ้งเหตุทั้งหมด (Circle Map)")

    if filtered_data.empty:
        st.warning("ไม่มีข้อมูลการแจ้งเหตุที่แสดงในขณะนี้")
        return

    # ------------------------------------------------
    # 🎨 กำหนดสีเดียว: สีน้ำเงิน (Blue)
    # ------------------------------------------------
    # [R, G, B, A] - A = Alpha (ความทึบแสง)
    SINGLE_COLOR = [0, 100, 255, 200] 
    
    # ------------------------------------------------
    # ⭐ Scatter Layer (ใช้สีเดียวสำหรับทุกจุด)
    # ------------------------------------------------
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        filtered_data,
        get_position=["longitude", "latitude"],
        get_fill_color=SINGLE_COLOR, # กำหนดสีเดียว
        get_line_color=[0, 0, 0, 100], # กำหนดสีขอบเป็นสีดำจางๆ
        get_radius=100,
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.7,
    )

    # ------------------------------------------------
    # ⭐ ตั้งค่า view ตาม center ของข้อมูล
    # ------------------------------------------------
    view_state = pdk.ViewState(
        latitude=filtered_data["latitude"].mean(),
        longitude=filtered_data["longitude"].mean(),
        zoom=10
    )

    # แสดงแผนที่
    st.pydeck_chart(
        pdk.Deck(
            layers=[scatter_layer],
            initial_view_state=view_state,
            map_style=MAP_STYLES[map_style],
            tooltip={"text": "ตำแหน่งแจ้งเหตุ\nLatitude: {latitude}\nLongitude: {longitude}"}
        ),
        height=650
    )