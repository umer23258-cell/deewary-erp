import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
import base64

# --- 1. SUPABASE SETUP ---
# Ensure secrets are set in .streamlit/secrets.toml
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase Credentials missing or incorrect!")
    st.stop()

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 30px;
        border-radius: 20px;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing/Grinding", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except Exception as e:
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

# --- 4. SIDEBAR & DATA ---
df = fetch_data()

with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    # Handle Image carefully (ensure URL is valid)
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black';">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px;">PREMIUM CONSTRUCTION MANAGEMENT</p>
            <div style="background: #FF4B4B; color: white; padding: 5px 15px; border-radius: 5px; font-weight: bold; display: inline-block;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Metrics calculation
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
    m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

    # Progress Section
    status_df = fetch_project_status()
    if not status_df.empty:
        done_tasks = len(status_df[status_df['status'] == 'Done'])
        total_tasks = len(status_df)
        prog_val = int((done_tasks / total_tasks) * 100)
        
        st.write("### 📈 Overall Progress")
        st.progress(prog_val / 100)
        st.write(f"**{prog_val}% Completed**")

    # Quick Add Buttons
    st.subheader("⚡ Quick Transactions")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title/Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit"):
                        payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        del st.session_state["show_form"]
                        st.rerun()
        else:
            st.warning("Admin login required to add data.")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filter Logic
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        # Display Data
        st.dataframe(f_df, use_container_width=True)
        
        # Excel Download
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")
