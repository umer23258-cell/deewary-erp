import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
# Ensure these are set in your .streamlit/secrets.toml
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
            # Setup form defaults for Add vs Edit
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

    # --- SOFTWARE INFO SECTION ---
    st.write("##")
    st.divider()
    info_col1, info_col2 = st.columns([2, 1])
    
   
       st.subheader("🌟 About Deewary.com ERP")
        st.markdown("""
        **Simple. Powerful. Organized.**  
        This system helps you track every rupee spent on your construction projects. No more messy registers or lost records.
        
        **Why use this?**
        *   **✅ Automatic Backup:** Everything you save is instantly backed up on our cloud server.
        *   **✅ Data Safety:** Only authorized admins can edit or delete records, keeping your data safe.
        *   **✅ One-Click Reports:** Get your full history in an Excel sheet with just one button click.
        """)
        st.success("💡 *Quick Tip: Always check the ID number from the History page before trying to edit or delete a record!*")
    with info_col2:
        st.subheader("🛠️ System Support")
        st.markdown(f"""
        **Developer:** [Your Name/IT Team]  
        **Status:** Operational ✅  
        **Last Update:** April 2026  
        
        ---
        **Shortcuts:**
        - `R` reload page
        - `Admin Pass:` admin786
        """)

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Project Management Portal | Time: {datetime.now().strftime('%H:%M')}")

# --- 6. HISTORY PAGES ---
else:
    st.title(menu)
    if not df.empty:
        # Filter Logic
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

        # Excel Download
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
        
        # Manage Records (Edit/Delete)
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
                    st.success("ID Loaded! Ab 'Dashboard' par jayen.")
                else:
                    st.error("ID is view mein nahi mili.")

            if c_de.button("🗑️ Delete"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.success("Record Deleted!")
                    st.rerun()
    else:
        st.warning("Database khali hai.")
