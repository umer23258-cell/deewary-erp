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
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-size: 16px !important;
            margin-bottom: 10px;
        }
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
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

@st.cache_data(ttl=10)
def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        return pd.DataFrame(res.data)
    except:
        # Default list agar table empty ho ya na ho
        tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Wood Work", "Paint", "Ragarya", "Main Door", "Wasbasen Tottya", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])

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
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", use_container_width=True, caption="Active Site: Yousaf Colony")
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # HEADER (Waisa hi jaisa aapka tha)
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""<div style="text-align: center; background-color: #1E1E1E; padding: 15px; border-radius: 15px; border: 1px solid #333;">
            <h2 style="color: #FF4B4B; margin: 0;">DEEWARY.COM</h2>
            <p style="color: white; margin: 0;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
            <p style="color: #FF4B4B; font-weight: 700; margin: 0;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>""", unsafe_allow_html=True)

    st.write("##")

    # --- LIVE WORK CHART (DISPLAY) ---
    st.markdown("<h3 style='color: #FF4B4B;'>🚧 Project Work Status</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    
    cols = st.columns(2)
    for i, row in status_df.iterrows():
        t_name = row['task_name']
        t_status = row['status']
        with cols[i % 2]:
            color = "#28a745" if t_status == "Done" else "#ffc107" if t_status == "In Progress" else "#dc3545"
            icon = "✅" if t_status == "Done" else "⏳" if t_status == "In Progress" else "❌"
            st.markdown(f"""
                <div style="padding:10px; border-radius:10px; border-left: 8px solid {color}; background:#f9f9f9; margin-bottom:10px;">
                    <b style="font-size:16px;">{icon} {t_name}</b> <br>
                    <small style="color:{color}; font-weight:bold;">Status: {t_status}</small>
                </div>
            """, unsafe_allow_html=True)

    # --- ADMIN STATUS CONTROL (Sirf Admin ko dikhay ga) ---
    if is_auth:
        with st.expander("🛠️ Update Work Status (Admin Only)"):
            st.info("Yahan se aap kaam ka status change kar sakte hain.")
            selected_task = st.selectbox("Select Task", status_df['task_name'].tolist())
            new_status = st.radio("New Status", ["Pending", "In Progress", "Done"], horizontal=True)
            
            if st.button("Update Status"):
                # Supabase mein update karein
                supabase.table('project_status').upsert({"task_name": selected_task, "status": new_status}).execute()
                st.cache_data.clear()
                st.success(f"{selected_task} updated to {new_status}!")
                st.rerun()

    st.divider()

    # --- REMAINING DASHBOARD (Income/Expense/Metrics) ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"PKR {inc:,.0f}")
        col2.metric("Total Expenses", f"PKR {exp:,.0f}")
        col3.metric("Net Balance", f"PKR {bal:,.0f}")

    # --- QUICK ACTIONS (Forms) ---
    # (Aapka original logic yahan continue hoga...)
    st.divider()
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state and is_auth:
        form_type = st.session_state.show_form
        with st.form("entry_form"):
            d_date = st.date_input("Date", datetime.now())
            d_name = st.text_input("Name")
            d_amt = st.number_input("Amount", min_value=0.0)
            d_det = st.text_area("Details")
            if st.form_submit_button("Save"):
                payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det}
                supabase.table('transactions').insert(payload).execute()
                st.cache_data.clear()
                st.session_state.pop("show_form")
                st.rerun()

    # Footer/About (Waisa hi rahega)
    st.caption(f"© {datetime.now().year} Deewary.com | Management Portal")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    # (Aapka original history aur edit/delete ka poora code yahan ayega)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
