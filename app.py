import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
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

# --- 4. SIDEBAR MENU ---
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
    
    if menu == "📊 Dashboard":
        st.subheader("📅 Chart Settings")
        # Date Filter for Chart
        days_to_show = st.slider("Select Days for Chart", 1, 90, 7)
    
    st.divider()
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # HEADER
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1:
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""
            <div style="text-align: center; margin-top: 5px; background-color: #1E1E1E; padding: 15px; border-radius: 15px; border: 1px solid #333;">
                <h2 style="font-family: 'Arial Black', sans-serif; font-size: 28px; letter-spacing: 4px; color: #FF4B4B; text-transform: uppercase; margin: 0;">
                    DEEWARY.COM
                </h2>
                <hr style="width: 15%; margin: 8px auto; border: 1px solid #FF4B4B;">
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 12px; color: #FFFFFF; letter-spacing: 2px; margin-bottom: 5px; font-weight: 500;">
                    REAL ESTATE & CONSTRUCTION MANAGEMENT
                </p>
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #FF4B4B; font-weight: 700; margin: 0;">
                    C.E.O: SARDAR SAMI ULLAH
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("##")

    # PROGRESS SECTION
    st.markdown("<h3 style='color: #FF4B4B;'>📊 Project Work Progress</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / total_tasks) * 100)
    st.progress(prog_val / 100)
    st.markdown(f"<p style='text-align: right; font-weight: bold;'>{prog_val}% Completed</p>", unsafe_allow_html=True)

    task_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with task_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            color = "#155724" if row['status'] == "Done" else "#721c24"
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid {color};">
                    <span style="font-size: 14px;">{icon} {row['task_name']}</span><br>
                    <small style="color: {color}; font-weight: bold;">{row['status']}</small>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # FLOW ANALYTICS
    st.markdown("<h4 style='text-align: center; color: #444; font-size: 18px;'>Capital Flow Analytics</h4>", unsafe_allow_html=True)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    # --- CUSTOMIZABLE PAYMENT FLOW CHART ---
    if not df.empty:
        df_chart = df.copy()
        df_chart['date'] = pd.to_datetime(df_chart['date']).dt.date
        
        # User dynamic date filter from sidebar
        start_date = datetime.now().date() - timedelta(days=days_to_show)
        weekly_df = df_chart[df_chart['date'] >= start_date]
        
        if not weekly_df.empty:
            # Grouping and Sorting by Amount (As per your request)
            chart_data = weekly_df.groupby(['date', 'type'])['amount'].sum().reset_index()
            chart_data = chart_data.sort_values(by='amount', ascending=False)
            
            fig = px.bar(chart_data, x='date', y='amount', color='type', barmode='group', height=320,
                         color_discrete_map={'Income': '#28a745', 'Labor': '#dc3545', 'Material': '#fd7e14'},
                         labels={'amount': 'Amount (PKR)', 'date': 'Date', 'type': 'Category'})
            
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis={'categoryorder':'total descending'} # Payment ke hasab se arrange
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No transactions found in the last {days_to_show} days.")

    st.divider()

    # QUICK ACTIONS (Same as before)
    if "edit_id" not in st.session_state:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    # Form logic and footer (Keep as original)
    # ... [Rest of your original code remains exactly the same] ...
