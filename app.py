import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import io
import streamlit.components.v1 as components

# --- 1. SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Deewary.com ERP", layout="wide", page_icon="🏗️")

# --- MOBILE & COMPACT UI CSS ---
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stButton > button { width: 100%; border-radius: 8px; font-size: 14px !important; }
    }
    .main { background-color: #f8f9fa; }
    .compact-metric {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-top: 4px solid #6f42c1;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS (ORIGINAL) ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = supabase.table('transactions').select("*").order('date', desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        return pd.DataFrame()

def fetch_project_status():
    try:
        res = supabase.table('project_status').select("*").execute()
        if not res.data:
            tasks = ["Mistry Ka Kam", "Plumber", "Electric Work", "Celling", "Paint", "Wood Work", "Finishing"]
            return pd.DataFrame([{"task_name": t, "status": "Pending"} for t in tasks])
        return pd.DataFrame(res.data)
    except:
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
    
    # --- NEW COMPACT CHART SECTION ---
    status_df = fetch_project_status()
    done = len(status_df[status_df['status'] == 'Done'])
    total = len(status_df)
    prog = int((done/total)*100) if total > 0 else 0

    chart_col1, chart_col2 = st.columns([1, 1])
    
    with chart_col1:
        st.markdown(f'<div class="compact-metric"><b>Project Progress</b><h2 style="color:#6f42c1; margin:0;">{prog}%</h2></div>', unsafe_allow_html=True)
        st.progress(prog/100)
    
    with chart_col2:
        if not df.empty:
            inc_w = df[df['type'] == 'Income']['amount'].sum()
            exp_w = df[df['type'].isin(['Labor', 'Material'])]['amount'].sum()
            st.markdown(f'<div class="compact-metric" style="border-color:#28a745;"><b>Net Balance</b><h2 style="color:#28a745; margin:0;">PKR {inc_w - exp_w:,.0f}</h2></div>', unsafe_allow_html=True)

    st.write("##")
    
    # Work Analysis Chart (Small & Professional)
    c_left, c_right = st.columns([1, 1.5])
    with c_left:
        st.caption("Task Distribution")
        pie = f"graph TD\nT(( )) --> D(Done: {done})\nT --> P(Pending: {total-done})\nstyle D fill:#6f42c1,color:#fff\nstyle P fill:#e9ecef"
        components.html(f"<pre class='mermaid'>{pie}</pre><script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>", height=150)

    with c_right:
        st.caption("Live Status")
        for i, row in status_df.head(4).iterrows(): # Show only top 4 for compactness
            st.markdown(f"<small>{'✅' if row['status']=='Done' else '⏳'} {row['task_name']}</small>", unsafe_allow_html=True)
            st.progress(100 if row['status'] == "Done" else 0)

    st.divider()
    
    # --- ORIGINAL METRICS & FORMS (NO CHANGES) ---
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
        if check_password():
            defaults = {"date": datetime.now(), "name": "", "amount": 0.0, "detail": "", "occ": "", "rec": "", "meth": "Cash"}
            if is_editing and not df.empty:
                edit_row = df[df['id'] == st.session_state.edit_id]
                if not edit_row.empty:
                    row = edit_row.iloc[0]
                    defaults = {"date": datetime.strptime(str(row['date']), '%Y-%m-%d'), "name": str(row['name']), "amount": float(row['amount']), "detail": str(row['detail']), "occ": str(row.get('occupation', "")), "rec": str(row.get('received_by', "")), "meth": str(row.get('pay_method', "Cash"))}

            with st.expander(f"{'Edit' if is_editing else 'New'} {st.session_state.show_form} Entry", expanded=True):
                with st.form("entry_form"):
                    d_date = st.date_input("Date", defaults["date"])
                    d_name = st.text_input("Name", defaults["name"])
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
                        if is_editing: supabase.table('transactions').update(payload).eq('id', st.session_state.edit_id).execute()
                        else: supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        for k in ["show_form", "edit_id"]: 
                            if k in st.session_state: del st.session_state[k]
                        st.success("Synced!")
                        st.rerun()
            
            if st.button("❌ Close"):
                for k in ["show_form", "edit_id"]: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    st.divider()
    st.caption(f"© {datetime.now().year} Deewary.com | Project Management")

# --- 6. HISTORY PAGES (ORIGINAL LOGIC WITH EDIT/DELETE) ---
else:
    st.title(menu)
    if not df.empty:
        if "Income" in menu: filtered_df = df[df['type'] == 'Income']
        elif "Labor" in menu: filtered_df = df[df['type'] == 'Labor']
        elif "Material" in menu: filtered_df = df[df['type'] == 'Material']
        else: filtered_df = df.copy()

        search = st.text_input("🔍 Search...")
        if search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"Total: PKR {filtered_df['amount'].sum():,.2f}")

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
                    st.success("ID Loaded! Dashboard par jayen.")
                else: st.error("ID nahi mili.")

            if c_de.button("🗑️ Delete"):
                if target_id != 0:
                    supabase.table('transactions').delete().eq('id', target_id).execute()
                    st.cache_data.clear()
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.warning("Database khali hai.")
