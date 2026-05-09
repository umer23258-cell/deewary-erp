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
        .stButton > button { width: 100%; border-radius: 10px; height: 3em; font-size: 16px !important; margin-bottom: 10px; }
        [data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        h2 { font-size: 20px !important; }
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
    except Exception as e:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Paint", "Wood Work", "Ragarya", "Main Door", "Grill", "Wasbasen Tottya", "Finishing"]
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

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("⚙️ Update Project Status"):
            st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
            
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True, caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header logic
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""<div style="text-align: center; background-color: #1E1E1E; padding: 15px; border-radius: 15px; border: 1px solid #333;">
            <h2 style="color: #FF4B4B; margin: 0;">DEEWARY.COM</h2>
            <p style="color: #FFFFFF; font-size: 12px; margin: 0;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
            <p style="color: #FF4B4B; font-weight: 700; margin: 0;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>""", unsafe_allow_html=True)

    st.write("##")

    # --- ADMIN STATUS UPDATE FORM ---
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        status_df = fetch_project_status()
        with st.expander("🛠️ Control Task Status", expanded=True):
            with st.form("status_form"):
                c_task = st.selectbox("Select Task", status_df['task_name'].tolist())
                c_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Save Status"):
                    supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                    st.cache_data.clear()
                    st.session_state.show_status_form = False
                    st.rerun()

    # --- NEW PROFESSIONAL PROGRESS CHART REPORT ---
    st.markdown("<h3 style='color: #FF4B4B;'>📊 Overall Project Completion</h3>", unsafe_allow_html=True)
    
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    progress_percent = int((done_tasks / total_tasks) * 100)
    
    # Big Progress Bar
    st.progress(progress_percent / 100)
    st.markdown(f"<h2 style='text-align: center; color: #1E1E1E;'>{progress_percent}% Completed</h2>", unsafe_allow_html=True)
    
    # Task Breakdown in Columns
    st.write("### 🏗️ Detailed Work Report")
    
    # List of tasks showing status with professional icons
    cols = st.columns(3)
    for idx, row in status_df.iterrows():
        with cols[idx % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            color = "#155724" if row['status'] == "Done" else "#721c24"
            st.markdown(f"""
                <div style="padding: 10px; border-bottom: 1px solid #eee;">
                    <span style="font-size: 16px;">{icon} <b>{row['task_name']}</b></span><br>
                    <small style="color: {color}; font-weight: bold;">{row['status']}</small>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Capital Flow Metrics
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # Quick Actions (Same as before)
    if "edit_id" not in st.session_state:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    if "show_form" in st.session_state:
        if is_auth:
            form_type = st.session_state.show_form
            with st.expander(f"New {form_type} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name / Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    if form_type in ["Income", "Labor"]:
                        cf1, cf2 = st.columns(2)
                        d_occ = cf1.text_input("Occupation")
                        d_meth = cf1.selectbox("Method", ["Cash", "Bank", "EasyPaisa"])
                        d_rec = cf2.text_input("Received By")
                    d_det = st.text_area("Details")
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Management Portal")

# --- HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filtering and Excel Logic remains the same
        st.dataframe(df, use_container_width=True)
