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

# --- MOBILE OPTIMIZATION & COMPACT CSS ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 6px; height: 2.5em; font-size: 14px !important; }
    }
    .main { background-color: #f4f7f9; }
    /* Compact Metric Cards */
    .metric-card {
        background: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 3px solid #6f42c1;
    }
    .stProgress > div > div > div > div { background-color: #6f42c1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS ---
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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Tile Polish", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports", "⚙️ System Logic"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("⚙️ Update Progress"): st.session_state.show_status_form = True
        if st.button("Logout"): st.session_state["authenticated"] = False; st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True)

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Compact Header
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 10px 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #6f42c1;">
            <h2 style="margin:0; color:#1E1E1E; font-size: 22px;">PROJECT STATUS</h2>
            <p style="margin:0; color:#666; font-size: 14px;">Site: Yousaf Colony | 5 Marla</p>
        </div>
    """, unsafe_allow_html=True)

    status_df = fetch_project_status()
    done_count = len(status_df[status_df['status'] == 'Done'])
    total_tasks = len(status_df)
    prog_perc = int((done_count/total_tasks)*100) if total_tasks > 0 else 0

    # Professional Mini Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><small>COMPLETED</small><h3 style="color:#6f42c1; margin:0;">{prog_perc}%</h3></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card" style="border-top-color:#007bff;"><small>TASKS DONE</small><h3 style="color:#007bff; margin:0;">{done_count}/{total_tasks}</h3></div>', unsafe_allow_html=True)
    
    if not df.empty:
        inc_total = df[df['type'] == 'Income']['amount'].sum()
        exp_total = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        with m3: st.markdown(f'<div class="metric-card" style="border-top-color:#28a745;"><small>TOTAL INCOME</small><h4 style="color:#28a745; margin:0;">{inc_total/1000:,.1f}k</h4></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card" style="border-top-color:#dc3545;"><small>NET BALANCE</small><h4 style="color:#dc3545; margin:0;">{(inc_total-exp_total)/1000:,.1f}k</h4></div>', unsafe_allow_html=True)

    st.write("##")

    # Tracking Section
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown("##### 📊 Work Analysis")
        pie = f"graph TD\nTasks(( )) --> B(Done: {done_count})\nTasks --> C(Left: {total_tasks-done_count})\nstyle B fill:#6f42c1,color:#fff\nstyle C fill:#e9ecef"
        components.html(f"<pre class='mermaid'>{pie}</pre><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=180)

    with col_right:
        st.markdown("##### 🛠️ Task Progress")
        for i, row in status_df.iterrows():
            col_t1, col_t2 = st.columns([3, 1])
            col_t1.caption(f"**{row['task_name']}**")
            col_t2.caption(f"{'✅' if row['status']=='Done' else '⏳'}")
            st.progress(100 if row['status'] == "Done" else 0)

    st.divider()

    # Quick Action Buttons
    st.subheader("⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            f_type = st.session_state.show_form
            with st.form("entry_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Name")
                d_amt = st.number_input("Amount", min_value=0.0)
                d_occ, d_rec, d_meth = "", "", "Cash"
                if f_type in ["Income", "Labor"]:
                    c_f1, c_f2 = st.columns(2)
                    d_occ = c_f1.text_input("Occupation")
                    d_meth = c_f1.selectbox("Method", ["Cash", "Bank", "EasyPaisa"])
                    d_rec = c_f2.text_input("Received By")
                d_det = st.text_area("Details")
                if st.form_submit_button("Save"):
                    payload = {"date": str(d_date), "type": f_type, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.form("status_update"):
            c_task = st.selectbox("Task", status_df['task_name'].tolist())
            c_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Update"):
                supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

# --- 7. HISTORY PAGES (With DELETE & EDIT Buttons) ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        search = st.text_input("🔍 Search...")
        if search: f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        st.dataframe(f_df, use_container_width=True)
        st.info(f"Total: PKR {f_df['amount'].sum():,.0f}")

        # --- ORIGINAL EDIT & DELETE BUTTONS ---
        if is_auth:
            st.divider()
            st.subheader("🛠️ Record Actions")
            target_id = st.text_input("Enter ID to Edit/Delete")
            if target_id:
                target_row = df[df['id'].astype(str) == target_id]
                if not target_row.empty:
                    row_data = target_row.iloc[0]
                    st.warning(f"Selected: {row_data['name']}")
                    btn1, btn2 = st.columns(2)
                    if btn2.button("🗑️ Confirm Delete"):
                        supabase.table('transactions').delete().eq('id', target_id).execute()
                        st.cache_data.clear(); st.rerun()
                    with btn1:
                        with st.expander("📝 Edit Record"):
                            with st.form("edit_form"):
                                n_name = st.text_input("New Name", value=row_data['name'])
                                n_amt = st.number_input("New Amount", value=float(row_data['amount']))
                                if st.form_submit_button("Update"):
                                    supabase.table('transactions').update({"name": n_name, "amount": n_amt}).eq('id', target_id).execute()
                                    st.cache_data.clear(); st.rerun()

        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Excel", buffer.getvalue(), f"{menu}.xlsx")
    else: st.warning("No records.")
