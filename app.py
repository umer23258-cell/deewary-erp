import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
# Secrets mein SUPABASE_URL aur SUPABASE_KEY lazmi add karein
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
    
    with st.sidebar.expander("🔐 Admin Access", expanded=True):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin786"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False

# --- 4. SIDEBAR MENU & PROJECT INFO ---
with st.sidebar:
    # Title aur Navigation sabse upar
    st.title("🏗️ DEEWARY.COM ERP")
    menu = st.radio("Navigation", [
        "📊 Dashboard", 
        "💰 Income History", 
        "👷 Labor History", 
        "🏗️ Material History",
        "🔍 Search & All Reports"
    ])
    
    st.divider()

    # Project Image Navigation ke niche
    image_url = "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    st.image(image_url, use_container_width=True, caption="Site: Yousaf Colony")
    
    # Project Details Card
    st.markdown(f"""
        <div style="
            background-color: #f8f9fa; 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 5px solid #FF4B4B;
            color: #1E1E1E;
        ">
            <h4 style="margin: 0; color: #FF4B4B; font-size: 16px;">📍 Project Details</h4>
            <p style="margin: 5px 0; font-size: 13px;"><b>Location:</b> Yousaf Colony</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Size:</b> 5 Marla</p>
            <p style="margin: 5px 0; font-size: 13px;"><b>Structure:</b> 2.5 Story</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Admin Access Control
    is_auth = check_password()
    if is_auth:
        st.success("🔓 Admin Active")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

df = fetch_data()

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    st.title("Capital Flow Analytics")
    
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
    
    is_editing = "edit_id" in st.session_state
    
    if not is_editing:
        st.subheader("Quick Actions")
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
                            st.success("Transaction Synced!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            if st.button("❌ Close Form"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
        else:
            st.warning("Admin unlock required via sidebar.")

    # --- SOFTWARE INFO & SYSTEM SUPPORT ---
    st.write("##")
    st.divider()
    info_col1, info_col2 = st.columns([2, 1])
    
    with info_col1:
        st.subheader("🏡 Deewary.com ERP System")
        st.info("""
        Yeh software **Deewary.com** ke real estate aur construction projects ke financials 
        manage karne ke liye banaya gaya hai. 
        
        **System Features:**
        *   **Cloud Sync:** Supabase database ke sath connected.
        *   **Security:** Admin protected record management.
        *   **Excel Export:** Reports download karne ki sahulat.
        """)

    with info_col2:
        st.subheader("🛠️ System Support")
        whatsapp_url = "https://wa.me/923115190118"
        
        st.markdown(f"""
        **Developer:** umer sherin  
        **Status:** Operational ✅  
        **Last Update:** April 2026  
        
        ---
        **Need Help?**  
        <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
            <div style="
                background-color: #25D366;
                color: #000000;
                padding: 12px 20px;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                border: 1px solid #128C7E;
            ">
                💬 Chat on WhatsApp
            </div>
        </a>
        
        <style>
            div:hover {{
                background-color: #128C7E !important;
                color: white !important;
                transition: 0.3s;
            }}
        </style>
        
        ---
        `R` reload | Pass: `admin786`
        """, unsafe_allow_html=True)

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
        st.info(f"📊 **Total: PKR {filtered_df['amount'].sum():,.2f}**")

        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
        
        st.divider()
        st.subheader("🛠️ Manage Records")
        if is_auth:
            c_id, c_ed, c_de = st.columns([1, 1, 1])
            target_id = c_id.number_input("Enter ID to Edit/Delete", step=1, value=0)
            
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
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.warning("No data found in this category.")
