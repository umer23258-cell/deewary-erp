import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
# PDF ke liye libraries
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PDF GENERATION FUNCTION ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"<font color='#FF4B4B' size=16><b>{title}</b></font>", styles['Title']))
    elements.append(Paragraph(f"Deewary.com ERP - Smart Management", styles['Normal']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    cols = ['date', 'name', 'amount', 'detail']
    pdf_df = dataframe[cols].copy()
    total_val = pdf_df['amount'].sum()
    
    data = [["Date", "Item Name", "Amount (PKR)", "Detail"]] 
    for _, row in pdf_df.iterrows():
        data.append([str(row['date']), str(row['name']), f"{row['amount']:,.0f}", str(row['detail'])])
    
    data.append(["", "TOTAL", f"{total_val:,.0f}", ""])

    t = Table(data, colWidths=[80, 120, 90, 200])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1e1e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FF4B4B")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])
    
    t.setStyle(style)
    elements.append(t)
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
    }
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 30px;
        border-radius: 20px;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Wor", "polishing/grinding)", "Main Door", "Safety Grill", "Sanitary Fitting", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        if st.button("⚙️ Change Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg")

df = fetch_data()

# --- 6. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B;">DEEWARY.COM</h1>
            <p style="color: white;">C.E.O: SARDAR SAMI ULLAH</p>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
        m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
        m3.metric("⚖️ Net Balance", f"PKR {inc-exp:,.0f}")

    status_df = fetch_project_status()
    st.divider()
    st.subheader("⚡ Quick Transactions")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        with st.expander(f"Register {ftype}", expanded=True):
            with st.form("quick_form"):
                d_date = st.date_input("Date", datetime.now())
                d_name = st.text_input("Title")
                d_amt = st.number_input("Amount", min_value=0)
                uploaded_photo = None
                if ftype == "Material":
                    uploaded_photo = st.file_uploader("Upload Bill Image", type=['jpg', 'jpeg', 'png'])
                d_det = st.text_area("Notes")
                if st.form_submit_button("Submit"):
                    img_url = ""
                    if uploaded_photo:
                        f_name = f"{int(datetime.now().timestamp())}_{uploaded_photo.name}"
                        supabase.storage.from_('material_pics').upload(f_name, uploaded_photo.getvalue())
                        img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                    payload = {"date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, "detail": d_det, "image_url": img_url}
                    supabase.table('transactions').insert(payload).execute()
                    st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()

# --- 7. HISTORY PAGES ---
else:
    st.title(menu)
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
        
        # SEARCH KE MUTABIQ PIC LOGIC
        if search and not f_df.empty and 'image_url' in f_df.columns:
            st.markdown("### 🖼️ Result Detail & Photo")
            for _, row in f_df.iterrows():
                if row['image_url'] and str(row['image_url']) != "nan":
                    with st.expander(f"👁️ View Photo: ID {row['id']} - {row['name']}", expanded=True):
                        st.image(row['image_url'], use_container_width=True)

        st.metric("Total PKR", f"{f_df['amount'].sum():,.0f}")
        if is_auth:
            tid = st.text_input("Enter ID to Delete")
            if st.button("🗑️ Delete"):
                supabase.table('transactions').delete().eq('id', tid).execute()
                st.cache_data.clear(); st.rerun()

        st.divider()
        c1, c2 = st.columns(2)
        c1.download_button("📥 Excel", f_df.to_csv().encode('utf-8'), f"{menu}.csv")
        c2.download_button("📄 PDF Report", export_to_pdf(f_df, menu), f"{menu}.pdf")
