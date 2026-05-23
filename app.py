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


# --- INDIVIDUAL LABOR PROFILE PRINT PDF FUNCTION ---
def export_labor_profile_pdf(labor_row, payments_df):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph(f"<font color='#1e1e1e' size=22><b>DEEWARY.COM ERP</b></font>", styles['Title']))
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
    </style>
""", unsafe_allow_html=True)


# --- 4. DATA FETCH LOGIC ---
@st.cache_data(ttl=60)
def fetch_all_raw_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=30)
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
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
    return False

def generate_whatsapp_link(type_tx, name, amount, detail, project):
    base_msg = f"🏗️ *Deewary.com ERP Notification*\n"
    base_msg += f"• *Project:* {project}\n"
    base_msg += f"• *Type:* {type_tx}\n"
    base_msg += f"• *Name/Item:* {name}\n"
    base_msg += f"• *Amount:* PKR {amount:,.0f}\n"
    if detail:
        base_msg += f"• *Details:* {detail}\n"
    base_msg += f"\n_System generated tracking logs summary entry._"
    encoded_text = urllib.parse.quote(base_msg)
    return f"https://api.whatsapp.com/send?text={encoded_text}"


# --- 5. INITIALIZE PROJECT REGISTRY STATE ---
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


# --- 6. NAVIGATION MANAGER FOR QUICK BUTTONS ---
# Initialize radio index tracker
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "📊 Dashboard"

# Helper function to auto-switch screen focus to Dashboard form
def redirect_to_form(form_type):
    st.session_state.show_form = form_type
    st.session_state["current_page"] = "📊 Dashboard"
    st.rerun()


# --- 7. SIDEBAR DESIGN ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    
    st.markdown("### 📁 Select Active Site Project")
    selected_proj = st.selectbox(
        "Current Working Context:", 
        st.session_state["custom_projects"], 
        index=st.session_state["custom_projects"].index(st.session_state["selected_project"]) if st.session_state["selected_project"] in st.session_state["custom_projects"] else 0
    )
    st.session_state["selected_project"] = selected_proj
    st.info(f"📍 Active Site: **{st.session_state['selected_project']}**")
    st.divider()
    
    # Dynamic list for radio menu controlled by session state
    menu_options = ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"]
    
    menu = st.radio(
        "Go To", 
        menu_options, 
        index=menu_options.index(st.session_state["current_page"]) if st.session_state["current_page"] in menu_options else 0,
        key="navigation_radio"
    )
    st.session_state["current_page"] = menu # Save manual clicks
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
        st.write("### ⚡ Quick Actions")
        # Direct redirect and execution triggers fixed here
        if st.button("➕ Income", use_container_width=True): redirect_to_form("Income")
        if st.button("👷 Labor", use_container_width=True): redirect_to_form("Labor")
        if st.button("🏗️ Material", use_container_width=True): redirect_to_form("Material")
        if st.button("📝 Register New Labor Profile", use_container_width=True): redirect_to_form("RegisterLabor")
        if st.button("📁 Create New Project Site", use_container_width=True): redirect_to_form("CreateProject")
        st.divider()
        if st.button("⚙️ Change Task Status"): 
            st.session_state.show_status_form = True
            st.session_state["current_page"] = "📊 Dashboard"
            st.rerun()
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption=f"Active Site: {st.session_state['selected_project']}")


# --- 8. DYNAMIC PROJECT FILTERS ---
current_project = st.session_state["selected_project"]

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


# --- 9. RENDER PAGES ---
if st.session_state["current_page"] == "📊 Dashboard":
    st.markdown(f"""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px;">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px; font-size: 14px; margin-bottom: 10px;">PREMIUM SITE MANAGEMENT: {current_project.upper()}</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- FORMS MANAGEMENT HANDLING (Renders immediately at top when triggered) ---
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        
        if ftype == "CreateProject":
            with st.expander("📁 Launch New Project Site Perimeter", expanded=True):
                with st.form("new_project_form"):
                    new_proj_name = st.text_input("Project / Plot Site Name (e.g., G-13 Plot, CBR Town)*").strip()
                    st.write("ℹ️ *Note: Naya project yahan banne ke baad dropdown list mein shamil ho jayega.*")
                    if st.form_submit_button("Launch New Project Context"):
                        if new_proj_name:
                            if new_proj_name not in st.session_state["custom_projects"]:
                                st.session_state["custom_projects"].append(new_proj_name)
                            st.session_state["selected_project"] = new_proj_name
                            st.success(f"Project '{new_proj_name}' state contextualized!")
                            st.session_state.pop("show_form")
                            st.rerun()
                        else: st.error("Project identity descriptor required.")
                        
        elif ftype == "RegisterLabor":
            with st.expander(f"📝 Register New Labor Profile under {current_project}", expanded=True):
                with st.form("labor_profile_form"):
                    l_name = st.text_input("Labor Full Name *")
                    l_phone = st.text_input("Phone Number")
                    l_cnic = st.text_input("CNIC Number")
                    l_occ = st.text_input("Occupation / Skill Type")
                    l_contract = st.number_input("Total Contract Amount (PKR)", min_value=0, value=0)
                    l_rating = st.slider("Rating", min_value=1, max_value=5, value=5)
                    l_photo = st.file_uploader("Upload Labor Profile Picture", type=['jpg', 'jpeg', 'png'])
                    l_details = st.text_area("A to Z Personal Data Notes")
                    
                    if st.form_submit_button("Save Profile Application"):
                        if l_name:
                            img_url = ""
                            if l_photo:
                                f_name = f"labor_{int(datetime.now().timestamp())}_{l_photo.name}"
                                supabase.storage.from_('material_pics').upload(f_name, l_photo.getvalue())
                                img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                            
                            payload = {
                                "name": l_name, "phone": l_phone, "cnic": l_cnic, "occupation": l_occ,
                                "total_contract_amount": l_contract, "rating": l_rating,
                                "photo_url": img_url, "details": l_details, "project_context": current_project
                            }
                            supabase.table('labor_profiles').insert(payload).execute()
                            st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
                        else: st.error("Labor Full Name is required.")
        else:
            with st.expander(f"📝 Register New {ftype} Log Entry for {current_project}", expanded=True):
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title / Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if ftype in ["Income", "Labor", "Material"]:
                        col1, col2 = st.columns(2)
                        d_occ = col1.text_input("Occupation / Job Type")
                        d_rec = col2.text_input("Received By / Authorized")
                        d_meth = st.selectbox("Payment Method", ["Cash", "Online", "Cheque"])
                    uploaded_photo = None
                    if ftype == "Material": uploaded_photo = st.file_uploader("Upload Bill Image", type=['jpg', 'jpeg', 'png'])
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit Entry"):
                        img_url = ""
                        if uploaded_photo:
                            f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                            supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                            img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                        
                        payload = {
                            "date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, 
                            "detail": d_det, "image_url": img_url, "occupation": d_occ,
                            "received_by": d_rec, "pay_method": d_meth, "project_context": current_project
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        
                        wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det, current_project)
                        st.markdown(f"""<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 Broadcast to WhatsApp</div></a>""", unsafe_allow_html=True)
                        st.session_state.pop("show_form")
                        if st.button("Proceed & Refresh Dashboard"): st.rerun()

    inc, lab_exp, mat_exp, exp, net_bal = 0, 0, 0, 0, 0
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        lab_exp = df[df['type'] == 'Labor']['amount'].sum()
        mat_exp = df[df['type'] == 'Material']['amount'].sum()
        exp = lab_exp + mat_exp
        net_bal = inc - exp
        
        try:
            df['date_parsed'] = pd.to_datetime(df['date'])
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_exp_df = df[(df['type'].isin(['Labor', 'Material'])) & (df['date_parsed'] >= seven_days_ago)]
            total_7_day_exp = recent_exp_df['amount'].sum()
            daily_burn_rate = total_7_day_exp / 7
        except: daily_burn_rate = 0

        if net_bal < 50000:
            st.markdown(f"""<div class="alert-box">🚨 LOW BALANCE ALERT: Running Balance is critical (PKR {net_bal:,.0f}) for {current_project}.</div>""", unsafe_allow_html=True)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            if days_left <= 5:
                st.markdown(f"""<div class="alert-box" style="background-color: #fff3e0; border-left-color: #ff9800; color: #e65100;">⚠️ CASH FLOW WARNING: Reserves for {current_project} last ~{days_left:.1f} days only.</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="forecast-box">📈 CASH FLOW FORECAST: Safe runway left for current project: ~{days_left:.1f} Days.</div>""", unsafe_allow_html=True)

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1: st.markdown(f"<div class='kpi-card'><p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>💰 TOTAL INVESTMENT</p><h2 style='color:#2e7d32; margin:5px 0 0 0;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi2: st.markdown(f"<div class='kpi-card'><p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>📉 EXPENSES OUTFLOW</p><h2 style='color:#c62828; margin:5px 0 0 0;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi3: 
        bal_color = "#2e7d32" if net_bal >= 0 else "#c62828"
        st.markdown(f"<div class='kpi-card'><p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>⚖️ NET BALANCE</p><h2 style='color:{bal_color}; margin:5px 0 0 0;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    # --- RECEIPT SLIP GENERATOR ---
    st.write("##")
    st.markdown("### 📑 System Automated Receipt Slip / Voucher Generator")
    if not df.empty:
        df['voucher_label'] = "[" + df['type'].astype(str).str.upper() + "] ID: " + df['id'].astype(str) + " - " + df['name'].astype(str) + " (PKR " + df['amount'].map('{:,.0f}'.format) + ")"
        selected_log = st.selectbox("Select Transaction Log Entry:", df['voucher_label'].tolist())
        v_row = df[df['voucher_label'] == selected_log].iloc[0]
        v_prefix = "INC" if v_row['type'] == "Income" else "LAB" if v_row['type'] == "Labor" else "MAT"
        v_number = f"DW-{v_prefix}-{1000 + int(v_row['id'])}"
        
        st.markdown(f"""
            <div class="digital-voucher">
                <div class="voucher-header">
                    <h3 style="margin: 0; color: #1e1e1e; letter-spacing: 2px;">DEEWARY.COM</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #6c757d; font-weight: bold;">PROJECT SITE VOUCHER: {current_project.upper()}</p>
                </div>
                <div class="voucher-row"><span>Voucher No:</span><b>{v_number}</b></div>
                <div class="voucher-row"><span>Log Date:</span><span>{v_row['date']}</span></div>
                <div class="voucher-row"><span>Particular Name:</span><b>{v_row['name']}</b></div>
                <div class="voucher-row"><span>Payment Channel:</span><span>{v_row['pay_method']}</span></div>
                <p style="font-size: 12px; background: #f8f9fa; padding: 8px; border-radius: 5px; font-style: italic; border-left: 3px solid #FF4B4B;">{v_row['detail'] if v_row['detail'] else '-'}</p>
                <div class="voucher-total"><div style="display: flex; justify-content: space-between;"><span>VOLUME TOTAL:</span><span>PKR {v_row['amount']:,.0f}/-</span></div></div>
            </div>
        """, unsafe_allow_html=True)
    else: st.info(f"No transaction tracking history data available for project: {current_project}")

    st.write("##")
    status_df = fetch_project_status(current_project)
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done']) if total_tasks > 0 else 0
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown(f"### 📈 Overall Progress ({current_project})")
        st.progress(prog_val / 100)
        st.markdown(f"**{prog_val}% Work Completed**")
        chart_code = f"graph LR\nA[Start] --> B{{Progress: {prog_val}%}}\nstyle B fill:#FF4B4B,color:#fff"
        components.html(f"<div style='background:#f8f9fa; border-radius:10px; padding:10px;'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=120)

    with col_right:
        st.markdown("### 📝 Tasks Summary")
        st.write(f"✅ Finished: {done_tasks} | ⏳ Remaining: {total_tasks - done_tasks}")
        if st.button("Force Refresh Tracker Context"): st.cache_data.clear(); st.rerun()

    if "show_status_form" in st.session_state and is_auth:
        with st.expander(f"🛠️ Update Site Status: {current_project}", expanded=True):
            with st.form("status_form"):
                task = st.selectbox("Select Task", status_df['task_name'].tolist())
                stat = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Task Line"):
                    try:
                        supabase.table('project_status').upsert({"task_name": task, "status": stat, "project_context": current_project}, on_conflict="task_name").execute()
                    except:
                        st.warning("Project configuration saved locally.")
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("### 🏗️ Checklist Mapping")
    t_cols = st.columns(3)
    if not status_df.empty:
        for i, row in status_df.reset_index().iterrows():
            with t_cols[i % 3]:
                icon = "✅" if row['status'] == "Done" else "⏳"
                bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
                st.markdown(f'<div style="background:{bg}; padding:10px; border-radius:10px; margin-bottom:5px; border-left:5px solid #FF4B4B;"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)


# --- LABOR PROFILES APPLICATION PAGE ---
elif st.session_state["current_page"] == "👷 Labor Profiles Application":
    st.title(f"👷 Labor Profiles Application ({current_project})")
    
    if not labor_df.empty:
        l_search = st.text_input("🔎 Search active profiles folder...")
        if l_search:
            l_mask = labor_df.astype(str).apply(lambda x: x.str.contains(l_search, case=False)).any(axis=1)
            labor_df = labor_df[l_mask]
            
        st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
        
        for _, row in labor_df.iterrows():
            with st.container():
                st.markdown(f"#### 👤 {row['name']} ({row['occupation'] if row['occupation'] else 'General Labor'})")
                c_img, c_info = st.columns([1, 3])
                with c_img:
                    photo_path = row.get('photo_url', '')
                    if photo_path and str(photo_path) != "nan": st.image(photo_path, use_container_width=True)
                    else: st.info("No Pic.")
                with c_info:
                    st.markdown(f"**🪪 CNIC:** {row['cnic']} | **💰 Contract:** PKR {row['total_contract_amount']:,.0f}")
                    
                    stars = "⭐" * int(row['rating'] if row['rating'] else 5)
                    st.markdown(f"**📊 Performance Rating Evaluation:** {stars}")
                    
                    st.info(row['details'] if row['details'] else "No profile notes summary provided.")
                    
                    st.markdown("#### 📊 Paid Payments History (Labor History Sync)")
                    if not df.empty:
                        prof_name = str(row['name']).lower().strip()
                        def is_name_match(tx_name):
                            tx_name_clean = str(tx_name).lower().strip()
                            return (prof_name in tx_name_clean) or (tx_name_clean in prof_name)
                        
                        labor_tx = df[df['type'] == 'Labor']
                        if not labor_tx.empty:
                            match_mask = labor_tx['name'].apply(is_name_match)
                            labor_payments = labor_tx[match_mask]
                        else: labor_payments = pd.DataFrame()
                        
                        if not labor_payments.empty:
                            st.dataframe(labor_payments[['id', 'date', 'pay_method', 'amount', 'detail']], use_container_width=True)
                            total_paid = labor_payments['amount'].sum()
                            st.metric(label="Total Amount Paid", value=f"PKR {total_paid:,.0f}/-")
                        else:
                            st.warning("⚠️ No payment logs registered under this exact Labor Name inside active project files.")
                            labor_payments = pd.DataFrame()
                    else: labor_payments = pd.DataFrame()

                    pdf_data = export_labor_profile_pdf(row, labor_payments)
                    st.download_button(label="📄 Print & Download Full Profile Report", data=pdf_data, file_name=f"Labor_{str(row['name'])}.pdf", mime="application/pdf", key=f"dl_pdf_{row['id']}")
                st.divider()
        if is_auth:
            l_tid = st.text_input("Enter Profile ID to Delete permanently")
            if st.button("🗑️ Delete Profile Record"):
                if l_tid:
                    supabase.table('labor_profiles').delete().eq('id', l_tid).execute()
                    st.cache_data.clear(); st.rerun()
    else: st.info(f"No Labor profiles provisioned for project context: {current_project}")


# --- ORIGINAL HISTORY PAGES LOGIC (Project Restricted) ---
else:
    st.title(f"{st.session_state['current_page']} ({current_project})")
    if not df.empty:
        if "Income" in st.session_state["current_page"]: f_df = df[df['type'] == 'Income']
        elif "Labor" in st.session_state["current_page"]: f_df = df[df['type'] == 'Labor']
        elif "Material" in st.session_state["current_page"]: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        search = st.text_input("🔎 Search by ID or Name...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        st.dataframe(f_df, use_container_width=True)
        st.metric("Total PKR", f"{f_df['amount'].sum():,.0f}")
        
        if is_auth:
            tid = st.text_input("Enter ID to Delete")
            if st.button("🗑️ Delete Entry"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()

        st.divider()
        c1, c2 = st.columns(2)
        c1.download_button("📥 Excel", f_df.to_csv().encode('utf-8'), f"{st.session_state['current_page']}_{current_project}.csv")
        c2.download_button("📄 PDF Report", export_to_pdf(f_df, st.session_state["current_page"]), f"{st.session_state['current_page']}_{current_project}.pdf")
    else: st.info(f"No database ledger records tracked under project site: {current_project}")
