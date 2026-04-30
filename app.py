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

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.title("🏗️ ERP PANEL")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    # Sidebar image
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.divider()
    is_auth = check_password()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # --- HEADER SECTION (Logo Left, Text Mid) ---
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])
    
    with header_col1:
        # Logo side par
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=100)

    with header_col2:
        # Title chota aur mid mein
        st.markdown("""
            <div style="text-align: center; margin-top: -10px;">
                <h2 style="font-family: 'Arial', sans-serif; font-size: 38px; letter-spacing: 6px; color: #FF4B4B; text-transform: uppercase; margin-bottom: 0px;">
                    DEEWARY.COM
                </h2>
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #666; letter-spacing: 2px; margin-top: 5px;">
                    REAL ESTATE & CONSTRUCTION MANAGEMENT
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("<h4 style='text-align: center; color: #444;'>Capital Flow Summary</h4>", unsafe_allow_html=True)
    
    # --- METRICS SECTION (Amounts Choti ki hain) ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    # Custom CSS for smaller metrics
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 24px !important;
            font-weight: bold;
        }
        [data-testid="stMetricLabel"] {
            font-size: 14px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Total Income", f"PKR {inc:,.0f}")
    m_col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    m_col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # --- QUICK ACTIONS ---
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

    # (Form Logic remains same as previous code)
    if "show_form" in st.session_state:
        if is_auth:
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            # Form setup code...
            with st.expander(f"Entry Form: {st.session_state.show_form}", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Name / Description", defaults["name"])
                    d_amt = st.number_input("Amount", min_value=0.0, value=defaults["amount"])
                    d_det = st.text_area("Details", defaults["detail"])
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        col_a, col_b, col_c = st.columns(3)
                        d_occ = col_a.text_input("Occupation", defaults["occ"])
                        d_rec = col_b.text_input("Received By", defaults["rec"])
                        d_meth = col_c.selectbox("Method", ["Cash", "Online"])

                    if st.form_submit_button("Save Record"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        try:
                            supabase.table('transactions').insert(payload).execute()
                            st.cache_data.clear()
                            st.session_state.pop("show_form")
                            st.success("Synced!")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
            if st.button("❌ Close"):
                st.session_state.pop("show_form")
                st.rerun()

    # --- FOOTER & ABOUT ---
    st.write("##")
    st.divider()
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        st.caption(f"© {datetime.now().year} Deewary.com | Enterprise Resource Planning System")
    with f_col2:
        whatsapp_url = "https://wa.me/923115190118"
        st.markdown(f'<a href="{whatsapp_url}" style="color: #25D366; text-decoration: none; font-weight: bold; font-size: 12px;">💬 Support Representative</a>', unsafe_allow_html=True)

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filter logic remains same...
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()
        
        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.0f}**")
