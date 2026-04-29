import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- SUPABASE SETUP ---
# Ye values aapke Streamlit Secrets se aayengi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #0f1113; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stat-card { 
        padding: 20px; border-radius: 10px; border: 1px solid #2c2f33; 
        background-color: #1e2124; text-align: center; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        return pd.DataFrame()

def check_password():
    """Returns True if the user had the correct password."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if st.session_state["authenticated"]:
        return True

    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == "admin786":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Ghalat Password!")
    return False

# --- UI LAYOUT ---
st.sidebar.title("🏗️ DEEWARY.COM")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🔍 Search & Reports", "👷 Labor History", "🏗️ Material History"])

df = fetch_data()

# --- 1. DASHBOARD PAGE ---
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
    col2.metric("Net Balance", f"PKR {bal:,.0f}")
    col3.metric("Total Expenses", f"PKR {exp:,.0f}")

    st.divider()
    
    # --- Protected Actions ---
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("➕ Add Income"):
            st.session_state.show_form = "Income"
    with c2:
        if st.button("👷 Pay Labor"):
            st.session_state.show_form = "Labor"
    with c3:
        if st.button("🏗️ Buy Material"):
            st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if check_password():
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_cat = st.text_input("Name/Category")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    
                    # Extra fields for Labor
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        d_occ = st.text_input("Occupation")
                        d_rec = st.text_input("Received By")
                        d_meth = st.selectbox("Method", ["Cash", "Online"])

                    if st.form_submit_button("Save to Cloud"):
                        new_data = {
                            "date": str(d_date), "type": st.session_state.show_form,
                            "category": d_cat, "amount": d_amt, "detail": d_det,
                            "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth
                        }
                        supabase.table('transactions').insert(new_data).execute()
                        st.success("Data Saved!")
                        del st.session_state.show_form
                        st.rerun()
        else:
            st.warning("Please enter password in sidebar to add entries.")

# --- 2. SEARCH & HISTORY PAGE ---
elif menu in ["🔍 Search & Reports", "👷 Labor History", "🏗️ Material History"]:
    st.title(menu)
    
    if not df.empty:
        # Filter based on menu
        if "Labor" in menu:
            filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu:
            filtered_df = df[df['type'] == 'Material']
        else:
            search = st.text_input("Search Anything...")
            filtered_df = df[df.astype(str).apply(lambda x: search.lower() in x.str.lower().any(), axis=1)] if search else df

        st.dataframe(filtered_df, use_container_width=True)
        st.subheader(f"Grand Total: PKR {filtered_df['amount'].sum():,.2f}")

        # Export Options
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            buffer = io.BytesIO()
            filtered_df.to_excel(buffer, index=False)
            st.download_button("📊 Download Excel", buffer.getvalue(), "Report.xlsx")
        
        # Delete Action
        st.divider()
        st.write("🗑️ **Danger Zone**")
        if check_password():
            del_id = st.number_input("Enter ID to Delete", step=1)
            if st.button("Delete Record"):
                supabase.table('transactions').delete().eq('id', del_id).execute()
                st.success(f"ID {del_id} deleted!")
                st.rerun()
        else:
            st.info("Unlock admin access to delete records.")
    else:
        st.info("No data found in cloud.")
