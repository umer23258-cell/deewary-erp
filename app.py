import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- 3. CUSTOM CSS FOR BRANDING ---
st.markdown("""
    <style>
    .main-header {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #1E3A8A;
        margin-bottom: 25px;
        text-align: center;
    }
    .main-header h1 {
        color: #1E3A8A;
        margin-bottom: 0;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .main-header p {
        color: #555;
        font-size: 1.1rem;
        font-style: italic;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1E3A8A;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
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

# --- 5. PERMANENT PROJECT LIST ---
if "projects" not in st.session_state:
    st.session_state.projects = ["Yousaf Colony"]

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ ERP PANEL")
    st.subheader("📁 Project Selection")
    selected_project = st.selectbox("Current Active Site:", st.session_state.projects)
    
    st.divider()
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "➕ Create New Project",
        "🔍 All Reports"
    ])
    
    st.divider()
    is_auth = check_password()

# Data Logic
df_raw = fetch_data()
if not df_raw.empty:
    if 'project' in df_raw.columns:
        df = df_raw[df_raw['project'] == selected_project]
    else:
        df = df_raw.copy()
else:
    df = pd.DataFrame()

# --- 7. BRANDING HEADER (EVERY PAGE) ---
st.markdown(f"""
    <div class="main-header">
        <h1>DEEWARY.COM</h1>
        <p>Real Estate & Construction Company</p>
    </div>
    """, unsafe_allow_html=True)

# --- 8. PAGE CONTENT ---

if menu == "📊 Dashboard":
    st.subheader(f"Project Overview: {selected_project}")
    
    # Calculation
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    # Metric Display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"PKR {inc:,.0f}")
    with col2:
        st.metric("Total Expenses", f"PKR {exp:,.0f}")
    with col3:
        st.metric("Remaining Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # Entry Form Section
    if is_auth:
        st.write(f"### 📝 Quick Entry for {selected_project}")
        c1, c2, c3 = st.columns(3)
        if c1.button("💸 Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

        if "show_form" in st.session_state:
            with st.expander(f"Registering {st.session_state.show_form}", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name/Description")
                    d_amt = st.number_input("Amount (PKR)", min_value=0.0)
                    d_det = st.text_area("Additional Details")
                    
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        ca, cb, cc = st.columns(3)
                        d_occ = ca.text_input("Work Title (e.g. Mason)")
                        d_rec = cb.text_input("Receiver Name")
                        d_meth = cc.selectbox("Payment Method", ["Cash", "Bank Transfer"])

                    if st.form_submit_button("Save Record"):
                        payload = {
                            "date": str(d_date), "type": st.session_state.show_form, 
                            "project": selected_project, "name": d_name, "amount": d_amt, 
                            "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.success("Data successfully recorded!")
                        st.rerun()

    # Footer Support
    st.write("##")
    st.divider()
    footer_l, footer_r = st.columns([2,1])
    with footer_r:
        whatsapp_link = "https://wa.me/923115190118"
        st.markdown(f'<a href="{whatsapp_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:black; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">💬 WhatsApp Support</div></a>', unsafe_allow_html=True)

elif menu == "➕ Create New Project":
    st.title("Register New Site")
    if is_auth:
        new_project_name = st.text_input("New Project Title")
        if st.button("Create Project"):
            if new_project_name and new_project_name not in st.session_state.projects:
                st.session_state.projects.append(new_project_name)
                st.success(f"Project '{new_project_name}' has been added!")
                st.rerun()
    else:
        st.warning("Unlock Admin Access to add new projects.")

else:
    st.title(f"{menu} - {selected_project}")
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        st.dataframe(f_df, use_container_width=True)
        st.info(f"💰 Sum Total: PKR {f_df['amount'].sum():,.2f}")
    else:
        st.warning(f"No transactions found for {selected_project}.")
