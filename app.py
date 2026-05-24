import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components

# --- SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deewaryn.com ERP", layout="wide", page_icon="🏗️")

# --- PROFESSIONAL CSS (Glassmorphism & Large Amounts) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(240, 242, 245, 0.85), rgba(240, 242, 245, 0.85)), 
                          url("https://i.postimg.cc/Vs46KqYW/ej-yao-D46m-XLs-QRJw-unsplash.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .block-container {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(15px);
        border-radius: 30px;
        padding: 3rem !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }
    /* Amount styling - Big & Bold */
    .kpi-card { 
        background: rgba(255, 255, 255, 0.9); 
        padding: 30px; 
        border-radius: 20px; 
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .kpi-card h2 { 
        font-size: 42px !important; 
        font-weight: 900 !important; 
        color: #0f172a !important; 
        margin: 10px 0 0 0 !important;
    }
    .kpi-card p { 
        font-size: 14px !important; 
        font-weight: 700 !important; 
        text-transform: uppercase; 
        color: #64748b;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=60)
def fetch_all_raw_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏢 DEEWARYN ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income Ledger", "🏗️ Material Log"])
    st.divider()
    st.markdown("### ℹ️ About")
    st.caption("Site Infrastructure Control v2.0")

# --- DASHBOARD LOGIC ---
if "Dashboard" in menu:
    st.title("🏗️ Site Command Center")
    df = fetch_all_raw_data()
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
        
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='kpi-card'><p>💰 Total Income</p><h2>{inc:,.0f}</h2></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='kpi-card'><p>📉 Total Outflow</p><h2>{exp:,.0f}</h2></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='kpi-card'><p>⚖️ Net Balance</p><h2>{bal:,.0f}</h2></div>", unsafe_allow_html=True)
    
    st.write("##")
    st.info("System is operational. Ensure daily data entry for all active sites.")

# --- MOCKUP FIX FOR LINE 408 ERROR (WhatsApp) ---
# Agar aapko button par link lagana hai, to ye line use karein:
# st.markdown(f'<a href="{wa_url}" target="_blank">Share via WhatsApp \U0001F4F2</a>', unsafe_allow_html=True)
