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

# --- 3. PROFESSIONAL BRANDING & THEME ---
st.markdown("""
    <style>
    /* Main Branding Header */
    .branding-container {
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.1);
    }
    .branding-container h1 {
        color: white !important;
        font-family: 'Arial Black', sans-serif;
        font-size: 42px !important;
        margin: 0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .branding-container p {
        color: #E2E8F0 !important;
        font-size: 18px !important;
        margin-top: 5px;
        font-weight: 300;
        letter-spacing: 1px;
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #1E3A8A;
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #64748B;
    }
    </style>
    
    <div class="branding-container">
        <h1>DEEWARY.COM</h1>
        <p>Real Estate & Construction Company</p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. FUNCTIONS ---
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
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 5. SIDEBAR MENU & PROJECT INFO ---
with st.sidebar:
    st.title("🏗️ ERP PANEL")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Active Site: Yousaf Colony")
    
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #1E3A8A; color: #1E1E1E;">
            <h4 style="margin: 0; color: #1E3A8A; font-size: 16px;">📍 Current Project</h4>
            <p style="margin: 5px 0; font-size: 13px;"><b>Location:</b> Yousaf Colony</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Size:</b> 5 Marla</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Structure:</b> 2.5 Story</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 6. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.subheader("Financial Analytics Overview")
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Project Income", f"PKR {inc:,.0f}")
    col2.metric("Total Site Expenses", f"PKR {exp:,.0f}")
    col3.metric("Current Net Balance", f"PKR {bal:,.0f}")

    st.divider()
    
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("Quick Management Tools")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
        if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
        if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    else:
        st.warning(f"⚠️ Editing Mode Active (ID: {st.session_state.edit_id})")

    if "show_form" in st.session_state:
        if is_auth:
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            if is_editing and not df.empty:
                edit_row = df[df['id'] == st.session_state.edit_id]
                if not edit_row.empty:
                    row = edit_row.iloc[0]
                    defaults = {
                        "date": datetime.strptime(str(row['date']), '%Y-%m-%d'),
                        "name": str(row['name']), "amount": float(row['amount']),
                        "detail": str(row['detail']), "occ": str(row.get('occupation', "")),
                        "rec": str(row.get('received_by', "")), "meth": str(row.get('pay_method', "Cash"))
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
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        try:
                            if is_editing: supabase.table('transactions').update(payload).eq('id', st.session_state.edit_id).execute()
                            else: supabase.table('transactions').insert(payload).execute()
                            st.cache_data.clear()
                            [st.session_state.pop(k) for k in ["show_form", "edit_id"] if k in st.session_state]
                            st.success("Transaction Synced!")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
            if st.button("❌ Close Form"):
                [st.session_state.pop(k) for k in ["show_form", "edit_id"] if k in st.session_state]
                st.rerun()
        else: st.warning("Admin unlock required via sidebar.")

    # --- FOOTER & SUPPORT ---
    st.write("##")
    st.divider()
    supp_col1, supp_col2 = st.columns([2, 1])
    
    with supp_col1:
        st.subheader("🏗️ Management Portal Info")
        st.info("Deewary.com ERP system is active and monitoring project financial flow.")
    
    with supp_col2:
        whatsapp_url = "https://wa.me/923115190118"
        st.markdown(f"""
        <style>
            .wa-btn {{
                background-color: #25D366;
                color: #000000 !important;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                font-weight: 800;
                display: block;
                text-decoration: none !important;
                border: 2px solid #128C7E;
            }}
        </style>
        <a href="{whatsapp_url}" target="_blank" class="wa-btn">💬 WhatsApp Support</a>
        """, unsafe_allow_html=True)

# --- 7. HISTORY PAGES ---
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
        st.info(f"📊 **Category Total: PKR {filtered_df['amount'].sum():,.2f}**")
        
        buffer = io.BytesIO(); filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Report", buffer.getvalue(), f"{menu}.xlsx")
        
        st.divider(); st.subheader("🛠️ Record Management")
        if is_auth:
            c_id, c_ed, c_de = st.columns([1, 1, 1]); target_id = c_id.number_input("Enter ID", step=1, value=0)
            if c_ed.button("✏️ Edit"):
                if target_id in filtered_df['id'].values:
                    row = filtered_df[filtered_df['id'] == target_id].iloc[0]
                    st.session_state.show_form = row['type']; st.session_state.edit_id = target_id
                    st.rerun()
            if c_de.button("🗑️ Delete"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear(); st.success("Deleted!"); st.rerun()
    else: st.warning("No records found.")

st.divider()
st.caption(f"© {datetime.now().year} Deewary.com | Designed for Excellence")
