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

def delete_entry(id):
    try:
        supabase.table('transactions').delete().eq('id', id).execute()
        st.cache_data.clear()
        st.success("Record deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

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

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.title("🏗️ DEEWARY.COM ERP")
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
        <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF4B4B; color: #1E1E1E;">
            <h4 style="margin: 0; color: #FF4B4B; font-size: 16px;">📍 Current Project</h4>
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

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # (Same Header as your original code)
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1: st.image("https://i.ibb.co/HfKMwQJh/deewaryn-com-logo.jpg", width=110)
    with h_col2:
        st.markdown("""
            <div style="text-align: center; margin-top: 5px; background-color: #1E1E1E; padding: 15px; border-radius: 15px; border: 1px solid #333;">
                <h2 style="font-family: 'Arial Black', sans-serif; font-size: 28px; letter-spacing: 4px; color: #FF4B4B; text-transform: uppercase; margin: 0;">DEEWARY.COM</h2>
                <hr style="width: 15%; margin: 8px auto; border: 1px solid #FF4B4B;">
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 12px; color: #FFFFFF; letter-spacing: 2px; margin-bottom: 5px; font-weight: 500;">REAL ESTATE & CONSTRUCTION MANAGEMENT</p>
                <p style="font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #FF4B4B; font-weight: 700; margin: 0;">C.E.O: SARDAR SAMI ULLAH</p>
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
    
    # --- ADD/EDIT FORM ---
    if is_auth:
        if "edit_data" in st.session_state or "show_form" in st.session_state:
            form_type = st.session_state.get("show_form", st.session_state.get("edit_data", {}).get("type", "Income"))
            edit_mode = "edit_data" in st.session_state
            data = st.session_state.get("edit_data", {})

            with st.expander(f"{'📝 Edit' if edit_mode else '➕ New'} {form_type} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", datetime.strptime(data['date'], '%Y-%m-%d') if edit_mode else datetime.now())
                    d_name = st.text_input("Name / Description", data.get('name', ''))
                    d_amt = st.number_input("Amount", min_value=0.0, value=float(data.get('amount', 0.0)))
                    d_det = st.text_area("Details", data.get('detail', ''))
                    
                    if st.form_submit_button("Save to Cloud"):
                        payload = {"date": str(d_date), "type": form_type, "name": d_name, "amount": d_amt, "detail": d_det}
                        if edit_mode:
                            supabase.table('transactions').update(payload).eq('id', data['id']).execute()
                        else:
                            supabase.table('transactions').insert(payload).execute()
                        
                        st.cache_data.clear()
                        if "edit_data" in st.session_state: del st.session_state["edit_data"]
                        if "show_form" in st.session_state: del st.session_state["show_form"]
                        st.success("Done!")
                        st.rerun()

            if st.button("❌ Close Form"):
                if "edit_data" in st.session_state: del st.session_state["edit_data"]
                if "show_form" in st.session_state: del st.session_state["show_form"]
                st.rerun()
        else:
            st.subheader("Quick Actions")
            c1, c2, c3 = st.columns(3)
            if c1.button("➕ Add Income"): st.session_state.show_form = "Income"; st.rerun()
            if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"; st.rerun()
            if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"; st.rerun()

    # (About and Support sections remain the same)
    st.divider()
    st.markdown("<h3 style='color: #FF4B4B;'>🏘️ OUR COMPLETED PROJECT </h3>", unsafe_allow_html=True)
    # ... (Rest of your original Dashboard content)

# --- 6. HISTORY PAGES (With Edit/Delete) ---
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
        
        # Display Table
        st.dataframe(filtered_df.drop(columns=['id'], errors='ignore'), use_container_width=True)
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.2f}**")

        # Edit/Delete Actions (Only for Admin)
        if is_auth:
            st.subheader("Modify Records")
            for index, row in filtered_df.iterrows():
                col_id, col_name, col_amt, col_btn1, col_btn2 = st.columns([1, 3, 2, 1, 1])
                col_id.write(f"`{row['date']}`")
                col_name.write(row['name'])
                col_amt.write(f"PKR {row['amount']:,.0f}")
                
                if col_btn1.button("📝 Edit", key=f"edit_{row['id']}"):
                    st.session_state.edit_data = row.to_dict()
                    st.session_state.menu = "📊 Dashboard" # Redirect to dashboard to use the form
                    st.rerun()
                
                if col_btn2.button("🗑️ Del", key=f"del_{row['id']}"):
                    delete_entry(row['id'])

        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
    else:
        st.warning("No records found.")
