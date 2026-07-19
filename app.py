import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import html
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

# --- APPLICATION SHELL ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: #f5f7fb;
    }
    .block-container {
        max-width: 1440px;
        padding-top: 2.25rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {background: #ffffff; border-right: 1px solid #e8edf5;}
    [data-testid="stSidebar"] * {font-family: Inter, ui-sans-serif, system-ui, sans-serif;}
    h1, h2, h3 {letter-spacing: -.03em;}
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
        # Legacy databases keep one shared checklist and do not have project_context.
        # Those rows are real saved statuses, so never replace them with demo defaults.
        if not df_status.empty and 'project_context' not in df_status.columns:
            return df_status
        
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])
    except: 
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])

def save_project_status(project_name, task_name, new_status):
    """Save a checklist item without relying on an unavailable UPSERT constraint."""
    table = supabase.table('project_status')
    # `task_name` is supported by both the old and new versions of this table.
    existing = table.select('*').eq('task_name', task_name).execute().data or []

    # On the newer schema, one task can exist for more than one project.
    matching = [row for row in existing if row.get('project_context') == project_name]
    if matching:
        row = matching[0]
        if row.get('id') is not None:
            table.update({'status': new_status}).eq('id', row['id']).execute()
        else:
            table.update({'status': new_status}).eq('task_name', task_name).eq('project_context', project_name).execute()
        return

    # Old installations have no `project_context` column and store one shared checklist.
    if existing and 'project_context' not in existing[0]:
        row = existing[0]
        if row.get('id') is not None:
            table.update({'status': new_status}).eq('id', row['id']).execute()
        else:
            table.update({'status': new_status}).eq('task_name', task_name).execute()
        return

    # No matching row: create one. Fall back cleanly for the legacy schema.
    try:
        table.insert({'task_name': task_name, 'status': new_status, 'project_context': project_name}).execute()
    except Exception:
        table.insert({'task_name': task_name, 'status': new_status}).execute()

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


# --- 6. POPUP DIALOG FORMS ---
@st.dialog("📁 Create New Project Site Context", dismissible=False)
def popup_create_project():
    new_proj_name = st.text_input("Project / Plot Site Name (e.g., G-13 Plot, CBR Town)*").strip()
    st.write("ℹ️ *Note: Naya project aap ki session state aur dashboard par active ho jayega.*")
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("🚀 Launch Project", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        if new_proj_name:
            if new_proj_name not in st.session_state["custom_projects"]:
                st.session_state["custom_projects"].append(new_proj_name)
            st.session_state["selected_project"] = new_proj_name
            
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            for t in tasks:
                try:
                    save_project_status(new_proj_name, t, "Pending")
                except Exception:
                    pass
            
            st.success(f"Project '{new_proj_name}' successfully created!")
            st.rerun()
        else: st.error("Project identity descriptor required.")
        
    if cancel_btn:
        st.rerun()

@st.dialog("📝 Register New Labor Profile", dismissible=False)
def popup_register_labor(current_project):
    st.write(f"Adding to project: **{current_project}**")
    l_name = st.text_input("Labor Full Name *")
    l_phone = st.text_input("Phone Number")
    l_cnic = st.text_input("CNIC Number")
    l_occ = st.text_input("Occupation / Skill Type")
    l_contract = st.number_input("Total Contract Amount (PKR)", min_value=0, value=0)
    l_rating = st.slider("Rating", min_value=1, max_value=5, value=5)
    l_photo = st.file_uploader("Upload Labor Profile Picture", type=['jpg', 'jpeg', 'png'])
    l_details = st.text_area("A to Z Personal Data Notes")
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("💾 Save Profile", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        if l_name:
            img_url = ""
            if l_photo:
                try:
                    f_name = f"labor_{int(datetime.now().timestamp())}_{l_photo.name}"
                    supabase.storage.from_('material_pics').upload(f_name, l_photo.getvalue())
                    img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                except: pass
            
            payload = {
                "name": str(l_name), 
                "phone": str(l_phone), 
                "cnic": str(l_cnic), 
                "occupation": str(l_occ),
                "total_contract_amount": float(l_contract), 
                "rating": int(l_rating),
                "photo_url": str(img_url), 
                "details": str(l_details)
            }
            
            if 'project_context' in raw_labor_df.columns or not raw_labor_df.empty:
                payload["project_context"] = str(current_project)
            
            try:
                supabase.table('labor_profiles').insert(payload).execute()
                st.cache_data.clear()
                st.success("Labor profile registered successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
        else: st.error("Labor Full Name is required.")
        
    if cancel_btn:
        st.rerun()

@st.dialog("📝 Log Dynamic Transaction Entry", dismissible=False)
def popup_transaction_entry(ftype, current_project):
    st.write(f"Logging **{ftype}** entry for active project site: **{current_project}**")
    d_date = st.date_input("Date", datetime.now())
    d_name = st.text_input("Title / Name / Particular *")
    d_amt = st.number_input("Amount (PKR) *", min_value=0)
    
    col1, col2 = st.columns(2)
    d_occ = col1.text_input("Occupation / Job Type (If Labor)")
    d_rec = col2.text_input("Received By / Authorized Person")
    d_meth = st.selectbox("Payment Method", ["Cash", "Online", "Cheque"])
    
    uploaded_photo = None
    if ftype == "Material": 
        uploaded_photo = st.file_uploader("Upload Bill Image", type=['jpg', 'jpeg', 'png'])
        
    d_det = st.text_area("Notes / Particular Specs")
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("➕ Submit Entry", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        if d_name and d_amt > 0:
            img_url = ""
            if uploaded_photo:
                try:
                    f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                    supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                    img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                except: pass
            
            payload = {
                "date": str(d_date), 
                "type": str(ftype), 
                "name": str(d_name), 
                "amount": float(d_amt), 
                "detail": str(d_det), 
                "image_url": str(img_url)
            }
            
            if not raw_df.empty:
                if 'occupation' in raw_df.columns: payload["occupation"] = str(d_occ)
                if 'received_by' in raw_df.columns: payload["received_by"] = str(d_rec)
                if 'pay_method' in raw_df.columns: payload["pay_method"] = str(d_meth)
                if 'project_context' in raw_df.columns: payload["project_context"] = str(current_project)
            else:
                payload["project_context"] = str(current_project)
                payload["pay_method"] = str(d_meth)
            
            try:
                supabase.table('transactions').insert(payload).execute()
                st.cache_data.clear()
                st.success("Transaction Log Entry Saved!")
                
                wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det, current_project)
                st.markdown(f"""<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-top:5px;">📲 Share Via WhatsApp Broadcast</div></a>""", unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.error("Database Core Blocked execution.")
        else: st.error("Valid Title Name and Amount required.")
        
    if cancel_btn:
        st.rerun()

@st.dialog("🛠️ Update Site Checklist Status", dismissible=False)
def popup_update_status(current_project, status_df):
    task = st.selectbox("Select Task Line Target", status_df['task_name'].tolist())
    stat = st.radio("Status Milestone Alignment", ["Pending", "Done"], horizontal=True)
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("⚡ Update Status", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        try:
            save_project_status(current_project, task, stat)
            st.cache_data.clear()
            st.success("Task updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Task could not be updated: {str(e)}")
                
    if cancel_btn:
        st.rerun()


# --- 7. DYNAMIC PROJECT FILTERS ---
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


# --- 8. SIDEBAR DESIGN (Custom Branded Luxury Styling) ---
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
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg")


# --- 9. RENDER ACTIVE MAIN PAGE ---
if "Dashboard" in menu:
    # A data-driven command centre: every value belongs to the active project.
    st.markdown("""
        <style>
        .dash {color:#172033; font-family:Inter,ui-sans-serif,system-ui,sans-serif}
        .dash * {box-sizing:border-box}.dash-top{display:flex;justify-content:space-between;align-items:center;margin:0 0 24px}
        .dash-brand{display:flex;align-items:center;gap:12px}.dash-logo{width:43px;height:43px;border-radius:13px;display:grid;place-items:center;color:#fff;font-size:22px;font-weight:850;background:linear-gradient(135deg,#175cd3,#0b4a9b);box-shadow:0 9px 18px rgba(23,92,211,.22)}.dash-brand-name{font-size:15px;font-weight:850;color:#101828;letter-spacing:-.3px}.dash-brand-tag{font-size:10px;color:#667085;text-transform:uppercase;letter-spacing:.09em;font-weight:750;margin-top:2px}
        .dash-eyebrow{margin:0 0 5px;color:#6b7280;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
        .dash-title{margin:0;color:#101828;font-size:31px;font-weight:800;letter-spacing:-1.2px}.dash-date{color:#667085;font-size:13px}
        .dash-live{display:inline-flex;align-items:center;gap:7px;color:#157f3b;background:#eaf8ef;border-radius:99px;padding:8px 12px;font-size:12px;font-weight:700}
        .dash-dot{width:7px;height:7px;background:#22c55e;border-radius:50%}.dash-hero{position:relative;overflow:hidden;border-radius:24px;padding:30px 34px;margin-bottom:18px;background:linear-gradient(110deg,#101b35 0%,#17315d 56%,#235c98 130%);box-shadow:0 16px 38px rgba(20,42,80,.2)}
        .dash-hero:after{content:'';position:absolute;width:280px;height:280px;border:45px solid rgba(126,197,255,.13);border-radius:50%;right:-70px;top:-105px}.dash-hero *{position:relative;z-index:1}.dash-hero-label{color:#a9d6ff;font-size:12px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.dash-hero h2{color:#fff;font-size:28px;letter-spacing:-.8px;margin:12px 0 8px}.dash-hero p{max-width:540px;color:#c8daf2;font-size:14px;line-height:1.55;margin:0}.dash-kpi{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.14);border-radius:13px;padding:11px 15px;min-width:145px}.dash-kpi-label{color:#aec8e6;font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}.dash-kpi-value{color:#fff;font-size:17px;font-weight:780;margin-top:4px}
        .dash-card{height:100%;background:#fff;border:1px solid #e6eaf0;border-radius:18px;padding:19px;box-shadow:0 3px 12px rgba(16,24,40,.035)}.dash-card-label{font-size:11px;letter-spacing:.07em;color:#667085;font-weight:750;text-transform:uppercase}.dash-card-value{font-size:25px;color:#101828;font-weight:800;letter-spacing:-.7px;margin:8px 0 5px}.dash-card-foot{font-size:12px;color:#667085}.dash-icon{float:right;width:34px;height:34px;padding-top:7px;text-align:center;background:#f1f5f9;border-radius:10px;font-size:16px}
        .dash-panel{background:#fff;border:1px solid #e6eaf0;border-radius:18px;padding:22px;box-shadow:0 3px 12px rgba(16,24,40,.035)}.dash-panel-title{font-size:15px;color:#101828;font-weight:780;margin:0}.dash-panel-sub{font-size:12px;color:#667085;margin:5px 0 18px}.dash-progress{height:8px;background:#eaf0f6;border-radius:10px;overflow:hidden}.dash-progress-fill{height:100%;border-radius:10px;background:linear-gradient(90deg,#2e90fa,#7f56d9)}
        .dash-ring{width:132px;height:132px;border-radius:50%;display:grid;place-items:center}.dash-ring-inner{width:104px;height:104px;border-radius:50%;display:grid;place-items:center;text-align:center;background:#fff}.dash-ring-value{display:block;color:#101828;font-size:24px;font-weight:800}.dash-ring-note{display:block;color:#667085;font-size:10px;font-weight:700;text-transform:uppercase}.dash-task{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #edf0f4}.dash-task:last-child{border-bottom:0}.dash-task-bullet{width:19px;height:19px;border-radius:50%;flex:0 0 19px;text-align:center;font-size:11px;line-height:19px}.dash-task-name{font-size:13px;color:#344054;font-weight:650}.dash-task-status{font-size:11px;color:#98a2b3;margin-top:2px}.dash-feed{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #edf0f4}.dash-feed:last-child{border-bottom:0}.dash-feed-icon{width:34px;height:34px;flex:0 0 34px;border-radius:10px;display:grid;place-items:center;background:#eff6ff}.dash-feed-name{font-size:13px;color:#344054;font-weight:700}.dash-feed-meta{font-size:11px;color:#98a2b3;margin-top:3px}.dash-feed-amount{margin-left:auto;white-space:nowrap;color:#101828;font-size:13px;font-weight:780}
        .dash-company{margin-top:18px;background:#101b35;border-radius:18px;padding:23px 25px;display:flex;justify-content:space-between;align-items:center;gap:20px}.dash-company *{color:#fff}.dash-company-title{font-size:16px;font-weight:800;margin:0 0 5px}.dash-company-text{color:#b7c7df;font-size:12px;line-height:1.7}.dash-company-info{display:flex;flex-wrap:wrap;gap:18px 26px}.dash-company-item{font-size:12px;color:#d8e5f5}.dash-company-item strong{display:block;color:#7cc1ff;font-size:10px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}
        </style>
    """, unsafe_allow_html=True)

    status_df = fetch_project_status(current_project)
    completed_tasks = int((status_df['status'].astype(str).str.lower() == 'done').sum()) if not status_df.empty else 0
    total_tasks = len(status_df)
    progress = round(completed_tasks * 100 / total_tasks) if total_tasks else 0
    safe_project = html.escape(str(current_project))

    if df.empty:
        total_inc = total_exp = pending_total = 0.0
        transaction_count = 0
        expense_df = pd.DataFrame(columns=['type', 'amount'])
        recent_df = pd.DataFrame()
    else:
        recent_df = df.copy()
        recent_df['amount'] = pd.to_numeric(recent_df['amount'], errors='coerce').fillna(0)
        total_inc = recent_df.loc[recent_df['type'].eq('Income'), 'amount'].sum()
        total_exp = recent_df.loc[recent_df['type'].isin(['Labor', 'Material']), 'amount'].sum()
        pending_total = recent_df.loc[recent_df['type'].eq('Pending Bill'), 'amount'].sum()
        transaction_count = len(recent_df)
        expense_df = recent_df[recent_df['type'].isin(['Labor', 'Material'])].copy()
    balance = total_inc - total_exp
    balance_note = 'Positive cash position' if balance >= 0 else 'Review expense coverage'

    st.markdown(f'''<div class="dash"><div class="dash-top"><div class="dash-brand"><div class="dash-logo">D</div><div><div class="dash-brand-name">DEEWARYN.COM</div><div class="dash-brand-tag">Construction & Project Management</div></div></div><div><span class="dash-live"><i class="dash-dot"></i> Live project data</span><span class="dash-date">&nbsp;&nbsp;{datetime.now().strftime('%d %b %Y')}</span></div></div>
        <section class="dash-hero"><span class="dash-hero-label">Active construction site</span><h2>{safe_project}</h2><p>Monitor financial health, construction delivery and every site transaction from one executive workspace.</p><div style="display:flex;gap:10px;margin-top:23px"><div class="dash-kpi"><div class="dash-kpi-label">Site completion</div><div class="dash-kpi-value">{progress}%</div></div><div class="dash-kpi"><div class="dash-kpi-label">Checklist items</div><div class="dash-kpi-value">{completed_tasks} / {total_tasks}</div></div><div class="dash-kpi"><div class="dash-kpi-label">Transactions</div><div class="dash-kpi-value">{transaction_count}</div></div></div></section></div>''', unsafe_allow_html=True)

    metrics = [
        ('Capital received', total_inc, '↗', '#eaf8ef', '#157f3b', 'All recorded inflows'),
        ('Paid expenses', total_exp, '◫', '#fff1f3', '#d92d20', 'Labor and materials'),
        ('Available balance', balance, '◈', '#eff6ff', '#1570ef', balance_note),
        ('Pending bills', pending_total, '◷', '#fffaeb', '#b54708', 'Awaiting settlement'),
    ]
    metric_columns = st.columns(4)
    for column, (label, value, icon, bg, accent, note) in zip(metric_columns, metrics):
        column.markdown(f'''<div class="dash-card"><span class="dash-icon" style="background:{bg};color:{accent}">{icon}</span><div class="dash-card-label">{label}</div><div class="dash-card-value">PKR {value:,.0f}</div><div class="dash-card-foot">{note}</div></div>''', unsafe_allow_html=True)

    st.write('')
    main_col, side_col = st.columns([1.48, 1])
    with main_col:
        with st.container(border=True):
            st.markdown('<p class="dash-panel-title">Expense allocation</p><p class="dash-panel-sub">Paid costs broken down by ledger category.</p>', unsafe_allow_html=True)
            if expense_df.empty:
                st.info('Paid expense records will appear here once they are added.')
            else:
                st.bar_chart(expense_df.groupby('type')['amount'].sum(), color='#2e90fa')
    with side_col:
        ring_style = f'background:conic-gradient(#2e90fa 0 {progress}%, #edf2f7 {progress}% 100%)'
        open_count = total_tasks - completed_tasks
        st.markdown(f'''<div class="dash-panel"><p class="dash-panel-title">Project health</p><p class="dash-panel-sub">Site checklist delivery status.</p><div style="display:flex;align-items:center;gap:20px"><div class="dash-ring" style="{ring_style}"><div class="dash-ring-inner"><span class="dash-ring-value">{progress}%</span><span class="dash-ring-note">Complete</span></div></div><div><div style="font-size:13px;color:#344054;font-weight:750">{completed_tasks} milestones done</div><div style="font-size:12px;color:#667085;margin-top:6px">{open_count} item(s) remain in the site plan.</div></div></div><div class="dash-progress" style="margin-top:20px"><div class="dash-progress-fill" style="width:{progress}%"></div></div></div>''', unsafe_allow_html=True)

    st.write('')
    activity_col, tasks_col = st.columns([1.48, 1])
    with activity_col:
        activity_html = '<div class="dash-panel"><p class="dash-panel-title">Recent activity</p><p class="dash-panel-sub">Latest transactions recorded for this project.</p>'
        if recent_df.empty:
            activity_html += '<p class="dash-panel-sub">No activity has been recorded yet.</p>'
        else:
            icons = {'Income': '↙', 'Labor': '👷', 'Material': '▣', 'Pending Bill': '◷'}
            for _, row in recent_df.head(5).iterrows():
                tx_type = str(row.get('type', 'Transaction'))
                name = html.escape(str(row.get('name', 'Untitled entry')))
                date = html.escape(str(row.get('date', '')))
                icon = icons.get(tx_type, '•')
                activity_html += f'''<div class="dash-feed"><span class="dash-feed-icon">{icon}</span><div><div class="dash-feed-name">{name}</div><div class="dash-feed-meta">{html.escape(tx_type)} · {date}</div></div><span class="dash-feed-amount">PKR {float(row.get('amount', 0)):,.0f}</span></div>'''
        st.markdown(activity_html + '</div>', unsafe_allow_html=True)
    with tasks_col:
        task_html = '<div class="dash-panel"><p class="dash-panel-title">Construction checklist</p><p class="dash-panel-sub">Focus items for the active site.</p>'
        if status_df.empty:
            task_html += '<p class="dash-panel-sub">Checklist is not available yet.</p>'
        else:
            for _, task_row in status_df.head(5).iterrows():
                done = str(task_row.get('status', '')).lower() == 'done'
                task_name = html.escape(str(task_row.get('task_name', 'Site task')))
                marker = '✓' if done else '•'
                color, bg, label = ('#067647', '#ecfdf3', 'Completed') if done else ('#b54708', '#fffaeb', 'Pending')
                task_html += f'''<div class="dash-task"><span class="dash-task-bullet" style="background:{bg};color:{color}">{marker}</span><div><div class="dash-task-name">{task_name}</div><div class="dash-task-status">{label}</div></div></div>'''
        st.markdown(task_html + '</div>', unsafe_allow_html=True)

    st.markdown('''<div class="dash-company"><div><p class="dash-company-title">DEEWARYN.COM</p><div class="dash-company-text">Professional construction, development and project-management solutions.</div></div><div class="dash-company-info"><div class="dash-company-item"><strong>Chief Executive Officer</strong>Samii Ullah</div><div class="dash-company-item"><strong>Project Management</strong>Umer Sherin</div><div class="dash-company-item"><strong>Contact</strong>0332 0026666 · deewaryn@gmail.com</div><div class="dash-company-item"><strong>Office</strong>Bostan Khan Road, Shaheen Plaza,<br>Chaklala Scheme 3, Rawalpindi</div></div></div>''', unsafe_allow_html=True)
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
                    if photo_path and str(photo_path) != "nan": st.image(photo_path, use_container_width=True)
                    else: st.info("No Photo Uploaded.")
                with c_info:
                    st.markdown(f"**🪪 CNIC Identifier Pass:** {row['cnic']} | **💰 Total Pool Budget Allocation:** PKR {row['total_contract_amount']:,.0f}")
                    
                    stars = "⭐" * int(row['rating'] if row['rating'] else 5)
                    st.markdown(f"**📊 Performance Rating Score:** {stars}")
                    st.info(row['details'] if row['details'] else "No metadata profile details added.")
                    
                    st.markdown("##### 💵 Correlated Ledger Clearance Pipeline Sync")
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
                            st.metric(label="Sum Cleared Remittances", value=f"PKR {total_paid:,.0f}/-")
                        else:
                            st.warning("No payment logs linked under this exact structural profile context designation name.")
                            labor_payments = pd.DataFrame()
                    else: labor_payments = pd.DataFrame()

                    pdf_data = export_labor_profile_pdf(row, labor_payments)
                    st.write("##")
                    st.download_button(label="📄 Print Profile Evaluation Dossier", data=pdf_data, file_name=f"Labor_{str(row['name'])}.pdf", mime="application/pdf", key=f"dl_pdf_{row['id']}", type="primary")
                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()
        if is_auth:
            l_tid = st.text_input("Enter Worker Core Database Row ID to Delete")
            if st.button("🗑️ Delete Worker Record Permanently"):
                if l_tid:
                    supabase.table('labor_profiles').delete().eq('id', l_tid).execute()
                    st.cache_data.clear(); st.rerun()
    else: st.info(f"No active worker logs inside configuration directory: {current_project}")


# --- ORIGINAL HISTORY PAGES LOGIC (Project Restricted) ---
else:
    st.title(f"{menu} Terminal Portal")
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        elif "Pending Bills" in menu: f_df = df[df['type'] == 'Pending Bill']
        else: f_df = df.copy()
        
        search = st.text_input("🔎 Search targeted row indexing...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        st.dataframe(f_df, use_container_width=True)

        if "Pending Bills" in menu and not f_df.empty:
            st.subheader("✅ Mark Pending Bill as Paid")
            for _, row in f_df.iterrows():
                c1, c2 = st.columns([4,1])
                with c1:
                    st.write(f"ID #{row['id']} - {row['name']} - PKR {row['amount']:,.0f}")
                with c2:
                    if st.button("Mark Paid", key=f"paid_{row['id']}"):
                        update_transaction_status(row['id'], 'Material')

        st.metric("Total Operational Volume Aggregated", f"PKR {f_df['amount'].sum():,.0f}")
        
        if is_auth:
            tid = st.text_input("Enter Target Ledger ID to Remove")
            if st.button("🗑️ Remove Ledger Record Entry"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()

        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.download_button("📥 Export CSV Spreadsheet File", f_df.to_csv().encode('utf-8'), f"{menu}_{current_project}.csv", use_container_width=True)
        with c2: st.download_button("📄 Print Signature PDF Audit Ledger", export_to_pdf(f_df, menu), f"{menu}_{current_project}.pdf", use_container_width=True, type="primary")
    else: st.info(f"No active record data blocks synced under active site environment context: {current_project}")
