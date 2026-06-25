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

def update_transaction_status(row_id, new_type):
    try:
        supabase.table('transactions').update({"type": new_type}).eq("id", row_id).execute()
        st.cache_data.clear()
        st.success(f"Status update ho gaya!")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

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

# --- PREMIUM SOFTWARE STYLE CSS ---
st.markdown("""
    <style>
    :root {
        --bg-main: #f4f7fb;
        --panel: rgba(255, 255, 255, 0.78);
        --panel-strong: rgba(255, 255, 255, 0.92);
        --stroke: rgba(148, 163, 184, 0.22);
        --text: #0f172a;
        --muted: #64748b;
        --red: #ff4b4b;
        --red-dark: #e11d48;
        --green: #16a34a;
        --orange: #f59e0b;
        --shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
        --shadow-soft: 0 10px 30px rgba(15, 23, 42, 0.05);
        --radius-xl: 28px;
        --radius-lg: 20px;
        --radius-md: 16px;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(255, 75, 75, 0.10), transparent 22%),
            radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 18%),
            linear-gradient(180deg, #eef4fb 0%, #f8fafc 42%, #eef2f7 100%);
        background-attachment: fixed;
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,0) !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.88) 0%, rgba(248,250,252,0.94) 100%) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.18);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    h1, h2, h3 {
        color: var(--text) !important;
        letter-spacing: -0.03em;
    }

    .header-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.86) 0%, rgba(255,255,255,0.72) 100%);
        border: 1px solid var(--stroke);
        border-radius: var(--radius-xl);
        padding: 28px 30px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        position: relative;
        overflow: hidden;
        margin-bottom: 20px;
    }

    .header-box::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, rgba(255,75,75,0.10), transparent 35%, rgba(59,130,246,0.06));
        pointer-events: none;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.92) 100%);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 22px;
        padding: 22px 22px 18px 22px;
        box-shadow: var(--shadow-soft);
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
        min-height: 132px;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #ff4b4b, #fb7185);
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 35px rgba(15, 23, 42, 0.10);
    }

    .alert-box {
        background: linear-gradient(135deg, #fff1f2 0%, #ffffff 100%);
        color: #9f1239;
        border: 1px solid #fecdd3;
        border-left: 5px solid #ef4444;
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 18px;
        font-weight: 700;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.08);
    }

    .forecast-box {
        background: linear-gradient(135deg, #effdf4 0%, #ffffff 100%);
        color: #166534;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 18px;
        font-weight: 700;
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.08);
    }

    .soft-panel {
        background: var(--panel-strong);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 22px;
        padding: 22px;
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    .digital-voucher {
        background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.96) 100%);
        border: 1px solid rgba(226,232,240,0.9);
        border-radius: 26px;
        padding: 28px;
        box-shadow: var(--shadow);
    }

    .stButton > button {
        border-radius: 14px !important;
        border: 1px solid rgba(226,232,240,1) !important;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        min-height: 46px !important;
        box-shadow: 0 6px 18px rgba(15,23,42,0.05) !important;
    }

    .stButton > button:hover {
        border-color: rgba(255,75,75,0.35) !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        border-radius: 14px !important;
        font-weight: 700 !important;
        min-height: 46px !important;
    }

    div[data-baseweb="select"] > div {
        border-radius: 14px !important;
        border: 1px solid #dbe3ee !important;
        background: rgba(255,255,255,0.88) !important;
    }

    .stTextInput > div > div > input {
        border-radius: 14px !important;
        background: rgba(255,255,255,0.88) !important;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.92) 100%);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 20px;
        padding: 14px 18px;
        box-shadow: var(--shadow-soft);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(226,232,240,0.9);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: var(--shadow-soft);
        background: rgba(255,255,255,0.96);
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ff4b4b, #fb7185) !important;
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148,163,184,0.35), transparent);
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA FETCH LOGIC ---
@st.cache_data(ttl=60)
def fetch_all_raw_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_all_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

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
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
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
    return f"[api.whatsapp.com](https://api.whatsapp.com/send?text={encoded_text})"


# --- 5. INITIALIZE PROJECT REGISTRY STATE ---
raw_df = fetch_all_raw_data()
raw_labor_df = fetch_all_labor_profiles()

if "custom_projects" not in st.session_state:
    st.session_state["custom_projects"] = ["Yousaf Colony"]

if not raw_df.empty and 'project_context' in raw_df.columns:
    dynamic_projects = sorted([p for p in raw_df['project_context'].dropna().unique().tolist() if str(p).strip()])
    for proj in dynamic_projects:
        if proj not in st.session_state["custom_projects"]:
            st.session_state["custom_projects"].append(proj)

if "selected_project" not in st.session_state:
    st.session_state["selected_project"] = st.session_state["custom_projects"][0]

current_project = st.session_state["selected_project"]

# --- helper popup functions keep same ---
@st.dialog("➕ Create New Project Workspace")
def popup_create_project():
    new_proj = st.text_input("New Project Name / Site Context")
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Create Project", use_container_width=True):
            if new_proj and new_proj not in st.session_state["custom_projects"]:
                st.session_state["custom_projects"].append(new_proj)
                st.session_state["selected_project"] = new_proj
                st.success(f"Project '{new_proj}' create ho gaya.")
                st.rerun()
    with btn_col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("👤 Register New Labor Profile")
def popup_register_labor(current_project):
    st.markdown(f"**Project Context:** `{current_project}`")
    l_name = st.text_input("Full Labor Name")
    l_phone = st.text_input("Phone Number")
    l_cnic = st.text_input("CNIC Number")
    l_occupation = st.text_input("Occupation / Skill")
    l_amount = st.number_input("Total Contract Amount", min_value=0.0, step=1000.0)
    l_rating = st.slider("Performance Rating", 1, 5, 5)
    l_details = st.text_area("Profile Details / Notes")
    l_photo = st.text_input("Photo URL")
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Register Worker", use_container_width=True):
            try:
                payload = {
                    "name": l_name,
                    "phone": l_phone,
                    "cnic": l_cnic,
                    "occupation": l_occupation,
                    "total_contract_amount": l_amount,
                    "rating": l_rating,
                    "details": l_details,
                    "photo_url": l_photo,
                    "project_context": current_project
                }
                supabase.table("labor_profiles").insert(payload).execute()
                st.cache_data.clear()
                st.success("Labor profile register ho gaya.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with btn_col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("➕ Add Transaction Entry")
def popup_transaction_entry(ftype, current_project):
    st.markdown(f"**Project Context:** `{current_project}`")
    d_date = st.date_input("Date", value=datetime.now())
    d_name = st.text_input("Name / Item Title")
    d_amt = st.number_input("Amount", min_value=0.0, step=1000.0)
    d_det = st.text_area("Detail / Notes")
    col1, col2 = st.columns(2)
    d_occ = col1.text_input("Occupation / Job Type (If Labor)")
    d_rec = col2.text_input("Received By / Authorized Person")
    d_meth = st.selectbox("Payment Method", ["Cash", "Online", "Cheque"])
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Save Entry", use_container_width=True):
            try:
                payload = {
                    "date": str(d_date),
                    "type": ftype,
                    "name": d_name,
                    "amount": d_amt,
                    "detail": d_det,
                    "occupation": d_occ,
                    "received_by": d_rec,
                    "pay_method": d_meth,
                    "project_context": current_project
                }
                supabase.table("transactions").insert(payload).execute()
                st.cache_data.clear()
                st.success("Transaction save ho gayi.")
                wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det, current_project)
                st.markdown(f"""<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-top:5px;">📲 Share Via WhatsApp Broadcast</div></a>""", unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with btn_col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("⚙️ Update Project Checklist Status")
def popup_update_status(current_project, status_df):
    st.markdown(f"**Project Context:** `{current_project}`")
    task = st.selectbox("Select Task Line Target", status_df['task_name'].tolist())
    stat = st.radio("Status Milestone Alignment", ["Pending", "Done"], horizontal=True)
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Update Status", use_container_width=True):
            try:
                row_found = status_df[status_df['task_name'] == task]
                if not row_found.empty and 'id' in row_found.columns:
                    row_id = row_found.iloc[0]['id']
                    supabase.table("project_status").update({"status": stat}).eq("id", row_id).execute()
                else:
                    supabase.table("project_status").insert({
                        "task_name": task,
                        "status": stat,
                        "project_context": current_project
                    }).execute()
                st.cache_data.clear()
                st.success("Checklist update ho gayi.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    with btn_col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# --- 6. FILTER DATA BY CURRENT PROJECT ---
df = raw_df[raw_df['project_context'] == current_project].copy() if (not raw_df.empty and 'project_context' in raw_df.columns) else pd.DataFrame()
labor_df = raw_labor_df[raw_labor_df['project_context'] == current_project].copy() if (not raw_labor_df.empty and 'project_context' in raw_labor_df.columns) else pd.DataFrame()

# --- 8. SIDEBAR DESIGN ---
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
    st.session_state["selected_project"] = selected_proj
    current_project = st.session_state["selected_project"]
    st.divider()
    
    st.markdown("<p style='font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:8px;'>Navigation Menu</p>", unsafe_allow_html=True)
    menu = st.radio(
        "Navigation Portal",
        ["📊 Dashboard View", "📑 Receipt Voucher System", "💰 Income Ledger", "👷 Labor Ledger History", "🏗️ Material Log Vault", "📋 Pending Bills History", "👷 Labor Force Folder", "🔍 Search & Audit Reports"],
        label_visibility="collapsed"
    )
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.markdown("<p style='font-size:11px; font-weight:700; color:#166534; text-transform:uppercase; margin-bottom:8px;'>⚡ Admin Quick Control</p>", unsafe_allow_html=True)
        if st.button("➕ Record Income Flow", use_container_width=True): popup_transaction_entry("Income", st.session_state["selected_project"])
        if st.button("👷 Log Labor Disburse", use_container_width=True): popup_transaction_entry("Labor", st.session_state["selected_project"])
        if st.button("🏗️ Log Material Invoice", use_container_width=True): popup_transaction_entry("Material", st.session_state["selected_project"])
        if st.button("📋 Add Pending Bill", use_container_width=True): popup_transaction_entry("Pending Bill", st.session_state["selected_project"])
        if st.button("👤 Register New Worker", use_container_width=True): popup_register_labor(st.session_state["selected_project"])
        if st.button("📁 Deploy New Site Project", use_container_width=True): popup_create_project()
        st.divider()
        if st.button("⚙️ Calibrate Checklist Nodes", use_container_width=True):
            _status_df = fetch_project_status(st.session_state["selected_project"])
            popup_update_status(st.session_state["selected_project"], _status_df)
        if st.button("Terminate Session", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

# --- 9. RENDER ACTIVE MAIN PAGE ---
if "Dashboard" in menu:
    st.markdown(f"""
        <div class="header-box">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap;">
                <div>
                    <p style="margin:0 0 10px 0; color:#ff4b4b; font-size:12px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase;">
                        Enterprise Control Center
                    </p>
                    <h1 style="color:#0f172a; margin:0; font-weight:800; letter-spacing:-1px; font-size:36px;">
                        DEEWARYN<span style="color:#FF4B4B;">.COM</span>
                    </h1>
                    <p style="color:#64748b; letter-spacing:0.4px; font-size:14px; margin:8px 0 0 0; font-weight:500;">
                        Real-time construction finance and site operations dashboard for <b>{current_project}</b>
                    </p>
                </div>
                <div style="background:rgba(255,255,255,0.78); border:1px solid rgba(226,232,240,0.95); border-radius:18px; padding:14px 18px; min-width:220px; box-shadow:0 8px 24px rgba(15,23,42,0.05);">
                    <div style="font-size:11px; color:#64748b; text-transform:uppercase; font-weight:700; letter-spacing:1px;">Project Context</div>
                    <div style="font-size:18px; font-weight:800; color:#0f172a; margin-top:4px;">{current_project}</div>
                    <div style="font-size:12px; color:#ff4b4b; font-weight:700; margin-top:6px;">C.E.O: Sardar Sami Ullah</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    inc, lab_exp, mat_exp, exp, net_bal, pending_bill = 0, 0, 0, 0, 0, 0
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        lab_exp = df[df['type'] == 'Labor']['amount'].sum()
        mat_exp = df[df['type'] == 'Material']['amount'].sum()
        pending_bill = df[df['type'] == 'Pending Bill']['amount'].sum()
        exp = lab_exp + mat_exp
        net_bal = inc - exp
        
        try:
            df['date_parsed'] = pd.to_datetime(df['date'])
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_exp_df = df[(df['type'].isin(['Labor', 'Material'])) & (df['date_parsed'] >= seven_days_ago)]
            total_7_day_exp = recent_exp_df['amount'].sum()
            daily_burn_rate = total_7_day_exp / 7
        except:
            daily_burn_rate = 0

        if net_bal < 50000:
            st.markdown(f"""<div class="alert-box">🚨 RUNNING BALANCE WARNING: Capital pool reserve is critical (PKR {net_bal:,.0f}) inside {current_project}.</div>""", unsafe_allow_html=True)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            if days_left <= 5:
                st.markdown(f"""<div class="alert-box" style="background-color: #fffbeb; border-left-color: #f59e0b; color: #78350f; border: 1px solid #fef3c7;">⚠️ RESERVES DEFICIT: Capital status for {current_project} estimated to expire in ~{days_left:.1f} days.</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="forecast-box">📈 RUNWAY STABILITY PROJECTION: Safe operational buffer mapped for active site context: ~{days_left:.1f} Days.</div>""", unsafe_allow_html=True)

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        st.markdown(f"""
            <div class='kpi-card'>
                <p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>💰 Total Capital Arrival</p>
                <h2 style='color:#15803d; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {inc:,.0f}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
            <div class='kpi-card'>
                <p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>📉 Disbursed Outflows</p>
                <h2 style='color:#b91c1c; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {exp:,.0f}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        bal_color = "#15803d" if net_bal >= 0 else "#b91c1c"
        st.markdown(f"""
            <div class='kpi-card'>
                <p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>⚖️ Net Running Balance</p>
                <h2 style='color:{bal_color}; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {net_bal:,.0f}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.metric('📋 Pending Bills', f'PKR {pending_bill:,.0f}')

    st.write("##")
    status_df = fetch_project_status(current_project)
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done']) if total_tasks > 0 else 0
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("<div class='soft-panel'>", unsafe_allow_html=True)
        st.markdown("### 📈 Structural Framework Progress")
        st.progress(prog_val / 100)
        st.markdown(f"**{prog_val}% Tasks Mapped & Complete**")
        chart_code = f"graph LR\\nA[Start] --> B{{Progress: {prog_val}%}}\\nstyle B fill:#FF4B4B,color:#fff,stroke:none"
        components.html(
            f"<div style='background:#ffffff; border-radius:18px; padding:15px; border:1px solid #e2e8f0; box-shadow:0 6px 18px rgba(15,23,42,0.04);'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from '[cdn.jsdelivr.net](https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs)';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>",
            height=120
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='soft-panel'>", unsafe_allow_html=True)
        st.markdown("### 📝 Architectural Nodes Checklist")
        st.write(f"✅ Cleared Status Tasks: **{done_tasks}** | ⏳ Pending Core Nodes: **{total_tasks - done_tasks}**")
        if st.button("Re-Sync Ledger Memory Cache", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🏗️ Complete Site Blueprint Matrix Mapping")
    t_cols = st.columns(3)

    if not status_df.empty:
        for i, row in status_df.reset_index().iterrows():
            with t_cols[i % 3]:
                icon = "🟢 Clear" if row['status'] == "Done" else "⏳ Pending"
                bg = "#f8fafc" if row['status'] == "Done" else "#fff9f5"
                border_c = "#e2e8f0" if row['status'] == "Done" else "#ffedd5"
                st.markdown(
                    f'''
                    <div style="
                        background:{bg};
                        padding:18px;
                        border-radius:18px;
                        margin-bottom:12px;
                        border:1px solid {border_c};
                        color:#0f172a;
                        font-weight:600;
                        font-size:13.5px;
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        box-shadow:0 10px 24px rgba(15,23,42,0.05);
                        backdrop-filter: blur(10px);
                    ">
                        <span style="display:flex; flex-direction:column; gap:4px;">
                            <span style="font-size:14px; font-weight:700; color:#0f172a;">{row["task_name"]}</span>
                            <span style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:0.6px;">Project Workflow Node</span>
                        </span>
                        <span style="
                            font-size:11px;
                            font-weight:800;
                            opacity:0.95;
                            text-transform:uppercase;
                            padding:8px 10px;
                            border-radius:999px;
                            background:rgba(255,255,255,0.75);
                            border:1px solid rgba(255,255,255,0.8);
                        ">
                            {icon}
                        </span>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )


# --- ISOLATED INDEPENDENT PAGE: 📑 RECEIPT VOUCHER SYSTEM ---
elif menu == "📑 Receipt Voucher System":
    st.title(f"📑 Corporate Allocation Voucher Module")
    st.write("Dynamic cryptographic clearance invoice framework tailored for professional architectural firms.")
    st.divider()
    
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
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Designation Spec:</span><span style="color:#0f172a; font-weight:500;">{v_row.get('occupation', 'N/A') if pd.notna(v_row.get('occupation')) else 'N/A'}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13.5px; color:#475569;"><span>Disbursed/Authorized:</span><span style="color:#0f172a; font-weight:500;">{v_row.get('received_by', 'N/A') if pd.notna(v_row.get('received_by')) else 'N/A'}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 18px; font-size: 13.5px; color:#475569;"><span>Channel Pipeline:</span><span style="color:#0f172a; font-weight:500;">{v_row.get('pay_method', 'Cash') if pd.notna(v_row.get('pay_method')) else 'Cash'}</span></div>
                <p style="font-size: 12.5px; background: #f8fafc; padding: 14px; border-radius: 12px; font-style: italic; border-left: 4px solid #FF4B4B; margin-bottom:24px; color:#475569; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">Memo Notes: {v_row['detail'] if v_row['detail'] else 'No automated remarks logged.'}</p>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff; background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius:14px; padding: 14px; text-align:center; box-shadow: 0 4px 12px rgba(15,23,42,0.15);"><span style="font-size:12px; font-weight:500; opacity:0.7; margin-right:10px; letter-spacing:0.5px;">NET VOLUME TOTAL:</span>PKR {v_row['amount']:,.0f}/-</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"Is project site ({current_project}) ke under filhal koi transaction record mojud nahi hai.")


# --- LABOR PROFILES APPLICATION PAGE ---
elif "Labor Force" in menu:
    st.title(f"👷 Dynamic Human Resource Roster")
    
    if not labor_df.empty:
        l_search = st.text_input("🔎 Search Force Rosters Matrix...")
        if l_search:
            l_mask = labor_df.astype(str).apply(lambda x: x.str.contains(l_search, case=False)).any(axis=1)
            labor_df = labor_df[l_mask]
            
        st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
        
        for _, row in labor_df.iterrows():
            with st.container():
                st.markdown(f"<div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:20px; padding:25px; margin-bottom:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.01);'>", unsafe_allow_html=True)
                st.markdown(f"#### 👤 {row['name']} — <span style='color:#FF4B4B; font-weight:700;'>{row['occupation'] if row['occupation'] else 'General Force'}</span>", unsafe_allow_html=True)
                c_img, c_info = st.columns([1, 3])
                with c_img:
                    photo_path = row.get('photo_url', '')
                    if photo_path and str(photo_path) != "nan":
                        st.image(photo_path, use_container_width=True)
                    else:
                        st.info("No Photo Uploaded.")
                with c_info:
                    st.markdown(f"**🪪 CNIC Identifier Pass:** {row['cnic']} | **💰 Total Pool Budget Allocation:** PKR {row['total_contract_amount']:,.0f}")
                    stars = "⭐" * int(row['rating'] if row['rating'] else 5)
                    st.markdown(f"**📊 Performance Rating Score:** {stars}")
                    st.info(row['details'] if row['details'] else "No metadata profile details added.")
                st.markdown("</div>", unsafe_allow_html=True)

elif menu == "💰 Income Ledger":
    st.title("💰 Income Ledger")
    view_df = df[df['type'] == 'Income'].copy() if not df.empty else pd.DataFrame()
    if not view_df.empty:
        st.dataframe(view_df, use_container_width=True)
    else:
        st.info("No income records found.")

elif menu == "👷 Labor Ledger History":
    st.title("👷 Labor Ledger History")
    view_df = df[df['type'] == 'Labor'].copy() if not df.empty else pd.DataFrame()
    if not view_df.empty:
        st.dataframe(view_df, use_container_width=True)
    else:
        st.info("No labor records found.")

elif menu == "🏗️ Material Log Vault":
    st.title("🏗️ Material Log Vault")
    view_df = df[df['type'] == 'Material'].copy() if not df.empty else pd.DataFrame()
    if not view_df.empty:
        st.dataframe(view_df, use_container_width=True)
    else:
        st.info("No material records found.")

elif menu == "📋 Pending Bills History":
    st.title("📋 Pending Bills History")
    view_df = df[df['type'] == 'Pending Bill'].copy() if not df.empty else pd.DataFrame()
    if not view_df.empty:
        st.dataframe(view_df, use_container_width=True)
    else:
        st.info("No pending bill records found.")

elif menu == "🔍 Search & Audit Reports":
    st.title("🔍 Search & Audit Reports")
    if not df.empty:
        q = st.text_input("Search in transaction history")
        temp_df = df.copy()
        if q:
            mask = temp_df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)
            temp_df = temp_df[mask]
        st.dataframe(temp_df, use_container_width=True)

        pdf_file = export_to_pdf(temp_df, f"{current_project} - Search & Audit Reports")
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_file,
            file_name=f"{current_project}_audit_report.pdf",
            mime="application/pdf"
        )
    else:
        st.info("No records found for audit.")
