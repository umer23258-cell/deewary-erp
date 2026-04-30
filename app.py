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

# --- 3. FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        return pd.DataFrame()

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
    
    with st.sidebar.expander("🔐 Admin Access"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 4. SIDEBAR MENU ---
st.sidebar.title("🏗️ DEEWARY.COM ERP")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "💰 Income History", 
    "👷 Labor History", 
    "🏗️ Material History",
    "🔍 Search & All Reports"
])

# Sidebar Info Box
st.sidebar.divider()
st.sidebar.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 5px solid #FF4B4B; color: #333;">
        <p style="margin: 0; font-size: 13px;"><b>Active Site:</b> Yousaf Colony</p>
        <p style="margin: 0; font-size: 13px;"><b>Project:</b> 5 Marla (2.5 Story)</p>
    </div>
""", unsafe_allow_html=True)

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700; color: #1E1E1E; }
        [data-testid="stMetricLabel"] { font-size: 14px !important; color: #666; }
        </style>
    """, unsafe_allow_html=True)

    # --- HEADER SECTION (Logo Left, Title Mid) ---
    h_col1, h_col2, h_col3 = st.columns([1.2, 4, 1.2])
    
    with h_col1:
        # Aapka Logo
        st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=150)

    with h_col2:
        st.markdown("""
            <div style="text-align: center; margin-top: 10px;">
                <h1 style="font-family: 'Arial Black', sans-serif; font-size: 40px; letter-spacing: 7px; color: #FF4B4B; text-transform: uppercase; margin-bottom: 0px;">
                    DEEWARY.COM
                </h1>
                <hr style="width: 30%; margin: auto; border: 1.5px solid #FF4B4B; border-radius: 5px;">
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #555; letter-spacing: 3px; margin-top: 5px; font-weight: 500;">
                    REAL ESTATE & CONSTRUCTION MANAGEMENT
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("##")
    st.markdown("<h4 style='text-align: center; color: #444; font-size: 18px;'>Capital Flow Analytics</h4>", unsafe_allow_html=True)
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"PKR {inc:,.0f}")
    col2.metric("Total Expenses", f"PKR {exp:,.0f}")
    col3.metric("Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    # Edit Mode Check
    is_editing = "edit_id" in st.session_state
    
    if not is_editing:
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    else:
        st.warning(f"⚠️ Editing Mode Active (Record ID: {st.session_state.edit_id})")

    if "show_form" in st.session_state:
        if check_password():
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            
            if is_editing and not df.empty:
                edit_row = df[df['id'] == st.session_state.edit_id]
                if not edit_row.empty:
                    row = edit_row.iloc[0]
                    defaults = {
                        "date": datetime.strptime(str(row['date']), '%Y-%m-%d'),
                        "name": str(row['name']),
                        "amount": float(row['amount']),
                        "detail": str(row['detail']),
                        "occ": str(row.get('occupation', "")),
                        "rec": str(row.get('received_by', "")),
                        "meth": str(row.get('pay_method', "Cash"))
                    }

            with st.expander(f"{'Edit' if is_editing else 'New'} {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Name / Description", defaults["name"])
                    d_amt = st.number_input("Amount", min_value=0.0, value=defaults["amount"])
                    d_det = st.text_area("Details", defaults["detail"])
                    
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        col_a, col_b, col_c = st.columns(3)
                        d_occ = col_a.text_input("Occupation", defaults["occ"])
                        d_rec = col_b.text_input("Received By", defaults["rec"])
                        d_meth = col_c.selectbox("Method", ["Cash", "Online"], index=0 if defaults["meth"] == "Cash" else 1)

                    if st.form_submit_button("Update Record" if is_editing else "Save to Cloud"):
                        payload = {
                            "date": str(d_date), "type": st.session_state.show_form,
                            "name": d_name, "amount": d_amt, "detail": d_det,
                            "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth
                        }
                        try:
                            if is_editing:
                                supabase.table('transactions').update(payload).eq('id', st.session_state.edit_id).execute()
                            else:
                                supabase.table('transactions').insert(payload).execute()
                            
                            st.cache_data.clear()
                            for k in ["show_form", "edit_id"]: 
                                if k in st.session_state: del st.session_state[k]
                            st.success("Transaction Synced Successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            if st.button("❌ Close Form"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
        else:
            st.warning("Admin authentication required.")

    # --- INFO SECTION ---
    st.write("##")
    st.divider()
    info_col1, info_col2 = st.columns([2, 1])
    
    with info_col1:
        st.subheader("🏢 About Deewary.com ERP")
        st.info("A specialized portal for real estate management and construction cost tracking.")

    with info_col2:
        st.subheader("🛠️ Support")
        whatsapp_url = "https://wa.me/923115190118"
        st.markdown(f'<a href="{whatsapp_url}" style="color: #25D366; text-decoration: none; font-weight: bold;">💬 WhatsApp Support</a>', unsafe_allow_html=True)

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Project Management Portal")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()

        search = st.text_input("🔍 Search data...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.0f}**")

        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
        
        st.divider()
        st.subheader("🛠️ Manage Records")
        if check_password():
            c_id, c_ed, c_de = st.columns([1, 1, 1])
            target_id = c_id.number_input("Enter ID", step=1, value=0)
            
            if c_ed.button("✏️ Edit"):
                if target_id in filtered_df['id'].values:
                    row = filtered_df[filtered_df['id'] == target_id].iloc[0]
                    st.session_state.show_form = row['type']
                    st.session_state.edit_id = target_id
                    st.success("ID Loaded! Dashboard check karein.")
                    st.rerun()
                else:
                    st.error("ID nahi mili.")

            if c_de.button("🗑️ Delete"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.success("Record Deleted!")
                    st.rerun()
    else:
        st.warning("Database khali hai.")
