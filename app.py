import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
from fpdf import FPDF  # <--- Nayi library

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

# PDF GENERATOR FUNCTION
def generate_pdf(dataframe, report_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "DEEWARY.COM - Construction Report", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Report: {report_name} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(255, 75, 75)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 10)
    headers = ["Date", "Name", "Amount", "Type"]
    for h in headers:
        pdf.cell(45, 10, h, 1, 0, 'C', True)
    pdf.ln()

    # Table Data
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 9)
    for _, row in dataframe.iterrows():
        pdf.cell(45, 10, str(row['date']), 1)
        pdf.cell(45, 10, str(row['name'])[:20], 1)
        pdf.cell(45, 10, f"{row['amount']:,.0f}", 1)
        pdf.cell(45, 10, str(row['type']), 1)
        pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"Total: PKR {dataframe['amount'].sum():,.0f}", 0, 1, 'R')
    return pdf.output(dest='S')

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
    is_auth = check_password()
    if is_auth: st.success("🔓 Admin Mode")
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black';">DEEWARY.COM</h1>
            <p style="color: white;">PREMIUM CONSTRUCTION MANAGEMENT</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold;">C.E.O: SARDAR SAMI ULLAH</div>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
        m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
        m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

    # Progress Section
    status_df = fetch_project_status()
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog = int((done_tasks / len(status_df)) * 100) if len(status_df) > 0 else 0
    st.write(f"### 📈 Progress: {prog}%")
    st.progress(prog / 100)

    # Quick Actions (Inputs)
    st.subheader("⚡ Quick Entry")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.expander(f"Add {ftype}", expanded=True):
            with st.form("entry_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Name/Item")
                d_amt = st.number_input("Amount", min_value=0)
                if st.form_submit_button("Save"):
                    payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

# --- 6. HISTORY & PDF DOWNLOAD ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        st.dataframe(f_df, use_container_width=True)
        
        c1, c2 = st.columns(2)
        # Excel Button
        buf = io.BytesIO()
        f_df.to_excel(buf, index=False)
        c1.download_button("📥 Download Excel", buf.getvalue(), "Report.xlsx")
        
        # PDF Button
        pdf_bytes = generate_pdf(f_df, menu)
        c2.download_button("📄 Download PDF Report", data=pdf_bytes, file_name=f"Deewary_{menu}.pdf", mime="application/pdf")
    else:
        st.warning("No records found.")
