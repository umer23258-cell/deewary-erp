# --- QUICK ACTIONS (Updated with Occupation, Received By, and Pay Method) ---
is_editing = "edit_id" in st.session_state
if not is_editing:
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ Add Income"): st.session_state.show_form = "Income"
    if c2.button("👷 Pay Labor"): st.session_state.show_form = "Labor"
    if c3.button("🏗️ Buy Material"): st.session_state.show_form = "Material"

if "show_form" in st.session_state:
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
                    # Sirf Income aur Labor ke liye extra fields
                    if form_type in ["Income", "Labor"]:
                        d_meth = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "EasyPaisa/JazzCash"])
                    else:
                        d_meth = "Cash" # Default for Material

                # Extra fields for Labor & Income
                d_occ = ""
                d_rec = ""
                if form_type in ["Income", "Labor"]:
                    c1, c2 = st.columns(2)
                    with c1:
                        d_occ = st.text_input("Occupation (Haisiyat/Pisha)")
                    with c2:
                        d_rec = st.text_input("Received By (Kis ne wasool kiya)")

                d_det = st.text_area("Details (Remarks)")

                if st.form_submit_button("Save to Cloud"):
                    # Payload mein naye fields add kar diye gaye hain
                    payload = {
                        "date": str(d_date), 
                        "type": form_type, 
                        "name": d_name, 
                        "amount": d_amt, 
                        "detail": d_det,
                        "occupation": d_occ,      # Naya Column
                        "received_by": d_rec,     # Naya Column
                        "payment_method": d_meth   # Naya Column
                    }
                    try:
                        supabase.table('transactions').insert(payload).execute()
                        st.cache_data.clear()
                        st.success(f"{form_type} record saved successfully!")
                        st.session_state.pop("show_form")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving data: {e}")
            
            if st.button("❌ Close Form"):
                st.session_state.pop("show_form")
                st.rerun()
