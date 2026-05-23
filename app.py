import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import urllib.parse
import streamlit.components.v1 as components
# PDF ke liye libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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
    .sidebar-btn-container { margin-bottom: 10px; }
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3.5em; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
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

@st.cache_data(ttl=30)
def fetch_labor_profiles():
    try:
        res = supabase.table('labor_profiles').select("*").order('id', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

# --- HELPER FUNCTION FOR WHATSAPP LINK GENERATION ---
def generate_whatsapp_link(type_tx, name, amount, detail):
    base_msg = f"🏗️ *Deewary.com ERP Notification*\n\n"
    base_msg += f"• *Type:* {type_tx}\n"
    base_msg += f"• *Name/Item:* {name}\n"
    base_msg += f"• *Amount:* PKR {amount:,.0f}\n"
    if detail:
        base_msg += f"• *Details:* {detail}\n"
    base_msg += f"\n_System generated tracking logs summary entry._"
    encoded_text = urllib.parse.quote(base_msg)
    return f"https://api.whatsapp.com/send?text={encoded_text}"


# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "👷 Labor Profiles Application", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    
    if is_auth:
        st.success("🔓 Admin Mode")
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

# --- 6. DASHBOARD INTERFACE ---
if menu == "📊 Dashboard":
    st.markdown("""
        <div class="header-box">
            <h1 style="color: #FF4B4B; margin: 0; font-family: 'Arial Black'; letter-spacing: 3px;">DEEWARY.COM</h1>
            <p style="color: white; letter-spacing: 2px; font-size: 12px; margin-bottom: 10px;">PREMIUM CONSTRUCTION MANAGEMENT</p>
            <div style="background: #FF4B4B; color: white; display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;">
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
        
        # --- NEW CONTEXT BLOCK: CASH FLOW FORECAST & ALERTS ---
        try:
            df['date_parsed'] = pd.to_datetime(df['date'])
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_exp_df = df[(df['type'].isin(['Labor', 'Material'])) & (df['date_parsed'] >= seven_days_ago)]
            total_7_day_exp = recent_exp_df['amount'].sum()
            daily_burn_rate = total_7_day_exp / 7
        except:
            daily_burn_rate = 0

        # High visibility warnings check configuration sequence
        if net_bal < 50000:
            st.markdown(f"""
                <div class="alert-box">
                    🚨 LOW BALANCE ALERT: Running Liquid Balance is critical (PKR {net_bal:,.0f}). 
                    Please arrange funds to ensure workflow stability at the construction perimeter line.
                </div>
            """, unsafe_allow_html=True)
        elif daily_burn_rate > 0:
            days_left = net_bal / daily_burn_rate
            if days_left <= 5:
                st.markdown(f"""
                    <div class="alert-box" style="background-color: #fff3e0; border-left-color: #ff9800; color: #e65100;">
                        ⚠️ CASH FLOW WARNING: At the current velocity of PKR {daily_burn_rate:,.0f}/day, 
                        your reserve balance will sustain operations for approximately {days_left:.1f} days only.
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="forecast-box">
                        📈 CASH FLOW FORECAST: Current Burn Rate is PKR {daily_burn_rate:,.0f}/day. 
                        Safe operational runway left: ~{days_left:.1f} Days.
                    </div>
                """, unsafe_allow_html=True)

        # --- EXECUTIVE KPI CARDS ---
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.markdown(f"""<div class='kpi-card'>
                <p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>💰 TOTAL INVESTMENT RECEIPT</p>
                <h2 style='color:#2e7d32; margin:5px 0 0 0;'>PKR {inc:,.0f}</h2>
            </div>""", unsafe_allow_html=True)
        with col_kpi2:
            st.markdown(f"""<div class='kpi-card'>
                <p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>📉 RUNNING OUTFLOW EXPENSES</p>
                <h2 style='color:#c62828; margin:5px 0 0 0;'>PKR {exp:,.0f}</h2>
            </div>""", unsafe_allow_html=True)
        with col_kpi3:
            bal_color = "#2e7d32" if net_bal >= 0 else "#c62828"
            st.markdown(f"""<div class='kpi-card'>
                <p style='color:#6c757d; margin:0; font-size:14px; font-weight:bold;'>⚖️ NET LIQUID BALANCE</p>
                <h2 style='color:{bal_color}; margin:5px 0 0 0;'>PKR {net_bal:,.0f}</h2>
            </div>""", unsafe_allow_html=True)

    # --- SHOW FORMS (When buttons in Sidebar are clicked) ---
    if "show_form" in st.session_state and is_auth:
        ftype = st.session_state.show_form
        
        if ftype == "RegisterLabor":
            with st.expander("📝 Register New Labor Profile Document Application", expanded=True):
                with st.form("labor_profile_form"):
                    l_name = st.text_input("Labor Full Name *")
                    l_phone = st.text_input("Phone Number")
                    l_cnic = st.text_input("CNIC Number")
                    l_occ = st.text_input("Occupation / Skill Type (e.g., Mistry, Plumber)")
                    l_contract = st.number_input("Total Contract Amount / Taka Amount (PKR)", min_value=0, value=0)
                    l_rating = st.slider("Rating / Performance evaluation", min_value=1, max_value=5, value=5)
                    l_photo = st.file_uploader("Upload Labor Profile Picture", type=['jpg', 'jpeg', 'png'])
                    l_details = st.text_area("A to Z Personal Data Notes / Address / References")
                    
                    if st.form_submit_button("Save Profile Application"):
                        if l_name:
                            img_url = ""
                            if l_photo:
                                f_name = f"labor_{int(datetime.now().timestamp())}_{l_photo.name}"
                                supabase.storage.from_('material_pics').upload(f_name, l_photo.getvalue())
                                img_url = supabase.storage.from_('material_pics').get_public_url(f_name)
                                
                            payload = {
                                "name": l_name, "phone": l_phone, "cnic": l_cnic, "occupation": l_occ,
                                "total_contract_amount": l_contract, "rating": l_rating,
                                "photo_url": img_url, "details": l_details
                            }
                            supabase.table('labor_profiles').insert(payload).execute()
                            st.cache_data.clear()
                            st.session_state.pop("show_form")
                            st.rerun()
                        else:
                            st.error("Labor Full Name is strictly required.")
        else:
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title / Name")
                    d_amt = st.number_input("Amount", min_value=0)
                    
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if ftype in ["Income", "Labor", "Material"]:
                        col1, col2 = st.columns(2)
                        d_occ = col1.text_input("Occupation / Job Type")
                        d_rec = col2.text_input("Received By / Authorized")
                        d_meth = st.selectbox("Payment Method", ["Cash", "Online", "Cheque"])

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
                        
                        payload = {
                            "date": str(d_date), "type": ftype, "name": d_name, "amount": d_amt, 
                            "detail": d_det, "image_url": img_url, "occupation": d_occ,
                            "received_by": d_rec, "pay_method": d_meth
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        
                        # --- DYNAMIC AUTOMATED WHATSAPP NOTIFICATION TRIGGER ---
                        wa_url = generate_whatsapp_link(ftype, d_name, d_amt, d_det)
                        st.markdown(f"""<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; margin-top:10px;">📲 Click to Broadcast This Entry Receipt to WhatsApp Instantly</div></a>""", unsafe_allow_html=True)
                        st.info("Record inserted into database cloud files successfully. Click button above if you wish to push to messaging channels before app reloading refreshes states context views.")
                        
                        st.session_state.pop("show_form")
                        if st.button("Proceed & Refresh View Dashboard"):
                            st.rerun()

    st.write("##")
    status_df = fetch_project_status()
    total_tasks = len(status_df)
    done_tasks = len(status_df[status_df['status'] == 'Done'])
    prog_val = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("### 📈 Overall Progress")
        st.progress(prog_val / 100)
        st.markdown(f"**{prog_val}% Work Completed**")
        chart_code = f"graph LR\nA[Start] --> B{{Progress: {prog_val}%}}\nstyle B fill:#FF4B4B,color:#fff"
        components.html(f"<div style='background:#f8f9fa; border-radius:10px; padding:10px;'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=120)

    with col_right:
        st.markdown("### 📝 Tasks Summary")
        st.write(f"✅ Finished: {done_tasks}")
        st.write(f"⏳ Remaining: {total_tasks - done_tasks}")
        if st.button("Refresh Data"): st.cache_data.clear(); st.rerun()

    if "show_status_form" in st.session_state and is_auth:
        with st.expander("🛠️ Admin: Update Site Status", expanded=True):
            with st.form("status_form"):
                task = st.selectbox("Select Task", status_df['task_name'].tolist())
                stat = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update"):
                    supabase.table('project_status').upsert({"task_name": task, "status": stat}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("### 🏗️ Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
            st.markdown(f'<div style="background:{bg}; padding:10px; border-radius:10px; margin-bottom:5px; border-left:5px solid #FF4B4B;"><strong>{icon} {row["task_name"]}</strong></div>', unsafe_allow_html=True)

    st.divider()
    st.video("https://youtu.be/AiA4PkXturU")


# --- LABOR PROFILES APPLICATION PAGE ---
elif menu == "👷 Labor Profiles Application":
    st.title("👷 Labor Profiles Application Directory")
    st.write("Labor card entries database file records, detailing specialized contracts and ratings metrics configuration.")
    
    labor_df = fetch_labor_profiles()
    
    if not labor_df.empty:
        l_search = st.text_input("🔎 Search Profile Directory by Name, CNIC, or Job Skillset Type...")
        if l_search:
            l_mask = labor_df.astype(str).apply(lambda x: x.str.contains(l_search, case=False)).any(axis=1)
            labor_df = labor_df[l_mask]
            
        st.dataframe(labor_df[["id", "name", "phone", "cnic", "occupation", "total_contract_amount", "rating"]], use_container_width=True)
        
        st.write("### 🖼️ Profiles Deep Dive Cards View")
        for _, row in labor_df.iterrows():
            with st.container():
                st.markdown(f"#### 👤 {row['name']} ({row['occupation'] if row['occupation'] else 'General Labor'})")
                c_img, c_info = st.columns([1, 3])
                
                with c_img:
                    photo_path = row.get('photo_url', '')
                    if photo_path and str(photo_path) != "nan":
                        st.image(photo_path, use_container_width=True)
                    else:
                        st.info("No Profile Pic uploaded.")
                        
                with c_info:
                    st.markdown(f"**📞 Phone:** {row['phone']} | **🪪 CNIC:** {row['cnic']}")
                    st.markdown(f"**💰 Total Contract (Taka):** PKR {row['total_contract_amount']:,.0f}")
                    
                    stars = "⭐" * int(row['rating'] if row['rating'] else 5)
                    st.markdown(f"**📊 Performance Rating Evaluation:** {stars}")
                    st.markdown(f"**📝 Complete Detailed Information Dossier (A to Z Data):**")
                    st.info(row['details'] if row['details'] else "No additional background profile summary logs provided.")
                
                st.divider()
                
        if is_auth:
            st.write("### 🛠️ Administrative Operations")
            l_tid = st.text_input("Enter Profile Row Unique Identity ID to Delete File permanently")
            if st.button("🗑️ Delete Profile Record", key="del_lab_prof_btn"):
                if l_tid:
                    supabase.table('labor_profiles').delete().eq('id', l_tid).execute()
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("No Labor profiles have been provisioned inside the system ledger table tracking logs configuration folder yet.")


# --- 8. ORIGINAL HISTORY PAGES LOGIC (As it was) ---
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
