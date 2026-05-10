import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import plotly.express as px  # Professional Graphs ke liye

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (For Dynamic Dashboard Look) ---
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #f4f7f6; }
    
    /* Stats Cards */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-bottom: 5px solid #FF4B4B;
    }
    
    /* Custom Card Containers */
    .card-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .custom-card {
        flex: 1;
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    .blue-card { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }
    .yellow-card { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
    .green-card { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .orange-card { background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
    }
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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Finishing"]
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
    st.title("🏗️ DEEWARY.COM")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & Reports"])
    
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

# --- 5. DASHBOARD PAGE ---
df = fetch_data()

if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #1E1E1E;'>Dynamic Financial Dashboard</h2>", unsafe_allow_html=True)
    
    # Calculation Logic
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        lab = df[df['type'] == 'Labor']['amount'].sum()
        mat = df[df['type'] == 'Material']['amount'].sum()
        exp = lab + mat
        bal = inc - exp
    else:
        inc, lab, mat, exp, bal = 0, 0, 0, 0, 0

    # Colorful Cards (Like the picture)
    st.markdown(f"""
        <div class="card-container">
            <div class="custom-card blue-card">
                <h3 style="margin:0;">PKR {inc:,.0f}</h3>
                <p style="margin:0;">Total Income</p>
            </div>
            <div class="custom-card yellow-card">
                <h3 style="margin:0;">PKR {lab:,.0f}</h3>
                <p style="margin:0;">Labor Cost</p>
            </div>
            <div class="custom-card green-card">
                <h3 style="margin:0;">PKR {mat:,.0f}</h3>
                <p style="margin:0;">Material Cost</p>
            </div>
            <div class="custom-card orange-card">
                <h3 style="margin:0;">PKR {bal:,.0f}</h3>
                <p style="margin:0;">Net Balance</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Graphs Section
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown("<div style='background:white; padding:15px; border-radius:15px;'>", unsafe_allow_html=True)
        st.subheader("Revenue vs Expense Trend")
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            trend_df = df.groupby(['date', 'type'])['amount'].sum().reset_index()
            fig_line = px.line(trend_df, x='date', y='amount', color='type', template="plotly_white", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with g2:
        st.markdown("<div style='background:white; padding:15px; border-radius:15px;'>", unsafe_allow_html=True)
        st.subheader("Expense Distribution")
        if not df.empty and exp > 0:
            fig_pie = px.pie(values=[lab, mat], names=['Labor', 'Material'], hole=0.4, color_discrete_sequence=['#fda085', '#38ef7d'])
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense data to show chart.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    
    # Quick Actions & Progress
    st.subheader("🏗️ Project Progress")
    status_df = fetch_project_status()
    done = len(status_df[status_df['status'] == 'Done'])
    total = len(status_df)
    prog = int((done/total)*100) if total > 0 else 0
    st.progress(prog/100)
    st.write(f"**{prog}% Tasks Completed** ({done}/{total})")

    st.divider()
    
    # Forms (Quick Actions)
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    if st.form_submit_button("Save Record"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        del st.session_state.show_form
                        st.success("Saved!")
                        st.rerun()

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df
        
        st.dataframe(f_df, use_container_width=True)
        
        # Excel Export
        buffer = io.BytesIO()
        f_df.to_excel(buffer, index=False)
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")
