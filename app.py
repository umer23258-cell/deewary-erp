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
        st.error(f"Error fetching data: {e}")
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
    col3.metric("Net Balance", f"PKR {bal:,.0f}", delta_color="normal")

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
        st.warning(f"⚠️ Editing Record ID: {st.session_state.edit_id}")

    if "show_form" in st.session_state:
        if check_password():
            # Set default values for Form (Pre-fill if editing)
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            
            if is_editing and not df.empty:
                edit_row = df[df['id'] == st.session_state.edit_id]
                if not edit_row.empty:
                    row = edit_row.iloc[0]
                    defaults["date"] = datetime.strptime(str(row['date']), '%Y-%m-%d')
                    defaults["name"] = str(row['name'])
                    defaults["amount"] = float(row['amount'])
                    defaults["detail"] = str(row['detail'])
                    defaults["occ"] = str(row.get('occupation', ""))
                    defaults["rec"] = str(row.get('received_by', ""))
                    defaults["meth"] = str(row.get('pay_method', "Cash"))

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

                    submit_label = "Update Record" if is_editing else "Save to Cloud"
                    if st.form_submit_button(submit_label):
                        new_data = {
                            "date": str(d_date), 
                            "type": st.session_state.show_form,
                            "name": d_name, 
                            "amount": d_amt, 
                            "detail": d_det,
                            "occupation": d_occ, 
                            "received_by": d_rec, 
                            "pay_method": d_meth
                        }
                        try:
                            if is_editing:
                                supabase.table('transactions').update(new_data).eq('id', st.session_state.edit_id).execute()
                                st.success("Record Updated!")
                            else:
                                supabase.table('transactions').insert(new_data).execute()
                                st.success("Data Saved!")
                            
                            st.cache_data.clear()
                            # Clean up session state
                            for key in ["show_form", "edit_id"]:
                                if key in st.session_state: del st.session_state[key]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database Error: {e}")
            
            if st.button("❌ Cancel / Close Form"):
                for key in ["show_form", "edit_id"]:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
        else:
            st.warning("Admin access required to add/edit data.")

# --- 6. HISTORY & ALL REPORTS ---
else:
    st.title(menu)
    if not df.empty:
        # Filtering logic
        if menu == "💰 Income History":
            filtered_df = df[df['type'] == 'Income']
        elif menu == "👷 Labor History":
            filtered_df = df[df['type'] == 'Labor']
        elif menu == "🏗️ Material History":
            filtered_df = df[df['type'] == 'Material']
        else:
            filtered_df = df.copy()

        search = st.text_input("🔍 Search in this view...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"📊 **Total for this view: PKR {filtered_df['amount'].sum():,.2f}**")

        # Excel Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", buffer.getvalue(), f"{menu}.xlsx")
        
        # --- EDIT & DELETE SECTION ---
        st.divider()
        st.subheader("🛠️ Manage Records")
        if check_password():
            col_id, col_edit, col_del = st.columns([1, 1, 1])
            target_id = col_id.number_input("Enter ID to Modify", step=1, value=0)
            
            if col_edit.button("✏️ Edit Record"):
                if target_id in filtered_df['id'].values:
                    # Identify the type and set session state
                    row = filtered_df[filtered_df['id'] == target_id].iloc[0]
                    st.session_state.show_form = row['type']
                    st.session_state.edit_id = target_id
                    st.success(f"ID {target_id} loaded! Click 'Dashboard' to edit.")
                else:
                    st.error("ID not found in current view.")

            if col_del.button("🗑️ Delete Record"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.success(f"Record {target_id} Deleted!")
                    st.rerun()
                else:
                    st.error("Please enter a valid ID.")
        else:
            st.info("Unlock 'Admin Access' in sidebar to Edit or Delete records.")
    else:
        st.warning("No data found in Supabase.")
