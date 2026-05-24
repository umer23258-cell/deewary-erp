import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components
import requests  # Image fetch karne ke liye
# PDF ke liye libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
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
    elements.append(Paragraph(f"Deewaryn.com ERP - Full System Report", styles['Normal']))
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


# --- INDIVIDUAL LABOR PROFILE PRINT PDF FUNCTION ---
def export_labor_profile_pdf(labor_row, payments_df):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph(f"<font color='#1e1e1e' size=22><b>DEEWARYN.COM ERP</b></font>", styles['Title']))
    elements.append(Paragraph(f"<font color='#FF4B4B' size=14><b>LABOR PROFILE DOSSIER & LEDGER REPORT</b></font>", styles['Normal']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Profile Picture Logic
    photo_url = labor_row.get('photo_url', '')
    if photo_url and str(photo_url) != "nan" and photo_url.startswith("http"):
        try:
            img_data = requests.get(photo_url).content
            img_buf = io.BytesIO(img_data)
            img = Image(img_buf, width=100, height=100)
            img.hAlign = 'LEFT'
            elements.append(img)
            elements.append(Spacer(1, 15))
        except:
            elements.append(Paragraph("<i>[Profile Image Attached in Cloud File]</i>", styles['Normal']))
            elements.append(Spacer(1, 10))

    # Personal Details Table
    det_data = [
        [Paragraph("<b>Full Name:</b>", styles['Normal']), Paragraph(str(labor_row['name']), styles['Normal'])],
        [Paragraph("<b>Occupation / Skill:</b>", styles['Normal']), Paragraph(str(labor_row['occupation'] if labor_row['occupation'] else 'General Labor'), styles['Normal'])],
        [Paragraph("<b>Phone Number:</b>", styles['Normal']), Paragraph(str(labor_row['phone']), styles['Normal'])],
        [Paragraph("<b>CNIC Number:</b>", styles['Normal']), Paragraph(str(labor_row['cnic']), styles['Normal'])],
        [Paragraph("<b>Total Contract (Taka):</b>", styles['Normal']), Paragraph(f"PKR {labor_row['total_contract_amount']:,.0f}", styles['Normal'])],
        [Paragraph("<b>Personal Details / Notes:</b>", styles['Normal']), Paragraph(str(labor_row['details'] if labor_row['details'] else 'N/A'), styles['Normal'])],
    ]
    det_table = Table(det_data, colWidths=[150, 350])
    det_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8f9fa")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(det_table)
    elements.append(Spacer(1, 20))
    
    # Payments History Table Section
    elements.append(Paragraph("<font color='#1e1e1e' size=12><b>💵 STATEMENT OF PAID PAYMENTS HISTORY</b></font>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    
    pay_data = [["ID", "Date", "Payment Channel / Method", "Amount (PKR)", "Remarks / Details"]]
    if not payments_df.empty:
        for _, p in payments_df.iterrows():
            pay_data.append([
                str(p.get('id', '')),
                str(p.get('date', '')),
                str(p.get('pay_method', 'Cash')),
                f"{p.get('amount', 0):,.0f}",
                str(p.get('detail', ''))
            ])
        total_p = payments_df['amount'].sum()
        pay_data.append(["", "", "TOTAL PAID AMOUNT:", f"{total_p:,.0f}", ""])
    else:
        pay_data.append(["-", "-", "No active transaction logs.", "0", "-"])
        
    pay_table = Table(pay_data, colWidths=[40, 80, 150, 100, 150])
    pay_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1e1e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0,0), (-1,-1), 6),
    ]
    if not payments_df.empty:
        pay_style.extend([
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FF4B4B")),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
    pay_table.setStyle(TableStyle(pay_style))
    elements.append(pay_table)
    
    doc.build(elements)
    buf.seek(0)
    return buf


# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="Deewaryn.com ERP", layout="wide", page_icon="🏗️")

# --- ULTRA PREMIUM BRANDED LUXURY CSS INJECTION ---
st.markdown("""
<style>
    /* Background Image Injection */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://i.postimg.cc/Vs46KqYW/ej-yao-D46m-XLs-QRJw-unsplash.jpg");
        background-size: 100% 100%;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    /* Content readability overlay */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 255, 255, 0.65);
        z-index: 0;
    }

    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Styled Voucher Container */
    .digital-voucher {
        background: #ffffff;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        max-width: 600px;
        margin: 20px auto;
    }

    /* KPI Card Enhancement */
    .kpi-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. DATA FETCH LOGIC ---
@st.cache_data(ttl=10)
def fetch_all_raw_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=10)
def fetch_all_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def fetch_project_status(project_name):
    try:
        res = supabase.table('project_status').select("*").execute()
        df_status = pd.DataFrame(res.data)
        if not df_status.empty and 'project_context' in df_status.columns:
            df_filtered = df_status[df_status['project_context'] == project_name]
            if not df_filtered.empty:
                return df_filtered
        
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])
    except: 
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access Portal", expanded=True):
        pwd = st.text_input("Admin Secret Pin", type="password")
        if st.button("Unlock Terminal"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
    return False

def generate_whatsapp_link(type_tx, name, amount, detail, project):
    base_msg = f"🏗️ *Deewaryn.com ERP Notification*\n"
    base_msg += f"• *Project:* {project}\n"
    base_msg += f"• *Type:* {type_tx}\n"
    base_msg += f"• *Name/Item:* {name}\n"
    base_msg += f"• *Amount:* PKR {amount:,.0f}\n"
    if detail:
        base_msg += f"• *Details:* {detail}\n"
    base_msg += f"\n_System generated tracking logs summary entry._"
    encoded_text = urllib.parse.quote(base_msg)
    return f"https://api.whatsapp.com/send?text={encoded_text}"


# --- 5. INITIALIZE DATA & STATES ---
raw_df = fetch_all_raw_data()
raw_labor_df = fetch_all_labor_profiles()

if "custom_projects" not in st.session_state:
    st.session_state["custom_projects"] = ["Yousaf Colony"]

if not raw_df.empty and 'project_context' in raw_df.columns:
    proj_list = raw_df['project_context'].dropna().unique().tolist()
    for p in proj_list:
        if p and p not in st.session_state["custom_projects"]: 
            st.session_state["custom_projects"].append(p)

if "selected_project" not in st.session_state:
    st.session_state["selected_project"] = st.session_state["custom_projects"][0]

current_project = st.session_state["selected_project"]

# --- DYNAMIC FILTERS FOR CURRENT SELECTION ---
if not raw_df.empty:
    if 'project_context' in raw_df.columns:
        df = raw_df[raw_df['project_context'] == current_project]
    else:
        df = raw_df.copy() if current_project == "Yousaf Colony" else pd.DataFrame()
else:
    df = pd.DataFrame()

if not raw_labor_df.empty:
    if 'project_context' in raw_labor_df.columns:
        labor_df = raw_labor_df[raw_labor_df['project_context'] == current_project]
    else:
        labor_df = raw_labor_df.copy() if current_project == "Yousaf Colony" else pd.DataFrame()
else:
    labor_df = pd.DataFrame()


# --- 6. SIDEBAR DESIGN (Custom Branded Luxury Styling) ---
with st.sidebar:
    st.markdown("<h2 style='color:#FF4B4B; font-weight:800; margin-bottom:0; font-size:24px; letter-spacing:-0.5px;'>DEEWARYN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px; color:#64748b; font-weight:500; margin-top:2px; text-transform:uppercase; letter-spacing:1px;'>Site Infrastructure ERP</p>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:4px;'>Active Project</p>", unsafe_allow_html=True)
    selected_proj = st.selectbox(
        "Working Site Selection:", 
        st.session_state["custom_projects"], 
        index=st.session_state["custom_projects"].index(st.session_state["selected_project"]) if st.session_state["selected_project"] in st.session_state["custom_projects"] else 0,
        label_visibility="collapsed"
    )
    if selected_proj != st.session_state["selected_project"]:
        st.session_state["selected_project"] = selected_proj
        st.rerun()
        
    st.divider()
    
    st.markdown("<p style='font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:8px;'>Navigation Menu</p>", unsafe_allow_html=True)
    menu = st.radio(
        "Navigation Portal", 
        ["📊 Dashboard View", "📑 Receipt Voucher System", "💰 Income Ledger", "👷 Labor Ledger History", "🏗️ Material Log Vault", "👷 Labor Force Folder", "🔍 Search & Audit Reports"],
        label_visibility="collapsed"
    )
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.markdown("<p style='font-size:11px; font-weight:700; color:#166534; text-transform:uppercase; margin-bottom:8px;'>⚡ Admin Quick Control</p>", unsafe_allow_html=True)
        from __main__ import popup_transaction_entry, popup_register_labor, popup_create_project, popup_update_status
        if st.button("➕ Record Income Flow", use_container_width=True): popup_transaction_entry("Income", st.session_state["selected_project"])
        if st.button("👷 Log Labor Disburse", use_container_width=True): popup_transaction_entry("Labor", st.session_state["selected_project"])
        if st.button("🏗️ Log Material Invoice", use_container_width=True): popup_transaction_entry("Material", st.session_state["selected_project"])
        if st.button("👤 Register New Worker", use_container_width=True): popup_register_labor(st.session_state["selected_project"])
        if st.button("📁 Deploy New Site Project", use_container_width=True): popup_create_project()
        st.divider()
        if st.button("⚙️ Calibrate Checklist Nodes", use_container_width=True): 
            _status_df = fetch_project_status(st.session_state["selected_project"])
            popup_update_status(st.session_state["selected_project"], _status_df)
        if st.button("Terminate Session", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg")


# --- GLOBAL HEADER CODE ---
def render_premium_header():
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e24 0%, #0f172a 100%); padding: 35px; border-radius: 24px; box-shadow: 0 12px 30px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                <div>
                    <h1 style="color: #ffffff; margin: 0; font-weight: 900; letter-spacing: -1px; font-size: 52px; text-shadow: 0 4px 10px rgba(0,0,0,0.3);">DEEWARYN<span style="color:#FF4B4B;">.COM</span></h1>
                    <p style="color: #94a3b8; letter-spacing: 1px; font-size: 14px; margin: 6px 0 0 0; font-weight: 600; text-transform: uppercase;">PREMIUM CORPORATE ENTERPRISE FRAMEWORK</p>
                    <div style="margin-top: 10px; display: inline-flex; align-items: center; gap: 8px;">
                        <span style="background: #FF4B4B; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 5px rgba(255,75,75,0.3);">ACTIVE PROJECT LABEL</span>
                        <span style="color: #ffffff; font-size: 14px; font-weight: 700; letter-spacing: 0.5px;">📍 SITE: {current_project.upper()}</span>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; align-items: flex-end;">
                    <div style="background: linear-gradient(90deg, #d4af37 0%, #aa7c11 100%); padding: 12px 24px; border-radius: 16px; border: 1px solid #ffe082; box-shadow: 0 4px 15px rgba(212,175,55,0.25); text-align: center;">
                        <span style="color: #000000; display: block; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; opacity: 0.8;">Executive Management</span>
                        <span style="color: #000000; font-size: 18px; font-weight: 900; letter-spacing: -0.5px;">C.E.O: SARDAR SAMI ULLAH</span>
                    </div>
                    <a href="https://wa.me/923115190118" target="_blank" style="text-decoration: none; display: flex; align-items: center; gap: 8px; background: #25D366; color: white; padding: 10px 18px; border-radius: 12px; font-weight: 700; font-size: 13px; box-shadow: 0 4px 12px rgba(37,211,102,0.3);">
                        <span>📲 Official WhatsApp Line: 03115190118</span>
                    </a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- 9. RENDER DYNAMIC PAGES ---
if "Dashboard" in menu:
    render_premium_header()
    st.markdown("""
        <div style="background: #ffffff; padding: 25px; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 25px;">
            <h3 style="color: #0f172a; margin-top: 0; font-weight: 800; font-size: 20px; display: flex; align-items: center; gap: 8px;">🏢 About Our Enterprise</h3>
            <p style="color: #475569; font-size: 14.5px; line-height: 1.6; margin: 8px 0 0 0;">
                <b>Deewaryn.com</b> is an elite, modern, and high-fidelity construction infrastructure firm dedicated to transforming architectural blueprints into magnificent realities. Managed under the apex vision of <b>Sardar Sami Ullah</b>, our real-time ERP cloud terminal ensures full corporate visibility, unmatched resource mapping, asset management efficiency, and data clearance metrics across all premium active building sites. We construct futures with premium grade-A engineering standards.
            </p>
        </div>
    """, unsafe_allow_html=True)

    inc = df[df['type'] == 'Income']['amount'].sum() if not df.empty else 0
    lab_exp = df[df['type'] == 'Labor']['amount'].sum() if not df.empty else 0
    mat_exp = df[df['type'] == 'Material']['amount'].sum() if not df.empty else 0
    exp = lab_exp + mat_exp
    net_bal = inc - exp

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>💰 TOTAL CAPITAL ARRIVAL</p><h2 style='color:#15803d; margin:8px 0 0 0; font-weight:900; font-size:40px; letter-spacing:-1px;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi2: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>📉 DISBURSED OUTFLOWS</p><h2 style='color:#b91c1c; margin:8px 0 0 0; font-weight:900; font-size:40px; letter-spacing:-1px;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi3: 
        bal_color = "#15803d" if net_bal >= 0 else "#b91c1c"
        st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>⚖️ NET RUNNING BALANCES</p><h2 style='color:{bal_color}; margin:8px 0 0 0; font-weight:900; font-size:40px; letter-spacing:-1px;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    st.write("##")
    status_df = fetch_project_status(current_project)
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done']) if total_tasks > 0 else 0
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown(f"### 📈 Structural Framework Progress")
        st.progress(prog_val / 100)
        st.markdown(f"**{prog_val}% Tasks Mapped & Complete**")
    with col_right:
        st.markdown("### 📝 Architectural Nodes Checklist")
        st.write(f"✅ Cleared Status Tasks: **{done_tasks}** | ⏳ Pending Core Nodes: **{total_tasks - done_tasks}**")

    st.divider()
    st.markdown("### 🏗️ Complete Site Blueprint Matrix Mapping")
    t_cols = st.columns(3)
    if not status_df.empty:
        for i, row in status_df.reset_index().iterrows():
            with t_cols[i % 3]:
                icon = "🟢 Clear" if row['status'] == "Done" else "⏳ Pending"
                bg = "#f8fafc" if row['status'] == "Done" else "#fff9f5"
                border_c = "#e2e8f0" if row['status'] == "Done" else "#ffedd5"
                text_c = "#334155" if row['status'] == "Done" else "#ea580c"
                st.markdown(f'<div style="background:{bg}; padding:16px; border-radius:16px; margin-bottom:10px; border:1px solid {border_c}; color:{text_c}; font-weight:600; font-size:13.5px; display:flex; justify-content:space-between; align-items:center;"><span>{row["task_name"]}</span><span style="font-size:11px; font-weight:700; opacity:0.9; text-transform:uppercase;">{icon}</span></div>', unsafe_allow_html=True)

elif "Income Ledger" in menu:
    render_premium_header()
    st.subheader("💰 Income Accounts & Capital Flow")
    income_data = df[df['type'] == 'Income'] if not df.empty else pd.DataFrame()
    if not income_data.empty:
        st.metric("Total Income Received", f"PKR {income_data['amount'].sum():,.0f}")
        st.dataframe(income_data[['id', 'date', 'name', 'amount', 'detail', 'pay_method']], use_container_width=True)
    else:
        st.info("No income records found for this project context.")

elif "Labor Ledger History" in menu:
    render_premium_header()
    st.subheader("👷 Labor Ledger & Payout History")
    labor_data = df[df['type'] == 'Labor'] if not df.empty else pd.DataFrame()
    if not labor_data.empty:
        st.metric("Total Labor Disbursed", f"PKR {labor_data['amount'].sum():,.0f}")
        st.dataframe(labor_data[['id', 'date', 'name', 'occupation', 'amount', 'received_by', 'pay_method', 'detail']], use_container_width=True)
    else:
        st.info("No labor payout transactions found for this project context.")

elif "Material Log Vault" in menu:
    render_premium_header()
    st.subheader("🏗️ Material Expense Log Vault")
    material_data = df[df['type'] == 'Material'] if not df.empty else pd.DataFrame()
    if not material_data.empty:
        st.metric("Total Material Cost", f"PKR {material_data['amount'].sum():,.0f}")
        st.dataframe(material_data[['id', 'date', 'name', 'amount', 'received_by', 'pay_method', 'detail']], use_container_width=True)
        
        st.markdown("### 📸 Digital Bill / Invoice Previews")
        for idx, row in material_data.iterrows():
            if row.get('image_url') and str(row['image_url']) != "nan":
                with st.expander(f"📄 View Invoice for {row['name']} (PKR {row['amount']:,.0f})"):
                    st.image(row['image_url'], use_container_width=True)
    else:
        st.info("No material tracking logs mapped to this site context yet.")

elif "Labor Force Folder" in menu:
    render_premium_header()
    st.subheader("👥 Registered Labor Force Folder")
    if not labor_df.empty:
        for idx, row in labor_df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    if row.get('photo_url') and str(row['photo_url']) != "nan":
                        st.image(row['photo_url'], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/150", use_container_width=True)
                with col2:
                    st.markdown(f"### {row['name']} ({row['occupation']})")
                    st.write(f"📞 **Phone:** {row['phone']} | 🆔 **CNIC:** {row['cnic']}")
                    st.write(f"💰 **Total Contract Amount:** PKR {row['total_contract_amount']:,.0f}")
                    st.write(f"📝 **Profile Notes:** {row['details']}")
                st.divider()
    else:
        st.info("No workforce personnel registered on this active project context.")

elif "Search & Audit Reports" in menu:
    render_premium_header()
    st.subheader("🔍 Master Search, Audit & Export")
    if not df.empty:
        q = st.text_input("Enter keywords to filter entire system data logs:")
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)] if q else df
        st.dataframe(filtered_df, use_container_width=True)
        
        pdf_buf = export_to_pdf(filtered_df, f"Audit Report - {current_project}")
        st.download_button("📥 Download PDF Audit Sheet", data=pdf_buf, file_name=f"Deewaryn_Audit_{current_project}.pdf", mime="application/pdf")
    else:
        st.info("No system records available to run queries.")

elif menu == "📑 Receipt Voucher System":
    render_premium_header()
    st.title(f"📑 Corporate Allocation Voucher Module")
    if not df.empty:
        df['voucher_label'] = "[" + df['type'].astype(str).str.upper() + "] ID: " + df['id'].astype(str) + " - " + df['name'].astype(str) + " (PKR " + df['amount'].map('{:,.0f}'.format) + ")"
        selected_log = st.selectbox("Select System Transaction Target Entry:", df['voucher_label'].tolist())
        v_row = df[df['voucher_label'] == selected_log].iloc[0]
        v_prefix = "INC" if v_row['type'] == "Income" else "LAB" if v_row['type'] == "Labor" else "MAT"
        v_number = f"DW-{v_prefix}-{1000 + int(v_row['id'])}"
        
        st.markdown(f"""
            <div class="digital-voucher">
                <div style="text-align: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 18px; margin-bottom: 22px;">
                    <h3 style="margin: 0; color: #0f172a; letter-spacing: -0.5px; font-weight:800; font-size:22px;">DEEWARYN<span style="color:#FF4B4B;">.COM</span></h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #64748b; font-weight: 600; text-transform:uppercase; letter-spacing:1px;">Official Transaction Clearance Record</p>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Voucher Reference ID:</span><b style="color:#FF4B4B; font-weight:700;">{v_number}</b></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Execution Log Date:</span><span style="color:#0f172a; font-weight:500;">{v_row['date']}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Ledger Allocation:</span><b style="color:#0f172a;">{str(v_row['type']).upper()}</b></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Particular Scope:</span><b style="color:#0f172a;">{v_row['name']}</b></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Payment Method:</span><span style="color:#0f172a; font-weight:500;">{v_row.get('pay_method', 'Cash') if pd.notna(v_row.get('pay_method')) else 'Cash'}</span></div>
                <div style="margin-top: 18px; padding-top: 18px; border-top: 1px dashed #cbd5e1; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; font-weight: 700; color:#0f172a;">TOTAL AMOUNT:</span>
                    <span style="font-size: 22px; font-weight: 800; color: #15803d;">PKR {v_row['amount']:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No logs available to generate digital vouchers for this project context yet.")
