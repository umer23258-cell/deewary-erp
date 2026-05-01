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

# --- 4. SIDEBAR MENU & PROJECT INFO ---
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
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF4B4B; color: #1E1E1E;">
            <h4 style="margin: 0; color: #FF4B4B; font-size: 16px;">📍 Current Project</h4>
            <p style="margin: 5px 0; font-size: 13px;"><b>Location:</b> Yousaf Colony</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Size:</b> 5 Marla</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Structure:</b> 2.5 Story</p>
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

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # --- HEADER SECTION ---
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1:
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""
            <div style="text-align: center; margin-top: 5px; background-color: #1E1E1E; padding: 15px; border-radius: 15px; border: 1px solid #333;">
                <h2 style="font-family: 'Arial Black', sans-serif; font-size: 28px; letter-spacing: 4px; color: #FF4B4B; text-transform: uppercase; margin: 0;">
                    DEEWARY.COM
                </h2>
                <hr style="width: 15%; margin: 8px auto; border: 1px solid #FF4B4B;">
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 12px; color: #FFFFFF; letter-spacing: 2px; margin-bottom: 5px; font-weight: 500;">
                    REAL ESTATE & CONSTRUCTION MANAGEMENT
                </p>
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #FF4B4B; font-weight: 700; margin: 0;">
                    C.E.O: SARDAR SAMI ULLAH
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("##")
    st.markdown("<h4 style='text-align: center; color: #444; font-size: 18px;'>Capital Flow Analytics</h4>", unsafe_allow_html=True)
    
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
    
    # --- QUICK ACTIONS ---
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    if "show_form" in st.session_state:
        if is_auth:
            # (Form logic remains same as previous version)
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Name / Description", defaults["name"])
                    d_amt = st.number_input("Amount", min_value=0.0, value=defaults["amount"])
                    d_det = st.text_area("Details", defaults["detail"])
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()
            if st.button("❌ Close"):
                st.session_state.pop("show_form")
                st.rerun()
        else: st.warning("Admin unlock required.")

    # --- 🟢 OUR COMPLETED PROJECTS SECTION ---
    st.write("##")
    st.divider()
    st.subheader("🏘️ Our Completed Projects")
    
    proj_col1, proj_col2 = st.columns([1.5, 1])
    
    with proj_col1:
        st.video("https://youtu.be/AiA4PkXturU")
        st.caption("Video Tour: Modern House Design by Deewary.com")

    with proj_col2:
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border: 1px solid #ddd;">
                <h4 style="color: #FF4B4B; margin-top: 0;">🏡 Latest Handover</h4>
                <p style="font-size: 14px; color: #333;">Hamara haaliya mukammal shuda project jo modern aesthetics aur quality ka munta hazir namuna hai.</p>
                <ul style="font-size: 13px; color: #555;">
                    <li>High-end Finishing</li>
                    <li>Modern Interior Layout</li>
                    <li>Structural Integrity Certified</li>
                </ul>
                <a href="https://youtu.be/AiA4PkXturU" target="_blank" style="background-color: #FF0000; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px;">
                    ▶️ Watch on YouTube
                </a>
            </div>
        """, unsafe_allow_html=True)

    # --- ABOUT & SUPPORT ---
    st.write("##")
    st.divider()
    st.subheader("🏢 About Deewary.com")
    about_col1, about_col2 = st.columns([1.5, 1])
    with about_col1:
        st.markdown("**Deewary.com** aik premium Real Estate aur Construction firm hai.")
    with about_col2:
        st.markdown('<div style="background-color: #1E1E1E; padding: 15px; border-radius: 12px; color: white;">🚀 <b>Our Vision:</b> Behtareen tameerati kaam.</div>', unsafe_allow_html=True)

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Management Portal")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    # (History page logic remains same as previous version)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
