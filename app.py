import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG (Mobile Friendly) ---
st.set_page_config(page_title="Deewary ERP", layout="wide", page_icon="🏗️")

# --- 3. ADVANCED MOBILE CSS (App-like Look) ---
st.markdown("""
    <style>
    /* Hide Streamlit Header/Footer for App feel */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global Styling */
    .stApp { background-color: #ffffff; }
    
    /* App Header Styling */
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 20px 10px;
        border-radius: 0px 0px 25px 25px; /* Round bottom corners */
        border-bottom: 5px solid #FF4B4B;
        margin: -60px -20px 25px -20px; /* Full width on mobile */
    }

    /* Professional Cards */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 10px !important;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    /* Mobile Button Styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
        text-transform: uppercase;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transition: 0.3s;
    }

    /* Checklist Item Styling */
    .task-card {
        background: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid #FF4B4B;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* Mobile Responsive Adjustments */
    @media (max-width: 768px) {
        .header-box h1 { font-size: 24px !important; }
        .stMetric label { font-size: 14px !important; }
        .stMetric div { font-size: 18px !important; }
        /* Make columns stack nicely on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 calc(100%) !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock App"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong password!")
    return False

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏗️ DEEWARY MENU")
    menu = st.radio("Navigate App", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Mode Active")
        if st.button("⚙️ Manage Site Tasks"): st.session_state.show_status_form = True
        if st.button("🚪 Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True)

df = fetch_data()

# --- 6. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    # --- APP HEADER ---
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black';">DEEWARY.COM</h1>
            <p style="color: white; font-size: 11px; margin-bottom: 8px;">SMART CONSTRUCTION PORTAL</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- TOP CARDS ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    st.metric("💰 Income", f"PKR {inc:,.0f}")
    st.metric("📉 Expense", f"PKR {exp:,.0f}")
    st.metric("⚖️ Balance", f"PKR {bal:,.0f}")

    # --- PROJECT PROGRESS ---
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    st.divider()
    st.markdown("### 🏗️ Site Progress")
    st.progress(prog_val / 100)
    st.write(f"**{prog_val}% Completed** | ✅ {done_tasks} Done")

    # --- QUICK ACTION BUTTONS (BIG FOR MOBILE) ---
    st.write("### ⚡ Quick Entry")
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("➕ Income"): st.session_state.show_form = "Income"
    if col_b.button("👷 Labor"): st.session_state.show_form = "Labor"
    if col_c.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.form("mobile_entry"):
            st.info(f"Adding {ftype} Entry")
            d_date = st.date_input("Date", datetime.now())
            d_name = st.text_input("Title / Name")
            d_amt = st.number_input("Amount", min_value=0)
            d_occ = st.text_input("Occupation / Dept") if ftype != "Material" else ""
            d_rec = st.text_input("Approved By")
            d_meth = st.selectbox("Method", ["Cash", "Online", "Cheque"])
            d_det = st.text_area("Short Note")
            if st.form_submit_button("✅ Save Data"):
                payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                supabase.table('transactions').insert(payload).execute()
                st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

    st.divider()

    # --- TASK GRID (SCROLLABLE LIST FOR MOBILE) ---
    st.markdown("### 📋 Checklist")
    for i, row in status_df.iterrows():
        icon = "✅" if row['status'] == "Done" else "⏳"
        color = "#28a745" if row['status'] == "Done" else "#FF8C00"
        st.markdown(f"""
            <div class="task-card" style="border-left-color: {color};">
                <span style="float: right; color: {color}; font-weight: bold;">{icon}</span>
                <strong>{row['task_name']}</strong><br>
                <small style="color: grey;">Status: {row['status']}</small>
            </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")
    st.caption(f"Deewary Portal v2.0 | Mobile Optimized")

# --- 7. HISTORY PAGES ---
else:
    st.markdown(f"## {menu}")
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        # Mobile optimized search
        search = st.text_input("🔍 Search record...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        # Display as simple table for mobile
        st.dataframe(f_df, use_container_width=True, hide_index=True)
        st.metric("Total Sum", f"PKR {f_df['amount'].sum():,.0f}")

        if is_auth:
            tid = st.text_input("ID to Delete")
            if st.button("🗑️ Delete"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()
    else:
        st.warning("No records found.")
