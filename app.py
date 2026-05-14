import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components
import urllib.parse
# PDF libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. MASTER PDF GENERATION (Dashboard Summary + Categorized Tables) ---
def export_to_pdf(dataframe, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    # PAGE 1: EXECUTIVE SUMMARY
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
    elements.append(Paragraph("<b>1. Project Financial Summary (Dashboard Overview)</b>", styles['Heading2']))
    elements.append(sum_t)
    elements.append(PageBreak())

    # SECTIONS LOGIC
    def create_section(df_type, section_name, header_color):
        sub_df = dataframe[dataframe['type'] == df_type]
        if not sub_df.empty:
            elements.append(Paragraph(f"<b>{section_name}</b>", styles['Heading2']))
            data = [["Date", "Name/Item", "Amount", "Detail", "Occupation", "Method"]]
            for _, row in sub_df.iterrows():
                data.append([
                    str(row.get('date', '')),
                    str(row.get('name', '')),
                    f"{row.get('amount', 0):,.0f}",
                    str(row.get('detail', ''))[:40],
                    str(row.get('occupation', '')),
                    str(row.get('pay_method', ''))
                ])
            # Total Row
            data.append(["", "TOTAL", f"{sub_df['amount'].sum():,.0f}", "", "", ""])
            
            t = Table(data, colWidths=[80, 120, 100, 200, 100, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 25))

    create_section("Income", "2. Income Details", "#2E7D32")
    create_section("Labor", "3. Labor Payment Details", "#1565C0")
    create_section("Material", "4. Material Cost Details", "#E65100")

    doc.build(elements)
    buf.seek(0)
    return buf

# --- 3. WHATSAPP LINK (FIXED) ---
def get_wa_link(phone, dataframe):
    # Clean phone number (remove +, spaces, dashes)
    clean_phone = "".join(filter(str.isdigit, phone))
    
    inc = dataframe[dataframe['type'] == 'Income']['amount'].sum()
    lab = dataframe[dataframe['type'] == 'Labor']['amount'].sum()
    mat = dataframe[dataframe['type'] == 'Material']['amount'].sum()
    
    # Message Body
    msg = (
        f"🏗️ *DEEWARY.COM MASTER REPORT*\n\n"
        f"Dear Client,\n"
        f"Project summary of Yousaf Colony as of today:\n\n"
        f"💰 *Total Income:* PKR {inc:,.0f}\n"
        f"👷 *Labor Expense:* PKR {lab:,.0f}\n"
        f"🏗️ *Material Expense:* PKR {mat:,.0f}\n"
        f"--------------------------\n"
        f"⚖️ *Net Balance:* PKR {inc - (lab + mat):,.0f}\n"
        f"--------------------------\n\n"
        f"Please check the attached Master PDF for full details.\n"
        f"*Sardar Sami Ullah (C.E.O)*"
    )
    # Proper URL encoding for WhatsApp
    return f"https://api.whatsapp.com/send?phone={clean_phone}&text={urllib.parse.quote(msg)}"

# --- 4. CORE APP LOGIC ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

# CSS
st.markdown("""
    <style>
    .header-box { text-align: center; background: #1e1e1e; padding: 20px; border-radius: 15px; border-bottom: 5px solid #FF4B4B; margin-bottom: 20px; }
    div[data-testid="stMetric"] { background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Navigation", ["📊 Dashboard", "🔍 Search & Master Report", "💰 Income", "👷 Labor", "🏗️ Material"])
    st.divider()
    pwd = st.text_input("Admin Password", type="password")
    is_auth = (pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"))

df = fetch_data()

# DASHBOARD
if menu == "📊 Dashboard":
    st.markdown('<div class="header-box"><h1 style="color:#FF4B4B;">DEEWARY.COM</h1><p style="color:white;">C.E.O: Sardar Sami Ullah</p></div>', unsafe_allow_html=True)
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Income", f"PKR {inc:,.0f}")
        c2.metric("Total Expenses", f"PKR {exp:,.0f}")
        c3.metric("Net Balance", f"PKR {inc-exp:,.0f}")
        
    st.info("Select 'Search & Master Report' from sidebar to send full reports to WhatsApp.")

# MASTER REPORT & WHATSAPP
elif menu == "🔍 Search & Master Report":
    st.title("Strategic Master Report")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        col_pdf, col_wa = st.columns(2)
        
        with col_pdf:
            st.subheader("1. Generate Report")
            st.download_button(
                label="📄 Download Master PDF (All Tables)",
                data=export_to_pdf(df, "Master Project Report"),
                file_name=f"Deewary_Master_{datetime.now().strftime('%d_%m')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_wa:
            st.subheader("2. Send to WhatsApp")
            phone = st.text_input("Enter WhatsApp Number (e.g., 923001234567)")
            if phone:
                url_wa = get_wa_link(phone, df)
                # Using a clickable link with styling to ensure it opens
                st.markdown(f"""
                    <a href="{url_wa}" target="_blank">
                        <div style="background-color:#25D366; color:white; padding:12px; border-radius:8px; text-align:center; font-weight:bold; cursor:pointer;">
                            💬 Open WhatsApp Chat & Send Summary
                        </div>
                    </a>
                """, unsafe_allow_html=True)
                st.caption("Note: Download the PDF first, then click the button to attach it in the chat.")

# DATA ENTRY SECTIONS (Simplified)
else:
    st.title(f"{menu} Management")
    if is_auth:
        with st.form("entry_form"):
            name = st.text_input("Name/Item")
            amt = st.number_input("Amount", min_value=0)
            det = st.text_area("Details")
            if st.form_submit_button("Save Record"):
                payload = {"date": str(datetime.now().date()), "type": menu, "name": name, "amount": amt, "detail": det}
                supabase.table('transactions').insert(payload).execute()
                st.cache_data.clear()
                st.success("Saved!")
                st.rerun()
    else:
        st.warning("Please enter correct Admin Password in sidebar to add records.")
