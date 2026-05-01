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
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            with st.expander(f"New {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Name / Description")
                    d_amt = st.number_input("Amount", min_value=0.0)
                    d_det = st.text_area("Details")
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det}
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.pop("show_form")
                        st.rerun()
            if st.button("❌ Close Form"):
                st.session_state.pop("show_form")
                st.rerun()

    # --- 🟢 OUR COMPLETED PROJECTS (Video Choti kar di hai) ---
    st.write("##")
    st.divider()
    st.markdown("<h3 style='color: #FF4B4B;'>🏘️ Portfolio Highlight</h3>", unsafe_allow_html=True)
    
    proj_col1, proj_col2 = st.columns([1, 1.2]) # Adjusted ratio to make video smaller
    with proj_col1:
        # Small YouTube Video Container
        st.video("https://youtu.be/AiA4PkXturU")
        st.caption("Latest Project: Premium Finish House")

    with proj_col2:
        st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #ddd;">
                <h4 style="color: #1E1E1E; margin-top: 0;">🏡 Modern Architecture Design</h4>
                <p style="font-size: 14px; color: #444; line-height: 1.5;">
                    Hamara ye project modern aesthetics aur structural durability ka behtareen imtizaaj hai. 
                    Deewary.com har tameer mein quality ko yaqeeni banata hai.
                </p>
                <a href="https://youtu.be/AiA4PkXturU" target="_blank" style="background-color: #FF0000; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;">
                    ▶️ Watch Tour on YouTube
                </a>
            </div>
        """, unsafe_allow_html=True)

    # --- 🟢 ABOUT DEEWARY.COM & VISION (Professional Detail) ---
    st.write("##")
    st.divider()
    
    about_col1, about_col2 = st.columns([1.6, 1])
    
    with about_col1:
        st.subheader("🏢 About Deewary.com")
        st.markdown("""
        **Deewary.com** Pakistan ki construction aur real estate industry mein aik premium aur barosa-mand naam hai. Hum sirf imaraten tameer nahi karte, balkay hum aap ke khuwabon ko aik mazboot aur jadeed shakal dete hain. Islamabad aur Rawalpindi mein kae kamyab projects ke baad, hamari pehchan hamara **A+ Quality Standard** aur **Digital Transparency** ban chuki hai.

        **Key Services:**
        *   **Turnkey Construction:** Design se le kar handover tak mukammal zimadari.
        *   **Architectural Excellence:** Modern lifestyle ke mutabiq hawa-dar aur functional layouts.
        *   **Material Integrity:** Har project mein sirf certified aur premium brands ka istemal.
        *   **Investment Guidance:** Property investment mein behtareen returns ke liye expert advice.
        """)

    with about_col2:
        st.markdown("""
        <div style="background-color: #1E1E1E; padding: 25px; border-radius: 20px; color: white; border: 2px solid #FF4B4B; box-shadow: 0px 8px 15px rgba(0,0,0,0.3);">
            <h3 style="margin-top: 0; color: #FF4B4B; font-size: 22px;">🚀 Our Vision</h3>
            <p style="font-size: 14px; line-height: 1.6; font-style: italic;">
                "Hamara maqsad Pakistan ki construction industry mein technology aur imandari ka naya mayar qaim karna hai. Hum chahte hain ke har client ko digital transparency ke sath apne ghar ki tameer ka sukoon mile."
            </p>
            <hr style="border: 0.5px solid #444;">
            <p style="font-size: 12px; color: #AAA; text-align: center;">
                <b>Values:</b> Transparency | Durability | Innovation
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- 🟢 SUPPORT & WHATSAPP ---
    st.write("##")
    st.divider()
    supp_col1, supp_col2 = st.columns([2, 1])
    with supp_col1:
        st.subheader("🖥️ ERP Digital Portal")
        st.info("Yeh portal Deewary.com ki digital transparency ka saboot hai, jahan har kharch aur material ka record real-time update kiya jata hai.")
    with supp_col2:
        st.subheader("🛠️ System Support")
        whatsapp_url = "https://wa.me/923115190118"
        st.markdown(f"""
            <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: black; padding: 12px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; border: 1px solid #128C7E;">
                💬 WhatsApp Support
            </a>
            <p style="font-size: 11px; text-align: center; margin-top: 8px; color: #666;">Developer: umer sherin | Status: Active ✅</p>
        """, unsafe_allow_html=True)

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
        
        search = st.text_input("🔍 Search data...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]
            
        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.2f}**")
        
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No records found.")
