import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Page Config
st.set_page_config(page_title="Deewary ERP", layout="wide", initial_sidebar_state="expanded")

# 2. Supabase Setup (Make sure secrets are in one line)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Configuration Error: Please check your Streamlit Secrets.")

# 3. Modern UI Styling (Mobile Friendly)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .property-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #007bff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .property-card:hover { transform: translateY(-5px); }
    .price-tag { color: #28a745; font-weight: bold; font-size: 1.2em; }
    .location-text { color: #6c757d; font-size: 0.9em; }
    .sidebar-title { color: #007bff; font-weight: bold; font-size: 20px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. Sidebar Menu
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏢 Deewary ERP</div>', unsafe_allow_html=True)
    menu = st.radio("Navigation", ["📊 Dashboard", "➕ Add Property", "📋 Inventory List"])
    st.info("Logged in as: Anas (Admin)")

# 5. Dashboard
if menu == "📊 Dashboard":
    st.title("Business Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Units", "124", "↑ 5")
    c2.metric("Available", "85", "-2")
    c3.metric("Sold", "39", "↑ 12")
    
    st.subheader("Recent Activity")
    st.write("Abhi tak koi naya notification nahi hai.")

# 6. Add Property
elif menu == "➕ Add Property":
    st.title("New Property Entry")
    with st.container():
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            p_name = col1.text_input("Property Name / Title", placeholder="e.g. Blue Area Office")
            p_price = col2.text_input("Demand Price", placeholder="e.g. 2.5 Crore")
            p_loc = st.text_input("Full Address", placeholder="Sector, City")
            
            # Form button styling - centered and small as per your preference
            sub_col1, sub_col2, sub_col3 = st.columns([1,1,1])
            with sub_col2:
                btn = st.form_submit_button("Save to Inventory")
            
            if btn:
                if p_name and p_price:
                    data = {"name": p_name, "price": p_price, "location": p_loc}
                    try:
                        supabase.table("properties").insert(data).execute()
                        st.success(f"✅ {p_name} has been added to Deewary database.")
                    except:
                        st.error("Database connection failed. Table name 'properties' check karein.")
                else:
                    st.warning("Please fill required fields.")

# 7. Inventory List (HTML View)
elif menu == "📋 Inventory List":
    st.title("Current Inventory")
    
    try:
        res = supabase.table("properties").select("*").execute()
        properties = res.data
        
        if properties:
            for p in properties:
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 20px; font-weight: 600; color: #1f2937;">{p['name']}</span>
                        <span style="background: #e1ecfe; color: #007bff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">ACTIVE</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="location-text">📍 {p.get('location', 'Islamabad')}</span><br>
                        <span class="price-tag">PKR {p['price']}</span>
                    </div>
                    <div style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px; font-size: 11px; color: #999;">
                        ID: {p.get('id', 'N/A')} | Deewary Pro Management System
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Inventory is empty.")
    except Exception as e
