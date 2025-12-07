import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.neighbors import KernelDensity

try:
    from scipy.spatial import cKDTree
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


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

# FN Heat Map
try:
    from page.fn_heatmap import render_fn_heat_map
except ImportError:
    st.error("ไม่พบโมดูล 'page.fn_heatmap' หรือฟังก์ชัน 'render_fn_heat_map'")
   
# FN Hexagon Map
try:
    from page.fn_hexmap import render_fn_hex_map
except ImportError:
    st.error("ไม่พบโมดูล 'page.fn_hexmap' หรือฟังก์ชัน 'render_fn_hex_map'")
 
# IM Heat Map
try:
    from page.im_heatmap import render_im_heat_map
except ImportError:
    st.error("ไม่พบโมดูล 'page.im_heatmap' หรือฟังก์ชัน 'render_im_heat_map'")
 
# -----------------------------------------------------
# Title
# -----------------------------------------------------

st.title('Urban LiveRisk & Priority Estimation System') 
st.subheader('ระบบประเมินความเสี่ยงและความเร่งด่วนแบบเรียลไทม์')

# -----------------------------------------------------
# 🗄️ การโหลดข้อมูล Traffy Fondue (result.csv) และ สถานที่
# -----------------------------------------------------

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

@st.cache_data
def load_place_data(file_name, place_type):
    try:
        data = pd.read_csv(file_name)
        data = data.dropna(subset=['lat', 'lng', 'district'])
        data = data.rename(columns={'lng': 'longitude', 'lat': 'latitude'})
        
        data['place_type'] = place_type
        
        if place_type == "Department (หน่วยงานราชการ)":
             data = data.rename(columns={'department_name': 'name'})
        elif place_type == "Community (ชุมชน)":
             data = data.rename(columns={'community_name': 'name'})
        elif place_type == "School (โรงเรียน)":
             data = data.rename(columns={'school_name': 'name'})
        elif place_type == "Hospital (โรงพยาบาล)":
             data = data.rename(columns={'hospital_name': 'name'})
        
        required_cols = ['name', 'district', 'latitude', 'longitude', 'place_type']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
             if 'name' in missing_cols:
                 st.warning(f"ไฟล์ {file_name} ไม่มีคอลัมน์ชื่อสถานที่ที่เหมาะสม")
                 data['name'] = f"Unnamed {place_type}"
             
             data_cols = [col for col in required_cols if col in data.columns]
             return data[data_cols]
            
        return data[required_cols]
    except FileNotFoundError:
        st.error(f"ไม่พบไฟล์: {file_name}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลด {file_name}: {e}")
        return pd.DataFrame()
    
data_department = load_place_data('department_clean.csv', 'Department (หน่วยงานราชการ)')
data_community = load_place_data('community_clean.csv', 'Community (ชุมชน)')
data_school = load_place_data('school_clean.csv', 'School (โรงเรียน)')
data_hospital = load_place_data('hospital_clean.csv', 'Hospital (โรงพยาบาล)')

data_places_all = pd.concat([data_department, data_community, data_school, data_hospital], ignore_index=True)

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
selected_place_type = params['selected_place_type'] 

# -----------------------------------------------------
## ⚙️ Global Data Filtering Logic (🔥 ย้ายตรรกะทั้งหมดมาที่นี่)
# -----------------------------------------------------

# 1. เริ่มต้นด้วยข้อมูล Traffy Fondue ทั้งหมด
filtered_data = data_result.copy()

# *** ลบส่วนที่แสดง 'ผลการกรองเหตุการณ์ (Global)' ออกจาก Sidebar ***
st.sidebar.markdown('---')
# st.sidebar.subheader('ผลการกรองเหตุการณ์ (Global)') <--- บรรทัดนี้ถูกลบ
# st.sidebar.write(f"เหตุการณ์เริ่มต้น: **{len(filtered_data)}**") <--- บรรทัดนี้ถูกลบ

# 2. ฟิลเตอร์เขต
if selected_district != "ทั้งหมด":
    filtered_data = filtered_data[filtered_data["district"] == selected_district]
    # st.sidebar.write(f"หลังกรองเขต: **{len(filtered_data)}**") <--- บรรทัดนี้ถูกลบ

# 3. ฟิลเตอร์ปี
if selected_year != "ทั้งหมด":
    if pd.api.types.is_datetime64_any_dtype(filtered_data['timestamp']):
        filtered_data = filtered_data[filtered_data["timestamp"].dt.year == selected_year]
        # st.sidebar.write(f"หลังกรองปี: **{len(filtered_data)}**") <--- บรรทัดนี้ถูกลบ

# 4. ฟิลเตอร์ประเภทสถานที่ (Spatial Filtering Logic)
if selected_place_type != "ทั้งหมด":
    
    if selected_place_type == "Department (หน่วยงานราชการ)":
        place_data_for_filter = data_department
    elif selected_place_type == "Community (ชุมชน)":
        place_data_for_filter = data_community
    elif selected_place_type == "School (โรงเรียน)":
        place_data_for_filter = data_school
    elif selected_place_type == "Hospital (โรงพยาบาล)":
        place_data_for_filter = data_hospital
    else:
        place_data_for_filter = pd.DataFrame() 

    if SCIPY_AVAILABLE and not place_data_for_filter.empty and not filtered_data.empty:
        
        search_radius_meters = st.sidebar.slider(
            'รัศมีการค้นหาเหตุการณ์ใกล้สถานที่ (เมตร):',
            min_value=10, 
            max_value=1000, 
            value=200,
            step=10,
            key='search_radius_global' 
        )
        
        radius_degree = search_radius_meters / 111000 
        
        place_coords = place_data_for_filter[['latitude', 'longitude']].values
        tree = cKDTree(place_coords)
        
        incident_coords = filtered_data[['latitude', 'longitude']].values
        
        indices = tree.query_ball_point(incident_coords, r=radius_degree)
        
        filtered_indices = [i for i, neighbors in enumerate(indices) if neighbors]
        filtered_data = filtered_data.iloc[filtered_indices]

        # st.sidebar.write(f"หลังกรองสถานที่ (ใกล้ {selected_place_type} ใน {search_radius_meters}m): **{len(filtered_data)}**") <--- บรรทัดนี้ถูกลบ
        # st.sidebar.markdown(f"**เหตุการณ์ที่เหลือ: {len(filtered_data)}**") <--- บรรทัดนี้ถูกลบ

    elif not SCIPY_AVAILABLE:
        st.sidebar.warning("⚠️ SciPy ไม่พร้อมใช้งาน. ข้ามการกรองเชิงพื้นที่")
    elif place_data_for_filter.empty:
        st.sidebar.info(f"ไม่พบสถานที่ประเภท **{selected_place_type}** ที่จะใช้กรองเหตุการณ์")

st.sidebar.markdown('---')

# -----------------------------------------------------
## 📑 Main Panel Code (ใช้ Tabs)
# -----------------------------------------------------

# 1. กำหนดชื่อ Tabs
tab_ranking, tab_scatter = st.tabs([
    "🥇 Ranking & Summary",
    "🗺️ Urgency Map", 
])

# -----------------------------------------------------
## 🥇 Tab 1: Ranking & Summary
# -----------------------------------------------------
with tab_ranking:
    
    # ใช้ filtered_data ที่ถูกกรองครบถ้วนแล้ว
    
    # ---------------------------------------------------
    # 🔥 แสดงหัวข้อตามสถานะการกรอง
    # ---------------------------------------------------
    if selected_district != 'ทั้งหมด' and 'district' in filtered_data.columns:
        st.header(f'📑 แสดงข้อมูลเฉพาะ: **เขต{selected_district}**')
    else:
        st.header('📑 แสดงข้อมูล: **ทุกเขต**')
    # ---------------------------------------------------
    # 🔥 แสดงจำนวนข้อมูลที่แจ้งเหตุเข้ามา
    # ---------------------------------------------------
    st.write(f"จำนวนข้อมูลที่แจ้งเหตุเข้ามา: **{len(filtered_data)}** รายการ")

    st.header('🥇 District Ranking: เขตที่แจ้งเหตุเข้ามามากที่สุด')
    
    # ใช้ filtered_data ในการนับจำนวนเหตุการณ์
    if 'district' in filtered_data.columns and not filtered_data.empty:
        district_counts = filtered_data['district'].value_counts() 
        ranking_df = district_counts.reset_index()
        ranking_df.columns = ['District', 'Number of Incidents']
        ranking_df = ranking_df.sort_values(by='Number of Incidents', ascending=False).reset_index(drop=True)

        st.caption('ข้อมูลจากการนับคอลัมน์ "district" ใน: result.csv')

        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรองที่กำหนด")

    st.markdown("---")
    
    st.header('🔍 ข้อมูลเหตุการณ์ที่ถูกกรอง (Data Table)')
    st.caption(f'แสดงข้อมูล **{len(filtered_data)}** รายการ ที่ผ่านตัวกรองทั้งหมด')

    map_data = filtered_data[[
        'comment',
        'district',
        'timestamp',
        'count_reopen',
        'longitude',
        'latitude',
        'public_impact',
        'predicted_urgency',
        'predicted_score',
        'final_hybrid_score'
    ]].copy()
    
    if not map_data.empty:
        st.dataframe(map_data, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรองที่กำหนด เพื่อแสดงในตารางนี้")
    # -----------------------------------------------------

# -----------------------------------------------------
## 🗺️ Tab 2: Scatter Map
# -----------------------------------------------------
with tab_scatter:
    st.header('🗺️ Urgency Map: ตำแหน่งเหตุการณ์')

    st.write(f"แสดงเหตุการณ์จำนวน **{len(filtered_data)}** รายการที่ผ่านการกรอง")
 
    if not filtered_data.empty:
        try:
            render_scatter_map(filtered_data, map_style)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการแสดง Urgency Map: {e}")
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรอง")

    if not filtered_data.empty:
        try:
            render_im_heat_map(filtered_data, map_style)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการแสดง Urgency Map: {e}")
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรอง")

    if not filtered_data.empty:
        try:
            render_fn_heat_map(filtered_data, map_style)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการแสดง Urgency Map: {e}")
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรอง")

    if not filtered_data.empty:
        try:
            render_fn_hex_map(filtered_data, map_style)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการแสดง Urgency Map: {e}")
    else:
        st.info("ไม่พบข้อมูลเหตุการณ์ที่ตรงตามตัวกรอง")