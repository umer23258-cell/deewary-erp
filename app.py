import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
import urllib.parse
# PDF ke liye libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. MASTER PDF GENERATION FUNCTION ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    # --- PAGE 1: EXECUTIVE SUMMARY (DASHBOARD STYLE) ---
    elements.append(Paragraph(f"<font color='#FF4B4B' size=22><b>DEEWARY.COM - MASTER ERP REPORT</b></font>", styles['Title']))
    elements.append(Paragraph(f"Project: Yousaf Colony | Report Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 25))

    inc_total = dataframe[dataframe['type'] == 'Income']['amount'].sum()
    lab_total = dataframe[dataframe['type'] == 'Labor']['amount'].sum()
    mat_total = dataframe[dataframe['type'] == 'Material']['amount'].sum()
    exp_total = lab_total + mat_total

    summary_data = [
        ["DESCRIPTION", "TOTAL AMOUNT (PKR)"],
        ["TOTAL INCOME (Cash In)", f"{inc_total:,.0f}"],
        ["TOTAL LABOR EXPENSES", f"{lab_total:,.0f}"],
        ["TOTAL MATERIAL EXPENSES", f"{mat_total:,.0f}"],
        ["TOTAL EXPENDITURE", f"{exp_total:,.0f}"],
        ["CURRENT NET BALANCE", f"{inc_total - exp_total:,.0f}"]
    ]
    
    sum_t = Table(summary_data, colWidths=[250, 200])
    sum_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1e1e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FF4B4B")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
    ]))
    elements.append(Paragraph("<b>1. Project Financial Summary</b>", styles['Heading2']))
    elements.append(sum_t)
    elements.append(PageBreak())

    # --- HELPER FUNCTION FOR SECTIONS ---
    def create_section(df_type, section_name, header_color):
        sub_df = dataframe[dataframe['type'] == df_type]
        if not sub_df.empty:
            elements.append(Paragraph(f"<b>{section_name}</b>", styles['Heading2']))
            data = [["Date", "Name/Item", "Amount", "Detail", "Occupation", "Rec. By", "Method"]]
            for _, row in sub_df.iterrows():
                data.append([
                    str(row.get('date', '')),
                    str(row.get('name', '')),
                    f"{row.get('amount', 0):,.0f}",
                    str(row.get('detail', ''))[:30],
                    str(row.get('occupation', '')),
                    str(row.get('received_by', '')),
                    str(row.get('pay_method', ''))
                ])
            # Total Row for this section
            data.append(["", "SECTION TOTAL", f"{sub_df['amount'].sum():,.0f}", "", "", "", ""])
            
            t = Table(data, colWidths=[70, 100, 80, 150, 90, 90, 70])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

    # Adding the 3 sections separately
    create_section("Income", "2. Income Details", "#2E7D32")    # Green
    create_section("Labor", "3. Labor Payment Details", "#1565C0") # Blue
    create_section("Material", "4. Material Cost Details", "#E65100") # Orange

    doc.build(elements)
    buf.seek(0)
    return buf

# --- 3. WHATSAPP LINK FUNCTION ---
def get_whatsapp_master_link(phone, dataframe):
    inc = dataframe[dataframe['type'] == 'Income']['amount'].sum()
    exp = dataframe[dataframe['type'].isin(['Labor', 'Material'])]['amount'].sum()
    msg = (f"🏗️ *DEEWARY.COM - MASTER ERP REPORT*\n\n"
           f"Assalam-o-Alaikum,\n"
           f"Project Summary:\n"
           f"💰 Total Income: {inc:,.0f}\n"
           f"📉 Total Expenses: {exp:,.0f}\n"
           f"⚖️ Net Balance: {inc-exp:,.0f}\n\n"
           f"Mukammal PDF Report neechay check karein.\n"
           f"*C.E.O: Sardar Sami Ullah*")
    return f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"

# --- 4. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa; border: 1px solid #e9ecef;
        padding: 15px 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .header-box {
        text-align: center; background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 30px; border-radius: 20px; border-bottom: 5px solid #FF4B4B; margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. DATA FETCHING ---
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
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "Polishing", "Main Door", "Safety Grill", "Sanitary", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

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

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & Master Report"])
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
        if st.button("➕ Income", use_container_width=True): st.session_state.show_form = "Income"
        if st.button("👷 Labor", use_container_width=True): st.session_state.show_form = "Labor"
        if st.button("🏗️ Material", use_container_width=True): st.session_state.show_form = "Material"
        st.divider()
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Site: Yousaf Colony")

df = fetch_data()

# --- 7. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    st.markdown('<div class="header-box"><h1 style="color: #FF4B4B; margin: 0;">DEEWARY.COM</h1><p style="color: white;">C.E.O: SARDAR SAMI ULLAH</p></div>', unsafe_allow_html=True)

    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
        m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
        m3.metric("⚖️ Net Balance", f"PKR {inc-exp:,.0f}")

    # Entry Form (Logic wahi purani)
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.expander(f"Register {ftype}", expanded=True):
            with st.form("entry_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Name")
                d_amt = st.number_input("Amount", min_value=0)
                d_occ = st.text_input("Occupation/Type")
                d_rec = st.text_input("Authorized By")
                d_meth = st.selectbox("Method", ["Cash", "Online", "Cheque"])
                d_det = st.text_area("Notes")
                if st.form_submit_button("Submit"):
                    payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

    # Progress Section
    st.divider()
    st.markdown("### 📈 Site Progress Overview")
    status_df = fetch_project_status()
    total = len(status_df); done = len(status_df[status_df['status'] == 'Done'])
    prog = int((done/total)*100) if total > 0 else 0
    st.progress(prog/100)
    st.write(f"**{prog}% Work Completed** ({done}/{total} Tasks)")

# --- 8. HISTORY & MASTER REPORT ---
else:
    st.title(menu)
    if not df.empty:
        # Filter logic
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy() # Master report calls this
        
        search = st.text_input("🔎 Search records...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        st.dataframe(f_df, use_container_width=True)
        
        # Action Buttons
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        # Download Master PDF (Dashboard + All Tables)
        c1.download_button("📄 Download Master Report", export_to_pdf(f_df, "Master Report"), "Deewary_Master.pdf", use_container_width=True)
        
        # WhatsApp Functionality
        with st.container():
            st.markdown("### 📲 Send Report to Client")
            w_col1, w_col2 = st.columns([2, 1])
            phone = w_col1.text_input("Client Phone (e.g. 923001234567)")
            if phone:
                wa_url = get_whatsapp_master_link(phone, f_df)
                w_col2.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:10px;text-align:center;font-weight:bold;margin-top:25px;">💬 Open WhatsApp</div></a>', unsafe_allow_html=True)
        
        if is_auth:
            st.divider()
            del_id = st.text_input("Delete Record (Enter ID)")
            if st.button("🗑️ Delete Now"):
                supabase.table('transactions').delete().eq('id', del_id).execute()
                st.cache_data.clear(); st.rerun()
