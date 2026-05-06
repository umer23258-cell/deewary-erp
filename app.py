import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# --- 1. SUPABASE SETUP ---
# (Yahan aapka purana secrets wala code rahega)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ... (Baqi Page Config aur Functions purane hi rahenge) ...

# --- 5. DASHBOARD PAGE ---
if menu == "📊 Dashboard":
    # ... (Header aur Metrics wala purana code) ...

    st.divider()
    
    # --- QUICK ACTIONS (Yahan error fix kiya gaya hai) ---
    if "show_form" not in st.session_state:
        st.session_state.show_form = None

    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"
    
    if st.session_state.show_form:
        form_type = st.session_state.show_form
        if is_auth:
            with st.expander(f"New {form_type} Entry", expanded=True):
                with st.form("entry_form"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        d_date = st.date_input("Date", datetime.now())
                        d_name = st.text_input("Name / Description")
                    with col_b:
                        d_amt = st.number_input("Amount", min_value=0.0)
                        # Payment Method Field
                        d_meth = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "EasyPaisa"])

                    # Occupation aur Received By (Sirf Income aur Labor ke liye)
                    d_occ = ""
                    d_rec = ""
                    if form_type in ["Income", "Labor"]:
                        c1, c2 = st.columns(2)
                        with c1:
                            d_occ = st.text_input("Occupation")
                        with c2:
                            d_rec = st.text_input("Received By")

                    d_det = st.text_area("Details")

                    if st.form_submit_button("Save to Cloud"):
                        payload = {
                            "date": str(d_date), 
                            "type": form_type, 
                            "name": d_name, 
                            "amount": d_amt, 
                            "detail": d_det,
                            "occupation": d_occ,      # New
                            "received_by": d_rec,     # New
                            "payment_method": d_meth   # New
                        }
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.session_state.show_form = None
                        st.rerun()
            
            if st.button("❌ Close Form"):
                st.session_state.show_form = None
                st.rerun()
