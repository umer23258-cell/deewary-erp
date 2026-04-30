import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# Custom CSS for WhatsApp and Styling
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    .whatsapp-float {
        position: fixed; width: 60px; height: 60px; bottom: 40px; right: 40px;
        background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center;
        font-size: 30px; box-shadow: 2px 2px 3px #999; z-index: 100;
    }
    .whatsapp-float:hover { background-color: #128C7E; color: white; }
    </style>
    <a href="https://wa.me/923115190118" class="whatsapp-float" target="_blank">
        <i style="margin-top:16px;" class="fa fa-whatsapp"></i>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css">
    </a>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Wrong password!")
    return False

# --- 4. SIDEBAR MENU ---
st.sidebar.title("🏗️ DEEWARY.COM ERP")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "💰 Income History", "👷 Labor History", "🏗️ Material History", "🔍 Search & Reports"])

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.title("Capital Flow Analytics")
    
    # --- LEVEL 1: AMOUNTS ---
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else: inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # --- LEVEL 2: QUICK ACTIONS ---
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("⚡ Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income", use_container_width=True): st.session_state.show_form = "Income"; st.rerun()
        if c2.button("👷 Pay Labor", use_container_width=True): st.session_state.show_form = "Labor"; st.rerun()
        if c3.button("🏗️ Buy Material", use_container_width=True): st.session_state.show_form = "Material"; st.rerun()
    else:
        st.warning(f"⚠️ Editing Mode Active (ID: {st.session_state.edit_id})")

    # --- LEVEL 3: SOFTWARE DETAIL ---
    st.write("##")
    with st.container():
        st.markdown("""
        <div style="background-color: #f1f3f5; padding: 20px; border-radius: 15px; border-left: 8px solid #007bff;">
            <h3 style="margin:0; color:#007bff;">🛠️ Deewary.com Enterprise System</h3>
            <p style="margin-top:10px;">Yeh ERP solution Deewary.com ke construction aur real estate projects ke mali muamlat ko digitalize karne ke liye design kiya gaya hai. 
            Is mein <b>Supabase Cloud Database</b> ka istemal kiya gaya hai jo aapke data ko 100% secure aur live rakhta hai.</p>
            <p><b>Developer:</b> Umer Sherin | <b>Status:</b> Premium Version</p>
        </div>
        """, unsafe_allow_html=True)

    # --- LEVEL 4: PIC & PROJECT DETAIL ---
    st.write("##")
    st.divider()
    st.subheader("📸 Project Site: Yousaf Colony")
    
    p_col1, p_col2, p_detail = st.columns([1, 1, 2])
    
    with p_col1:
        st.image("https://i.ibb.co/6Jbx8yjD/Whats-App-Image-2026-04-30-at-12-11-01-PM.jpg", width=250, caption="Front Elevation")
    with p_col2:
        st.image("https://i.ibb.co/6R0yR8Xz/1JK5M0FR.jpg", width=250, caption="Interior Work")
        
    with p_detail:
        st.markdown("""
        <div style="background-color: white; border: 1px solid #ddd; padding: 15px; border-radius: 10px;">
            <h4 style="color: #333;">📋 Project Technical Specs</h4>
            <hr style="margin: 5px 0;">
            <b>Plot Size:</b> 5 Marla (G-11 Type)<br>
            <b>Phase:</b> Paint & Woodwork Phase<br>
            <b>Lead Supervisor:</b> Umer Sherin<br>
            <b>Labor Force:</b> 12 Registered Workers<br>
            <b>Completion Target:</b> 25th May 2026
        </div>
        """, unsafe_allow_html=True)
        st.write("🏗️ **Site Completion:**")
        st.progress(85)

    # --- FORM LOGIC (Original) ---
    if "show_form" in st.session_state:
        if check_password():
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            if is_editing and not df.empty:
                row = df[df['id'] == st.session_state.edit_id].iloc[0]
                defaults = {"date": datetime.strptime(str(row['date']), '%Y-%m-%d'), "name": str(row['name']), "amount": float(row['amount']), "detail": str(row['detail']), "occ": str(row.get('occupation', "")), "rec": str(row.get('received_by', "")), "meth": str(row.get('pay_method', "Cash"))}

            with st.expander(f"{st.session_state.show_form} Entry Form", expanded=True):
                with st.form("main_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Description", defaults["name"])
                    d_amt = st.number_input("Amount", min_value=0.0, value=defaults["amount"])
                    d_det = st.text_area("Notes", defaults["detail"])
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        c_a, c_b, c_c = st.columns(3)
                        d_occ = c_a.text_input("Occupation", defaults["occ"])
                        d_rec = c_b.text_input("Received By", defaults["rec"])
                        d_meth = c_c.selectbox("Method", ["Cash", "Online"], index=0)
                    
                    if st.form_submit_button("Sync to Cloud"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        if is_editing: supabase.table('transactions').update(payload).eq('id', st.session_state.edit_id).execute()
                        else: supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        for k in ["show_form", "edit_id"]: 
                            if k in st.session_state: del st.session_state[k]
                        st.success("Data Updated!"); st.rerun()

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: f_df = df[df['type'] == 'Income']
        elif "Labor" in menu: f_df = df[df['type'] == 'Labor']
        elif "Material" in menu: f_df = df[df['type'] == 'Material']
        else: f_df = df.copy()

        search = st.text_input("🔍 Search...")
        if search: f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(f_df, use_container_width=True)
        st.success(f"Total Amount: PKR {f_df['amount'].sum():,.0f}")
        
        if check_password():
            st.divider()
            st.subheader("Manage Records")
            t_id = st.number_input("Enter ID", step=1, value=0)
            if st.button("Delete"):
                supabase.table('transactions').delete().eq('id', t_id).execute()
                st.cache_data.clear(); st.rerun()
