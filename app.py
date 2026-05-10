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

# --- CUSTOM CSS (Modern & Dynamic Look) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Dynamic Dashboard Cards */
    .status-card {
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS (ORIGINAL LOGIC) ---
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

# --- 4. SIDEBAR (PROJECT INFO) ---
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

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Custom Header (CEO & Logo)
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1:
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)
    with h_col2:
        st.markdown("<h2 style='margin:0; color:#1E1E1E; letter-spacing: 2px;'>DEEWARY.COM</h2><p style='color:#FF4B4B; font-weight:bold; margin:0;'>C.E.O: SARDAR SAMI ULLAH</p>", unsafe_allow_html=True)

    st.write("##")

    # Original Calculations
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    # Dynamic Cards Layout (Using Original Metrics: Income, Expense, Balance)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(135deg, #2193b0, #6dd5ed);"><h3>PKR {inc:,.0f}</h3><p>Total Income</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(135deg, #f12711, #f5af19);"><h3>PKR {exp:,.0f}</h3><p>Total Expenses</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="status-card" style="background: linear-gradient(135deg, #11998e, #38ef7d);"><h3>PKR {bal:,.0f}</h3><p>Net Balance</p></div>', unsafe_allow_html=True)

    st.write("##")
    
    # Graphs for "Dynamic Dashboard" feel
    g1, g2 = st.columns([2, 1])
    with g1:
        st.subheader("📈 Capital Flow Trend")
        if not df.empty:
            line_fig = px.line(df, x='date', y='amount', color='type', template="plotly_white", color_discrete_map={"Income": "#2193b0", "Labor": "#f12711", "Material": "#f5af19"})
            st.plotly_chart(line_fig, use_container_width=True)
    with g2:
        st.subheader("📊 Expense Distribution")
        if exp > 0:
            lab_sum = df[df['type'] == 'Labor']['amount'].sum()
            mat_sum = df[df['type'] == 'Material']['amount'].sum()
            pie_fig = px.pie(values=[lab_sum, mat_sum], names=['Labor', 'Material'], hole=0.5, color_discrete_sequence=["#f12711", "#f5af19"])
            st.plotly_chart(pie_fig, use_container_width=True)

    st.divider()

    # Progress & Tasks
    st.markdown("<h3 style='color: #FF4B4B;'>🏗️ Project Work Progress</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    done = len(status_df[status_df['status'] == 'Done'])
    total = len(status_df)
    prog = int((done/total)*100) if total > 0 else 0
    st.progress(prog/100)
    st.write(f"**{prog}% Work Completed**")

    task_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with task_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            color = "#155724" if row['status'] == "Done" else "#721c24"
            st.markdown(f"""
                <div style="background-color: #ffffff; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid {color}; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                    <span style="font-size: 14px;">{icon} {row['task_name']}</span>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Completed Project Section
    st.markdown("### 🏘️ OUR COMPLETED PROJECT")
    v1, v2 = st.columns([1.5, 1])
    with v1: st.video("https://youtu.be/AiA4PkXturU")
    with v2:
        st.markdown("""<div style="background-color: #1E1E1E; padding: 20px; border-radius: 15px; color: white;">
                <h4 style="color: #FF4B4B; margin-top: 0;">Modern Architecture</h4>
                <p>Hamara ye project modern aesthetics aur structural durability ka behtareen imtizaaj hai.</p>
                <a href="https://youtu.be/AiA4PkXturU" target="_blank" style="color: #FF4B4B; text-decoration: none; font-weight: bold;">▶ Watch Tour</a>
            </div>""", unsafe_allow_html=True)

    # Quick Actions
    if is_auth:
        st.subheader("➕ Quick Entry")
        qa1, qa2, qa3 = st.columns(3)
        if qa1.button("Add Income"): st.session_state.show_form = "Income"
        if qa2.button("Pay Labor"): st.session_state.show_form = "Labor"
        if qa3.button("Buy Material"): st.session_state.show_form = "Material"

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df
        
        st.dataframe(f_df, use_container_width=True)
        
        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Download Excel Report", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No records found in database.")
