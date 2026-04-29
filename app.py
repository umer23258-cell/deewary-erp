import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Deewary Smart ERP", page_icon="🏗️", layout="wide")

# Database Connection
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Connection Error: Check your Secrets! {e}")
        return None

supabase = init_connection()

# --- STYLING ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🏗️ Deewary.com - Smart ERP")
st.write(f"Logged in as Admin | {datetime.now().strftime('%A, %d %B %Y')}")
st.divider()

# --- APP LOGIC ---
if supabase:
    # 1. Fetch Data
    try:
        res = supabase.table("deewary_records").select("*").order("date", desc=True).execute()
        df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Database Table Not Found! Please run SQL code in Supabase. Error: {e}")
        df = pd.DataFrame()

    # 2. Dashboard Metrics
    if not df.empty:
        total_in = df[df['type'] == 'Income']['amount'].sum()
        total_ex = df[df['type'] == 'Expense']['amount'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"{total_in:,.0f} PKR")
        m2.metric("Total Expense", f"{total_ex:,.0f} PKR", delta_color="inverse")
        m3.metric("Net Balance", f"{total_in - total_ex:,.0f} PKR")
    
    st.divider()

    # 3. Tabs
    tab_add, tab_history = st.tabs(["➕ Add Transaction", "📜 History & Management"])

    with tab_add:
        with st.form("main_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                d = st.date_input("Transaction Date")
                t = st.selectbox("Type", ["Income", "Expense"])
            with c2:
                cat = st.selectbox("Category", ["Advance", "Material", "Labor", "Salary", "Rent", "Utility", "Misc"])
                amt = st.number_input("Amount (PKR)", min_value=0.0)
            
            det = st.text_area("Details / Remarks")
            if st.form_submit_button("🚀 Sync to Deewary Cloud"):
                if amt > 0:
                    new_row = {"date": str(d), "type": t, "category": cat, "amount": amt, "details": det}
                    try:
                        supabase.table("deewary_records").insert(new_row).execute()
                        st.success("Successfully Saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save Failed: {e}")
                else:
                    st.warning("Please enter an amount.")

    with tab_history:
        if not df.empty:
            for index, row in df.iterrows():
                with st.expander(f"📅 {row['date']} | {row['category']} | {row['amount']:,.0f} PKR"):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"**Remarks:** {row['details']}")
                    if col_b.button("🗑️ Delete", key=f"del_{row['id']}"):
                        supabase.table("deewary_records").delete().eq("id", row['id']).execute()
                        st.toast("Record Removed!")
                        st.rerun()
        else:
            st.info("No records found in the cloud database.")

else:
    st.warning("Waiting for database connection...")
