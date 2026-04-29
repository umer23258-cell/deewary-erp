import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import base64

# --- 1. CONNECTION (Aapka Purana Style) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏗️ Deewary.com - Office Manager")

# --- 2. DATA FETCHING (History ke liye) ---
def fetch_data():
    res = supabase.table("deewary_records").select("*").order("date", desc=True).execute()
    return pd.DataFrame(res.data)

df = fetch_data()

# --- 3. ADD NEW ENTRY (Aapka Purana Form) ---
with st.expander("➕ Add New Income/Expense", expanded=False):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.now())
            type_entry = st.selectbox("Type", ["Income", "Expense"])
        with col2:
            category = st.text_input("Category (e.g. Salary, Advance)")
            amount = st.number_input("Amount", min_value=0.0)
        
        details = st.text_area("Details")
        if st.form_submit_button("Save Record"):
            data = {"date": str(date), "type": type_entry, "category": category, "amount": amount, "details": details}
            supabase.table("deewary_records").insert(data).execute()
            st.success("Data Saved!")
            st.rerun()

st.divider()

# --- 4. HISTORY, EDIT & DELETE SECTION ---
st.subheader("📜 Transaction History & Management")

if not df.empty:
    # --- PDF PRINT FUNCTION ---
    def create_download_link(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="deewary_report.csv" style="text-decoration:none;"><button style="background-color:#4CAF50; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer;">📥 Download Report (CSV/Excel)</button></a>'
        return href

    st.markdown(create_download_link(df), unsafe_allow_html=True)
    st.write("")

    # Display Records with Edit/Delete
    for index, row in df.iterrows():
        # Aik line mein record dikhayein
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
        c1.text(row['date'])
        c2.text(row['type'])
        c3.text(f"{row['amount']:,}")
        
        # DELETE BUTTON
        if c4.button("🗑️", key=f"del_{row['id']}"):
            supabase.table("deewary_records").delete().eq("id", row['id']).execute()
            st.warning("Deleted!")
            st.rerun()
            
        # EDIT BUTTON (Simple layout)
        if c5.button("📝", key=f"edit_{row['id']}"):
            st.info(f"Editing ID: {row['id']} - Niche form mein change karein")
            # Edit ka form yahan dikha sakte hain (Simple rakhne ke liye delete zaroori tha)

    st.table(df[["date", "type", "category", "amount", "details"]]) # Full Table view
else:
    st.info("No history found.")

# --- 5. TOTALS ---
if not df.empty:
    st.divider()
    total_in = df[df['type'] == 'Income']['amount'].sum()
    total_ex = df[df['type'] == 'Expense']['amount'].sum()
    st.write(f"### Total Income: {total_in:,} | Total Expense: {total_ex:,}")
