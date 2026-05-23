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


# --- 6. POPUP DIALOG FORMS (With Submit + Cancel Side-by-Side Control) ---
@st.dialog("📁 Create New Project Site Context", dismissible=False)
def popup_create_project():
    new_proj_name = st.text_input("Project / Plot Site Name (e.g., G-13 Plot, CBR Town)*").strip()
    st.write("ℹ️ *Note: Naya project aap ki session state aur dashboard par active ho jayega.*")
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("🚀 Launch Project Context", type="primary", use_container_width=True)
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
                    supabase.table('project_status').insert({"task_name": t, "status": "Pending", "project_context": new_proj_name}).execute()
                except:
                    try:
                        supabase.table('project_status').upsert({"task_name": t, "status": "Pending", "project_context": new_proj_name}, on_conflict="task_name").execute()
                    except:
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
        submit_btn = st.button("💾 Save Profile Application", type="primary", use_container_width=True)
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
        submit_btn = st.button("➕ Submit Transaction", type="primary", use_container_width=True)
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
        submit_btn = st.button("⚡ Update Task Line", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        try:
            supabase.table('project_status').upsert({"task_name": task, "status": stat, "project_context": current_project}, on_conflict="task_name").execute()
            st.cache_data.clear()
            st.success("Task updated successfully!")
            st.rerun()
        except:
            try:
                supabase.table('project_status').insert({"task_name": task, "status": stat, "project_context": current_project}).execute()
                st.cache_data.clear()
                st.success("Task aligned successfully!")
                st.rerun()
            except Exception as e:
                st.error("Schema constraint failed to align state.")
                
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


# --- 8. SIDEBAR DESIGN ---
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
    
    menu = st.radio(
        "Go To", 
        ["📊 Dashboard", "📑 Receipt Voucher System", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"]
    )
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
        st.write("### ⚡ Quick Actions (Popups)")
        if st.button("➕ Income", use_container_width=True): popup_transaction_entry("Income", st.session_state["selected_project"])
        if st.button("👷 Labor", use_container_width=True): popup_transaction_entry("Labor", st.session_state["selected_project"])
        if st.button("🏗️ Material", use_container_width=True): popup_transaction_entry("Material", st.session_state["selected_project"])
        if st.button("📝 Register New Labor Profile", use_container_width=True): popup_register_labor(st.session_state["selected_project"])
        if st.button("📁 Create New Project Site", use_container_width=True): popup_create_project()
        st.divider()
        if st.button("⚙️ Change Task Status", use_container_width=True): 
            _status_df = fetch_project_status(st.session_state["selected_project"])
            popup_update_status(st.session_state["selected_project"], _status_df)
        if st.button("Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption=f"Active Site: {st.session_state['selected_project']}")


# --- 9. RENDER ACTIVE MAIN PAGE ---
if menu == "📊 Dashboard":
    st.markdown(f"""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px;">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px; font-size: 14px; margin-bottom: 10px;">PREMIUM SITE MANAGEMENT: {current_project.upper()}</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

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
        if st.button("Force Refresh Tracker Context", use_container_width=True): st.cache_data.clear(); st.rerun()

    st.divider()
    st.markdown("### 🏗️ Checklist Mapping")
    t_cols = st.columns(3)
    if not status_df.empty:
        for i, row in status_df.reset_index().iterrows():
            with t_cols[i % 3]:
                icon = "✅" if row['status'] == "Done" else "⏳"
                bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
                st.markdown(f'<div style="background:{bg}; padding:10px; border-radius:10px; margin-bottom:5px; border-left:5px solid #FF4B4B;"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)


# --- ISOLATED INDEPENDENT PAGE: 📑 RECEIPT VOUCHER SYSTEM ---
elif menu == "📑 Receipt Voucher System":
    st.title(f"📑 System Automated Receipt Slip / Voucher Generator ({current_project})")
    st.write("Kisi bhi transaction log entry ko select karein taake uska official premium digital voucher display ho.")
    st.divider()
    
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
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #6c757d; font-weight: bold;">OFFICIAL LOGISTIC TRANSACTION VOUCHER</p>
                </div>
                <div class="voucher-row"><span>Voucher No:</span><b>{v_number}</b></div>
                <div class="voucher-row"><span>Log Date:</span><span>{v_row['date']}</span></div>
                <div class="voucher-row"><span>Flow Category:</span><b>{str(v_row['type']).upper()}</b></div>
                <div class="voucher-row"><span>Particular Name:</span><b>{v_row['name']}</b></div>
                <div class="voucher-row"><span>Job Designation:</span><span>{v_row.get('occupation', 'N/A') if pd.notna(v_row.get('occupation')) else 'N/A'}</span></div>
                <div class="voucher-row"><span>Authorized Dispense:</span><span>{v_row.get('received_by', 'N/A') if pd.notna(v_row.get('received_by')) else 'N/A'}</span></div>
                <div class="voucher-row"><span>Payment Channel:</span><span>{v_row.get('pay_method', 'Cash') if pd.notna(v_row.get('pay_method')) else 'Cash'}</span></div>
                <p style="font-size: 12px; background: #f8f9fa; padding: 8px; border-radius: 5px; font-style: italic; border-left: 3px solid #FF4B4B;">Internal Remarks: {v_row['detail'] if v_row['detail'] else '-'}</p>
                <div class="voucher-total"><div style="display: flex; justify-content: space-between;"><span>VOLUME TOTAL:</span><span>PKR {v_row['amount']:,.0f}/-</span></div></div>
            </div>
        """, unsafe_allow_html=True)
    else: 
        st.info(f"Is project site ({current_project}) ke under filhal koi transaction record mojud nahi hai.")


# --- LABOR PROFILES APPLICATION PAGE ---
elif menu == "👷 Labor Profiles Application":
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
    st.title(f"{menu} ({current_project})")
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
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
        c1.download_button("📥 Excel", f_df.to_csv().encode('utf-8'), f"{menu}_{current_project}.csv")
        c2.download_button("📄 PDF Report", export_to_pdf(f_df, menu), f"{menu}_{current_project}.pdf")
    else: st.info(f"No database ledger records tracked under project site: {current_project}")
