import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import plotly.express as px

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (Interface ko Modern banane ke liye) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-bottom: 4px solid #FF4B4B;
    }
    /* Dynamic Cards Style */
    .status-card {
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS (APKA ORIGINAL LOGIC) ---
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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
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

# --- 4. SIDEBAR (APKA ORIGINAL DESIGN) ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF4B4B; color: #1E1E1E;">
            <h4 style="margin: 0; color: #FF4B4B; font-size: 16px;">📍 Current Project</h4>
            <p style="margin: 5px 0; font-size: 13px;"><b>Location:</b> Yousaf Colony</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Size:</b> 5 Marla</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Structure:</b> 2.5 Story</p>
        </div>
    """, unsafe_allow_html=True)

df = fetch_data()

# --- 5. DASHBOARD PAGE (NEW DYNAMIC INTERFACE) ---
if menu == "📊 Dashboard":
    # Header Section
    h_col1, h_col2 = st.columns([1, 5])
    with h_col1:
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)
    with h_col2:
        st.markdown("<h1 style='margin:0; color:#1E1E1E;'>Project Performance</h1><p style='color:red; font-weight:bold;'>C.E.O: SARDAR SAMI ULLAH</p>", unsafe_allow_html=True)

    # Calculations
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        lab = df[df['type'] == 'Labor']['amount'].sum()
        mat = df[df['type'] == 'Material']['amount'].sum()
        exp = lab + mat
        bal = inc - exp
    else: inc, lab, mat, exp, bal = 0, 0, 0, 0, 0

    # Dynamic Cards Layout
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(45deg, #2193b0, #6dd5ed);"><h3>PKR {inc:,.0f}</h3><p>Total Income</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(45deg, #f12711, #f5af19);"><h3>PKR {lab:,.0f}</h3><p>Labor Cost</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(45deg, #11998e, #38ef7d);"><h3>PKR {mat:,.0f}</h3><p>Material Cost</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(45deg, #4b6cb7, #182848);"><h3>PKR {bal:,.0f}</h3><p>Net Balance</p></div>', unsafe_allow_html=True)

    st.write("##")
    
    # Graphs
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("📈 Cash Flow Trend")
        if not df.empty:
            line_fig = px.line(df, x='date', y='amount', color='type', template="plotly_white")
            st.plotly_chart(line_fig, use_container_width=True)
    with g2:
        st.subheader("📊 Expense Split")
        if exp > 0:
            pie_fig = px.pie(values=[lab, mat], names=['Labor', 'Material'], hole=0.5)
            st.plotly_chart(pie_fig, use_container_width=True)

    st.divider()

    # Original Progress Bars & Task Management
    st.markdown("<h3 style='color: #FF4B4B;'>🏗️ Site Work Progress</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    done = len(status_df[status_df['status'] == 'Done'])
    total = len(status_df)
    prog = int((done/total)*100) if total > 0 else 0
    st.progress(prog/100)
    st.write(f"**{prog}% Completed**")

    # Display Tasks in 3 Columns (Apka Original Style)
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            st.markdown(f"**{'✅' if row['status']=='Done' else '⏳'} {row['task_name']}**")

    st.divider()

    # Video & About (Apka Original)
    st.markdown("### 🏘️ OUR COMPLETED PROJECT")
    v1, v2 = st.columns([1, 1])
    with v1: st.video("https://youtu.be/AiA4PkXturU")
    with v2:
        st.info("Hamara ye project modern aesthetics aur structural durability ka behtareen imtizaaj hai.")

    # Quick Actions
    if is_auth:
        st.subheader("➕ Quick Entry")
        qa1, qa2, qa3 = st.columns(3)
        if qa1.button("Income"): st.session_state.show_form = "Income"
        if qa2.button("Labor"): st.session_state.show_form = "Labor"
        if qa3.button("Material"): st.session_state.show_form = "Material"

# --- 6. HISTORY PAGES (MUKAMMAL SAME) ---
else:
    st.title(menu)
    if not df.empty:
        # Filter logic same as original
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df
        
        st.dataframe(f_df, use_container_width=True)
        
        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Export Excel", buffer.getvalue(), f"{menu}.xlsx")
