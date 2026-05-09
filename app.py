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

# --- MOBILE OPTIMIZATION CSS ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3em; margin-bottom: 10px; }
        [data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    }
    .main { background-color: #ffffff; }
    .whatsapp-btn {
        background-color: #25D366;
        color: white !important;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
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
            tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Paint", "Wood Work", "Ragarya", "Main Door", "Grill", "Wasbasen Tottya", "Finishing"]
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
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.subheader("🛠️ Management")
        if st.button("📝 Update Work Progress"): st.session_state.show_update_panel = True
        if st.session_state.get("show_update_panel", False):
            status_df = fetch_project_status()
            with st.expander("Update Task Status", expanded=True):
                with st.form("sidebar_status_form"):
                    u_task = st.selectbox("Task", status_df['task_name'].tolist())
                    u_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
                    if st.form_submit_button("Save Status"):
                        supabase.table('project_status').upsert({"task_name": u_task, "status": u_status}).execute()
                        st.cache_data.clear()
                        st.session_state.show_update_panel = False
                        st.rerun()
    
    st.divider()
    st.info("📞 **Contact Support**\n\nFor any technical issues, contact the administrator.")
    if is_auth and st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # HEADER SECTION
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)
    with h_col2:
        st.markdown("<div style='background-color: #1E1E1E; padding: 15px; border-radius: 15px; text-align: center;'><h2 style='color: #FF4B4B; margin: 0; letter-spacing: 2px;'>DEEWARY.COM ERP</h2></div>", unsafe_allow_html=True)

    st.write("##")

    # PROGRESS & CHART
    status_df = fetch_project_status()
    done_count = len(status_df[status_df['status'] == 'Done'])
    total_count = len(status_df)
    progress_percent = (done_count / total_count) * 100

    c1, c2 = st.columns([1.5, 2])
    with c1:
        st.markdown("<h4 style='color: #FF4B4B;'>📈 Overall Completion</h4>", unsafe_allow_html=True)
        fig = px.pie(values=[done_count, total_count-done_count], names=['Done', 'Pending'], 
                     hole=0.7, color_discrete_map={'Done':'#28a745', 'Pending':'#efefef'})
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=220)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<h2 style='text-align: center; margin-top: -145px;'>{progress_percent:.0f}%</h2>", unsafe_allow_html=True)
        st.write("##")

    with c2:
        st.markdown("<h4 style='color: #FF4B4B;'>📋 Work Progress Report</h4>", unsafe_allow_html=True)
        r_col1, r_col2 = st.columns(2)
        for idx, row in status_df.iterrows():
            t_col = r_col1 if idx % 2 == 0 else r_col2
            with t_col:
                color = "#28a745" if row["status"] == "Done" else "#dc3545"
                st.markdown(f"<div style='border-left: 4px solid {color}; background: #f9f9f9; padding: 6px; border-radius: 4px; margin-bottom: 4px; font-size: 12px;'>{'✅' if row['status'] == 'Done' else '⏳'} {row['task_name']}</div>", unsafe_allow_html=True)

    st.divider()

    # VIDEO & ABOUT DEEWARY SECTION (Wapis Shamil Kiya)
    v1, v2 = st.columns([2, 1.5])
    with v1:
        st.subheader("🎥 Site Overview Video")
        # Yahan apni video ka URL ya file path dalain
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Example URL, replace with yours

    with v2:
        st.subheader("🏢 About Deewary.com")
        st.write("Deewary.com is a leading name in Real Estate and Construction Management. We provide end-to-end solutions for residential and commercial projects with transparency and quality.")
        
        st.markdown("### 💬 Contact Us")
        st.markdown(f'<a href="https://wa.me/923XXXXXXXXX" class="whatsapp-btn">📱 Chat on WhatsApp</a>', unsafe_allow_html=True)
        st.write("**Phone:** +92 3XX XXXXXXX")

    st.divider()

    # FINANCIALS
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"PKR {inc:,.0f}")
        m2.metric("Total Expenses", f"PKR {exp:,.0f}")
        m3.metric("Net Balance", f"PKR {inc-exp:,.0f}")

    st.caption(f"© {datetime.now().year} Deewary.com | Project: Yousaf Colony")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        st.dataframe(f_df, use_container_width=True)
        st.info(f"📊 **Total: PKR {f_df['amount'].sum():,.2f}**")
