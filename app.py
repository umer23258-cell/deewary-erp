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

# --- CUSTOM CSS (Original Style) ---
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

# --- 4. SIDEBAR & MENU ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    is_auth = check_password()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="header-box"><h1 style="color:#FF4B4B;">DEEWARY.COM</h1><p style="color:white;">C.E.O: SARDAR SAMI ULLAH</p></div>', unsafe_allow_html=True)

    # Metrics
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
    m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

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
                # Photo section - Mandatory for Material
                photo_data = None
                if ftype == "Material":
                    st.write("📸 **Attach Bill (Photo)**")
                    cam = st.camera_input("Take Picture")
                    up = st.file_uploader("Upload Image", type=['jpg','png','jpeg'])
                    photo_data = cam if cam else up

                with st.form("entry_form", clear_on_submit=True):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title/Party Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if ftype in ["Income", "Labor"]:
                        d_occ = st.text_input("Occupation")
                        d_meth = st.selectbox("Method", ["Cash", "Online", "Cheque"])
                        d_rec = st.text_input("Authorized By")
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("SUBMIT"):
                        bill_url = ""
                        # Image Upload Logic
                        if photo_data:
                            try:
                                f_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                                supabase.storage.from_('bill_images').upload(f"bills/{f_name}", photo_data.getvalue())
                                bill_url = supabase.storage.from_('bill_images').get_public_url(f"bills/{f_name}")
                            except:
                                st.warning("Note: Photo could not be uploaded. Saving data without photo.")

                        payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth, "bill_url": bill_url}
                        supabase.table('transactions').insert(payload).execute()
                        st.success("Data Saved!")
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()
        else: st.warning("Please Login as Admin")

# --- 6. HISTORY ---
else:
    st.title(menu)
    if not df.empty:
        f_df = df[df['type'] == menu.split()[1]] if "History" in menu else df
        search = st.text_input("🔎 Search...")
        if search:
            f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(f_df, use_container_width=True)

        if "Material" in menu:
            st.divider()
            st.subheader("🖼️ View Bill Photo")
            bills = f_df[f_df['bill_url'].notna() & (f_df['bill_url'] != "")]
            if not bills.empty:
                s_id = st.selectbox("Select ID to View Photo", bills['id'].tolist())
                path = bills[bills['id'] == s_id]['bill_url'].values[0]
                st.image(path, width=400)
    else: st.warning("No data found.")
