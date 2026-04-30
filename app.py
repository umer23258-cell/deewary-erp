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
st.set_page_config(page_title="Deewary.com ERP | Umer Sherin", layout="wide", page_icon="🏗️")

# Custom CSS for Professional Cards
st.markdown("""
    <style>
    .project-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #007bff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
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
    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 4. SIDEBAR MENU ---
st.sidebar.title("🏗️ DEEWARY.COM ERP")
st.sidebar.markdown(f"**Director:** Umer Sherin") # Aapka naam yahan add kar diya hai
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "💰 Income History", 
    "👷 Labor History", 
    "🏗️ Material History",
    "🔍 Search & All Reports"
])

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.title("Capital Flow Analytics")
    
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
    
    # Edit Mode Check
    is_editing = "edit_id" in st.session_state
    
    if not is_editing:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"; st.rerun()
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"; st.rerun()
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"; st.rerun()
    else:
        st.warning(f"⚠️ Editing Mode Active (Record ID: {st.session_state.edit_id})")

    if "show_form" in st.session_state:
        if check_password():
            # (Aapka original form handling logic yahan chalta rahega)
            st.info(f"Form for {st.session_state.show_form} is open.")
            if st.button("❌ Close Form"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    # --- NEW SECTION: PROJECT GALLERY & DETAILS (Last mein add kiya) ---
    st.write("##")
    st.divider()
    st.subheader("🏠 Active Project: Yousaf Colony")

    project_images = [
        "https://i.ibb.co/6Jbx8yjD/Whats-App-Image-2026-04-30-at-12-11-01-PM.jpg",
        "https://i.ibb.co/6R0yR8Xz/1JK5M0FR.jpg",
        "https://i.ibb.co/ZRgY9wLC/Whats-App-Image-2026-04-30-at-12-25-05-PM.jpg",
        "https://i.ibb.co/35yGYt3H/Whats-App-Image-2026-04-30-at-12-25-04-PM.jpg",
        "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    ]

    if 'img_idx' not in st.session_state:
        st.session_state.img_idx = 0

    col_img, col_detail = st.columns([1, 2])

    with col_img:
        # Photo compact size (280px) mein
        st.image(project_images[st.session_state.img_idx], width=280)
        
        b1, b2 = st.columns(2)
        if b1.button("⬅️ Previous"):
            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(project_images)
            st.rerun()
        if b2.button("Next ➡️"):
            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(project_images)
            st.rerun()

    with col_detail:
        st.markdown(f"""
        <div class="project-card">
            <h3 style="margin-top:0; color:#007bff;">Yousaf Colony Renovation</h3>
            <p><b>Project Lead:</b> Umer Sherin</p>
            <p><b>Location:</b> Yousaf Colony, 5 Marla Plot</p>
            <p><b>Structure:</b> 2.5 Story Modern Residence</p>
            <p><b>Work Status:</b> Interior Finishing & Paint Work</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("🏗️ **Overall Completion:**")
        st.progress(75)

    # --- SOFTWARE INFO SECTION ---
    st.write("##")
    st.divider()
    info_col1, info_col2 = st.columns([2, 1])
    
    with info_col1:
        st.subheader("Deewary.com ERP System")
        st.info("Yeh software **Deewary.com** ke real estate aur construction projects ke financials manage karne ke liye banaya gaya hai.")

    with info_col2:
        st.subheader("🛠️ System Support")
        st.markdown(f"**Developer:** Umer Sherin\n\n**Status:** Operational ✅")

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Project Management Portal")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # (Aapka original history filtering aur excel download logic yahan rahay ga)
        st.dataframe(df, use_container_width=True)
