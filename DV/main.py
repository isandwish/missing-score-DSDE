import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.neighbors import KernelDensity

# Sidebar
try:
    from page.sidebar_filters import render_sidebar_filters
except ImportError:
    st.error("ไม่พบโมดูล 'page.sidebar_filters' กรุณาตรวจสอบว่าไฟล์ 'page/sidebar_filters.py' ถูกสร้างและมีฟังก์ชัน 'render_sidebar_filters' อยู่หรือไม่")

# Scatter Map
try:
    from page.scattermap import render_scatter_map
except ImportError:
    st.error("ไม่พบโมดูล 'page.scattermap' หรือฟังก์ชัน 'render_scatter_map'")

# # District Map
# try:
#     from page.districtmap import render_district_map
# except ImportError:
#     st.error("ไม่พบโมดูล 'page.districtmap' หรือฟังก์ชัน 'render_district_map'")

# Place Map
try:
    from page.placemap import render_place_map
except ImportError:
    st.error("ไม่พบโมดูล 'page.placemap' หรือฟังก์ชัน 'render_place_map'")

st.title('Data Science for Traffy Fondue Dataset') 

# From test_data.csv
@st.cache_data
def load_result_data():
    data_result = pd.read_csv('result.csv')
    data_result = data_result.dropna(subset=['lat', 'lng'])
    data_result = data_result.rename(columns={'lng': 'longitude', 'lat': 'latitude'})
    
    if 'final_hybrid_score' in data_result.columns:
        data_result['final_hybrid_score'] = pd.to_numeric(data_result['final_hybrid_score'], errors='coerce')
    else:
        st.error("Column 'final_hybrid_score' not found. Please check your CSV file.")

    if 'timestamp' in data_result.columns:
        data_result['timestamp'] = pd.to_datetime(data_result['timestamp'], errors='coerce')
        data_result = data_result.dropna(subset=['timestamp'])
            
    return data_result

data_result = load_result_data()

# # From gdf_public_impact.csv
# @st.cache_data
# def load_gdf_data():
#     data_gdf = pd.read_csv('gdf_public_impact.csv')
#     data_gdf = data_gdf.dropna(subset=['lat', 'lng'])
#     data_gdf = data_gdf.rename(columns={'lng': 'longitude', 'lat': 'latitude'})

#     if 'timestamp' in data_gdf.columns:
#         data_gdf['timestamp'] = pd.to_datetime(data_gdf['timestamp'], errors='coerce')
#         data_gdf = data_gdf.dropna(subset=['timestamp'])
        
#     return data_gdf

# data_gdf = load_gdf_data()


MAP_STYLES = {
    'Light': pdk.map_styles.LIGHT,
    'Dark': pdk.map_styles.DARK,
    'Road': pdk.map_styles.ROAD,
    'Satellite': pdk.map_styles.SATELLITE,
}

# -----------------------------------------------------
## 🗄️ Sidebar Filters and Parameters 
# -----------------------------------------------------

params = render_sidebar_filters(data_result) 
map_style = params['map_style']
selected_district = params['selected_district']
selected_year = params['selected_year']

# -----------------------------------------------------
## 📑 Main Panel Code (ใช้ Tabs)
# -----------------------------------------------------

# 1. กำหนดชื่อ Tabs
tab_ranking, tab_scatter, tab_placemap = st.tabs([
# tab_ranking, tab_scatter, tab_district, tab_placemap = st.tabs([
    "🥇 Ranking & Summary",
    "🗺️ Scatter Map",
    # "📊 District Map (gdf_public_impact)",
    "📍 Place Map" 
])

# -----------------------------------------------------
## 🥇 Tab 1: Ranking & Summary
# -----------------------------------------------------
with tab_ranking:
    # ตรรกะการฟิลเตอร์ (ยังคงต้องทำ เพราะ Tab อื่นใช้ filtered_data_gdf)
    if selected_district != 'ทั้งหมด' and 'district' in data_result.columns:
        filtered_data_result = data_result[data_result['district'] == selected_district].copy()
        st.header(f'📑 แสดงข้อมูลเฉพาะ: **เขต{selected_district}**')
    elif 'district' in data_result.columns and not data_result.empty:
        filtered_data_result = data_result.copy()
        st.header('📑 แสดงข้อมูล: **ทุกเขต**')
    else:
        filtered_data_result = data_result.copy()

    st.write(f"จำนวนข้อมูลที่แจ้งเหตุเข้ามา: **{len(filtered_data_result)}** รายการ")

    st.header('🥇 District Ranking: เขตที่แจ้งเหตุเข้ามามากที่สุด')
    
    district_counts = data_result['district'].value_counts()
    ranking_df = district_counts.reset_index()
    ranking_df.columns = ['District', 'Number of Incidents']
    ranking_df = ranking_df.sort_values(by='Number of Incidents', ascending=False).reset_index(drop=True)

    st.caption('ข้อมูลจากการนับคอลัมน์ "district" ใน: gdf_public_impact.csv')

    if not ranking_df.empty:
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลเขต หรือคอลัมน์ 'district' มีปัญหา")
    
# -----------------------------------------------------
## 🗺️ Tab 2: Scatter Map
# -----------------------------------------------------
with tab_scatter:
    st.header('🗺️ Scatter Map: ตำแหน่งเหตุการณ์ (test_data.csv)')

    # -------------------------------
    # ⭐ ใช้ค่าฟิลเตอร์จาก Sidebar
    # -------------------------------
    filtered_data = data_result.copy()

    # ฟิลเตอร์เขต
    if selected_district != "ทั้งหมด":
        filtered_data = filtered_data[filtered_data["district"] == selected_district]

    # ฟิลเตอร์ปี
    if selected_year != "ทั้งหมด":
        filtered_data = filtered_data[filtered_data["timestamp"].dt.year == selected_year]

    # -------------------------------
    # ⭐ ส่งเข้า Scatter Map (อันนี้สำคัญ)
    # -------------------------------
    try:
        render_scatter_map(filtered_data, map_style)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการแสดง Scatter Map: {e}")

# # -----------------------------------------------------
# ## 📊 Tab 3: District Map
# # -----------------------------------------------------
# with tab_district:
#     st.header('📊 District Map: แผนที่ตามเขต (gdf_public_impact.csv)')
#     try:
#         # ใช้ filtered_data_gdf ที่ถูกฟิลเตอร์จาก Sidebar
#         render_district_map(filtered_data_gdf, map_style) 
#     except Exception as e:
#         st.error(f"เกิดข้อผิดพลาดในการแสดง District Map: {e}")

# -----------------------------------------------------
## 📍 Tab 4: Placemap
# -----------------------------------------------------
with tab_placemap:
    # เรียกใช้ฟังก์ชันจากไฟล์ใหม่
    render_place_map() 

