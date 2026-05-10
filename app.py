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
    /* Professional Tracking Cards */
    .tracking-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports", "⚙️ System Logic"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("⚙️ Update Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"): st.session_state["authenticated"] = False; st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True, caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header Section
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""
            <div style="text-align: center; background-color: #1E1E1E; padding: 15px; border-radius: 15px;">
                <h2 style="color: #FF4B4B; margin: 0; letter-spacing: 2px;">DEEWARY.COM</h2>
                <p style="color: white; margin: 0; font-size: 14px;">SITE MONITORING & FINANCIAL TRACKING</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.write("##")

    # --- PROFESSIONAL TRACKING SECTION ---
    st.markdown("<h2 style='text-align: center; color: #333;'>🚀 Live Project Tracking</h2>", unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 🏗️ Work Execution Flow")
        status_df = fetch_project_status()
        done = len(status_df[status_df['status'] == 'Done'])
        total = len(status_df)
        
        # Mermaid Progress Chart
        work_chart = f"""
        graph TD
            A[Project: Yousaf Colony] --> B(Completed Tasks: {done})
            A --> C(Remaining Tasks: {total - done})
            style B fill:#28a745,stroke:#fff,color:#fff
            style C fill:#dc3545,stroke:#fff,color:#fff
        """
        components.html(f"""
            <pre class="mermaid">{work_chart}</pre>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
            </script>
        """, height=250)
        
        st.progress(int((done/total)*100))
        st.caption(f"Overall Completion: {int((done/total)*100)}%")

    with chart_col2:
        st.markdown("#### 💰 Weekly Financial Flow")
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            week_df = df[df['date'] >= (datetime.now() - timedelta(days=7))]
            w_inc = week_df[week_df['type'] == 'Income']['amount'].sum()
            w_lab = week_df[week_df['type'] == 'Labor']['amount'].sum()
            w_mat = week_df[week_df['type'] == 'Material']['amount'].sum()
            
            amt_chart = f"""
            graph LR
                W[Weekly Flow] --> I(Income: {w_inc:,.0f})
                W --> L(Labor: {w_lab:,.0f})
                W --> M(Material: {w_mat:,.0f})
                style I fill:#d4edda,stroke:#155724
                style L fill:#f8d7da,stroke:#721c24
                style M fill:#fff3cd,stroke:#856404
            """
            components.html(f"""
                <pre class="mermaid">{amt_chart}</pre>
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true, theme: 'base' }});
                </script>
            """, height=250)
        else: st.info("No data for this week.")

    st.divider()

    # Admin Form for Status
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        status_df = fetch_project_status()
        with st.expander("🛠️ Update Task Status", expanded=True):
            with st.form("sidebar_status_form"):
                c_task = st.selectbox("Select Task", status_df['task_name'].tolist())
                c_status = st.radio("New Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Now"):
                    supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    # Analytics Metrics
    st.markdown("#### 📑 Lifetime Totals")
    inc = df[df['type'] == 'Income']['amount'].sum() if not df.empty else 0
    exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum() if not df.empty else 0
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"PKR {inc:,.0f}")
    m2.metric("Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("Net Balance", f"PKR {inc-exp:,.0f}")

    st.divider()
    
    # Quick Actions
    st.subheader("⚡ Quick Management")
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
                    d_name = st.text_input("Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
            if st.button("❌ Close"): st.session_state.pop("show_form"); st.rerun()

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Authorized Access Only")

# --- 6. SYSTEM LOGIC ---
elif menu == "⚙️ System Logic":
    st.title("⚙️ ERP System Logic")
    components.html("""
        <pre class="mermaid">
        graph TD
            A[User Interface] --> B{Menu Selection}
            B --> Dashboard --> DB[(Supabase Cloud)]
            B --> History --> Excel[Export Excel]
            DB --> Analytics[Progress & Flow Charts]
        </pre>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({ startOnLoad: true });
        </script>
    """, height=400)

# --- 7. HISTORY PAGES ---
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
        st.info(f"📊 **Total: PKR {f_df['amount'].sum():,.2f}**")

        if is_auth:
            st.divider()
            target_id = st.text_input("Enter ID to Delete/Edit")
            if target_id and st.button("🗑️ Delete"):
                supabase.table('transactions').delete().eq('id', target_id).execute()
                st.cache_data.clear(); st.rerun()

        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Excel Download", buffer.getvalue(), f"{menu}.xlsx")
    else: st.warning("No records found.")
