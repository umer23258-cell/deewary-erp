
import io
import urllib.parse
import html
import base64
import os
import streamlit.components.v1 as components
import requests  # Image fetch karne ke liye
# PDF ke liye libraries

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="Deewaryn.com ERP", layout="wide", page_icon="🏗️")

def get_logo_data_uri():
    """Embed the company logo so it travels with the deployed application."""
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "deewaryn-logo.jpg")
    try:
        with open(logo_path, "rb") as logo_file:
            encoded = base64.b64encode(logo_file.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except OSError:
        return ""

# --- APPLICATION SHELL ---
st.markdown("""


# --- 8. SIDEBAR DESIGN (Custom Branded Luxury Styling) ---
with st.sidebar:
    st.markdown("<h2 style='color:#FF4B4B; font-weight:800; margin-bottom:0; font-size:24px; letter-spacing:-0.5px;'>DEEWARYN</h2>", unsafe_allow_html=True)
with st.sidebar:
    st.image("assets/deewaryn-logo.jpg", use_container_width=True)
    st.write("")
    st.markdown("<h2 style='color:#FF4B4B; font-weight:800; margin-bottom:0; font-size:24px; letter-spacing:-0.5px;'>DEEWARYN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px; color:#64748b; font-weight:500; margin-top:2px; text-transform:uppercase; letter-spacing:1px;'>Site Infrastructure ERP</p>", unsafe_allow_html=True)
    st.divider()
    
    total_tasks = len(status_df)
    progress = round(completed_tasks * 100 / total_tasks) if total_tasks else 0
    safe_project = html.escape(str(current_project))
    logo_data_uri = get_logo_data_uri()

    if df.empty:
        total_inc = total_exp = pending_total = 0.0
    balance = total_inc - total_exp
    balance_note = 'Positive cash position' if balance >= 0 else 'Review expense coverage'

    logo_html = f'<img src="{logo_data_uri}" alt="DEEWARYN.COM logo">' if logo_data_uri else 'D'
    st.markdown(f'''<div class="dash"><div class="dash-top"><div class="dash-brand"><div class="dash-logo">{logo_html}</div><div><div class="dash-brand-name">DEEWARYN.COM</div><div class="dash-brand-tag">Construction & Project Management</div></div></div><div><span class="dash-live"><i class="dash-dot"></i> Live project data</span><span class="dash-date">&nbsp;&nbsp;{datetime.now().strftime('%d %b %Y')}</span></div></div>
    st.markdown(f'''<div class="dash"><div class="dash-top"><div class="dash-brand"><div><div class="dash-brand-name">DEEWARYN.COM</div><div class="dash-brand-tag">Construction & Project Management</div></div></div><div><span class="dash-live"><i class="dash-dot"></i> Live project data</span><span class="dash-date">&nbsp;&nbsp;{datetime.now().strftime('%d %b %Y')}</span></div></div>
        <section class="dash-hero"><span class="dash-hero-label">Active construction site</span><h2>{safe_project}</h2><p>Monitor financial health, construction delivery and every site transaction from one executive workspace.</p><div style="display:flex;gap:10px;margin-top:23px"><div class="dash-kpi"><div class="dash-kpi-label">Site completion</div><div class="dash-kpi-value">{progress}%</div></div><div class="dash-kpi"><div class="dash-kpi-label">Checklist items</div><div class="dash-kpi-value">{completed_tasks} / {total_tasks}</div></div><div class="dash-kpi"><div class="dash-kpi-label">Transactions</div><div class="dash-kpi-value">{transaction_count}</div></div></div></section></div>''', unsafe_allow_html=True)

    metrics = [
