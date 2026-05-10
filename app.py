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
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
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

# --- 5. INITIALIZE DATA ---
df = fetch_data()
status_df = fetch_project_status()

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### 🏗️ DEEWARY ERP")
    # Menu definition (Is se NameError khatam ho jayega)
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

    if not df.empty:
        inc = float(df[df['type'] == 'Income']['amount'].sum())
        exp = float(df[df['type'].isin(['Labor', 'Material'])]['amount'].sum())
        bal = inc - exp
    else: inc, exp, bal = 0.0, 0.0, 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"PKR {inc:,.0f}")
    m2.metric("Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("Net Balance", f"PKR {bal:,.0f}")

    # Charts & Progress
    c_chart, c_prog = st.columns([1, 1])
    with c_chart:
        st.markdown("##### 💰 Cash Flow Analysis")
        c_inc = int(inc) if inc > 0 else 1
        c_exp = int(exp) if exp > 0 else 1
        # Simple Chart Logic to avoid Syntax Error
        chart_code = f'pie title "Cash Flow" \n "Income" : {c_inc} \n "Expenses" : {c_exp}'
        components.html(f"""
            <div style='background:#f8f9fa; border-radius:15px; padding:10px;'>
                <pre class='mermaid'>{chart_code}</pre>
            </div>
            <script type='module'>
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{startOnLoad:true, theme:'neutral'}});
            </script>
        """, height=300)

    with c_prog:
        prog_val = int((len(status_df[status_df['status'] == 'Done']) / len(status_df)) * 100) if not status_df.empty else 0
        st.markdown("##### 🏗️ Project Progress")
        st.write(f"Overall Progress: **{prog_val}%**")
        st.progress(prog_val / 100)
        if is_auth and st.button("⚙️ Manage Tasks"): st.session_state.show_status_form = True

    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.form("st_update"):
            t_n = st.selectbox("Task", status_df['task_name'].tolist())
            t_s = st.radio("Status", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Update"):
                supabase.table('project_status').upsert({"task_name": t_n, "status": t_s}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("##### 📋 Work Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            color = "#28a745" if row['status'] == "Done" else "#dc3545"
            st.markdown(f'<div class="status-card" style="border-left-color: {color};"><b>{icon} {row["task_name"]}</b><br><small>{row["status"]}</small></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("##### ⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"Add New {ftype}", expanded=True):
                with st.form("entry_form"):
                    ca, cb = st.columns(2)
                    d_date = ca.date_input("Date", datetime.now())
                    d_name = cb.text_input("Name")
                    d_amt = ca.number_input("Amount", min_value=0.0)
                    d_occ = cb.text_input("Occupation")
                    d_rec = ca.text_input("Received By")
                    d_meth = cb.selectbox("Method", ["Cash", "Bank Transfer", "EasyPaisa", "JazzCash", "Cheque"])
                    d_det = st.text_area("Details")
                    if st.form_submit_button("Save"):
                        p = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth, "detail": d_det}
                        supabase.table('transactions').insert(p).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Login as Admin.")

# --- 8. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        st.dataframe(f_df, use_container_width=True)
        st.metric("Sub-Total", f"PKR {f_df['amount'].sum():,.0f}")
        if is_auth:
            tid = st.text_input("ID to Delete")
            if tid and st.button("🗑️ Delete"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()
    else: st.warning("No data found.")
