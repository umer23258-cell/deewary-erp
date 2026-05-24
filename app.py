import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewaryn.com ERP", layout="wide", page_icon="🏗️")

# --- ULTRA PREMIUM BRANDED LUXURY CSS INJECTION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Typography Override & Background Image Logic */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        
        /* Background Image Link */
        background-image: url("https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=2070") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }
    
    /* Main area overlay wrapper for better content readability (Glassmorphic Tint) */
    [data-testid="stMainBlockContainer"] {
        background: rgba(248, 250, 252, 0.95) !important; 
        border-radius: 24px;
        margin-top: 1.5rem !important;
        margin-bottom: 2rem !important;
        padding: 2.5rem !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.05);
    }
    
    .block-container {
        max-width: 1250px !important;
    }

    /* Sidebar Clean Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.02) !important;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio > div {
        gap: 6px !important;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio label {
        background-color: #f1f5f9;
        padding: 12px 16px !important;
        border-radius: 12px !important;
        color: #334155 !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 2px;
        cursor: pointer;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio label:hover {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-checked="true"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15) !important;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio label [data-testid="stMarkdownContainer"] p {
        color: inherit !important;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio [data-testid="stFiberManualRecord"] {
        display: none !important;
    }
    
    div.stButton > button {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        padding: 12px 24px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        width: 100%;
    }
    div.stButton > button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.08);
        transform: translateY(-1px);
    }
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #FF4B4B 0%, #dc2626 100%);
        color: white !important;
        border: none !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        box-shadow: 0 6px 20px rgba(220, 38, 38, 0.25);
    }

    .header-box {
        text-align: center;
        background: #ffffff;
        padding: 40px 20px;
        border-radius: 28px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01), 0 10px 15px -3px rgba(0, 0, 0, 0.02);
        margin-bottom: 30px;
        border: 1px solid #f1f5f9;
        position: relative;
    }
    .header-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 5px;
        background: linear-gradient(90deg, #FF4B4B, #dc2626);
        border-radius: 28px 28px 0 0;
    }
    
    .kpi-card {
        background: #ffffff;
        padding: 26px;
        border-radius: 22px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.02), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
        transition: all 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.04);
    }
    
    .alert-box {
        background-color: #fff5f5;
        border-left: 5px solid #ef4444;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 25px;
        color: #991b1b;
        font-size: 14px;
        font-weight: 600;
        border: 1px solid #fee2e2;
    }
    .forecast-box {
        background-color: #f0fdf4;
        border-left: 5px solid #22c55e;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 25px;
        color: #166534;
        font-size: 14px;
        font-weight: 600;
        border: 1px solid #dcfce7;
    }
    
    .digital-voucher {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 35px;
        border-radius: 28px;
        max-width: 500px;
        margin: 20px auto;
        color: #0f172a;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.06);
    }
    
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem !important;
        }
        .header-box {
            padding: 30px 15px;
            border-radius: 20px;
        }
        .kpi-card {
            padding: 20px;
            border-radius: 18px;
        }
        div[data-testid="stSidebarUserContent"] div.stRadio label {
            padding: 14px 16px !important;
            font-size: 14px !important;
        }
    }
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
    tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing/Grinding", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
    try:
        res = supabase.table('project_status').select("*").eq('project_context', project_name).execute()
        df_status = pd.DataFrame(res.data)
        if not df_status.empty:
            return df_status
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])
    except: 
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
            else:
                st.error("Invalid Secret Pin")
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
            
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing/Grinding", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            for t in tasks:
                try:
                    supabase.table('project_status').insert({"task_name": t, "status": "Pending", "project_context": new_proj_name}).execute()
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
    task = st.selectbox("Select Task Line Target", status_df['task_name'].tolist() if 'task_name' in status_df.columns else [])
    stat = st.radio("Status Milestone Alignment", ["Pending", "Done"], horizontal=True)
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_btn = st.button("⚡ Update Status", type="primary", use_container_width=True)
    with btn_col2:
        cancel_btn = st.button("❌ Cancel", use_container_width=True)
        
    if submit_btn:
        try:
            supabase.table('project_status').upsert({"task_name": task, "status": stat, "project_context": current_project}, on_conflict="task_name").execute()
            st.cache_data.clear()
            st.success("Task updated successfully!")
            st.rerun()
        except:
            st.error("Schema configuration error while changing status state.")
                
    if cancel_btn:
        st.rerun()

# --- 7. DYNAMIC PROJECT FILTERS ---
current_project = st.session_state["selected_project"]

if not raw_df.empty:
    df = raw_df[raw_df['project_context'] == current_project] if 'project_context' in raw_df.columns else raw_df.copy()
else:
    df = pd.DataFrame()

if not raw_labor_df.empty:
    labor_df = raw_labor_df[raw_labor_df['project_context'] == current_project] if 'project_context' in raw_labor_df.columns else raw_labor_df.copy()
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
        ["📊 Dashboard View", "📑 Receipt Voucher System", "💰 Income Ledger", "👷 Labor Ledger History", "🏗️ Material Log Vault", "👷 Labor Force Folder", "🔍 Search & Audit Reports"],
        label_visibility="collapsed"
    )
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.markdown("<p style='font-size:11px; font-weight:700; color:#166534; text-transform:uppercase; margin-bottom:8px;'>⚡ Admin Quick Control</p>", unsafe_allow_html=True)
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

# --- 9. RENDER ACTIVE MAIN PAGE ---
if "Dashboard" in menu:
    st.markdown(f"""
        <div class="header-box">
            <h1 style="color: #0f172a; margin: 0; font-weight:800; letter-spacing: -0.5px; font-size:36px;">DEEWARYN<span style="color:#FF4B4B;">.COM</span></h1>
            <p style="color: #64748b; letter-spacing: 0.5px; font-size: 14px; margin: 6px 0 18px 0; font-weight:500;">PREMIUM SYSTEM INTERFACE • DESIGNATED CONTEXT: {current_project.upper()}</p>
            <div style="background: rgba(255, 75, 75, 0.06); color: #FF4B4B; display: inline-block; padding: 6px 20px; border-radius: 30px; font-weight: 700; font-size: 13px; border: 1px solid rgba(255, 75, 75, 0.15);">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    inc, lab_exp, mat_exp, exp, net_bal = 0, 0, 0, 0, 0
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum() if 'type' in df.columns else 0
        lab_exp = df[df['type'] == 'Labor']['amount'].sum() if 'type' in df.columns else 0
        mat_exp = df[df['type'] == 'Material']['amount'].sum() if 'type' in df.columns else 0
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
            st.markdown(f"""<div class="alert-box">🚨 RUNNING BALANCE WARNING: Capital pool reserve is critical (PKR {net_bal:,.0f}) inside {current_project}.</div>""", unsafe_allow_html=True)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            if days_left <= 5:
                st.markdown(f"""<div class="alert-box" style="background-color: #fffbeb; border-left-color: #f59e0b; color: #78350f; border: 1px solid #fef3c7;">⚠️ RESERVES DEFICIT: Capital status for {current_project} estimated to expire in ~{days_left:.1f} days.</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="forecast-box">📈 RUNWAY STABILITY PROJECTION: Safe operational buffer mapped for active site context: ~{days_left:.1f} Days.</div>""", unsafe_allow_html=True)

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>💰 TOTAL CAPITAL ARRIVAL</p><h2 style='color:#15803d; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi2: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>📉 DISBURSED OUTFLOWS</p><h2 style='color:#b91c1c; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi3: 
        bal_color = "#15803d" if net_bal >= 0 else "#b91c1c"
        st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>⚖️ NET RUNNING BALANCES</p><h2 style='color:{bal_color}; margin:8px 0 0 0; font-weight:800; font-size:26px; letter-spacing:-0.5px;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    st.write("##")
    st.subheader("🏗️ Construction Milestone Checklist Tracker")
    status_df = fetch_project_status(current_project)
    
    if not status_df.empty:
        col_chk1, col_chk2 = st.columns(2)
        mid = len(status_df) // 2
        
        with col_chk1:
            for idx, row in status_df.iloc[:mid].iterrows():
                icon = "✅" if row['status'] == "Done" else "⏳"
                st.markdown(f"**{icon} {row['task_name']}** — *{row['status']}*")
        with col_chk2:
            for idx, row in status_df.iloc[mid:].iterrows():
                icon = "✅" if row['status'] == "Done" else "⏳"
                st.markdown(f"**{icon} {row['task_name']}** — *{row['status']}*")

elif "Receipt Voucher" in menu:
    st.subheader("📑 Digital Receipt Voucher Generation")
    if not df.empty:
        v_id = st.selectbox("Select Transaction Log Item:", df['id'].tolist() if 'id' in df.columns else [])
        v_row = df[df['id'] == v_id].iloc[0]
        
        st.markdown(f"""
        <div class="digital-voucher">
            <h3 style="text-align:center; color:#FF4B4B; margin-top:0;">DEEWARYN.COM ERP</h3>
            <p style="text-align:center; font-size:12px; color:#64748b;">OFFICIAL DIGITAL PAYMENT VOUCHER</p>
            <hr>
            <p><b>Voucher Reference ID:</b> {v_row.get('id', 'N/A')}</p>
            <p><b>Date Documented:</b> {v_row.get('date', 'N/A')}</p>
            <p><b>Transaction Category:</b> {v_row.get('type', 'N/A')}</p>
            <p><b>Particular Particulars:</b> {v_row.get('name', 'N/A')}</p>
            <h4 style="background:#f1f5f9; padding:10px; border-radius:8px;"><b>Net Amount Executed:</b> PKR {v_row.get('amount', 0):,.0f}</h4>
            <p><b>Payment Channel:</b> {v_row.get('pay_method', 'Cash')}</p>
            <p><b>Remarks:</b> {v_row.get('detail', 'None')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Active site context containing zero database transaction references.")

elif "Income Ledger" in menu:
    st.subheader("💰 Project Capital Inflow Registry")
    inc_df = df[df['type'] == 'Income'] if not df.empty and 'type' in df.columns else pd.DataFrame()
    if not inc_df.empty:
        st.dataframe(inc_df[['id', 'date', 'name', 'amount', 'pay_method', 'detail']], use_container_width=True)
    else:
        st.info("No active capital arrivals logged for this project.")

elif "Labor Ledger History" in menu:
    st.subheader("👷 Labor Force Ledger Disburse Records")
    lab_exp_df = df[df['type'] == 'Labor'] if not df.empty and 'type' in df.columns else pd.DataFrame()
    if not lab_exp_df.empty:
        st.dataframe(lab_exp_df[['id', 'date', 'name', 'occupation', 'amount', 'pay_method', 'detail']], use_container_width=True)
    else:
        st.info("No active labor financial transactions found.")

elif "Material Log Vault" in menu:
    st.subheader("🏗️ Material Invoices & Procurement Records")
    mat_df = df[df['type'] == 'Material'] if not df.empty and 'type' in df.columns else pd.DataFrame()
    if not mat_df.empty:
        for idx, row in mat_df.iterrows():
            with st.expander(f"📦 {row.get('date')} — {row.get('name')} (PKR {row.get('amount', 0):,.0f})"):
                st.write(f"**Details:** {row.get('detail')}")
                st.write(f"**Payment Method:** {row.get('pay_method')}")
                if row.get('image_url'):
                    st.image(row['image_url'], caption="Uploaded Invoice Copy", width=400)
    else:
        st.info("No procurement invoices documented yet.")

elif "Labor Force Folder" in menu:
    st.subheader("👤 Labor Profile Dossiers")
    if not labor_df.empty:
        selected_labor = st.selectbox("Select Worker Profile:", labor_df['name'].tolist())
        l_row = labor_df[labor_df['name'] == selected_labor].iloc[0]
        
        p_history = df[(df['type'] == 'Labor') & (df['name'] == selected_labor)] if not df.empty and 'type' in df.columns else pd.DataFrame()
        
        col_prof1, col_prof2 = st.columns([1, 2])
        with col_prof1:
            if l_row.get('photo_url'):
                st.image(l_row['photo_url'], use_container_width=True)
            else:
                st.info("No profile picture uploaded.")
        with col_prof2:
            st.markdown(f"### **Name:** {l_row.get('name')}")
            st.write(f"**Skill / Occupation:** {l_row.get('occupation', 'General')}")
            st.write(f"**Contact Number:** {l_row.get('phone', 'N/A')}")
            st.write(f"**CNIC Record:** {l_row.get('cnic', 'N/A')}")
            st.markdown(f"#### **Contract Value:** PKR {l_row.get('total_contract_amount', 0):,.0f}")
            st.write(f"**Internal Management Profile Notes:** {l_row.get('details', 'N/A')}")
            
        st.write("---")
        st.write("#### 💵 Ledger Log Statements")
        if not p_history.empty:
            st.dataframe(p_history[['date', 'amount', 'pay_method', 'detail']], use_container_width=True)
        else:
            st.info("No dynamic payment records linked with this structural profile.")
    else:
        st.info("No profile structures synchronized inside this site scope registry.")

elif "Search & Audit Reports" in menu:
    st.subheader("🔍 Master Audit Ledger")
    if not df.empty:
        st.dataframe(df[['id', 'date', 'type', 'name', 'amount', 'pay_method', 'detail']], use_container_width=True)
    else:
        st.info("Database matrix contains no operational data.")
