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

# --- 3. HARDCODED PROPERTY LISTINGS (ZAMEEN.COM STYLE) ---
# Note: Kal ko aap isko Supabase table se bhi connect kar sakte hain.
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
    },
    {
        "title": "Luxury Residential Block",
        "location": "Yousaf Colony Site",
        "size": "10 Marla",
        "price": "PKR 12,500,000",
        "status": "Sold Out 🤝",
        "image": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?q=80&w=600&auto=format&fit=crop",
        "desc": "Premium boundary wall block allocated to executive investor partners."
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

# --- 6. ADVANCED PROFESSIONAL CSS ---
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
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .kpi-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border-left: 5px solid #FF4B4B;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    .alert-box { background-color: #fef2f2; border-left: 6px solid #ef4444; padding: 15px; border-radius: 12px; margin-bottom: 25px; color: #991b1b; font-weight: bold; }
    .forecast-box { background-color: #f0fdf4; border-left: 6px solid #22c55e; padding: 15px; border-radius: 12px; margin-bottom: 25px; color: #166534; font-weight: bold; }
    
    /* ZAMEEN.COM STYLE SHOWCASE CARDS */
    .property-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        margin-bottom: 20px;
    }
    .property-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .property-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
    }
    .badge-sale { background-color: #ef4444; }
    .badge-construction { background-color: #f59e0b; }
    .badge-sold { background-color: #64748b; }
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
    msg = f"Assalam-o-Alaikum Deewary.com, \nI am interested in booking/details of the following property listing:\n\n🏡 *Property:* {title}\n📍 *Location:* {location}\n💰 *Price:* {price}\n\nPlease share the installment schedule and layout plan."
    return f"https://api.whatsapp.com/send?phone={st.secrets.get('ALERT_PHONE_NUMBER', '')}&text={urllib.parse.quote(msg)}"

# --- 8. SIDEBAR MANAGEMENT PANEL ---
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
    # Main Modern Header Panel
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px; font-size: 36px;">DEEWARY.COM</h1>
            <p style="color: #9ca3af; letter-spacing: 2px; font-size: 13px; margin-bottom: 12px; font-weight: bold;">PREMIUM REAL ESTATE PORTAL & ERP</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 6px 18px; border-radius: 8px; font-weight: bold; font-size: 14px;">
                C.E.O: SARDAR SAMI ULLAH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- SECTION A: PREMIUM PROPERTY SHOWROOM (ZAMEEN.COM STYLE GRID) ---
    st.markdown("## 🏢 Exclusive Property Showroom")
    st.markdown("<p style='color:#64748b; font-size:14px; margin-top:-10px;'>Live available inventory showcase for investors & corporate buyers.</p>", unsafe_allow_html=True)
    
    p_cols = st.columns(3)
    for idx, prop in enumerate(PROPERTY_INVENTORY):
        with p_cols[idx % 3]:
            # Status Badge Color Determination
            badge_class = "badge-sale" if "Sale" in prop["status"] else "badge-construction" if "Construction" in prop["status"] else "badge-sold"
            enquiry_url = generate_property_enquiry_link(prop["title"], prop["location"], prop["price"])
            
            # Rendering HTML Card Layout
            st.markdown(f"""
                <div class="property-card">
                    <img src="{prop["image"]}" style="width:100%; height:200px; object-fit:cover;">
                    <div style="padding: 16px;">
                        <div class="property-badge {badge_class}">{prop["status"]}</div>
                        <h4 style="margin: 0 0 8px 0; color:#1f2937; font-size:18px;">{prop["title"]}</h4>
                        <p style="color:#64748b; font-size:13px; margin: 0 0 10px 0;">📍 {prop["location"]} | 📐 <b>{prop["size"]}</b></p>
                        <p style="color:#94a3b8; font-size:12px; line-height:1.4; min-height:40px;">{prop["desc"]}</p>
                        <hr style="border:0; border-top:1px solid #f1f5f9; margin:12px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="color:#ef4444; font-weight:bold; font-size:18px;">{prop["price"]}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Direct Booking Action Button
            st.markdown(f'<a href="{enquiry_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#111827; color:white; padding:8px; border-radius:8px; text-align:center; font-size:12px; font-weight:bold; margin-top:-10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);">💬 Instant WhatsApp Enquiry / Booking</div></a>', unsafe_allow_html=True)

    st.divider()

    # --- SECTION B: BACKEND ERP BUSINESS SUITE ---
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

        # Automated Alerts
        if net_bal < 50000:
            st.markdown(f'<div class="alert-box">🚨 CRITICAL LIQUID BUDGET ALERT: Balance is PKR {net_bal:,.0f}. Background warning ping dispatch operational.</div>', unsafe_allow_html=True)
            send_automated_low_balance_alert(net_bal)
        elif daily_burn_rate > 0:
            st.markdown(f'<div class="forecast-box">📈 OPERATIONAL RUNWAY: Daily site burn speed is PKR {daily_burn_rate:,.0f}/day. Liquid resources available for ~{net_bal/daily_burn_rate:.1f} Safe Days.</div>', unsafe_allow_html=True)

        # Corporate KPI Blocks
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:bold;'>💰 CAPITAL RECEIPTS RESERVES</p><h2 style='color:#166534; margin:5px 0 0 0; font-size:26px;'>PKR {inc:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi2:
            st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:bold;'>📉 CUMULATIVE OUTFLOW DEBITS</p><h2 style='color:#991b1b; margin:5px 0 0 0; font-size:26px;'>PKR {exp:,.0f}</h2></div>", unsafe_allow_html=True)
        with col_kpi3:
            bal_color = "#166534" if net_bal >= 0 else "#991b1b"
            st.markdown(f"<div class='kpi-card'><p style='color:#64748b; margin:0; font-size:12px; font-weight:bold;'>⚖️ NET RUNNING LIQUID BAL</p><h2 style='color:{bal_color}; margin:5px 0 0 0; font-size:26px;'>PKR {net_bal:,.0f}</h2></div>", unsafe_allow_html=True)

    # --- ADMINISTRATIVE DATA ENTRY FORMS (CRUD) ---
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.expander(f"📥 New System Record Deployment Entry: {ftype}", expanded=True):
            with st.form("entry_form"):
                d_date = st.date_input("Processing Logging Date", datetime.now())
                d_name = st.text_input("Particular Title Item Name")
                d_amt = st.number_input("Transaction Volume Valuation (PKR)", min_value=0)
                d_occ = st.text_input("Operational Designation Category / Skill Tag")
                d_rec = st.text_input("Authorized Clearing Staff Person")
                d_meth = st.selectbox("Clearing Settlement Mechanism", ["Cash", "Online", "Cheque"])
                uploaded_photo = st.file_uploader("Document Scan Attachment Upload", type=['jpg', 'jpeg', 'png']) if ftype == "Material" else None
                d_det = st.text_area("Detailed Log Description Notes Context")
                
                if st.form_submit_button("Commit Ledger Document Entry"):
                    img_url = ""
                    if uploaded_photo:
                        f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                        supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                        img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                    supabase.table('transactions').insert({"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "image_url": img_url, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}).execute()
                    st.cache_data.clear()
                    wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det)
                    st.markdown(f'<a href="{wa_url}" target="_blank"><div style="background-color:#25D366; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">📲 Push Voucher Data Slip via WhatsApp</div></a>', unsafe_allow_html=True)
                    st.session_state.pop("show_form")

    # --- MILESTONE TRACKING PROGRESS LINE ---
    st.write("##")
    status_df = fetch_project_status()
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / len(status_df)) * 100) if not status_df.empty else 0
    st.markdown(f"### 📈 Construction Milestone Mapping Progress ({prog_val}% Work Completed)")
    st.progress(prog_val / 100)

    if "show_status_form" in st.session_state and is_auth:
        with st.form("status_update"):
            task = st.selectbox("Choose Target Project Task Line", status_df['task_name'].tolist())
            stat = st.radio("Status Target Parameter", ["Pending", "Done"], horizontal=True)
            if st.form_submit_button("Confirm Status Transition"):
                supabase.table('project_status').upsert({"task_name": task, "status": stat}).execute()
                st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("### 🏗️ Quality Verification Field Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#f0fdf4" if row['status'] == "Done" else "#fffbb1"
            st.markdown(f'<div style="background:{bg}; padding:12px; border-radius:12px; margin-bottom:6px; border-left:4px solid #FF4B4B; color:#1f2937;"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")

# --- OTHER APPLICATION DESKS (RETAINING ORIGINAL DATA MATRIX INTEGRITY) ---
elif menu == "👷 Labor Profiles Application":
    st.title("👷 Labor Resource Master Application Ledger")
    labor_df = fetch_labor_profiles()
    if not labor_df.empty:
        st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
    else: st.info("No records present inside database resource folder paths.")

else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        st.dataframe(f_df, use_container_width=True)
        st.metric("Aggregate Data Column Total Volume Valuation Value Sum", f"PKR {f_df['amount'].sum():,.0f}")
