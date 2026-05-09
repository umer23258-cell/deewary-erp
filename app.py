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

# --- MOBILE OPTIMIZATION CSS ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-size: 16px !important;
            margin-bottom: 10px;
        }
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
    }
    .main { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS ---
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
            tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Paint", "Wood Work", "Ragarya", "Main Door", "Grill", "Wasbasen Tottya", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except Exception:
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

# --- 4. SIDEBAR NAVIGATION & FORMS ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        # --- SECTION 1: TRANSACTION ENTRIES ---
        st.subheader("➕ New Entry")
        c1, c2, c3 = st.columns(3)
        if c1.button("💰"): st.session_state.show_form = "Income"
        if c2.button("👷"): st.session_state.show_form = "Labor"
        if c3.button("🏗️"): st.session_state.show_form = "Material"
        
        if "show_form" in st.session_state:
            with st.expander(f"Add {st.session_state.show_form}", expanded=True):
                with st.form("sidebar_entry"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    if st.form_submit_button("Save Entry"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()

        st.divider()
        
        # --- SECTION 2: PROGRESS CONTROL ---
        st.subheader("🛠️ Progress Control")
        if st.button("📝 Update Work Status"):
            st.session_state.show_update_form = True

        if st.session_state.get("show_update_form", False):
            status_df = fetch_project_status()
            with st.expander("Update Task Status", expanded=True):
                with st.form("status_form"):
                    c_task = st.selectbox("Select Task", status_df['task_name'].tolist())
                    c_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
                    if st.form_submit_button("Confirm Change"):
                        supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                        st.cache_data.clear()
                        st.session_state.show_update_form = False
                        st.rerun()
                if st.button("Cancel"):
                    st.session_state.show_update_form = False
                    st.rerun()

    st.divider()
    if is_auth and st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # HEADER
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)
    with h_col2:
        st.markdown("<div style='background-color: #1E1E1E; padding: 10px; border-radius: 10px; text-align: center;'><h2 style='color: #FF4B4B; margin: 0;'>DEEWARY.COM</h2></div>", unsafe_allow_html=True)

    st.write("##")

    # PROGRESS REPORT (Dashboard par sirf report dikhayi degi)
    st.markdown("<h3 style='color: #FF4B4B;'>🏗️ Project Work Progress</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    t_col1, t_col2 = st.columns(2)
    for idx, row in status_df.iterrows():
        target_col = t_col1 if idx % 2 == 0 else t_col2
        with target_col:
            is_done = row["status"] == "Done"
            bg = "#d4edda" if is_done else "#f8d7da"
            icon = "✅" if is_done else "⏳"
            st.markdown(f"<div style='background-color: {bg}; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid gray;'><b>{icon} {row['task_name']}</b></div>", unsafe_allow_html=True)

    st.divider()

    # ANALYTICS
    st.markdown("<h4 style='text-align: center;'>Capital Flow Analytics</h4>", unsafe_allow_html=True)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"PKR {inc:,.0f}")
        col2.metric("Total Expenses", f"PKR {exp:,.0f}")
        col3.metric("Net Balance", f"PKR {bal:,.0f}")
    else:
        st.info("No financial data to display charts.")

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()
        
        st.dataframe(filtered_df, use_container_width=True)
        
        if is_auth:
            target_id = st.text_input("Enter Row ID to Delete")
            if st.button("🗑️ Delete Record") and target_id:
                supabase.table('transactions').delete().eq('id', target_id).execute()
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("No records found.")
