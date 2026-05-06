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

# --- MOBILE OPTIMIZATION CSS ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3em; font-size: 16px !important; margin-bottom: 10px; }
        [data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        h2 { font-size: 20px !important; }
    }
    .main { background-color: #ffffff; }
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
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth and st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header & Metrics (Pehle wala same logic)
    st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>DEEWARY.COM</h2>", unsafe_allow_html=True)
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # Quick Actions for NEW entries
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    if "show_form" in st.session_state and is_auth:
        form_type = st.session_state.show_form
        with st.expander(f"New {form_type} Entry", expanded=True):
            with st.form("entry_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Name")
                d_amt = st.number_input("Amount", min_value=0.0)
                
                # Naye mangay gaye fields
                d_occ, d_rec, d_meth = "", "", "Cash"
                if form_type in ["Income", "Labor"]:
                    f1, f2 = st.columns(2)
                    d_occ = f1.text_input("Occupation")
                    d_meth = f1.selectbox("Method", ["Cash", "Bank", "EasyPaisa"])
                    d_rec = f2.text_input("Received By")
                
                d_det = st.text_area("Details")
                if st.form_submit_button("Save"):
                    payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear()
                    st.session_state.pop("show_form")
                    st.rerun()

# --- 6. HISTORY & EDIT/DELETE LOGIC ---
else:
    st.title(menu)
    if not df.empty:
        # Filtering data based on menu
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        st.dataframe(f_df, use_container_width=True)

        # --- ADMIN EDIT/DELETE SECTION ---
        if is_auth:
            st.divider()
            st.subheader("🛠️ Edit or Delete Record")
            target_id = st.text_input("Enter ID to Edit/Delete")
            
            if target_id:
                row = df[df['id'].astype(str) == target_id]
                if not row.empty:
                    data = row.iloc[0]
                    st.warning(f"Editing: {data['name']} - PKR {data['amount']}")
                    
                    with st.form("edit_form"):
                        u_name = st.text_input("Name", value=data['name'])
                        u_amt = st.number_input("Amount", value=float(data['amount']))
                        u_det = st.text_area("Details", value=data['detail'])
                        
                        col_up1, col_up2 = st.columns(2)
                        if col_up1.form_submit_button("✅ Update Record"):
                            supabase.table('transactions').update({"name": u_name, "amount": u_amt, "detail": u_det}).eq('id', target_id).execute()
                            st.cache_data.clear()
                            st.success("Updated!")
                            st.rerun()
                        
                        if col_up2.form_submit_button("🗑️ Delete Record"):
                            supabase.table('transactions').delete().eq('id', target_id).execute()
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.error("Invalid ID")
    else:
        st.warning("No data found.")
