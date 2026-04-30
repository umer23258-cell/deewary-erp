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

# --- 3. PREMIUM BRANDING & LOGO HEADER ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');

    /* Main Branding Header */
    .branding-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 35px;
        border: 1px solid #e2e8f0;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.05);
    }
    
    .logo-img {
        width: 100px;
        margin-bottom: 15px;
    }

    .branding-card h1 {
        color: #1E3A8A !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 48px !important;
        font-weight: 800 !important;
        margin: 0;
        letter-spacing: -1px;
        text-transform: uppercase;
    }
    .branding-card p {
        color: #B8860B !important; /* Golden Color */
        font-family: 'Playfair Display', serif !important;
        font-size: 22px !important;
        margin-top: -5px;
        font-weight: 600;
        font-style: italic;
    }
    
    /* Global Styles */
    .stMetric {
        background: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #edf2f7;
    }
    </style>
    
    <div class="branding-card">
        <!-- Logo Placeholder: Aap apna logo URL yahan paste kar sakte hain -->
        <img src="https://cdn-icons-png.flaticon.com/512/3061/3061184.png" class="logo-img">
        <h1>DEEWARY.COM</h1>
        <p>Real Estate & Construction Company</p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. FUNCTIONS ---
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

# --- 5. SIDEBAR MENU & PROJECT INFO ---
with st.sidebar:
    st.markdown("<h2 style='color:#1E3A8A; font-family:Montserrat;'>🏗️ ERP PANEL</h2>", unsafe_allow_html=True)
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 15px; border-radius: 12px; color: white;">
            <h4 style="margin: 0; color: #FFD700; font-size: 16px; font-family:Montserrat;">📍 Current Project</h4>
            <p style="margin: 8px 0 0 0; font-size: 13px;"><b>Site:</b> Yousaf Colony</p>
            <p style="margin: 3px 0; font-size: 13px;"><b>Area:</b> 5 Marla (2.5 Story)</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 6. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.markdown("<h3 style='font-family:Montserrat; color:#334155;'>Financial Overview</h3>", unsafe_allow_html=True)
    
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
    
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("Manage Transactions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    if "show_form" in st.session_state:
        if is_auth:
            # Form Logic (Wahi same logic jo aapne di thi)
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Name / Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        ca, cb, cc = st.columns(3)
                        d_occ = ca.text_input("Occupation")
                        d_rec = cb.text_input("Received By")
                        d_meth = cc.selectbox("Method", ["Cash", "Online"])

                    if st.form_submit_button("Sync to Cloud"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.success("Record Saved!")
                        st.rerun()
            if st.button("❌ Close Form"):
                st.session_state.pop("show_form")
                st.rerun()

# --- 7. HISTORY PAGES ---
else:
    st.markdown(f"<h2 style='font-family:Montserrat; color:#1E3A8A;'>{menu}</h2>", unsafe_allow_html=True)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()
        
        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total Category Flow: PKR {filtered_df['amount'].sum():,.2f}**")
        
        buffer = io.BytesIO(); filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Export to Excel", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")

# WhatsApp Button Global Style
whatsapp_url = "https://wa.me/923115190118"
st.sidebar.markdown(f"""
<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
    <div style="background-color:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; margin-top:20px;">
        💬 WhatsApp Support
    </div>
</a>
""", unsafe_allow_html=True)
