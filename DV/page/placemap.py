# page/placemap.py

import streamlit as st
import pydeck as pdk
import pandas as pd

MAP_STYLES = {
    'Dark': pdk.map_styles.DARK,
    'Light': pdk.map_styles.LIGHT,
    'Road': pdk.map_styles.ROAD,
    'Satellite': pdk.map_styles.SATELLITE,
}

@st.cache_data
def load_data_placemap(file_path):
    df = pd.read_csv(file_path)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    df.rename(columns={'lng': 'lon'}, inplace=True)
    df.dropna(subset=['lat', 'lon'], inplace=True)
    return df

@st.cache_data
def load_all_placemap_data():
    try:
        dataframes = {
            "🏬 Department": load_data_placemap('department_clean.csv'),
            "📠 Community": load_data_placemap('community_clean.csv'),
            "🏫 School": load_data_placemap('school_clean.csv'),
            "🏥 Hospital": load_data_placemap('hospital_clean.csv'),
        }
        return dataframes
    except FileNotFoundError as e:
        st.error(f"⚠️ **ไม่พบไฟล์ข้อมูล Placemap**: ตรวจสอบว่าไฟล์ `{e.filename.split('/')[-1]}` อยู่ในโฟลเดอร์หลัก")
        return None


def render_place_map():
    """แสดงผลส่วนของ Placemap โดยใช้ Tabs"""
    
    dataframes = load_all_placemap_data()
    
    if dataframes is None:
        return

    categories = list(dataframes.keys())
    
    st.header("📍 ข้อมูลสถานที่สำคัญ (แยกตามหมวดหมู่)")
    st.caption("ข้อมูลจาก Department.csv, Community.csv, School.csv, Hospital.csv")

    tabs = st.tabs(categories)

    for i, tab in enumerate(tabs):
        category_name = categories[i]
        df_selected = dataframes[category_name]
        
        with tab:
            st.subheader(f"แผนที่: **{category_name}**")
            
            if not df_selected.empty:
                map_data = df_selected[['lat', 'lon']]
                
                # แสดงแผนที่
                st.map(map_data, zoom=10)
                
                # แสดงตารางข้อมูล
                st.caption(f"ตารางข้อมูล {category_name} ({len(df_selected)} รายการ)")
                st.dataframe(df_selected, use_container_width=True)

            else:
                st.info(f"❌ ไม่พบข้อมูล หรือข้อมูลพิกัดไม่สมบูรณ์สำหรับหมวดหมู่ {category_name}")