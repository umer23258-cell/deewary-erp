import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import plotly.express as px

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (Compact & Small Buttons) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* Buttons ko chota aur sidebar ke mutabiq set karne ke liye */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        height: 2.2em;
        font-size: 13px !important;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .status-card {
        padding: 15px;
        border-radius: 12px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .status-card h3 { font-size: 18px !important; margin: 0; }
    .status-card p { font-size: 12px !important; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS (ORIGINAL LOGIC) ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 4. SIDEBAR (COMPACT BUTTONS SHIFTED HERE) ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & Reports"])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.markdown("### ➕ Quick Entry")
        # Buttons shifted to sidebar and made compact
        if st.button("💰 Add Income"): st.session_state.show_form = "Income"
        if st.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if st.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
        
        st.divider()
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True)

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1:
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=80)
    with h_col2:
        st.markdown("<h3 style='margin:0;'>DEEWARY.COM ERP</h3><p style='color:#FF4B4B; font-weight:bold; margin:0; font-size:14px;'>C.E.O: SARDAR SAMI ULLAH</p>", unsafe_allow_html=True)

    # Original Stats (Compact Cards)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="status-card" style="background: #2193b0;"><h3>PKR {inc:,.0f}</h3><p>Total Income</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="status-card" style="background: #f12711;"><h3>PKR {exp:,.0f}</h3><p>Total Expenses</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="status-card" style="background: #11998e;"><h3>PKR {bal:,.0f}</h3><p>Net Balance</p></div>', unsafe_allow_html=True)

    # Forms Display (Dashboard par hi dikhengy jab click hoga)
    if "show_form" in st.session_state:
        with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
            with st.form("quick_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Description")
                d_amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Save to Cloud"):
                    payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear()
                    del st.session_state.show_form
                    st.rerun()
            if st.button("Close Form"):
                del st.session_state.show_form
                st.rerun()

    # Progress & Charts
    g1, g2 = st.columns([2, 1])
    with g1:
        if not df.empty:
            fig = px.line(df, x='date', y='amount', color='type', height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    with g2:
        status_df = fetch_project_status()
        done = len(status_df[status_df['status'] == 'Done'])
        total = len(status_df)
        prog = int((done/total)*100) if total > 0 else 0
        st.markdown(f"<p style='text-align:center;'><b>Progress: {prog}%</b></p>", unsafe_allow_html=True)
        st.progress(prog/100)
        
    st.divider()
    
    # Original Tasks Layout (Compact)
    t_cols = st.columns(4)
    for i, row in status_df.iterrows():
        with t_cols[i % 4]:
            st.caption(f"{'✅' if row['status']=='Done' else '⏳'} {row['task_name']}")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df
        
        st.dataframe(f_df, use_container_width=True)
