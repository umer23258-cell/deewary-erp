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

# --- 3. HARDCODED PROPERTY LISTINGS (ZAMEEN STYLE INTEGRITY) ---
PROPERTY_INVENTORY = [
    {
        "title": "Premium Corner Plot - Yousaf Colony",
        "location": "Sector B-17, Islamabad",
        "size": "5 Marla",
        "price": "PKR 4,500,000",
        "status": "For Sale 🔥",
        "image": "https://images.unsplash.com/photo-1524813686514-a57563d77d61?q=80&w=600&auto=format&fit=crop",
        "desc": "Ideal location near the main commercial boulevard wall perimeter line. Perfect for investment."
    },
    {
        "title": "Commercial Front File - Block A",
        "location": "Faisal Town, Rawalpindi",
        "size": "7 Marla",
        "price": "PKR 8,200,000",
        "status": "Under Construction 🏗️",
        "image": "https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?q=80&w=600&auto=format&fit=crop",
        "desc": "Foundation and boundary wall work completed. High appreciation expected within months."
    }
]

# --- 4. PDF GENERATION FUNCTION ---
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

# --- 5. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP & Portal", layout="wide", page_icon="🏗️")

# --- 6. ELITE CORE UI CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        padding: 35px;
        border-radius: 24px;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 30px;
    }
    .kpi-card {
        background: #ffffff; padding: 20px; border-radius: 16px; border-left: 5px solid #FF4B4B;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;
    }
    .alert-box { background-color: #fef2f2; border-left: 6px solid #ef4444; padding: 15px; border-radius: 12px; margin-bottom: 25px; color: #991b1b; font-weight: bold; }
    .forecast-box { background-color: #f0fdf4; border-left: 6px solid #22c55e; padding: 15px; border-radius: 12px; margin-bottom: 25px; color: #166534; font-weight: bold; }
    
    /* VOUCHER RECEIPT CASH SLIP FORMATTING */
    .digital-voucher {
        background-color: #fafafa;
        border: 2px dashed #cbd5e1;
        padding: 25px;
        border-radius: 16px;
        max-width: 550px;
        margin: 15px auto;
        font-family: 'Courier New', Courier, monospace;
        color: #1e2937;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.02);
    }
    .voucher-header { text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px; }
    .voucher-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
    .voucher-total { font-size: 20px; font-weight: bold; color: #FF4B4B; border-top: 2px dashed #cbd5e1; border-bottom: 2px dashed #cbd5e1; padding: 8px 0; margin-top: 15px; }
    
    .property-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .property-badge { display: inline-block; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; color: white; margin-bottom: 10px; }
    .badge-sale { background-color: #ef4444; } .badge-construction { background-color: #f59e0b; }
    </style>
""", unsafe_allow_html=True)

# --- 7. LOGIC FUNCTIONS ---
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

def fetch_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def generate_whatsapp_link(type_tx, name, amount, detail):
    base_msg = f"🏗️ *Deewary.com ERP Notification*\n\n• *Type:* {type_tx}\n• *Name/Item:* {name}\n• *Amount:* PKR {amount:,.0f}\n"
    if detail: base_msg += f"• *Details:* {detail}\n"
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(base_msg)}"

def generate_property_enquiry_link(title, location, price):
    msg = f"Assalam-o-Alaikum Deewary.com, \nI am interested in booking/details of:\n🏡 *Property:* {title}\n📍 *Location:* {location}\n💰 *Price:* {price}"
    return f"https://api.whatsapp.com/send?phone={st.secrets.get('ALERT_PHONE_NUMBER', '')}&text={urllib.parse.quote(msg)}"

# --- 8. SIDEBAR CONTROL CENTER ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To Desk", ["📊 Dashboard & Showroom", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"])
    st.divider()
    
    is_auth = False
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: is_auth = True
    else:
        with st.sidebar.expander("🔐 Staff Admin Access", expanded=True):
            pwd = st.text_input("Admin Password", type="password")
            if st.button("Unlock Management"):
                if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                    st.session_state["authenticated"] = True
                    st.rerun()
    
    if is_auth:
        st.success("🔓 Manager Mode On")
        st.write("### ⚡ Quick Ledger Input")
        if st.button("➕ Income Receipt", use_container_width=True): st.session_state.show_form = "Income"
        if st.button("👷 Labor Expense", use_container_width=True): st.session_state.show_form = "Labor"
        if st.button("🏗️ Material Bill", use_container_width=True): st.session_state.show_form = "Material"
        if st.button("📝 Register New Profile", use_container_width=True): st.session_state.show_form = "RegisterLabor"
        st.divider()
        if st.button("⚙️ Update Project Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 9. INTERFACE ENGINE ---
if menu == "📊 Dashboard & Showroom":
    # Premium Header Desk
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px; font-size: 36px;">DEEWARY.COM</h1>
            <p style="color: #9ca3af; letter-spacing: 2px; font-size: 13px; margin-bottom: 12px; font-weight: bold;">PREMIUM REAL ESTATE PORTAL & ERP</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 6px 18px; border-radius: 8px; font-weight: bold; font-size: 14px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # PROPERTY SHOWROOM 
    st.markdown("## 🏢 Exclusive Property Showroom")
    p_cols = st.columns(2)
    for idx, prop in enumerate(PROPERTY_INVENTORY):
        with p_cols[idx % 2]:
            badge_class = "badge-sale" if "Sale" in prop["status"] else "badge-construction"
            enquiry_url = generate_property_enquiry_link(prop["title"], prop["location"], prop["price"])
            st.markdown(f"""
                <div class="property-card">
                    <img src="{prop["image"]}" style="width:100%; height:180px; object-fit:cover;">
                    <div style="padding:15px;">
                        <div class="property-badge {badge_class}">{prop["status"]}</div>
                        <h4 style="margin:0 0 5px 0; color:#1f2937;">{prop["title"]}</h4>
                        <p style="color:#64748b; font-size:12px; margin:0 0 10px 0;">📍 {prop["location"]} | 📐 {prop["size"]}</p>
                        <span style="color:#ef4444; font-weight:bold; font-size:16px;">{prop["price"]}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # BUSINESS OUTFLOW ENGINE
    st.markdown("## 📊 Construction Administrative Suite")
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
            daily_burn_rate = recent_exp_df['amount'].sum() / 7
        except: daily_burn_rate = 0

        if net_bal < 50000:
            st.markdown(f'<div class="alert-box">🚨 CRITICAL BUDGET ALERT: Balance is PKR {net_bal:,.0f}.</div>', unsafe_allow_html=True)
            send_automated_low_balance_alert(net_bal)
        elif daily_burn_rate > 0:
            st.markdown(f'<div class="forecast-box">📈 OPERATIONAL RUNWAY: Resource burn speed is PKR {daily_burn_rate:,.0f}/day. Left runtime: ~{net_bal/daily_burn_rate:.1f} Safe Days.</div>', unsafe_allow_html=True)

        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px;'>💰 CAPITAL RECEIPTS</p><h2 style='color:#166534; margin:5px 0 0 0;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi2: st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px;'>📉 CUMULATIVE DEBITS</p><h2 style='color:#991b1b; margin:5px 0 0 0;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi3:
            bal_color = "#166534" if net_bal >= 0 else "#991b1b"
            st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px;'>⚖️ NET LIQUID BAL</p><h2 style='color:{bal_color}; margin:5px 0 0 0;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    # --- SECTION C: INTERACTIVE DIGITAL VOUCHER DESK (NEW FEATURE) ---
    st.write("##")
    st.markdown("### 📑 Live Digital Receipt / Voucher Generator")
    st.markdown("<p style='color:#64748b; font-size:13px; margin-top:-10px;'>Select any recent entry block below to compute its dynamic verification receipt voucher.</p>", unsafe_allow_html=True)
    
    if not df.empty:
        # Dynamic drop selector item arrays
        df['select_label'] = "[" + df['type'].astype(str).str.upper() + "] ID: " + df['id'].astype(str) + " - " + df['name'].astype(str) + " (PKR " + df['amount'].map('{:,.0f}'.format) + ")"
        selected_voucher_label = st.selectbox("Select Transaction Log Entry", df['select_label'].tolist())
        
        selected_row = df[df['select_label'] == selected_voucher_label].iloc[0]
        v_type_prefix = "INC" if selected_row['type'] == "Income" else "LAB" if selected_row['type'] == "Labor" else "MAT"
        voucher_number = f"DW-{v_type_prefix}-{1000 + int(selected_row['id'])}"
        
        # HTML Render Structure inside interactive dashboard pane
        st.markdown(f"""
            <div class="digital-voucher">
                <div class="voucher-header">
                    <h3 style="margin:0; font-family:'Helvetica Neue',Arial; color:#111827; letter-spacing:2px;">DEEWARY.COM</h3>
                    <p style="margin:5px 0 0 0; font-size:11px; color:#64748b;">OFFICIAL VOUCHER RECEIPT CERTIFICATE</p>
                </div>
                <div class="voucher-row"><span>Voucher No:</span><b>{voucher_number}</b></div>
                <div class="voucher-row"><span>Logging Date:</span><span>{selected_row['date']}</span></div>
                <div class="voucher-row"><span>Category Type:</span><span>{str(selected_row['type']).upper()}</span></div>
                <div class="voucher-row"><span>Particular Name:</span><b>{selected_row['name']}</b></div>
                <div class="voucher-row"><span>Job Designation:</span><span>{selected_row['occupation'] if selected_row['occupation'] else 'N/A'}</span></div>
                <div class="voucher-row"><span>Clearing Agent:</span><span>{selected_row['received_by'] if selected_row['received_by'] else 'Authorized Desk'}</span></div>
                <div class="voucher-row"><span>Settlement Mode:</span><span>{selected_row['pay_method']}</span></div>
                <div class="voucher-row" style="margin-top:10px;"><span style="font-size:12px; color:#64748b;">Description Notes:</span></div>
                <p style="font-size:12px; background:#f1f5f9; padding:8px; border-radius:6px; margin:4px 0; font-style:italic;">{selected_row['detail'] if selected_row['detail'] else 'No additional parameters logged inside security file paths.'}</p>
                <div class="voucher-total">
                    <div style="display:flex; justify-content:space-between;">
                        <span>SETTLED VOLUME:</span>
                        <span>PKR {selected_row['amount']:,.0f}/-</span>
                    </div>
                </div>
                <div style="margin-top:20px; text-align:center; font-size:10px; color:#94a3b8;">
                    🔒 System Generated Digital Slips Record V2.0<br>Deewary Premium ERP Perimeter Logs
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.info("No logs present to process voucher print operations.")

    # CRUD Form Inputs
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.expander(f"📥 New Deployment Entry: {ftype}", expanded=True):
            with st.form("entry_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Particular Title")
                d_amt = st.number_input("Valuation Amount (PKR)", min_value=0)
                d_occ = st.text_input("Designation Skill Tag")
                d_rec = st.text_input("Clearing Staff Person")
                d_meth = st.selectbox("Method", ["Cash", "Online", "Cheque"])
                uploaded_photo = st.file_uploader("Scan Attachment", type=['jpg', 'jpeg', 'png']) if ftype == "Material" else None
                d_det = st.text_area("Log Description")
                if st.form_submit_button("Commit Ledger Entry"):
                    img_url = ""
                    if uploaded_photo:
                        f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                        supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                        img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                    supabase.table('transactions').insert({"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "image_url": img_url, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}).execute()
                    st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

    # CHECKLIST MILESTONES
    st.write("##")
    status_df = fetch_project_status()
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / len(status_df)) * 100) if not status_df.empty else 0
    st.markdown(f"### 📈 Milestone Progress Runway ({prog_val}% Completed)")
    st.progress(prog_val / 100)

    st.divider()
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#f0fdf4" if row['status'] == "Done" else "#fffbb1"
            st.markdown(f'<div style="background:{bg}; padding:12px; border-radius:12px; margin-bottom:6px; border-left:4px solid #FF4B4B; color:#1f2937;"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# PRESERVE INTEGRITY OF ALL OTHER REVENUE VIEWS
elif menu == "👷 Labor Profiles Application":
    st.title("👷 Labor Master Ledger Applications")
    labor_df = fetch_labor_profiles()
    if not labor_df.empty: st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
    else: st.info("No records inside folders data servers path.")

else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        st.dataframe(f_df, use_container_width=True)
        st.metric("Aggregate Data Total Column Volume", f"PKR {f_df['amount'].sum():,.0f}")
