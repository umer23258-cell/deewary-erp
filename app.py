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

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumbering", "Electric Work", "Celling", "Paint", "Wood Work", "Ragarya", "Main Door", "Grill", "Wasbasen Tottya", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except:
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

# --- 4. SIDEBAR MENU & FORMS ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    
    # Check Auth for Entry Forms in Sidebar
    is_auth = check_password()
    
    if is_auth:
        st.subheader("➕ Quick Entry")
        c1, c2, c3 = st.columns(3)
        # Buttons are now compact in sidebar
        if c1.button("💰"): st.session_state.show_form = "Income"
        if c2.button("👷"): st.session_state.show_form = "Labor"
        if c3.button("🏗️"): st.session_state.show_form = "Material"
        
        if "show_form" in st.session_state:
            form_type = st.session_state.show_form
            with st.expander(f"New {form_type} Entry", expanded=True):
                with st.form("sidebar_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name/Desc")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    
                    if st.form_submit_button("Save"):
                        payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()
            if st.button("❌ Close"):
                st.session_state.pop("show_form")
                st.rerun()

    st.divider()
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF4B4B; color: #1E1E1E;">
            <h4 style="margin: 0; color: #FF4B4B; font-size: 16px;">📍 Current Project</h4>
            <p style="margin: 5px 0; font-size: 13px;"><b>Location:</b> Yousaf Colony</p>
        </div>
    """, unsafe_allow_html=True)
    
    if is_auth:
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # --- HEADER ---
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""
            <div style="text-align: center; background-color: #1E1E1E; padding: 15px; border-radius: 15px;">
                <h2 style="color: #FF4B4B; margin: 0;">DEEWARY.COM</h2>
                <p style="color: white; font-size: 12px; margin: 0;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("##")

    # --- PROGRESS SECTION ---
    st.markdown("<h3 style='color: #FF4B4B;'>🏗️ Project Work Progress</h3>", unsafe_allow_html=True)
    status_df = fetch_project_status()
    t_col1, t_col2 = st.columns(2)
    for idx, row in status_df.iterrows():
        target_col = t_col1 if idx % 2 == 0 else t_col2
        with target_col:
            is_done = row["status"] == "Done"
            bg = "#d4edda" if is_done else "#f8d7da"
            icon = "✅" if is_done else "⏳"
            st.markdown(f"<div style='background-color: {bg}; padding: 10px; border-radius: 8px; margin-bottom: 8px; border: 1px solid gray;'><b>{icon} {row['task_name']}</b></div>", unsafe_allow_html=True)

    if is_auth:
        with st.expander("🛠️ Admin: Update Work Status"):
            c_task = st.selectbox("Task", status_df['task_name'].tolist())
            c_status = st.radio("Status", ["Pending", "Done"], horizontal=True)
            if st.button("Update Status"):
                supabase.table('project_status').upsert({"task_name": c_task, "status": c_status}).execute()
                st.cache_data.clear()
                st.rerun()

    st.divider()

    # --- ANALYTICS SECTION ---
    st.markdown("<h4 style='text-align: center;'>Capital Flow Analytics</h4>", unsafe_allow_html=True)
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
    st.caption(f"© {datetime.now().year} Deewary.com | Management Portal")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()
        
        search = st.text_input("🔍 Search...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]
            
        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.2f}**")

        if is_auth:
            st.divider()
            target_id = st.text_input("Enter Row ID to Edit/Delete")
            if target_id:
                if st.button("🗑️ Delete"):
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.rerun()
        
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Excel", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No records found.")
