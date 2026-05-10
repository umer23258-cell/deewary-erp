import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP (Logic Same) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- 3. PROFESSIONAL UI CSS ---
st.markdown("""
    <style>
    /* Main Background and Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Premium Header */
    .main-header {
        background: linear-gradient(90deg, #1a1a1a 0%, #434343 100%);
        padding: 40px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 6px solid #FF4B4B;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #f0f0f0;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #FF4B4B;
    }

    /* Status Cards */
    .status-box {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #FF4B4B;
        background: #fdfdfd;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }

    /* Mobile Tweaks */
    @media (max-width: 640px) {
        .main-header { padding: 20px; }
        .stButton > button { width: 100%; height: 3.5rem; border-radius: 12px; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE FUNCTIONS (Same Logic) ---
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
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong password!")
    return False

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=150)
    st.title("DEEWARY ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Access On")
        if st.button("⚙️ Update Project Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.info("📍 Site: Yousaf Colony")

df = fetch_data()

# --- 6. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    # Hero Header
    st.markdown("""
        <div class="main-header">
            <h1 style="color: #FF4B4B; margin: 0; font-size: 40px; font-weight: 800;">DEEWARY.COM</h1>
            <p style="color: #cccccc; letter-spacing: 4px; font-size: 14px;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
            <p style="color: #FF4B4B; font-weight: bold; margin-top: 15px;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TOP SECTION: CAPITAL FLOW ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}", help="Total received from clients")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}", help="Labor + Material costs")
    col3.metric("Net Balance", f"PKR {bal:,.0f}", delta=f"{bal:,.0f}", delta_color="normal")

    st.write("##")
    
    # --- MIDDLE SECTION: PROGRESS ---
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    p_col1, p_col2 = st.columns([1, 1])
    with p_col1:
        st.subheader("🏗️ Site Progress")
        st.progress(prog_val / 100)
        st.write(f"Overall Completion: **{prog_val}%**")
        
        # Compact Mermaid Graph
        chart_code = f"graph LR\nStart((Start)) --> Done{{ {prog_val}% Done }}\nstyle Done fill:#FF4B4B,color:#fff"
        components.html(f"<div style='background:#f9f9f9; padding:10px; border-radius:15px;'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=100)

    with p_col2:
        st.subheader("📈 Quick Stats")
        st.write(f"✅ Tasks Finished: **{done_tasks}**")
        st.write(f"⏳ Tasks Pending: **{total_tasks - done_tasks}**")
        if st.button("🔄 Refresh Dashboard"): st.cache_data.clear(); st.rerun()

    # Admin Form
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.expander("📝 Update Project Milestone", expanded=True):
            with st.form("milestone_form"):
                t_name = st.selectbox("Select Task", status_df['task_name'].tolist())
                t_stat = st.radio("New Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Now"):
                    supabase.table('project_status').upsert({"task_name": t_name, "status": t_stat}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()

    # --- TASK CHECKLIST GRID ---
    st.markdown("### 📋 Construction Milestones")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "🟢" if row['status'] == "Done" else "⚪"
            st.markdown(f"""
                <div class="status-box">
                    <span style="font-weight: bold;">{icon} {row['task_name']}</span><br>
                    <small style="color: gray;">Status: {row['status']}</small>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- ACTIONS ---
    st.subheader("⚙️ Quick Management")
    a1, a2, a3 = st.columns(3)
    if a1.button("➕ Record Income"): st.session_state.show_form = "Income"
    if a2.button("👷 Record Labor"): st.session_state.show_form = "Labor"
    if a3.button("🏗️ Record Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            f_type = st.session_state.show_form
            with st.expander(f"Add New {f_type} Entry", expanded=True):
                with st.form("main_entry_form"):
                    d_date = st.date_input("Transaction Date", datetime.now())
                    d_name = st.text_input("Name / Description")
                    d_amt = st.number_input("Amount (PKR)", min_value=0)
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if f_type in ["Income", "Labor"]:
                        cc1, cc2 = st.columns(2)
                        d_occ = cc1.text_input("Occupation/Category")
                        d_meth = cc1.selectbox("Payment Method", ["Cash", "Bank Transfer", "EasyPaisa", "Cheque"])
                        d_rec = cc2.text_input("Received/Approved By")
                    d_det = st.text_area("Additional Details")
                    if st.form_submit_button("Save Transaction"):
                        payload = {"date": str(d_date), "type": f_type, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Please unlock Admin Access from the sidebar to add data.")

    # --- SHOWCASE ---
    st.divider()
    st.markdown("### 🎥 Featured Project")
    v_col1, v_col2 = st.columns([1.5, 1])
    with v_col1: st.video("https://youtu.be/AiA4PkXturU")
    with v_col2:
        st.markdown("""
            <div style="background: #1a1a1a; color: white; padding: 20px; border-radius: 15px;">
                <h4 style="color: #FF4B4B;">Modern Excellence</h4>
                <p>Hamara har project quality aur reliability ka sabot hai. Yousaf colony project ki completion details yahan dekhen.</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Powered by Sami Ullah")

# --- 7. HISTORY PAGES (Logic Same) ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filter_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filter_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filter_df = df[df['type'] == 'Material']
        else: filter_df = df.copy()
        
        search_term = st.text_input("🔍 Search records...")
        if search_term:
            mask = filter_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filter_df = filter_df[mask]
        
        st.dataframe(filter_df, use_container_width=True)
        st.subheader(f"Total: PKR {filter_df['amount'].sum():,.0f}")

        # Admin Edit Logic
        if is_auth:
            st.divider()
            edit_id = st.text_input("Enter Row ID to Delete")
            if edit_id and st.button("🗑️ Delete Record"):
                supabase.table('transactions').delete().eq('id', edit_id).execute()
                st.cache_data.clear(); st.rerun()

        # Excel Export
        excel_buf = io.BytesIO()
        filter_df.to_excel(excel_buf, index=False)
        st.download_button("📥 Export to Excel", excel_buf.getvalue(), f"Deewary_{menu}.xlsx")
    else:
        st.warning("No records found in the database.")
