import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Deewary Smart ERP", page_icon="🏗️", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Secrets missing! Please add SUPABASE_URL and SUPABASE_KEY in Streamlit.")
    st.stop()

# --- APP HEADER ---
st.title("🏗️ Deewary.com - Smart ERP")
st.write(f"Logged in as Admin | Date: {datetime.now().strftime('%d-%m-%Y')}")
st.divider()

# --- DASHBOARD METRICS ---
def get_data():
    res = supabase.table("deewary_records").select("*").order("date", desc=True).execute()
    return pd.DataFrame(res.data)

df = get_data()

if not df.empty:
    income = df[df['type'] == 'Income']['amount'].sum()
    expense = df[df['type'] == 'Expense']['amount'].sum()
    st.columns(3)[0].metric("Total Income", f"{income:,.0f} PKR")
    st.columns(3)[1].metric("Total Expense", f"{expense:,.0f} PKR")
    st.columns(3)[2].metric("Net Balance", f"{income - expense:,.0f} PKR")

st.divider()

# --- TABS ---
tab_add, tab_history = st.tabs(["➕ Add Entry", "📜 History & Delete"])

with tab_add:
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_date = st.date_input("Date", datetime.now())
            t_type = st.selectbox("Type", ["Income", "Expense"])
        with col2:
            t_cat = st.selectbox("Category", ["Material", "Labor", "Salary", "Advance", "Rent", "Utility", "Misc"])
            t_amount = st.number_input("Amount (PKR)", min_value=0.0)
        
        t_details = st.text_area("Details")
        if st.form_submit_button("🚀 Save to Cloud"):
            if t_amount > 0:
                payload = {"date": str(t_date), "type": t_type, "category": t_cat, "amount": t_amount, "details": t_details}
                supabase.table("deewary_records").insert(payload).execute()
                st.success("Saved!")
                st.rerun()

with tab_history:
    if not df.empty:
        for index, row in df.iterrows():
            with st.expander(f"📅 {row['date']} | {row['category']} | {row['amount']:,.0f} PKR"):
                st.write(f"**Details:** {row['details']}")
                if st.button("🗑️ Delete Record", key=f"del_{row['id']}"):
                    supabase.table("deewary_records").delete().eq("id", row['id']).execute()
                    st.rerun()
    else:
        st.info("No records yet.")
