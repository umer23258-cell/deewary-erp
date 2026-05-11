import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- CUSTOM CSS FOR INTERFACE ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #ffffff; }
    
    /* Metric Cards Styling */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Professional Header Box */
    .header-box {
        text-align: center;
        background: linear-gradient(135deg, #1e1e1e 0%, #333333 100%);
        padding: 30px;
        border-radius: 20px;
        border-bottom: 5px solid #FF4B4B;
        margin-bottom: 25px;
    }

    /* Task Progress Card */
    .task-card {
        background: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 10px; height: 3.5em; }
        h2 { font-size: 1.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
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
            else: st.error("Wrong password!")
    return False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏗️ DEEWARY ERP")
    menu = st.radio("Go To", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & All Reports"])
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Mode")
        if st.button("⚙️ Change Task Status"): st.session_state.show_status_form = True
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
    st.divider()
    st.image("https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg", caption="Active Site: Yousaf Colony")

df = fetch_data()

# --- 5. DASHBOARD INTERFACE ---
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
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Income", f"PKR {inc:,.0f}")
    m2.metric("📉 Total Expenses", f"PKR {exp:,.0f}")
    m3.metric("⚖️ Net Balance", f"PKR {bal:,.0f}")

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
        chart_code = f"graph LR\nA[Project Start] --> B{{Progress: {prog_val}%}}\nstyle B fill:#FF4B4B,color:#fff"
        components.html(f"<div style='background:#f8f9fa; border-radius:10px; padding:10px;'><pre class='mermaid'>{chart_code}</pre></div><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=120)

    with col_right:
        st.markdown("### 📝 Quick Tasks View")
        st.write(f"✅ Finished: {done_tasks}")
        st.write(f"⏳ In Progress: {total_tasks - done_tasks}")
        if st.button("Refresh Data"): st.cache_data.clear(); st.rerun()

    if "show_status_form" in st.session_state and st.session_state.show_status_form:
        with st.expander("🛠️ Admin: Update Site Status", expanded=True):
            with st.form("status_form"):
                task = st.selectbox("Select Project Task", status_df['task_name'].tolist())
                stat = st.radio("Status", ["Pending", "Done"], horizontal=True)
                if st.form_submit_button("Update Status"):
                    supabase.table('project_status').upsert({"task_name": task, "status": stat}).execute()
                    st.cache_data.clear(); st.session_state.show_status_form = False; st.rerun()

    st.divider()
    st.markdown("### 🏗️ Construction Checklist")
    t_cols = st.columns(3)
    for i, row in status_df.iterrows():
        with t_cols[i % 3]:
            icon = "✅" if row['status'] == "Done" else "⏳"
            bg = "#e8f5e9" if row['status'] == "Done" else "#fff3e0"
            st.markdown(f"""
                <div style="background:{bg}; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #ddd;">
                    <strong style="font-size:14px;">{icon} {row['task_name']}</strong><br>
                    <small>{row['status']}</small>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("⚡ Quick Transactions")
    q1, q2, q3 = st.columns(3)
    if q1.button("➕ Income"): st.session_state.show_form = "Income"
    if q2.button("👷 Labor"): st.session_state.show_form = "Labor"
    if q3.button("🏗️ Material"): st.session_state.show_form = "Material"

    if "show_form" in st.session_state:
        if is_auth:
            ftype = st.session_state.show_form
            with st.expander(f"Register {ftype}", expanded=True):
                with st.form("quick_form"):
                    d_date = st.date_input("Date", datetime.now())
                    d_name = st.text_input("Title")
                    d_amt = st.number_input("Amount", min_value=0)
                    
                    # --- NEW IMAGE UPLOAD FOR MATERIAL ---
                    img_file = None
                    if ftype == "Material":
                        img_file = st.file_uploader("Upload Bill/Material Photo", type=['jpg', 'png', 'jpeg'])
                    
                    d_occ, d_rec, d_meth = "", "", "Cash"
                    if ftype in ["Income", "Labor"]:
                        c_a, c_b = st.columns(2)
                        d_occ = c_a.text_input("Occupation")
                        d_meth = c_a.selectbox("Method", ["Cash", "Online", "Cheque"])
                        d_rec = c_b.text_input("Authorized By")
                    d_det = st.text_area("Notes")
                    
                    if st.form_submit_button("Submit"):
                        img_url = ""
                        # Handle Image Upload to Supabase Storage
                        if img_file and ftype == "Material":
                            file_path = f"bills/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{img_file.name}"
                            supabase.storage.from_('bill_images').upload(file_path, img_file.getvalue())
                            img_url = supabase.storage.from_('bill_images').get_public_url(file_path)

                        payload = {
                            "date": str(d_date), 
                            "type": ftype, 
                            "name": d_name, 
                            "amount": d_amt, 
                            "detail": d_det, 
                            "occupation": d_occ, 
                            "received_by": d_rec, 
                            "pay_method": d_meth,
                            "bill_url": img_url # Make sure to add this column in your Supabase 'transactions' table
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear(); st.session_state.pop("show_form"); st.rerun()
        else: st.warning("Please login as Admin to add data.")

    st.divider()
    st.markdown("### 🏘️ Showcase Project")
    v1, v2 = st.columns([1, 1])
    with v1: st.video("https://youtu.be/AiA4PkXturU")
    with v2:
        st.info("Hamara ye project modern aesthetics aur structural durability ka behtareen namuna hai. Yousaf Colony ki top site.")

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com Portal | Smart Management")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()
        
        search = st.text_input("🔎 Filter results...")
        if search:
            mask = f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            f_df = f_df[mask]
        
        st.dataframe(f_df, use_container_width=True)
        st.metric("Total PKR", f"{f_df['amount'].sum():,.0f}")

        if is_auth:
            st.divider()
            tid = st.text_input("Enter ID to Delete/Edit")
            if tid:
                if st.button("🗑️ Delete Permanently"):
                    supabase.table('transactions').delete().eq('id', tid).execute()
                    st.cache_data.clear(); st.rerun()

        buf = io.BytesIO()
        f_df.to_excel(buf, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No data found.")
