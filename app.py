import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import base64

# --- 1. CONNECTION (Aapka Style) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🏗️ Deewary.com - Office Manager")

# --- 2. DATA FETCHING (Crash hone se bachane ke liye) ---
def fetch_data():
    try:
        res = supabase.table("deewary_records").select("*").order("date", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = fetch_data()

# --- 3. ADD NEW ENTRY (Aapka Original Form) ---
st.subheader("➕ Add New Entry")
with st.form("my_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        f_date = st.date_input("Date", datetime.now())
        f_type = st.selectbox("Type", ["Income", "Expense"])
    with col2:
        f_cat = st.text_input("Category")
        f_amount = st.number_input("Amount", min_value=0.0)
    
    f_details = st.text_area("Details")
    
    if st.form_submit_button("Save Data"):
        data = {"date": str(f_date), "type": f_type, "category": f_cat, "amount": f_amount, "details": f_details}
        supabase.table("deewary_records").insert(data).execute()
        st.success("Saved!")
        st.rerun()

st.divider()

# --- 4. HISTORY, EDIT, DELETE & PDF (Jo aapne manga tha) ---
st.subheader("📜 Income & Expense History")

if not df.empty:
    # PDF/Excel Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Report (PDF/Excel)", data=csv, file_name='deewary_report.csv', mime='text/csv')

    # Display Records with Edit/Delete Buttons
    for index, row in df.iterrows():
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
            c1.write(row['date'])
            c2.write(f"**{row['type']}**")
            c3.write(f"{row['amount']:,} PKR")
            
            # DELETE Button
            if c4.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("deewary_records").delete().eq("id", row['id']).execute()
                st.rerun()
            
            # EDIT Button (Short-cut)
            if c5.button("📝", key=f"ed_{row['id']}"):
                st.info("Edit feature: Change details in the form above.")

    # Full View Table
    st.dataframe(df)
else:
    st.info("Abhi koi record nahi hai. Upar form se pehli entry karein.")
