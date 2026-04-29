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

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #0f1113; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #1e2124; padding: 15px; border-radius: 10px; border: 1px solid #2c2f33; }
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

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Ghalat Password!")
    return False

# --- 4. UI LAYOUT & SIDEBAR ---
st.sidebar.title("🏗️ DEEWARY.COM")
# Yahan maine "Income History" ka option add kar diya hai
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "💰 Income History", 
    "👷 Labor History", 
    "🏗️ Material History",
    "🔍 Search & All Reports"
])

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.title("Enterprise Dashboard")
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if check_password():
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_cat = st.text_input("name")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        col_a, col_b, col_c = st.columns(3)
                        d_occ = col_a.text_input("Occupation")
                        d_rec = col_b.text_input("Received By")
                        d_meth = col_c.selectbox("Method", ["Cash", "Online"])

                    if st.form_submit_button("Save to Cloud"):
                        new_data = {
                            "date": str(d_date), "type": st.session_state.show_form,
                            "category": d_cat, "amount": d_amt, "detail": d_det,
                            "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth
                        }
                        supabase.table('transactions').insert(new_data).execute()
                        st.cache_data.clear()
                        st.success("Data Saved!")
                        del st.session_state.show_form
                        st.rerun()
        else:
            st.warning("Sidebar mein password dalein.")

# --- 6. ALL HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filter Logic for all types
        if menu == "💰 Income History":
            filtered_df = df[df['type'] == 'Income']
        elif menu == "👷 Labor History":
            filtered_df = df[df['type'] == 'Labor']
        elif menu == "🏗️ Material History":
            filtered_df = df[df['type'] == 'Material']
        else:
            filtered_df = df.copy() # All Reports

        # Search Bar
        search = st.text_input("🔍 Search in this view...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total for {menu}: PKR {filtered_df['amount'].sum():,.2f}**")

        # Excel Download
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
        
        # Delete Option
        st.divider()
        if check_password():
            del_id = st.number_input("Enter ID to Delete", step=1, value=0)
            if st.button("Delete"):
                supabase.table('transactions').delete().eq('id', del_id).execute()
                st.cache_data.clear()
                st.success("Deleted!")
                st.rerun()
    else:
        st.info("No data found.")
