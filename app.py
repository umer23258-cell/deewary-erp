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

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- 3. PREMIUM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-header {
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 25px; border-radius: 15px; text-align: center;
        border-bottom: 5px solid #FF4B4B; margin-bottom: 20px;
    }
    div[data-testid="stMetric"] {
        background: #f8f9fa; border: 1px solid #eee;
        padding: 15px !important; border-radius: 12px !important;
    }
    .status-card {
        background: #ffffff; padding: 10px; border-radius: 8px;
        border-left: 5px solid #FF4B4B; margin-bottom: 8px; font-size: 14px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE FUNCTIONS ---
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
        pwd = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong!")
    return False

# --- 5. DATA INITIALIZATION ---
df = fetch_data()
status_df = fetch_project_status()

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### 🏗️ DEEWARY ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        if st.button("Logout"): 
            st.session_state["authenticated"] = False
            st.rerun()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Site: Yousaf Colony")

# --- 7. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="main-header">
            <h1 style="color: #FF4B4B; margin: 0; font-size: 28px;">DEEWARY.COM</h1>
            <p style="color: white; font-size: 12px; margin: 0;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>
    """, unsafe_allow_html=True)

    # Calculate Totals
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    # Charts Section
    c_chart, c_prog = st.columns([1, 1])
    with c_chart:
        st.markdown("##### 💰 Cash Flow Analysis")
        pie_chart = f'pie title Income vs Expense \n "Income" : {int(inc) if inc>0 else 1} \n "Expense" : {int(exp) if exp>0 else 1}'
        components.html(f"<div style='background:#f8f9fa; border-radius:15px; padding:10px;'><pre class='mermaid'>{pie_chart}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=300)

    with c_prog:
        total_t = len(status_df)
        done_t = len(status_df[status_df['status'] == 'Done'])
        prog_val = int((done_t / total_t) * 100) if total_t > 0 else 0
        st.markdown("##### 🏗️ Project Progress")
        st.write(f"Overall Progress: **{prog_val}%**")
        st.progress(prog_val / 100)
        if is_auth and st.button("⚙️ Manage Tasks"): st.session_state.show_status_form = True

    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.form("task_update"):
            t_n = st.selectbox("Select Task", status_df['task_name'].tolist())
            t_s = st.radio("Status", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Update Status"):
                supabase.table('project_status').upsert({"task_name": t_n, "status": t_s}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()

    # --- QUICK ENTRY FORMS ---
    st.markdown("##### ⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("entry_form"):
                    fa, fb = st.columns(2)
                    d_date = fa.date_input("Date", datetime.now())
                    d_name = fb.text_input("Name / Title")
                    d_amt = fa.number_input("Amount (PKR)", min_value=0)
                    d_occ = fb.text_input("Occupation")
                    d_rec = fa.text_input("Received By")
                    d_meth = fb.selectbox("Payment Method", ["Cash", "Bank Transfer", "EasyPaisa", "JazzCash", "Cheque"])
                    d_det = st.text_area("Details")
                    
                    if st.form_submit_button("Save Entry"):
                        payload = {
                            "date": str(d_date), "type": ftype, "name": d_name, 
                            "amount": d_amt, "occupation": d_occ, "received_by": d_rec, 
                            "pay_method": d_meth, "detail": d_det
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Login as Admin first.")

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# --- 8. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filter based on menu selection
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        st.dataframe(f_df, use_container_width=True)
        st.info(f"Total: PKR {f_df['amount'].sum():,.0f}")
        
        if is_auth:
            st.divider()
            tid = st.text_input("Enter Row ID to Delete")
