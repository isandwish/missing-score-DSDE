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
# 🎨 label ระดับความรุนแรง
# -----------------------------
def final_hybrid_score_label(final_hybrid_score):
    if final_hybrid_score >= 9:
        return "แดง (ฉุกเฉินมาก)"
    elif final_hybrid_score >= 7:
        return "ส้ม (ค่อนข้างรุนแรง)"
    elif final_hybrid_score >= 5:
        return "เหลือง (ปานกลาง)"
    elif final_hybrid_score >= 3:
        return "เขียวอ่อน (เล็กน้อย)"
    else:
        return "เขียว (ไม่เร่งรีบ)"

# -----------------------------
# 🎨 สีของแต่ละ label
# -----------------------------
def final_hybrid_score_color(final_hybrid_score):
    if final_hybrid_score >= 9:
        return [255, 0, 0, 230]           # แดง
    elif final_hybrid_score >= 7:
        return [255, 128, 0, 230]         # ส้ม
    elif final_hybrid_score >= 5:
        return [255, 255, 0, 230]         # เหลือง
    elif final_hybrid_score >= 3:
        return [173, 255, 47, 230]        # เขียวอ่อน
    else:
        return [0, 255, 0, 230]           # เขียว

# -----------------------------
# 🟢 Urgency Map
# -----------------------------
def render_scatter_map(filtered_data, map_style):

    if filtered_data.empty:
        st.warning("ไม่มีข้อมูล")
        return

    # -------------------------------
    # 🟢 1) เตรียม label + สี (ทำครั้งเดียว!!)
    # -------------------------------
    filtered_data["final_hybrid_score_label"] = filtered_data["final_hybrid_score"].apply(final_hybrid_score_label)
    filtered_data["final_hybrid_score_color"] = filtered_data["final_hybrid_score"].apply(final_hybrid_score_color)

    # -------------------------------
    # 🟢 2) Filter สี
    # -------------------------------
    color_options = [
        "แดง (ฉุกเฉินมาก)",
        "ส้ม (ค่อนข้างรุนแรง)",
        "เหลือง (ปานกลาง)",
        "เขียวอ่อน (เล็กน้อย)",
        "เขียว (ไม่เร่งรีบ)",
    ]

    color_filter = st.multiselect(
        "เลือกสีที่ต้องการแสดงบนแผนที่",
        options=color_options,
        default=color_options
    )

    filtered_data = filtered_data[filtered_data["final_hybrid_score_label"].isin(color_filter)]

    if filtered_data.empty:
        st.warning("ไม่มีข้อมูลหลังใช้ตัวกรองสี")
        return

    # -------------------------------
    # 🟢 3) ✂️ ตัด column ให้เหลือเฉพาะที่จำเป็นหลังจาก filter แล้ว
    # -------------------------------
    map_data = filtered_data[[
        "longitude",
        "latitude",
        "comment",
        "district",
        "timestamp",
        "final_hybrid_score_color",
        "final_hybrid_score_label",
    ]].copy()

    # 🕒 แก้ timestamp ไม่ให้เป็น [object Object]
    map_data["timestamp"] = pd.to_datetime(map_data["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------
    # 🟢 4) สร้าง Scatter Layer
    # -------------------------------
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        map_data,
        get_position=["longitude", "latitude"],
        get_fill_color="final_hybrid_score_color",
        get_line_color="final_hybrid_score_color",
        get_radius=150,
        line_width_min_pixels=2,
        pickable=True,
        opacity=0.8,
    )

    # view state
    view_state = pdk.ViewState(
        latitude=map_data["latitude"].mean(),
        longitude=map_data["longitude"].mean(),
        zoom=10
    )

    # show map
    st.pydeck_chart(
        pdk.Deck(
            layers=[scatter_layer],
            initial_view_state=view_state,
            map_style=MAP_STYLES[map_style],
            tooltip={"text": "Urgency: {final_hybrid_score_label}\nDistrict: {district}\nComment: {comment}\nTime: {timestamp}"}
        ),
        height=650
    )
