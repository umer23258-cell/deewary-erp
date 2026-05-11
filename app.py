import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS (0% Change) ---
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
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3.5em; }
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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
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
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="header-box"><h1 style="color: #FF4B4B; margin: 0;">DEEWARY.COM</h1><p style="color: white;">C.E.O: SARDAR SAMI ULLAH</p></div>', unsafe_allow_html=True)

    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
    m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

    # Progress section
    status_df = fetch_project_status()
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / len(status_df)) * 100) if len(status_df) > 0 else 0
    st.write(f"### 📈 Progress: {prog_val}%")
    st.progress(prog_val / 100)

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
                # Image Upload only for Material
                img_file = None
                if ftype == "Material":
                    img_file = st.file_uploader("Upload Bill/Material Photo", type=['jpg', 'png', 'jpeg'])

                with st.form("entry_form", clear_on_submit=True):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title/Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit"):
                        final_url = ""
                        if img_file:
                            try:
                                f_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{img_file.name}"
                                supabase.storage.from_('bill_images').upload(f_name, img_file.getvalue())
                                final_url = supabase.storage.from_('bill_images').get_public_url(f_name)
                            except: st.error("Storage Error: Check bucket settings.")

                        payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "bill_url": final_url}
                        supabase.table('transactions').insert(payload).execute()
                        st.success("Saved!")
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Login as Admin.")

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# --- 6. HISTORY & SEARCH ---
else:
    st.title(menu)
    if not df.empty:
        # Filter logic
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        search = st.text_input("🔎 Search by ID, Name or Detail...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]

        st.dataframe(f_df, use_container_width=True)

        # Show Photo if searched/selected
        if not f_df.empty:
            st.divider()
            # Select ID to view details/image
            selected_id = st.selectbox("Select Transaction ID to view details/image", f_df['id'].tolist())
            row = f_df[f_df['id'] == selected_id].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {row['name']}")
                st.write(f"**Amount:** PKR {row['amount']:,.0f}")
                st.write(f"**Notes:** {row['detail']}")
            
            with col2:
                if 'bill_url' in row and row['bill_url']:
                    st.image(row['bill_url'], caption="Bill Photo", width=400)
                else:
                    st.info("No photo attached to this record.")

        # Excel Download
        buf = io.BytesIO()
        f_df.to_excel(buf, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")
