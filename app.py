import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components
import requests

# PDF ke liye libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. AUTOMATED LOW BALANCE NOTIFIER FUNCTION ---
def send_automated_low_balance_alert(current_balance):
    sms_api_url = st.secrets.get("SMS_API_URL", "")
    receiver_number = st.secrets.get("ALERT_PHONE_NUMBER", "03001234567")
    msg_text = f"⚠️ DEEWARY ERP ALERT:\nSardar Sahab, Yousaf Colony site ka balance critical level par hai. Current Balance: PKR {current_balance:,.0f}."
    if sms_api_url:
        try:
            payload = {"api_key": st.secrets.get("SMS_API_KEY"), "to": receiver_number, "message": msg_text, "sender": "DEEWARY"}
            requests.post(sms_api_url, data=payload, timeout=5)
        except: pass

# --- 3. PDF GENERATION FUNCTION ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"<font color='#FF4B4B' size=18><b>{title}</b></font>", styles['Title']))
    elements.append(Spacer(1, 15))
    pdf_df = dataframe.copy()
    data = [["ID", "Date", "Item/Name", "Amount", "Detail", "Occupation", "Rec. By", "Method"]]
    for _, row in pdf_df.iterrows():
        data.append([
            str(row.get('id', '')), str(row.get('date', '')), str(row.get('name', '')),
            f"{row.get('amount', 0):,.0f}", str(row.get('detail', ''))[:30],
            str(row.get('occupation', '')), str(row.get('received_by', '')), str(row.get('pay_method', ''))
        ])
    total_val = pdf_df['amount'].sum()
    data.append(["", "", "TOTAL", f"{total_val:,.0f}", "", "", "", ""])
    t = Table(data, colWidths=[40, 70, 110, 80, 150, 90, 90, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1e1e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FF4B4B")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
    ]))
    elements.append(t)
    doc.build(elements)
    buf.seek(0)
    return buf

# --- 4. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- 5. SIDEBAR & THEME SELECTION ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    
    # PREMIUM THEME SWITCHER INTERACTIVE ELEMENT
    theme_choice = st.selectbox("🎨 Select System Theme", ["Sardar Sahab Gold Edition 👑", "Classic Business Professional 🏢"])
    
    st.divider()
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"])
    st.divider()

# --- 6. DYNAMIC CSS INJECTION BASED ON THEME ---
if theme_choice == "Sardar Sahab Gold Edition 👑":
    st.markdown("""
        <style>
        .stApp { background-color: #0d0d0d; color: #ffffff; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #ffffff !important; }
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #141414 0%, #1f1f1f 100%) !important;
            border: 1px solid #D4AF37 !important;
            padding: 15px 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(212,175,55,0.15) !important;
        }
        div[data-testid="stMetric"] label p { color: #b3b3b3 !important; }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] div { color: #D4AF37 !important; font-weight: bold; }
        .header-box {
            text-align: center;
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%) !important;
            padding: 30px;
            border-radius: 20px;
            border-bottom: 5px solid #D4AF37 !important;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        }
        .kpi-card {
            background: #141414 !important;
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid #D4AF37 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-bottom: 15px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #D4AF37 0%, #AA7C11 100%) !important;
            color: #000000 !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 10px rgba(212,175,55,0.2);
        }
        .stButton > button:hover { color: #ffffff !important; box-shadow: 0 4px 15px rgba(212,175,55,0.4); }
        .alert-box { background-color: #2b0c0c; border-left: 6px solid #ff4d4d; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #ff9999; font-weight: bold; }
        .forecast-box { background-color: #0c2b11; border-left: 6px solid #d4af37; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #d4af37; font-weight: bold; }
        div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: white !important; border-color: #D4AF37 !important; }
        input { background-color: #1a1a1a !important; color: white !important; border-color: #D4AF37 !important; }
        textarea { background-color: #1a1a1a !important; color: white !important; border-color: #D4AF37 !important; }
        </style>
    """, unsafe_allow_html=True)
else:
    # Classic White/Red Corporate Layout
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; }
        div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px 20px; border-radius: 15px; }
        .header-box { text-align: center; background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%); padding: 30px; border-radius: 20px; border-bottom: 5px solid #FF4B4B; margin-bottom: 25px; }
        .kpi-card { background: #f8f9fa; padding: 20px; border-radius: 15px; border-left: 5px solid #FF4B4B; margin-bottom: 15px; }
        .alert-box { background-color: #ffebee; border-left: 6px solid #c62828; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #c62828; font-weight: bold; }
        .forecast-box { background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #2e7d32; font-weight: bold; }
        .stButton > button { background-color: #FF4B4B !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 7. SIDEBAR ADMIN VALIDATION ---
with st.sidebar:
    is_auth = False
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: is_auth = True
    else:
        with st.sidebar.expander("🔐 Admin Access", expanded=True):
            pwd = st.text_input("Admin Password", type="password")
            if st.button("Unlock"):
                if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                    st.session_state["authenticated"] = True
                    st.rerun()
    
    if is_auth:
        st.success("🔓 Admin Mode Active")
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

# --- 8. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    gold_text_color = "#D4AF37" if theme_choice == "Sardar Sahab Gold Edition 👑" else "#FF4B4B"
    st.markdown(f"""
        <div class="header-box">
            <h1 style="color: {gold_text_color}; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px;">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px; font-size: 12px; margin-bottom: 10px;">PREMIUM CONSTRUCTION MANAGEMENT</p>
            <div style="background: {gold_text_color}; color: {'#000000' if theme_choice == 'Sardar Sahab Gold Edition 👑' else '#ffffff'}; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;">
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
        
        # Burn rate tracking metrics calculation
        try:
            df['date_parsed'] = pd.to_datetime(df['date'])
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_exp_df = df[(df['type'].isin(['Labor', 'Material'])) & (df['date_parsed'] >= seven_days_ago)]
            total_7_day_exp = recent_exp_df['amount'].sum()
            daily_burn_rate = total_7_day_exp / 7
        except: daily_burn_rate = 0

        if net_bal < 50000:
            st.markdown(f"""<div class="alert-box">🚨 LOW BALANCE ALERT: Running Liquid Balance is critical (PKR {net_bal:,.0f}). Background emergency broadcast sequence initiated.</div>""", unsafe_allow_html=True)
            send_automated_low_balance_alert(net_bal)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            st.markdown(f"""<div class="forecast-box">📈 CASH FLOW LOGS: Daily Burn Velocity is PKR {daily_burn_rate:,.0f}/day. Safe runtime window asset capacity: ~{days_left:.1f} Days.</div>""", unsafe_allow_html=True)

        # KPI Layout Processing
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.markdown(f"<div class='kpi-card'><p style='color:#b3b3b3; margin:0; font-size:12px;'>💰 TOTAL INVESTMENT RECEIPT</p><h2 style='color:#2e7d32; margin:5px 0 0 0;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi2:
            st.markdown(f"<div class='kpi-card'><p style='color:#b3b3b3; margin:0; font-size:12px;'>📉 RUNNING OUTFLOW EXPENSES</p><h2 style='color:#c62828; margin:5px 0 0 0;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi3:
            bal_color = "#D4AF37" if theme_choice == "Sardar Sahab Gold Edition 👑" else "#2e7d32"
            st.markdown(f"<div class='kpi-card'><p style='color:#b3b3b3; margin:0; font-size:12px;'>⚖️ NET LIQUID BALANCE</p><h2 style='color:{bal_color}; margin:5px 0 0 0;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    # --- SHOW FORMS (CRUD Engine Process) ---
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        if ftype == "RegisterLabor":
            with st.expander("📝 Register New Labor Profile Document", expanded=True):
                with st.form("labor_profile_form"):
                    l_name = st.text_input("Labor Full Name *")
                    l_phone = st.text_input("Phone Number")
                    l_cnic = st.text_input("CNIC Number")
                    l_occ = st.text_input("Occupation / Skill Type")
                    l_contract = st.number_input("Total Contract Amount (PKR)", min_value=0, value=0)
                    l_rating = st.slider("Rating", min_value=1, max_value=5, value=5)
                    l_photo = st.file_uploader("Profile Pic", type=['jpg', 'jpeg', 'png'])
                    l_details = st.text_area("Background Notes")
                    if st.form_submit_button("Save Profile"):
                        if l_name:
                            img_url = ""
                            if l_photo:
                                f_name = f"labor_{int(datetime.now().timestamp())}_{l_photo.name}"
                                supabase.storage.from_('material_pics').upload(f_name, l_photo.getvalue())
                                img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                            supabase.table('labor_profiles').insert({"name": l_name, "phone": l_phone, "cnic": l_cnic, "occupation": l_occ, "total_contract_amount": l_contract, "rating": l_rating, "photo_url": img_url, "details": l_details}).execute()
                            st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else:
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title / Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    d_occ = st.text_input("Occupation")
                    d_rec = st.text_input("Received/Authorized By")
                    d_meth = st.selectbox("Method", ["Cash", "Online", "Cheque"])
                    uploaded_photo = st.file_uploader("Bill Scan", type=['jpg', 'jpeg', 'png']) if ftype == "Material" else None
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit Entry"):
                        img_url = ""
                        if uploaded_photo:
                            f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                            supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                            img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                        supabase.table('transactions').insert({"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "image_url": img_url, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}).execute()
                        st.cache_data.clear()
                        wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det)
                        st.markdown(f'<a href="{wa_url}" target="_blank"><div style="background-color:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 Push Notification via WhatsApp</div></a>', unsafe_allow_html=True)
                        st.session_state.pop("show_form")

    # --- PROGRESS SECTION ---
    st.write("##")
    status_df = fetch_project_status()
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / len(status_df)) * 100) if not status_df.empty else 0
    st.markdown(f"### 📈 Progress Runway ({prog_val}% Work Completed)")
    st.progress(prog_val / 100)

    if "show_status_form" in st.session_state and is_auth:
        with st.form("status_form"):
            task = st.selectbox("Select Project Milestone", status_df['task_name'].tolist())
            stat = st.radio("Status Target", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Update Status Mapping"):
                supabase.table('project_status').upsert({"task_name": task, "status": stat}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("### 🏗️ Verification Checklist Grid")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "🏆" if row['status'] == "Done" else "⏳"
            bg = "#1b2611" if (row['status'] == "Done" and theme_choice == "Sardar Sahab Gold Edition 👑") else ("#e8f5e9" if row['status'] == "Done" else "#2b2211" if theme_choice == "Sardar Sahab Gold Edition 👑" else "#fff3e0")
            st.markdown(f'<div style="background:{bg}; padding:12px; border-radius:10px; margin-bottom:5px; border-left:5px solid {gold_text_color};"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# --- OTHER CORE PAGES INHERIT THE THEME DYNAMICALLY ---
elif menu == "👷 Labor Profiles Application":
    st.title("👷 VIP Labor Master Profile Ledger")
    labor_df = fetch_labor_profiles()
    if not labor_df.empty:
        st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
        for _, row in labor_df.iterrows():
            st.markdown(f"#### 👤 User Record Profile: {row['name']}")
            st.write(f"CNIC: {row['cnic']} | Skillset: {row['occupation']} | Valuation Contract: PKR {row['total_contract_amount']:,.0f}")
            st.divider()
    else: st.info("No records present inside secure file servers folder directory.")

else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        st.dataframe(f_df, use_container_width=True)
        st.metric("Aggregate Summation Data Value", f"PKR {f_df['amount'].sum():,.0f}")
        
