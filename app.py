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

# --- 3. PREMIUM COMPACT CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Main Header Box */
    .main-header {
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 20px;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #eee;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }

    /* Status Item Card */
    .status-card {
        background: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        font-size: 14px;
    }

    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3em; }
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
    with st.sidebar.expander("🔐 Admin Lock", expanded=True):
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
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Access")
        if st.button("Logout"): 
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Site: Yousaf Colony")

df = fetch_data()

# --- 6. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    # Header
    st.markdown("""
        <div class="main-header">
            <h1 style="color: #FF4B4B; margin: 0; font-size: 28px; letter-spacing: 2px;">DEEWARY.COM</h1>
            <p style="color: white; font-size: 12px; margin: 0;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
            <p style="color: #FF4B4B; font-weight: bold; margin-top: 5px; font-size: 14px;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TOP METRICS ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"PKR {inc:,.0f}")
    m2.metric("Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.write("##")

    # --- FINANCIAL CHART & PROGRESS ---
    col_chart, col_prog = st.columns([1, 1])

    with col_chart:
        st.markdown("##### 💰 Cash Flow Analysis")
        chart_inc = int(inc) if inc > 0 else 1
        chart_exp = int(exp) if exp > 0 else 1
        
        pie_chart = f"""
        pie title Income vs Expense
            "Income" : {chart_inc}
            "Expense" : {chart_exp}
        """
        components.html(f"""
            <div style="background:#f8f9fa; border-radius:15px; padding:10px; border:1px solid #eee;">
                <pre class="mermaid">{pie_chart}</pre>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
            </script>
        """, height=300)

    with col_prog:
        status_df = fetch_project_status()
        total_tasks = len(status_df)
        done_tasks = len(status_df[status_df['status'] == 'Done'])
        prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        st.markdown("##### 🏗️ Project Completion")
        st.write(f"Overall Progress: **{prog_val}%**")
        st.progress(prog_val / 100)
        
        st.write(f"✅ Tasks Finished: {done_tasks}")
        st.write(f"⏳ Tasks Pending: {total_tasks - done_tasks}")
        if is_auth and st.button("⚙️ Manage Tasks"): st.session_state.show_status_form = True

    # Task Update Form
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.expander("🛠️ Update Milestone Status", expanded=True):
            with st.form("status_update"):
                t_name = st.selectbox("Task Name", status_df['task_name'].tolist())
                t_stat = st.radio("New Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update"):
                    supabase.table('project_status').upsert({"task_name": t_name, "status": t_stat}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()

    # --- TASK GRID ---
    st.markdown("##### 📋 Work Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            color = "#28a745" if row['status'] == "Done" else "#dc3545"
            st.markdown(f"""
                <div class="status-card" style="border-left-color: {color};">
                    <b>{icon} {row['task_name']}</b><br>
                    <small style="color: {color};">{row['status']}</small>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- QUICK ACTIONS ---
    st.markdown("##### ⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"New {ftype} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Description")
                    d_amt = st.number_input("Amount", min_value=0)
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Please login as Admin to add data.")

    # --- SHOWCASE VIDEO ---
    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")
    st.caption(f"© {datetime.now().year} Deewary.com | Project Management")

# --- 7. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        st.dataframe(f_df, use_container_width=True)
        st.metric("Total PKR", f"{f_df['amount'].sum():,.0f}")

        if is_auth:
            st.divider()
            tid = st.text_input("Enter ID to Delete")
            if tid and st.button("🗑️ Delete"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()

        buf = io.BytesIO()
        f_df.to_excel(buf, index=False)
        st.download_button("📥 Export Excel", buf.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")
