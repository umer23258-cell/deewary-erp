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

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # Header with Time
    t1, t2 = st.columns([3, 1])
    t1.title("🚀 Business Analytics Dashboard")
    t2.write(f"📅 {datetime.now().strftime('%d %b, %Y')} | 🕒 {datetime.now().strftime('%H:%M')}")
    
    if not df.empty:
        inc = df[df['type'] == 'Income']['amount'].sum()
        exp = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
        bal = inc - exp
    else:
        inc, exp, bal = 0, 0, 0

    # Professional Metric Cards
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
        .stats-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue", f"PKR {inc:,.0f}", delta_color="normal")
    with col2:
        st.metric("Operating Expenses", f"PKR {exp:,.0f}", delta="-High", delta_color="inverse")
    with col3:
        st.metric("Net Cash Flow", f"PKR {bal:,.0f}", delta="In-Hand")

    st.divider()

    # --- PROFESSIONAL GALLERY & PROJECT SECTION ---
    st.subheader("🏗️ Project Intelligence: Yousaf Colony Site")
    
    # Photos in small tiles
    img_col1, img_col2, img_col3, detail_col = st.columns([1, 1, 1, 3])
    
    with img_col1:
        st.image("https://i.ibb.co/6Jbx8yjD/Whats-App-Image-2026-04-30-at-12-11-01-PM.jpg", use_container_width=True)
    with img_col2:
        st.image("https://i.ibb.co/6R0yR8Xz/1JK5M0FR.jpg", use_container_width=True)
    with img_col3:
        st.image("https://i.ibb.co/ZRgY9wLC/Whats-App-Image-2026-04-30-at-12-25-05-PM.jpg", use_container_width=True)

    with detail_col:
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; height: 100%;">
            <h4 style="margin-top:0;">📋 Project Summary</h4>
            <b>Site Location:</b> Plot 42-B, Yousaf Colony<br>
            <b>Lead Engineer:</b> Umer Sherin<br>
            <b>Phase:</b> Finishing & Interior<br>
            <b>Target:</b> Completion by end of May
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Quick Actions (Maintain original functionality)
    is_editing = "edit_id" in st.session_state
    if not is_editing:
        st.subheader("⚡ Quick Transactions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Register Income", use_container_width=True): st.session_state.show_form = "Income"; st.rerun()
        if c2.button("👷 Pay Labor Fee", use_container_width=True): st.session_state.show_form = "Labor"; st.rerun()
        if c3.button("🏗️ Purchase Material", use_container_width=True): st.session_state.show_form = "Material"; st.rerun()
    else:
        st.warning(f"⚠️ Editing Mode Active (Record ID: {st.session_state.edit_id})")

    # Entry Form (Same as original)
    if "show_form" in st.session_state:
        if check_password():
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            if is_editing and not df.empty:
                edit_row = df[df['id'] == st.session_state.edit_id]
                if not edit_row.empty:
                    row = edit_row.iloc[0]
                    defaults = {
                        "date": datetime.strptime(str(row['date']), '%Y-%m-%d'),
                        "name": str(row['name']), "amount": float(row['amount']), "detail": str(row['detail']),
                        "occ": str(row.get('occupation', "")), "rec": str(row.get('received_by', "")), "meth": str(row.get('pay_method', "Cash"))
                    }

            with st.expander(f"{'Update' if is_editing else 'New'} {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Entity Name", defaults["name"])
                    d_amt = st.number_input("Amount (PKR)", min_value=0.0, value=defaults["amount"])
                    d_det = st.text_area("Transaction Details", defaults["detail"])
                    
                    d_occ, d_rec, d_meth = "", "", ""
                    if st.session_state.show_form == "Labor":
                        col_a, col_b, col_c = st.columns(3)
                        d_occ = col_a.text_input("Role/Occupation", defaults["occ"])
                        d_rec = col_b.text_input("Recieved By", defaults["rec"])
                        d_meth = col_c.selectbox("Payment Method", ["Cash", "Online"], index=0 if defaults["meth"] == "Cash" else 1)

                    if st.form_submit_button("Confirm & Sync"):
                        payload = {"date": str(d_date), "type": st.session_state.show_form, "name": d_name, "amount": d_amt, "detail": d_det, "occupation": d_occ, "received_by": d_rec, "pay_method": d_meth}
                        try:
                            if is_editing: supabase.table('transactions').update(payload).eq('id', st.session_state.edit_id).execute()
                            else: supabase.table('transactions').insert(payload).execute()
                            st.cache_data.clear()
                            for k in ["show_form", "edit_id"]: 
                                if k in st.session_state: del st.session_state[k]
                            st.success("Synced to Cloud!")
                            st.rerun()
                        except Exception as e: st.error(f"Sync Error: {e}")
            if st.button("❌ Dismiss"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    # Footer
    st.write("##")
    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Enterprise Resource Planning | System Status: Active")

# --- 6. HISTORY PAGES (Original Logic) ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()

        search = st.text_input("🔍 Filter records...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Filtered Sum: PKR {filtered_df['amount'].sum():,.2f}**")
        
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Export to Excel", buffer.getvalue(), f"{menu}_Report.xlsx")
        
        st.divider()
        if check_password():
            st.subheader("🛠️ Record Management")
            c_id, c_ed, c_de = st.columns([1, 1, 1])
            target_id = c_id.number_input("Transaction ID", step=1, value=0)
            if c_ed.button("✏️ Edit Record", use_container_width=True):
                if target_id in filtered_df['id'].values:
                    row = filtered_df[filtered_df['id'] == target_id].iloc[0]
                    st.session_state.show_form = row['type']
                    st.session_state.edit_id = target_id
                    st.success("Redirecting to Dashboard...")
            if c_de.button("🗑️ Delete Permanently", use_container_width=True):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.rerun()
