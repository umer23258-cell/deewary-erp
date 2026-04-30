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

# --- 4. PROJECT LIST MANAGEMENT ---
# Hum session state use kar rahe hain taake projects list dynamically barhti rahe
if "projects" not in st.session_state:
    st.session_state.projects = ["Yousaf Colony"]

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "📁 Projects Manager",
        "🔍 All Reports"
    ])
    
    st.divider()
    
    # Project Selection
    selected_project = st.selectbox("Select Active Project:", st.session_state.projects)
    
    st.divider()
    is_auth = check_password()

# Data Fetching
df_raw = fetch_data()

# Filtering data for the selected project
if not df_raw.empty and 'project' in df_raw.columns:
    df = df_raw[df_raw['project'] == selected_project]
else:
    df = df_raw.copy() if df_raw.empty else pd.DataFrame()

# --- 6. PROJECTS MANAGER (NEW PROJECT CREATION) ---
if menu == "📁 Projects Manager":
    st.title("Manage Your Projects")
    
    if is_auth:
        st.subheader("Add a New Site/Project")
        new_p_name = st.text_input("Enter Project Name (e.g. Gulberg Phase 2)")
        if st.button("🚀 Create Project & Start Fresh"):
            if new_p_name and new_p_name not in st.session_state.projects:
                st.session_state.projects.append(new_p_name)
                st.success(f"Project '{new_p_name}' created! Select it from the sidebar to start.")
                st.rerun()
            else:
                st.warning("Please enter a unique project name.")
        
        st.divider()
        st.write("### Current Active Projects:")
        for p in st.session_state.projects:
            st.write(f"- {p}")
    else:
        st.warning("Please unlock Admin Access to manage projects.")

# --- 7. DASHBOARD PAGE ---
elif menu == "📊 Dashboard":
    st.title(f"Dashboard: {selected_project}")
    
    # Dashboard Metrics (Automatic Zero for new projects)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Project Income", f"PKR {inc:,.0f}")
    col2.metric("Project Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # Entry Forms
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("Quick Entry")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            with st.expander(f"New {st.session_state.show_form} for {selected_project}", expanded=True):
                with st.form("main_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Notes")
                    
                    # Labor specific fields
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        ca, cb, cc = st.columns(3)
                        d_occ = ca.text_input("Occupation")
                        d_rec = cb.text_input("Received By")
                        d_meth = cc.selectbox("Method", ["Cash", "Online"])

                    if st.form_submit_button("Save to Project"):
                        payload = {
                            "date": str(d_date), "type": st.session_state.show_form, 
                            "project": selected_project, "name": d_name, "amount": d_amt, 
                            "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.success("Saved!")
                        st.rerun()
            if st.button("Cancel"):
                st.session_state.pop("show_form")
                st.rerun()

    # Support & About (Niche ka wahi professional layout)
    st.write("##")
    st.divider()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("🏡 Deewary.com ERP")
        st.write("Managing multiple construction sites with precision and transparency.")
    with col_b:
        whatsapp_url = "https://wa.me/923115190118"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:black; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">💬 WhatsApp Support</div></a>', unsafe_allow_html=True)

# --- 8. HISTORY PAGES ---
else:
    st.title(f"{menu} - {selected_project}")
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        st.dataframe(f_df, use_container_width=True)
        st.info(f"💰 Project Total: PKR {f_df['amount'].sum():,.2f}")
    else:
        st.warning(f"No transactions yet for {selected_project}.")
