import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components
import requests
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- PDF & HELPERS (Aapka original logic) ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"<font color='#FF4B4B' size=18><b>{title}</b></font>", styles['Title']))
    # ... (Aapka baki PDF logic waisa hi hai)
    doc.build(elements)
    buf.seek(0)
    return buf

# --- STYLING & HERO DESIGN ---
st.set_page_config(page_title="Deewaryn.com ERP", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Hero Section - Image Design */
    .hero-container {
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url('https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=2070');
        background-size: cover;
        background-position: center;
        padding: 80px 40px;
        text-align: center;
        color: white;
        border-radius: 20px;
        margin-bottom: 30px;
    }
    .hero-title { font-size: 48px; font-weight: 800; text-transform: uppercase; margin: 0; }
    .hero-subtitle { font-size: 18px; font-weight: 300; opacity: 0.9; margin-top: 10px; }
    
    /* Baki aapka original CSS yahan append hoga */
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- 5. INITIALIZE STATE & DATA ---
raw_df = supabase.table('transactions').select("*").execute().data
raw_df = pd.DataFrame(raw_df)
if "selected_project" not in st.session_state: st.session_state["selected_project"] = "Yousaf Colony"
current_project = st.session_state["selected_project"]

# --- SIDEBAR (Aapka original) ---
with st.sidebar:
    st.markdown("## DEEWARYN ERP")
    menu = st.radio("Navigation", ["📊 Dashboard View", "📑 Receipt Voucher System", "💰 Income Ledger", "🏗️ Material Log Vault"])

# --- 9. RENDER DASHBOARD (Updated with Hero) ---
if "Dashboard" in menu:
    # --- Yahan humne aapka image wala Hero Section insert kiya hai ---
    st.markdown(f"""
        <div class="hero-container">
            <h1 class="hero-title">WE ARE BUILDERS AT HEART.</h1>
            <p class="hero-subtitle">And we build so much more than buildings.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- Yahan aapka original Dashboard logic continue karein ---
    st.subheader(f"Project Status: {current_project}")
    # (Baki ka aapka code yahan paste karein)
    
# --- (Baaki sab functions jaise popup_register_labor, etc. waise hi hain) ---
