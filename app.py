import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
from fpdf import FPDF

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS ---
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

# --- NEW: FUNCTION TO REMOVE EMOJIS (Prevents PDF Error) ---
def clean_text(text):
    return "".join(c for c in str(text) if ord(c) < 128)

# --- PDF GENERATOR LOGIC (UPDATED) ---
def export_to_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    
    # Title (Cleaning emoji from title)
    pdf.set_font("Arial", "B", 16)
    clean_title = clean_text(title)
    pdf.cell(190, 10, f"Deewary.com - {clean_title}", ln=True, align="C")
    
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 10, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # Header
    pdf.set_font("Arial", "B", 10)
    cols = ["date", "name", "amount", "type"]
    for col in cols:
        pdf.cell(47, 10, col.capitalize(), border=1, align="C")
    pdf.ln()
    
    # Data rows (Cleaning emojis from data)
    pdf.set_font("Arial", "", 9)
    for i, row in df.iterrows():
        pdf.cell(47, 10, clean_text(row['date']), border=1)
        pdf.cell(47, 10, clean_text(row['name'])[:20], border=1)
        pdf.cell(47, 10, f"{row['amount']:,.0f}", border=1)
        pdf.cell(47, 10, clean_text(row['type']), border=1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
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

    st.write("##")
    status_df = fetch_project_status()
    
    st.markdown("### 🏗️ Construction Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
            st.markdown(f"<div style='background:{bg}; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #ddd;'><strong>{icon} {row['task_name']}</strong><br><small>{row['status']}</small></div>", unsafe_allow_html=True)

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com Portal | Smart Management")

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
        st.metric("Total PKR", f"{f_df['amount'].sum():,.0f}")

        # DOWNLOAD SECTION
        st.divider()
        col_down1, col_down2 = st.columns(2)
        
        # 1. EXCEL DOWNLOAD
        excel_buf = io.BytesIO()
        f_df.to_excel(excel_buf, index=False)
        col_down1.download_button("📥 Download Excel", excel_buf.getvalue(), f"{menu}.xlsx")

        # 2. PROPER PDF DOWNLOAD (CLEANED)
        try:
            pdf_bytes = export_to_pdf(f_df, menu)
            col_down2.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"{menu}_Report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            col_down2.error(f"PDF Error: {e}")

    else:
        st.warning("No data found.")
