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

# --- 3. COMPACT & MODERN CSS ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    /* Compact Header */
    .header-container {
        background: #1e1e1e;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border-bottom: 4px solid #FF4B4B;
        margin-bottom: 10px;
    }
    /* Small Metric Cards */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #eee;
        padding: 10px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Small Status Cards */
    .status-item {
        padding: 8px;
        border-radius: 8px;
        margin-bottom: 5px;
        border-left: 4px solid #FF4B4B;
        background: #fff;
        font-size: 13px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    /* Button Optimization */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC (SAME AS BEFORE) ---
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
    with st.sidebar.expander("🔐 Unlock Admin", expanded=True):
        pwd = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong!")
    return False

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏗️ DEEWARY ERP")
    menu = st.radio("Menu", ["📊 Dashboard", "💰 Income", "👷 Labor", "🏗️ Material", "🔍 Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"): 
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 6. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    # Compact Header
    st.markdown("""
        <div class="header-container">
            <h2 style="color: #FF4B4B; margin: 0; font-size: 22px;">DEEWARY.COM</h2>
            <p style="color: #bbb; font-size: 11px; margin: 0;">SARDAR SAMI ULLAH | ERP PORTAL</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TOP METRICS & FINANCIAL CHART ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Income", f"Rs {inc:,.0f}")
    m2.metric("Expense", f"Rs {exp:,.0f}")
    m3.metric("Balance", f"Rs {bal:,.0f}")

    # Financial Graphic Chart (Mermaid)
    chart_inc_per = int((inc / (inc + exp) * 100)) if (inc + exp) > 0 else 50
    chart_exp_per = 100 - chart_inc_per
    
    financial_chart = f"""
    pie title Cash Flow Distribution
        "Income" : {chart_inc_per}
        "Expenses" : {chart_exp_per}
    """
    components.html(f"""
        <div style="background:white; padding:10px; border-radius:12px; border:1px solid #eee; text-align:center;">
            <pre class="mermaid">{financial_chart}</pre>
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'neutral', chart: {{ width: 200 }} }});
        </script>
    """, height=320)

    st.write("---")

    # --- WORK PROGRESS SECTION ---
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("##### 🏗️ Site Work")
        st.progress(prog_val / 100)
        st.caption(f"Completion: {prog_val}%")
        if is_auth and st.button("Update Tasks"): st.session_state.show_status_form = True

    with c2:
        st.markdown("##### 📋 Status List")
        # Display tasks in a very compact list
        t_list_cols = st.columns(2)
        for i, row in status_df.iterrows():
            with t_list_cols[i % 2]:
                color = "#28a745" if row['status'] == "Done" else "#6c757d"
                st.markdown(f"""<div class="status-item" style="border-left-color:{color};"><b>{row['task_name']}</b></div>""", unsafe_allow_html=True)

    # Status Edit Overlay
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.form("status_edit"):
            t_sel = st.selectbox("Task", status_df['task_name'].tolist())
            s_sel = st.radio("Status", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Save"):
                supabase.table('project_status').upsert({"task_name": t_sel, "status": s_sel}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.write("---")

    # --- QUICK ADD SECTION ---
    st.markdown("##### ⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            with st.expander(f"Add {st.session_state.show_form}", expanded=True):
                with st.form("add_val"):
                    f1, f2 = st.columns(2)
                    d_n = f1.text_input("Name/Description")
                    d_a = f2.number_input("Amount", min_value=0)
                    if st.form_submit_button("Confirm Save"):
                        payload = {"date": str(datetime.now().date()), "type": st.session_state.show_form, "name": d_n, "amount": d_a}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Login as admin first.")

    # --- VIDEO (COMPACT) ---
    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# --- 7. HISTORY PAGES ---
else:
    st.title(f"{menu} Records")
    if not df.empty:
        # Filter logic based on menu
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df
        
        st.dataframe(f_df, use_container_width=True)
        st.info(f"Total Amount: Rs {f_df['amount'].sum():,.0f}")
        
        # Simple Delete for Admin
        if is_auth:
            del_id = st.text_input("Enter ID to delete")
            if del_id and st.button("Delete"):
                supabase.table('transactions').delete().eq('id', del_id).execute()
                st.cache_data.clear(); st.rerun()
    else:
        st.warning("No data.")
