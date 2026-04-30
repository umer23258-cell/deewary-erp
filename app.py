import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- 3. CUSTOM STYLING (Dark Theme & High Contrast) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Metrics / Amounts Styling */
    [data-testid="stMetricValue"] {
        color: #f1c40f !important; /* Gold Color for Amounts */
        font-size: 35px !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 18px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* WhatsApp Button */
    .whatsapp-float {
        position: fixed; width: 60px; height: 60px; bottom: 40px; right: 40px;
        background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center;
        font-size: 30px; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); z-index: 100;
    }
    
    /* Software Info Box */
    .info-card {
        background-color: #111827;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #374151;
        margin-bottom: 20px;
    }
    
    /* Project Detail Box */
    .project-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-right: 4px solid #f1c40f;
    }
    </style>
    
    <a href="https://wa.me/923115190118" class="whatsapp-float" target="_blank">
        <i style="margin-top:16px;" class="fa fa-whatsapp"></i>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css">
    </a>
""", unsafe_allow_html=True)

# --- 4. FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong password!")
    return False

# --- 5. SIDEBAR ---
st.sidebar.title("🏗️ DEEWARY.COM")
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Reports"])

df = fetch_data()

# --- 6. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>Financial Overview</h1>", unsafe_allow_html=True)
    
    # --- LEVEL 1: AMOUNTS (High Contrast) ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL INCOME", f"PKR {inc:,.0f}")
    col2.metric("TOTAL EXPENSES", f"PKR {exp:,.0f}")
    col3.metric("NET BALANCE", f"PKR {bal:,.0f}")

    st.write("##")
    
    # --- LEVEL 2: QUICK ACTIONS ---
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("⚡ Quick Transactions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Register Income", use_container_width=True): st.session_state.show_form = "Income"; st.rerun()
        if c2.button("👷 Pay Labor Fee", use_container_width=True): st.session_state.show_form = "Labor"; st.rerun()
        if c3.button("🏗️ Buy Material", use_container_width=True): st.session_state.show_form = "Material"; st.rerun()
    
    # --- LEVEL 3: SOFTWARE INFORMATION ---
    st.write("##")
    st.markdown(f"""
    <div class="info-card">
        <h3 style="color: #3b82f6; margin-bottom: 10px;">🏗️ Deewary.com ERP - Enterprise Solution</h3>
        <p>Yeh software <b>Deewary.com</b> ke projects ki real-time monitoring aur expense management ke liye develop kiya gaya hai.</p>
        <div style="display: flex; gap: 20px; font-size: 14px; color: #9ca3af;">
            <span><b>Developer:</b> Umer Sherin</span>
            <span><b>Version:</b> 2.1.0 (Pro)</span>
            <span><b>Database:</b> Supabase Secure Cloud</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LEVEL 4: PROJECT PICTURES & DETAILS ---
    st.divider()
    st.subheader("📸 Site Inspection: Yousaf Colony")
    
    p_img1, p_img2, p_info = st.columns([1, 1, 2])
    
    with p_img1:
        st.image("https://i.ibb.co/6Jbx8yjD/Whats-App-Image-2026-04-30-at-12-11-01-PM.jpg", width=220)
    with p_img2:
        st.image("https://i.ibb.co/6R0yR8Xz/1JK5M0FR.jpg", width=220)
        
    with p_info:
        st.markdown("""
        <div class="project-card">
            <h4 style="color: #f1c40f; margin-top: 0;">📋 Project Site Analytics</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                <tr><td><b>Project:</b></td><td>Yousaf Colony Renovation</td></tr>
                <tr><td><b>Area:</b></td><td>5 Marla Double Story</td></tr>
                <tr><td><b>Supervisor:</b></td><td>Umer Sherin</td></tr>
                <tr><td><b>Current Phase:</b></td><td>Paint & Finishing Work</td></tr>
                <tr><td><b>Completion:</b></td><td>85% Achieved</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        st.write("🏗️ Progress Bar:")
        st.progress(85)

    # --- FORM LOGIC (Original Maintenance) ---
    if "show_form" in st.session_state:
        if check_password():
            # (Rest of your form logic remains untouched to preserve functionality)
            st.write("---")
            with st.expander(f"Add {st.session_state.show_form} Entry", expanded=True):
                with st.form("data_form"):
                    d_name = st.text_input("Name/Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(datetime.now().date()), "type": st.session_state.show_form, "name": d_name, "amount": d_amt}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        del st.session_state.show_form
                        st.success("Data Synced!")
                        st.rerun()

# --- 7. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        st.dataframe(f_df, use_container_width=True)
        st.info(f"Summary Total: PKR {f_df['amount'].sum():,.0f}")
