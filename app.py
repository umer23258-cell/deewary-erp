import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import streamlit.components.v1 as components

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
    }
    .main { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS (ORIGINAL LOGIC PRESERVED) ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Tile Polish", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports", "⚙️ System Logic"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("⚙️ Update Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"): 
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True)

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header
    st.markdown("""
        <div style="text-align: center; background-color: #1E1E1E; padding: 20px; border-radius: 15px; border-bottom: 5px solid #FF4B4B;">
            <h1 style="color: #FF4B4B; margin: 0; letter-spacing: 3px;">PROJECT STATUS REPORT</h1>
            <p style="color: white; margin: 0; font-size: 14px;">Real-Time Site Monitoring & Analytics</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("##")

    # --- PROFESSIONAL REPORT SECTION ---
    status_df = fetch_project_status()
    done_count = len(status_df[status_df['status'] == 'Done'])
    total_tasks = len(status_df)
    prog_perc = int((done_count/total_tasks)*100) if total_tasks > 0 else 0

    col_stats, col_main = st.columns([1, 3])

    with col_stats:
        st.markdown(f"""
            <div style="background: #6f42c1; color: white; padding: 20px; border-radius: 10px; margin-bottom: 10px; text-align: center;">
                <small>WORK DONE</small><h2 style="margin:0;">{prog_perc}%</h2>
            </div>
            <div style="background: #007bff; color: white; padding: 20px; border-radius: 10px; margin-bottom: 10px; text-align: center;">
                <small>TASKS DONE</small><h2 style="margin:0;">{done_count}/{total_tasks}</h2>
            </div>
            <div style="background: #28a745; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <small>PROJECT STATUS</small><h2 style="margin:0;">ACTIVE</h2>
            </div>
        """, unsafe_allow_html=True)

    with col_main:
        c1, c2 = st.columns([1.5, 2])
        with c1:
            st.markdown("#### 🥧 Task Distribution")
            pie_chart = f"""
            graph TD
                A((Tasks)) --> B(Done: {done_count})
                A --> C(Pending: {total_tasks - done_count})
                style B fill:#28a745,stroke:#fff,color:#fff
                style C fill:#6c757d,stroke:#fff,color:#fff
            """
            components.html(f"<pre class='mermaid'>{pie_chart}</pre><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=220)
        
        with c2:
            st.markdown("#### 📈 Progress Timeline")
            for i, row in status_df.iterrows():
                p_val = 100 if row['status'] == "Done" else 0
                st.write(f"**{row['task_name']}**")
                st.progress(p_val/100)

    st.divider()

    # --- WEEKLY AMOUNT FLOW ---
    st.markdown("### 💰 Weekly Financial Summary")
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        last_7 = datetime.now() - timedelta(days=7)
        w_df = df[df['date'] >= last_7]
        w_inc = w_df[w_df['type'] == 'Income']['amount'].sum()
        w_lab = w_df[w_df['type'] == 'Labor']['amount'].sum()
        w_mat = w_df[w_df['type'] == 'Material']['amount'].sum()

        f_col1, f_col2, f_col3 = st.columns(3)
        f_col1.metric("Income (7 Days)", f"PKR {w_inc:,.0f}")
        f_col2.metric("Labor (7 Days)", f"PKR {w_lab:,.0f}")
        f_col3.metric("Material (7 Days)", f"PKR {w_mat:,.0f}")

    st.divider()

    # --- QUICK ACTIONS (ORIGINAL) ---
    if "edit_id" not in st.session_state:
        st.subheader("⚡ Quick Actions")
        q1, q2, q3 = st.columns(3)
        if q1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if q2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if q3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            f_type = st.session_state.show_form
            with st.expander(f"New {f_type} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name / Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if f_type in ["Income", "Labor"]:
                        col_f1, col_f2 = st.columns(2)
                        d_occ = col_f1.text_input("Occupation")
                        d_meth = col_f1.selectbox("Payment Method", ["Cash", "Bank Transfer", "EasyPaisa", "Cheque"])
                        d_rec = col_f2.text_input("Received By")
                    d_det = st.text_area("Details")
                    if st.form_submit_button("Save Record"):
                        payload = {"date": str(d_date), "type": f_type, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()

    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.expander("🛠️ Update Project Progress", expanded=True):
            with st.form("status_update"):
                c_task = st.selectbox("Select Task", status_df['task_name'].tolist())
                c_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Status"):
                    supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                    st.cache_data.clear()
                    st.session_state.show_status_form = False
                    st.rerun()

# --- 6. SYSTEM LOGIC ---
elif menu == "⚙️ System Logic":
    st.title("⚙️ System Workflow")
    system_flow = "graph LR\nStart[User] --> Input[ERP Forms] --> DB[(Supabase Cloud)] --> Report[Professional Dashboard]"
    components.html(f"<pre class='mermaid'>{system_flow}</pre><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true}});</script>", height=300)

# --- 7. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        search = st.text_input("🔍 Search...")
        if search:
            f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        st.dataframe(f_df, use_container_width=True)
        st.info(f"Total: PKR {f_df['amount'].sum():,.0f}")
        
        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Excel Download", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No records found.")
