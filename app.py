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
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-size: 16px !important;
            margin-bottom: 10px;
        }
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
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
    except Exception:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Paint", "Wood Work", "Ragarya", "Main Door", "Grill", "Wasbasen Tottya", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except Exception:
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

# --- 4. SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        # Update Progress Button in Sidebar
        st.subheader("🛠️ Management")
        if st.button("📝 Update Work Progress"):
            st.session_state.show_update_panel = True

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
                if st.button("Cancel"):
                    st.session_state.show_update_panel = False
                    st.rerun()

    st.divider()
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    if is_auth and st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # HEADER
    h_col1, h_col2 = st.columns([1, 4])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)
    with h_col2:
        st.markdown("<div style='background-color: #1E1E1E; padding: 15px; border-radius: 15px; text-align: center;'><h2 style='color: #FF4B4B; margin: 0; letter-spacing: 2px;'>DEEWARY.COM ERP</h2></div>", unsafe_allow_html=True)

    st.write("##")

    # PROGRESS CHART & REPORT SECTION
    status_df = fetch_project_status()
    
    # Calculate Progress for Chart
    done_count = len(status_df[status_df['status'] == 'Done'])
    total_count = len(status_df)
    progress_percent = (done_count / total_count) * 100

    c1, c2 = st.columns([1.5, 2])
    
    with c1:
        st.markdown("<h4 style='color: #FF4B4B;'>📈 Overall Completion</h4>", unsafe_allow_html=True)
        # Professional Donut Chart
        chart_df = pd.DataFrame({
            "Category": ["Done", "Pending"],
            "Count": [done_count, total_count - done_count]
        })
        fig = px.pie(chart_df, values='Count', names='Category', 
                     hole=0.7, color_discrete_map={'Done':'#28a745', 'Pending':'#efefef'})
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<h2 style='text-align: center; margin-top: -160px;'>{progress_percent:.0f}%</h2>", unsafe_allow_html=True)
        st.write("##") # Spacer to push next content down

    with c2:
        st.markdown("<h4 style='color: #FF4B4B;'>📋 Work Progress Report</h4>", unsafe_allow_html=True)
        # Displaying Status list
        report_col1, report_col2 = st.columns(2)
        for idx, row in status_df.iterrows():
            target_col = report_col1 if idx % 2 == 0 else report_col2
            with target_col:
                is_done = row["status"] == "Done"
                color = "#28a745" if is_done else "#dc3545"
                icon = "✅" if is_done else "⏳"
                st.markdown(f"""
                    <div style="border-left: 5px solid {color}; background: #f9f9f9; padding: 8px; border-radius: 5px; margin-bottom: 5px; font-size: 13px;">
                        {icon} <b>{row['task_name']}</b>
                    </div>
                """, unsafe_allow_html=True)

    st.divider()

    # ANALYTICS METRICS
    st.markdown("<h4 style='text-align: center; color: #444;'>💰 Capital Flow Analytics</h4>", unsafe_allow_html=True)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"PKR {inc:,.0f}")
        m2.metric("Total Expenses", f"PKR {exp:,.0f}")
        m3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Project Location: Yousaf Colony")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()
        
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("No records found.")
