import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
import base64

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (Bilkul Aapke Wala) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 30px;
        border-radius: 20px;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 25px;
    }
    .task-card {
        background: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3.5em; }
        h2 { font-size: 1.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing/Grinding", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong password!")
    return False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Mode")
        if st.button("⚙️ Change Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px;">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px; font-size: 12px; margin-bottom: 10px;">PREMIUM CONSTRUCTION MANAGEMENT</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
    m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

    # --- Update Status Form ---
    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        status_df = fetch_project_status()
        with st.expander("🛠️ Admin: Update Site Status", expanded=True):
            with st.form("status_form"):
                task = st.selectbox("Select Project Task", status_df['task_name'].tolist())
                stat = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Status"):
                    supabase.table('project_status').upsert({"task_name": task, "status": stat}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    status_df = fetch_project_status()
    st.markdown("### 🏗️ Construction Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
            st.markdown(f"<div style='background:{bg}; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #ddd;'><strong>{icon} {row['task_name']}</strong><br><small>{row['status']}</small></div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("⚡ Quick Transactions")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("quick_form", clear_on_submit=True):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title")
                    d_amt = st.number_input("Amount", min_value=0)
                    
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    
                    if ftype in ["Income", "Labor"]:
                        c_a, c_b = st.columns(2)
                        d_occ = c_a.text_input("Occupation")
                        d_meth = c_a.selectbox("Method", ["Cash", "Online", "Cheque"])
                        d_rec = c_b.text_input("Authorized By")
                    
                    # Photo Feature for Material
                    photo_data = None
                    if ftype == "Material":
                        st.write("📷 **Take Bill Picture or Upload:**")
                        cam_photo = st.camera_input("Camera Snap")
                        file_photo = st.file_uploader("Upload from Gallery", type=["jpg", "png", "jpeg"])
                        if cam_photo: photo_data = cam_photo.getvalue()
                        elif file_photo: photo_data = file_photo.getvalue()

                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit"):
                        bill_url = ""
                        if photo_data:
                            try:
                                f_name = f"bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                                f_path = f"bills/{f_name}"
                                supabase.storage.from_('bill_images').upload(f_path, photo_data, {"content-type": "image/jpeg"})
                                bill_url = supabase.storage.from_('bill_images').get_public_url(f_path)
                            except Exception as e:
                                st.error(f"Image Error: {e}")

                        payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth, "bill_url": bill_url}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Please login as Admin to add data.")

    st.divider()
    st.markdown("### 🏘️ Showcase Project")
    v1, v2 = st.columns([1, 1])
    with v1: st.video("https://youtu.be/AiA4PkXturU")
    with v2: st.info("Hamara ye project modern aesthetics aur structural durability ka behtareen namuna hai.")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        st.dataframe(f_df, use_container_width=True)

        if "Material" in menu and "bill_url" in f_df.columns:
            st.subheader("🖼️ View Bill Photos")
            valid_bills = f_df[f_df['bill_url'].notna() & (f_df['bill_url'].str.strip() != "")]
            if not valid_bills.empty:
                s_id = st.selectbox("Select ID", valid_bills['id'].tolist())
                path = valid_bills[valid_bills['id'] == s_id]['bill_url'].values[0]
                if path and str(path).startswith("http"): st.image(path, width=400)
    else:
        st.warning("No data found.")
