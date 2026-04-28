import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CLOUD DATABASE SETUP ---
URL = "https://zegrqjwpjchwiuesmjvq.supabase.co"
KEY = "sb_publishable_GsDAptHmHsYBzDwbFFRBg_83lsotU1X1I9_kUof_4"
supabase: Client = create_client(URL, KEY)

# --- WEB PAGE STYLE (Custom CSS for same look) ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0f1113; color: white; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2979ff; color: white; }
    div[data-testid="stMetricValue"] { color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.title("🏗️ DEEWARY.COM - Admin Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login to System"):
        if user == "admin" and pw == "admin786":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Ghalat Details!")

if not st.session_state['logged_in']:
    login_page()
    st.stop()

# --- SIDEBAR (Navigation) ---
st.sidebar.title("DEEWARY.COM")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard Overview", "➕ Add New Entry", "🔍 Search & Reports"])

# --- DATA FUNCTIONS ---
def fetch_data():
    res = supabase.table('transactions').select("*").execute()
    return pd.DataFrame(res.data)

# --- PAGES ---
if choice == "📊 Dashboard Overview":
    st.header("Enterprise Dashboard")
    df = fetch_data()
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Installment", f"PKR {inc:,.0f}")
        c2.metric("Net Balance", f"PKR {bal:,.0f}")
        c3.metric("Total Expenses", f"PKR {exp:,.0f}")
        
        st.subheader("Recent Activity")
        st.dataframe(df.tail(10), use_container_width=True)

elif choice == "➕ Add New Entry":
    st.header("New Transaction Entry")
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            t_date = st.date_input("Date", datetime.now())
            t_type = st.selectbox("Type", ["Income", "Labor", "Material"])
            t_cat = st.text_input("Name/Category")
        with col2:
            t_amt = st.number_input("Amount", min_value=0.0)
            t_det = st.text_area("Details")
            
        occ, rec, meth = "", "", "Cash"
        if t_type == "Labor":
            occ = st.text_input("Occupation")
            rec = st.text_input("Received By")
            meth = st.radio("Payment Method", ["Cash", "Online"], horizontal=True)

        if st.form_submit_button("SAVE TO CLOUD"):
            data = {
                "date": str(t_date), "type": t_type, "category": t_cat,
                "amount": t_amt, "detail": t_det, "occupation": occ,
                "received_by": rec, "pay_method": meth
            }
            supabase.table('transactions').insert(data).execute()
            st.success("Data Saved Successfully!")

elif choice == "🔍 Search & Reports":
    st.header("Smart Search & Reports")
    df = fetch_data()
    search = st.text_input("Search anything...")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    
    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV Report", df.to_csv(index=False), "Report.csv")