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

    

    total_val = pdf_df['amount'].sum() if not pdf_df.empty else 0

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

    [data-testid="stAppViewContainer"] {

        background-image: url("https://i.postimg.cc/Vs46KqYW/ej-yao-D46m-XLs-QRJw-unsplash.jpg");

        background-size: cover;

        background-position: center;

        background-attachment: fixed;

    }



    .block-container {

        background: rgba(255, 255, 255, 0.85) !important;

        backdrop-filter: blur(10px) !important;

        -webkit-backdrop-filter: blur(10px) !important;

        border-radius: 30px !important;

        border: 1px solid rgba(255, 255, 255, 0.4) !important;

        padding: 2rem !important;

    }



    h1, h2, h3, p, div, span {

        color: #0f172a !important;

        font-weight: 500;

    }

    

    .kpi-card {

        background: white;

        padding: 20px;

        border-radius: 15px;

        border: 1px solid #e2e8f0;

        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);

    }

    

    .digital-voucher {

        background: white;

        border: 2px solid #e2e8f0;

        border-radius: 20px;

        padding: 30px;

        max-width: 600px;

        margin: auto;

        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

    }

    

    /* New Project Header Box Styling */

    .project-banner-box {

        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);

        border-radius: 20px;

        padding: 24px;

        border: 1px solid #334155;

        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);

        margin-bottom: 25px;

    }

    </style>

""", unsafe_allow_html=True)



# --- 4. DATA FETCH LOGIC ---

@st.cache_data(ttl=5) 

def fetch_all_raw_data():

    try:

        res = supabase.table('transactions').select("*").order('date', desc=True).execute()

        return pd.DataFrame(res.data)

    except: return pd.DataFrame()



@st.cache_data(ttl=5)

def fetch_all_labor_profiles():

    try:

        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()

        return pd.DataFrame(res.data)

    except: return pd.DataFrame()



def fetch_project_status(project_name):

    try:

        res = supabase.table('project_status').select("*").eq('project_context', project_name).execute()

        df_status = pd.DataFrame(res.data)

        if not df_status.empty:

            return df_status

        

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





# --- 5. INITIALIZE PROJECT REGISTRY STATE ---

raw_df = fetch_all_raw_data()

raw_labor_df = fetch_all_labor_profiles()



if "custom_projects" not in st.session_state:

    st.session_state["custom_projects"] = ["Yousaf Colony"]



# Global Database se automatic unique projects list extract karke load karna

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

                    supabase.table('project_status').insert({"task_name": t, "status": "Pending", "project_context": new_proj_name}).execute()

                except:

                    pass

            

            st.success(f"Project '{new_proj_name}' successfully created!")

            st.cache_data.clear()

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

                "details": str(l_details),

                "project_context": str(current_project) 

            }

            

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

                "image_url": str(img_url),

                "occupation": str(d_occ),

                "received_by": str(d_rec),

                "pay_method": str(d_meth),

                "project_context": str(current_project) 

            }

            

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

            supabase.table('project_status').upsert({"task_name": task, "status": stat, "project_context": current_project}, on_conflict="task_name,project_context").execute()

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





# --- 7. CRITICAL STAGE: HARD DYNAMIC PROJECT FILTERS ---

current_project = st.session_state["selected_project"]



if not raw_df.empty:

    if 'project_context' in raw_df.columns:

        df = raw_df[raw_df['project_context'] == current_project]

    else:

        df = pd.DataFrame() 

else:

    df = pd.DataFrame()



if not raw_labor_df.empty:

    if 'project_context' in raw_labor_df.columns:

        labor_df = raw_labor_df[raw_labor_df['project_context'] == current_project]

    else:

        labor_df = pd.DataFrame()

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





# --- 9. RENDER ACTIVE MAIN PAGE ---

if "Dashboard" in menu:

    # Top Branded corporate header

    st.markdown(f"""

        <div style="margin-bottom: 20px;">

            <h1 style="color: #0f172a; margin: 0; font-weight:800; letter-spacing: -0.5px; font-size:36px;">DEEWARYN<span style="color:#FF4B4B;">.COM</span></h1>

            <p style="color: #64748b; letter-spacing: 0.5px; font-size: 13px; margin: 4px 0 0 0; font-weight:500;">PREMIUM REAL ESTATE DEVELOPMENT NETWORK • C.E.O: SARDAR SAMI ULLAH</p>

        </div>

    """, unsafe_allow_html=True)



    # --- NEW DYNAMIC HEADLINE & DETAIL BOX FOR ACTIVE PROJECT ---

    total_logs_count = len(df) if not df.empty else 0

    active_workers_count = len(labor_df) if not labor_df.empty else 0

    

    st.markdown(f"""

        <div class="project-banner-box">

            <span style="color: #FF4B4B; font-weight: 800; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; display: block; margin-bottom: 4px;">📂 CURRENTLY VIEWING SITE</span>

            <h2 style="color: #ffffff !important; font-weight: 800; font-size: 30px; margin: 0; letter-spacing: -0.5px;">PROJECT: {current_project.upper()}</h2>

            <p style="color: #94a3b8 !important; font-size: 14px; margin: 8px 0 16px 0; line-height: 1.6; font-weight: 400;">

                Yeh dashboard temporary aur real-time state metrics ke mutabik <b>{current_project}</b> ka complete live infrastructure data, payments cashflow records, aur layout development parameters show kar raha hai. Is project file se related a to z entries database security layers ke sath filtered hain.

            </p>

            <div style="display: flex; gap: 20px; flex-wrap: wrap; border-top: 1px solid #334155; padding-top: 12px;">

                <span style="color: #cbd5e1 !important; font-size: 12px; font-weight: 600;">📊 Total Logs Filed: <b style="color: #FF4B4B !important;">{total_logs_count} Entries</b></span>

                <span style="color: #cbd5e1 !important; font-size: 12px; font-weight: 600;">👷 Registered Site Force: <b style="color: #38bdf8 !important;">{active_workers_count} Workers</b></span>

                <span style="color: #cbd5e1 !important; font-size: 12px; font-weight: 600;">📍 Sync Status: <b style="color: #4ade80 !important;">Live Guard Secure</b></span>

            </div>

        </div>

    """, unsafe_allow_html=True)

    # -----------------------------------------------------------



    inc, lab_exp, mat_exp, exp, net_bal = 0, 0, 0, 0, 0

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

        except: daily_burn_rate = 0



        if net_bal < 50000:

            st.markdown(f"""<div class="alert-box" style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 10px; margin-bottom: 10px; border-radius: 5px;">🚨 RUNNING BALANCE WARNING: Capital pool reserve is critical (PKR {net_bal:,.0f}) inside {current_project}.</div>""", unsafe_allow_html=True)

        elif daily_burn_rate > 0:

            days_left = net_bal / daily_burn_rate

            if days_left <= 5:

                st.markdown(f"""<div class="alert-box" style="background-color: #fffbeb; border-left: 5px solid #f59e0b; color: #78350f; padding: 10px; margin-bottom: 10px; border-radius: 5px;">⚠️ RESERVES DEFICIT: Capital status for {current_project} estimated to expire in ~{days_left:.1f} days.</div>""", unsafe_allow_html=True)

            else:

                st.markdown(f"""<div class="forecast-box" style="background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 10px; margin-bottom: 10px; border-radius: 5px;">📈 RUNWAY STABILITY PROJECTION: Safe operational buffer mapped for active site context: ~{days_left:.1f} Days.</div>""", unsafe_allow_html=True)



    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>💰 TOTAL CAPITAL ARRIVAL</p><h2 style='color:#15803d; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)

    with col_kpi2: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>📉 DISBURSED OUTFLOWS</p><h2 style='color:#b91c1c; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)

    with col_kpi3: 

        bal_color = "#15803d" if net_bal >= 0 else "#b91c1c"

        st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>⚖️ NET RUNNING BALANCES</p><h2 style='color:{bal_color}; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)



    st.write("##")

    st.metric('📋 Pending Bills Total Stack', f"PKR {df[df['type'] == 'Pending Bill']['amount'].sum() if not df.empty else 0:,.0f}")



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

        chart_code = f"graph LR\nA[Start] --> B{{Progress: {prog_val}%}}\nstyle B fill:#FF4B4B,color:#fff,stroke:none"

        components.html(f"<div style='background:#ffffff; border-radius:20px; padding:15px; border:1px solid #e2e8f0;'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=120)



    with col_right:

        st.markdown("### 📝 Architectural Nodes Checklist")

        st.write(f"✅ Cleared Status Tasks: **{done_tasks}** | ⏳ Pending Core Nodes: **{total_tasks - done_tasks}**")

        if st.button("Re-Sync Ledger Memory Cache", use_container_width=True): st.cache_data.clear(); st.rerun()



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





# --- ISOLATED INDEPENDENT PAGE: 📑 RECEIPT VOUCHER SYSTEM ---

elif menu == "📑 Receipt Voucher System":

    st.title(f"📑 Corporate Allocation Voucher Module")

    st.write(f"Active Project Context: **{current_project}**")

    st.divider()

    

    if not df.empty:

        df['voucher_label'] = "[" + df['type'].astype(str).str.upper() + "] ID: " + df['id'].astype(str) + " - " + df['name'].astype( 

