import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Deewaryn ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (Styled like the Image) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0f0f0f; color: white; }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url('https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=2070');
        background-size: cover;
        background-position: center;
        padding: 80px 40px;
        text-align: center;
        border-radius: 20px;
        margin-bottom: 30px;
        border: 1px solid #333;
    }
    .hero-title { font-size: 50px; font-weight: 800; text-transform: uppercase; margin: 0; }
    .hero-subtitle { font-size: 20px; color: #ff5b1a; font-weight: 400; margin-top: 10px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a1a; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data(): return pd.DataFrame(supabase.table('transactions').select("*").execute().data)

# --- INITIALIZATION ---
if "selected_project" not in st.session_state: st.session_state["selected_project"] = "Yousaf Colony"
raw_df = fetch_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARYN ERP")
    menu = st.radio("Navigation", ["Dashboard", "Reports", "Labor Logs"])

# --- MAIN DASHBOARD ---
if menu == "Dashboard":
    # Hero Section
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">WE ARE BUILDERS AT HEART.</h1>
            <p class="hero-subtitle">And we build so much more than buildings.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # KPIs
    if not raw_df.empty:
        inc = raw_df[raw_df['type'] == 'Income']['amount'].sum()
        exp = raw_df[raw_df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"PKR {inc:,.0f}")
        col2.metric("Total Expenses", f"PKR {exp:,.0f}")
        col3.metric("Net Balance", f"PKR {inc-exp:,.0f}")
    
    st.divider()
    st.subheader("Recent Activity")
    st.dataframe(raw_df.head(10), use_container_width=True)

elif menu == "Reports":
    st.title("📑 System Reports")
    st.write("View and export your project audit logs here.")
    if st.button("Download Data as CSV"):
        st.download_button("Click to download", raw_df.to_csv(index=False), "report.csv")

elif menu == "Labor Logs":
    st.title("👷 Labor Management")
    # Add Labor table code here...
    st.write("Labor profiles will appear here.")
