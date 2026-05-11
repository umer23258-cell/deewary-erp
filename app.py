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

# --- CUSTOM CSS FOR INTERFACE ---
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
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title/Party Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    
                    # Image Handling for Material
                    bill_img_data = None
                    if ftype == "Material":
                        st.write("📷 **Bill Photo (Select One Option)**")
                        photo_option = st.radio("How to add bill?", ["No Photo", "Camera", "Gallery"], horizontal=True)
                        if photo_option == "Camera":
                            bill_img_data = st.camera_input("Take Bill Photo")
                        elif photo_option == "Gallery":
                            bill_img_data = st.file_uploader("Upload Bill Image", type=["jpg", "png", "jpeg"])

                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if ftype in ["Income", "Labor"]:
                        c_a, c_b = st.columns(2)
                        d_occ = c_a.text_input("Occupation")
                        d_meth = c_a.selectbox("Method", ["Cash", "Online", "Cheque"])
                        d_rec = c_b.text_input("Authorized By")
                    
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit Transaction"):
                        bill_url = ""
                        # Upload Image if exists
                        if bill_img_data:
                            try:
                                file_name = f"bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                                file_path = f"bills/{file_name}"
                                supabase.storage.from_('bill_images').upload(file_path, bill_img_data.getvalue(), {"content-type": "image/jpeg"})
                                bill_url = supabase.storage.from_('bill_images').get_public_url(file_path)
                            except Exception as e:
                                st.warning(f"Image upload failed: {e}")

                        payload = {
                            "date": str(d_date), "type": ftype, "name": d_name, 
                            "amount": d_amt, "detail": d_det, "occupation": d_occ, 
                            "received_by": d_rec, "pay_method": d_meth, "bill_url": bill_url
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Please login as Admin to add data.")

    # Status Cards (Simplified for space)
    st.divider()
    status_df = fetch_project_status()
    st.markdown("### 🏗️ Construction Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
            st.markdown(f"<div style='background:{bg}; padding:10px; border-radius:10px; margin-bottom:5px; border:1px solid #ddd;'><strong>{row['task_name']}</strong> ({row['status']})</div>", unsafe_allow_html=True)

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        search = st.text_input("🔎 Filter results...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        st.dataframe(f_df, use_container_width=True)
        
        # --- ID SEARCH FOR BILL PREVIEW ---
        if "Material" in menu:
            st.divider()
            st.subheader("🔍 View Bill by ID")
            bill_id = st.text_input("Enter Transaction ID to see Bill Photo")
            if bill_id:
                try:
                    target_row = f_df[f_df['id'].astype(str) == bill_id]
                    if not target_row.empty:
                        img_url = target_row['bill_url'].values[0]
                        if img_url:
                            st.image(img_url, caption=f"Bill for ID: {bill_id}", width=500)
                        else:
                            st.info("Is transaction ka bill upload nahi kiya gaya.")
                    else:
                        st.error("ID nahi mili.")
                except: pass

        total_val = f_df['amount'].sum()
        st.metric(f"Total Amount", f"PKR {total_val:,.0f}")

        # DOWNLOAD SECTION (Bilkul Aapke Wala)
        st.divider()
        col_down1, col_down2 = st.columns(2)
        buf = io.BytesIO()
        f_df.to_excel(buf, index=False)
        col_down1.download_button("📥 Download Excel", buf.getvalue(), f"{menu}.xlsx")

        report_html = f"<html><body><h1>{menu} Report</h1>{f_df.to_html(index=False)}</body></html>"
        b64 = base64.b64encode(report_html.encode()).decode()
        pdf_href = f'<a href="data:text/html;base64,{b64}" download="{menu}_Report.html" style="text-decoration:none;"><button style="width:100%; background-color:#FF4B4B; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer; font-weight:bold;">📄 Download Report</button></a>'
        col_down2.markdown(pdf_href, unsafe_allow_html=True)

    else:
        st.warning("No data found.")
