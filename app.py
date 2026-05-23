import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components

# PDF ke liye libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PDF GENERATION FUNCTION (Full Table View) ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"<font color='#FF4B4B' size=18><b>{title}</b></font>", styles['Title']))
    elements.append(Paragraph(f"Deewary.com ERP - Full System Report", styles['Normal']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 15))

    pdf_df = dataframe.copy()
    data = [["ID", "Date", "Item/Name", "Amount", "Detail", "Occupation", "Rec. By", "Method"]]
    
    for _, row in pdf_df.iterrows():
        data.append([
            str(row.get('id', '')),
            str(row.get('date', '')),
            str(row.get('name', '')),
            f"{row.get('amount', 0):,.0f}",
            str(row.get('detail', ''))[:30] + "..." if len(str(row.get('detail', ''))) > 30 else str(row.get('detail', '')),
            str(row.get('occupation', '')),
            str(row.get('received_by', '')),
            str(row.get('pay_method', ''))
        ])
    
    total_val = pdf_df['amount'].sum()
    data.append(["", "", "TOTAL", f"{total_val:,.0f}", "", "", "", ""])

    t = Table(data, colWidths=[40, 70, 110, 80, 150, 90, 90, 70])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1e1e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FF4B4B")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])
    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    buf.seek(0)
    return buf

# --- 3. PAGE CONFIG ---
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
    .kpi-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #FF4B4B;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .alert-box {
        background-color: #ffebee;
        border-left: 6px solid #c62828;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #c62828;
        font-weight: bold;
    }
    .forecast-box {
        background-color: #e8f5e9;
        border-left: 6px solid #2e7d32;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #2e7d32;
        font-weight: bold;
    }
    
    /* VIP DIGITAL RECEIPT VOUCHER STYLING */
    .digital-voucher {
        background-color: #fefefe;
        border: 2px dashed #94a3b8;
        padding: 25px;
        border-radius: 15px;
        max-width: 550px;
        margin: 15px auto;
        font-family: 'Courier New', Courier, monospace;
        color: #1e2937;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    .voucher-header { text-align: center; border-bottom: 2px dashed #cbd5e1; padding-bottom: 12px; margin-bottom: 15px; }
    .voucher-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
    .voucher-total { font-size: 20px; font-weight: bold; color: #FF4B4B; border-top: 2px dashed #cbd5e1; border-bottom: 2px dashed #cbd5e1; padding: 8px 0; margin-top: 15px; }
    
    .sidebar-btn-container { margin-bottom: 10px; }
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3.5em; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
    return False

@st.cache_data(ttl=30)
def fetch_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

# --- HELPER FUNCTION FOR WHATSAPP LINK GENERATION ---
def generate_whatsapp_link(type_tx, name, amount, detail):
    base_msg = f"🏗️ *Deewary.com ERP Notification*\n\n"
    base_msg += f"• *Type:* {type_tx}\n"
    base_msg += f"• *Name/Item:* {name}\n"
    base_msg += f"• *Amount:* PKR {amount:,.0f}\n"
    if detail:
        base_msg += f"• *Details:* {detail}\n"
    base_msg += f"\n_System generated tracking logs summary entry._"
    encoded_text = urllib.parse.quote(base_msg)
    return f"https://api.whatsapp.com/send?text={encoded_text}"


# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
        st.write("### ⚡ Quick Actions")
        if st.button("➕ Income", use_container_width=True): st.session_state.show_form = "Income"
        if st.button("👷 Labor", use_container_width=True): st.session_state.show_form = "Labor"
        if st.button("🏗️ Material", use_container_width=True): st.session_state.show_form = "Material"
        if st.button("📝 Register New Labor Profile", use_container_width=True): st.session_state.show_form = "RegisterLabor"
        st.divider()
        if st.button("⚙️ Change Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 6. DASHBOARD INTERFACE ---
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
        lab_exp = df[df['type'] == 'Labor']['amount'].sum()
        mat_exp = df[df['type'] == 'Material']['amount'].sum()
        exp = lab_exp + mat_exp
        net_bal = inc - exp
        
        # --- CASH FLOW FORECAST & ALERTS ---
        try:
            df['date_parsed'] = pd.to_datetime(df['date'])
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_exp_df = df[(df['type'].isin(['Labor', 'Material'])) & (df['date_parsed'] >= seven_days_ago)]
            total_7_day_exp = recent_exp_df['amount'].sum()
            daily_burn_rate = total_7_day_exp / 7
        except:
            daily_burn_rate = 0

        if net_bal < 50000:
            st.markdown(f"""
                <div class="alert-box">
                    🚨 LOW BALANCE ALERT: Running Liquid Balance is critical (PKR {net_bal:,.0f}). 
                    Please arrange funds to ensure workflow stability at the construction perimeter line.
                </div>
            """, unsafe_allow_html=True)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            if days_left <= 5:
                st.markdown(f"""
                    <div class="alert-box" style="background-color: #fff3e0; border-left-color: #ff9800; color: #e65100;">
                        ⚠️ CASH FLOW WARNING: At the current velocity of PKR
