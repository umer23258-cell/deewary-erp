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
    
    # --- QUICK ACTIONS & FORMS ---
    if "show_form" in st.session_state:
        if check_password():
            is_editing = "edit_id" in st.session_state
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            
            if is_editing and not df.empty:
                row = df[df['id'] == st.session_state.edit_id].iloc[0]
                defaults = {
                    "date": datetime.strptime(str(row['date']), '%Y-%m-%d'),
                    "name": str(row['name']), "amount": float(row['amount']), "detail": str(row['detail']),
                    "occ": str(row.get('occupation', "")), "rec": str(row.get('received_by', "")), "meth": str(row.get('pay_method', "Cash"))
                }

            with st.expander(f"{'Edit' if is_editing else 'New'} {st.session_state.show_form}", expanded=True):
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
                            for k in ["show_form", "edit_id"]: 
                                if k in st.session_state: del st.session_state[k]
                            st.success("Successfully Synced!")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
            if st.button("❌ Close Form"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
    else:
        st.subheader("Quick Actions")
        qa1, qa2, qa3 = st.columns(3)
        if qa1.button("➕ Add Income"): st.session_state.show_form = "Income"; st.rerun()
        if qa2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"; st.rerun()
        if qa3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"; st.rerun()

    # --- 7. PROJECT SPOTLIGHT (Slider with all your images) ---
    st.write("##")
    st.divider()
    st.subheader("🏠 Project Gallery: Yousaf Colony")

    project_images = [
        "https://i.ibb.co/6Jbx8yjD/Whats-App-Image-2026-04-30-at-12-11-01-PM.jpg",
        "https://i.ibb.co/6R0yR8Xz/1JK5M0FR.jpg",
        "https://i.ibb.co/ZRgY9wLC/Whats-App-Image-2026-04-30-at-12-25-05-PM.jpg",
        "https://i.ibb.co/35yGYt3H/Whats-App-Image-2026-04-30-at-12-25-04-PM.jpg",
        "https://i.ibb.co/9HTJrtKK/Whats-App-Image-2026-04-30-at-12-24-56-PM.jpg"
    ]

    if 'img_idx' not in st.session_state:
        st.session_state.img_idx = 0

    col_img, col_txt = st.columns([1, 1])

    with col_img:
        st.image(project_images[st.session_state.img_idx], width=350, caption=f"View {st.session_state.img_idx + 1} of {len(project_images)}")
        
        # Slider Buttons
        btn1, btn2 = st.columns(2)
        if btn1.button("⬅️ Previous"):
            st.session_state.img_idx = (st.session_state.img_idx - 1) % len(project_images)
            st.rerun()
        if btn2.button("Next ➡️"):
            st.session_state.img_idx = (st.session_state.img_idx + 1) % len(project_images)
            st.rerun()

    with col_txt:
        st.markdown(f"""
        ### **Yousaf Colony Renovation**
        We are transforming this property into a modern residence.
        
        *   **📍 Location:** Yousaf Colony
        *   **📏 Size:** 5 Marla
        *   **🏗️ Structure:** 2.5 Story House
        *   **🛠️ Work Type:** Complete Interior & Exterior Renovation
        
        ---
        """)
        st.write("🏗️ **Renovation Progress:**")
        st.progress(70)
        st.caption("Current Phase: Paint, Woodwork, and Finishing touches.")

    # --- 8. ABOUT ERP (Full Detail Restored) ---
    st.write("##")
    st.divider()
    info_col1, info_col2 = st.columns([2, 1])
    with info_col1:
        st.subheader("🌟 About Deewary.com ERP")
        st.markdown("""
        **Simple. Powerful. Organized.**  
        This system helps track every rupee spent on construction projects with precision.
        
        *   **✅ Cloud Backup:** Everything is saved on our secure cloud server.
        *   **✅ Data Safety:** Only admins can edit or delete records.
        *   **✅ One-Click Reports:** Download full history in Excel instantly.
        """)
    with info_col2:
        st.subheader("⚙️ System Info")
        st.markdown(f"**Status:** Working Smoothly 🚀\n\n**Version:** 2.0.4\n\n**Dev:** IT Team")

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Precision in Every Project.")

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
        st.download_button("📥 Download Excel Report", buffer.getvalue(), f"{menu}.xlsx")
        
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
                    st.success("Loaded! Go to Dashboard.")
                else: st.error("ID not found.")
            if c_de.button("🗑️ Delete"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.success("Deleted!")
                    st.rerun()
