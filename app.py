import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components
import requests
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. DATA FETCH LOGIC (With Strict KeyError Fallbacks) ---
@st.cache_data(ttl=15)
def fetch_all_raw_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        df_raw = pd.DataFrame(res.data)
        if not df_raw.empty:
            # Safe checking for project context columns
            if 'project_context' not in df_raw.columns:
                if 'project' in df_raw.columns:
                    df_raw['project_context'] = df_raw['project']
                else:
                    df_raw['project_context'] = "Yousaf Colony"
        return df_raw
    except: 
        return pd.DataFrame()

@st.cache_data(ttl=15)
def fetch_all_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        df_labor = pd.DataFrame(res.data)
        
        # 🔥 CRITICAL FIX FOR THE KEYERROR IN SCREENSHOT 4 🔥
        # Agar labor_profiles ke andar 'project_context' ya 'project' nahi hai to fallback banayein
        if not df_labor.empty:
            if 'project_context' not in df_labor.columns:
                if 'project' in df_labor.columns:
                    df_labor['project_context'] = df_labor['project']
                else:
                    # Agar dono nahi hain to default initialize karein taake line 189 crash na ho
                    df_labor['project_context'] = "Yousaf Colony"
        return df_labor
    except: 
        return pd.DataFrame()

def fetch_project_status(project_name):
    try:
        res = supabase.table('project_status').select("*").execute()
        df_status = pd.DataFrame(res.data)
        if not df_status.empty and 'project_context' in df_status.columns:
            df_filtered = df_status[df_status['project_context'] == project_name]
            if not df_filtered.empty: return df_filtered
        
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])
    except: 
        tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Polishing", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
        return pd.DataFrame([{"task_name": t, "status": "Pending", "project_context": project_name} for t in tasks])

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- ✨ EASTUTE MINIMALIST LUXURY DESIGN SYSTEM ✨ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #f4f5f7 !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1150px !important;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio > div { gap: 6px !important; }
    div[data-testid="stSidebarUserContent"] div.stRadio label {
        background-color: #f9fafb;
        padding: 10px 16px !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        border: 1px solid #e5e7eb !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-checked="true"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-color: #0f172a !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebarUserContent"] div.stRadio [data-testid="stFiberManualRecord"] { display: none !important; }
    
    div.stButton > button {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #d1d5db;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        border-color: #0f172a;
        background-color: #f9fafb;
    }
    div.stButton > button[data-testid="baseButton-primary"] {
        background: #0f172a !important;
        color: white !important;
        border: none !important;
    }

    .premium-header {
        background: #ffffff;
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 30px;
    }
    
    .beauty-card {
        background: #ffffff;
        padding: 22px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
    }
    
    .premium-voucher-box {
        background-color: #ffffff; 
        border: 2px dashed #9ca3af; 
        padding: 40px; 
        border-radius: 16px; 
        max-width: 600px; 
        margin: 20px auto; 
        color: #0f172a;
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] div {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA INITIALIZATION ---
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

# --- Safe Dataframe Filtering Architecture ---
if not raw_df.empty and 'project_context' in raw_df.columns:
    df = raw_df[raw_df['project_context'] == current_project]
else:
    df = pd.DataFrame()

if not raw_labor_df.empty and 'project_context' in raw_labor_df.columns:
    labor_df = raw_labor_df[raw_labor_df['project_context'] == current_project]
else:
    labor_df = pd.DataFrame()


# --- 5. SAFE TRANSACTION ENGINE DIALOG ---
@st.dialog("📝 Log Dynamic Transaction Entry", dismissible=False)
def popup_transaction_entry(ftype, current_project):
    st.write(f"Add **{ftype}** entry for project: **{current_project}**")
    d_date = st.date_input("Date", datetime.now())
    d_name = st.text_input("Title / Particular Name *")
    d_amt = st.number_input("Amount (PKR) *", min_value=0)
    
    col1, col2 = st.columns(2)
    d_occ = col1.text_input("Occupation / Job (If Labor)")
    d_rec = col2.text_input("Received By")
    d_meth = st.selectbox("Payment Method", ["Cash", "Online", "Cheque"])
    d_det = st.text_area("Notes / Particular Specs")
    
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("➕ Submit Transaction", type="primary", use_container_width=True):
        if d_name and d_amt > 0:
            payload = {
                "date": str(d_date), 
                "type": str(ftype), 
                "name": str(d_name), 
                "amount": float(d_amt), 
                "detail": str(d_det),
                "occupation": str(d_occ),
                "received_by": str(d_rec),
                "pay_method": str(d_meth),
                "project_context": str(current_project),
                "project": str(current_project)
            }
            
            success = False
            try:
                supabase.table('transactions').insert(payload).execute()
                success = True
            except:
                try:
                    # Backup try: Send fallback basic scheme values if extra columns trigger error
                    minimal_payload = {
                        "date": str(d_date), "type": str(ftype), "name": str(d_name), "amount": float(d_amt), "detail": str(d_det)
                    }
                    supabase.table('transactions').insert(minimal_payload).execute()
                    success = True
                except:
                    st.error("Supabase dynamic mapping failure. Check columns schema keys inside panel.")
            
            if success:
                st.cache_data.clear()
                st.success("Entry Saved Safely!")
                st.rerun()
        else:
            st.error("Please fill required fields.")
            
    if btn_col2.button("❌ Cancel", use_container_width=True):
        st.rerun()


# --- 6. SIDEBAR MENU CONTROL ---
with st.sidebar:
    st.markdown("<h2 style='color:#0f172a; font-weight:800; margin-bottom:0; font-size:22px; letter-spacing:-0.5px;'>DEEWARY.COM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:10px; color:#6b7280; font-weight:600; margin-top:2px; text-transform:uppercase; letter-spacing:1px;'>Corporate Portal ERP</p>", unsafe_allow_html=True)
    st.divider()
    
    selected_proj = st.selectbox("Working Site Selection:", st.session_state["custom_projects"])
    st.session_state["selected_project"] = selected_proj
    st.divider()
    
    menu = st.radio("Navigation Portal", ["📊 Dashboard View", "📑 Receipt Voucher System", "👷 Labor Ledger History"], label_visibility="collapsed")
    st.divider()
    
    st.markdown("<p style='font-size:11px; font-weight:700; color:#374151; text-transform:uppercase;'>⚡ Quick Entry Panel</p>", unsafe_allow_html=True)
    if st.button("➕ Log Transaction Entry", use_container_width=True):
        popup_transaction_entry("Expense", current_project)


# --- 7. MAIN INTERFACE RENDERING ---
if "Dashboard" in menu:
    st.markdown(f"""
        <div class="premium-header">
            <h1 style="color: #0f172a; margin: 0; font-weight:800; letter-spacing: -0.5px; font-size:32px;">DEEWARY<span style="color:#6b7280;">.COM</span></h1>
            <p style="color: #6b7280; letter-spacing: 0.5px; font-size: 13px; margin: 4px 0 0 0; font-weight:500; text-transform:uppercase;">Premium System Interface &bull; Site Context: {current_project}</p>
        </div>
    """, unsafe_allow_html=True)
    
    inc = df[df['type'] == 'Income']['amount'].sum() if not df.empty else 0
    exp = df[df['type'] != 'Income']['amount'].sum() if not df.empty else 0
    net_bal = inc - exp
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1: st.markdown(f"<div class='beauty-card'><p style='color:#6b7280; margin:0; font-size:11px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>💰 Total Capital Inflow</p><h2 style='color:#0f172a; margin:8px 0 0 0; font-weight:800; font-size:24px;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi2: st.markdown(f"<div class='beauty-card'><p style='color:#6b7280; margin:0; font-size:11px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>📉 Outflow Disbursed</p><h2 style='color:#0f172a; margin:8px 0 0 0; font-weight:800; font-size:24px;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
    with col_kpi3: st.markdown(f"<div class='beauty-card'><p style='color:#6b7280; margin:0; font-size:11px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;'>⚖️ Net Liquid Reserve</p><h2 style='color:#0f172a; margin:8px 0 0 0; font-weight:800; font-size:24px;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    st.write("##")
    st.markdown("### 📋 Active Transactions Log Data")
    if not df.empty:
        st.dataframe(df[['date', 'type', 'name', 'amount', 'detail', 'pay_method']], use_container_width=True)
    else:
        st.info("Is active project context ka koi record data available nahi hai.")

elif "Voucher" in menu:
    st.markdown("<div style='text-align:center; padding: 20px 0;'><h2 style='color:#0f172a; font-weight:800; margin:0;'>📑 Logistic Clearance Voucher</h2></div>", unsafe_allow_html=True)
    st.divider()
    
    if not df.empty:
        df['voucher_label'] = "[" + df['type'].astype(str).str.upper() + "] ID: " + df['id'].astype(str) + " - " + df['name'].astype(str) + " (PKR " + df['amount'].map('{:,.0f}'.format) + ")"
        selected_log = st.selectbox("Select System Transaction Target Entry:", df['voucher_label'].tolist())
        v_row = df[df['voucher_label'] == selected_log].iloc[0]
        
        v_prefix = "INC" if v_row['type'] == "Income" else "EXP"
        v_number = f"DW-{v_prefix}-{1000 + int(v_row['id'])}"
        
        st.markdown(f"""
            <div class="premium-voucher-box">
                <div style="text-align: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 25px;">
                    <h2 style="margin: 0; color: #0f172a; font-weight:800; font-size:26px; letter-spacing: 1px;">DEEWARY.COM</h2>
                    <p style="margin: 6px 0 0 0; font-size: 11px; color: #6b7280; font-weight: 600; text-transform:uppercase; letter-spacing:1.5px;">OFFICIAL LOGISTIC TRANSACTION VOUCHER</p>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 14px; font-size: 14px;"><span style="color:#6b7280;">Voucher No:</span><b style="color:#0f172a; font-family: monospace; font-size:15px;">{v_number}</b></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 14px; font-size: 14px;"><span style="color:#6b7280;">Log Date:</span><span style="color:#0f172a; font-weight:600;">{v_row['date']}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 14px; font-size: 14px;"><span style="color:#6b7280;">Particular Name:</span><b style="color:#0f172a; font-size: 15px;">{v_row['name']}</b></div>
                <div style="background: #f9fafb; padding: 15px; border-radius: 8px; font-size: 13px; border: 1px solid #e5e7eb; margin-bottom: 30px; color:#4b5563;">{v_row['detail'] if v_row['detail'] else '-'}</div>
                <div style="border-top: 2px dashed #9ca3af; padding-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="color:#ef4444; font-weight:800; font-size:16px;">VOLUME TOTAL:</span>
                    <span style="color:#ef4444; font-weight:800; font-size:22px; font-family: monospace;">PKR {v_row['amount']:,.0f}/-</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

elif "Labor" in menu:
    st.markdown("### 👷 Labor Force Profiles Registry Ledger")
    if not labor_df.empty:
        st.dataframe(labor_df, use_container_width=True)
    else:
        st.info("Is site context ke liye koi labor data registered nahi mila.")
