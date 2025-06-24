import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
from fpdf import FPDF

# ---------------------------
# ✅ CONFIG
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

# ✅ STYLE (exact as yours)
st.markdown("""
<style>
body { background-color: #fcfbf5; }
.block-container { padding: 2rem 3rem; }
h1, h2, h3, h4 { color: #1f2937; font-family: 'Segoe UI', sans-serif; }
.metric-box {
    padding: 1.5rem; border-radius: 10px; color: white;
    font-size: 1.3rem; font-weight: 600; margin-bottom: 1rem;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
    transition: all 0.2s ease-in-out;
}
.metric-box:hover { transform: translateY(-3px); box-shadow: 0px 6px 14px rgba(0,0,0,0.3); }
.kpi-blue { background-color: #2563eb; }
.kpi-orange { background-color: #f59e0b; }
section[data-testid="stSidebar"] label { color: white !important; font-weight: 600; }
section[data-testid="stSidebar"] input:checked + div { color: white !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# ✅ AUTH
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!",
    "hamzaafsar94@gmail.com": "123PRA**!"
}
special_users = {
    "salmanzafars@gmail.com": "123PRA**!"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 PRA Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in approved_users and approved_users[email] == password:
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            st.session_state["section"] = "Welcome"
            st.rerun()
        elif email in special_users and special_users[email] == password:
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            st.session_state["section"] = "Current Stats / KPI"
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# ---------------------------
# ✅ SUPABASE CLIENT
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data(ttl=600)
def load_table(table): return pd.DataFrame(supabase.table(table).select("*").execute().data)

treated = load_table("treated_restaurant_data")
tracking = load_table("notice_followup_tracking")
survey = load_table("surveydata_treatmentgroup")
images = load_table("restaurant_images")
comments = load_table("officer_comments")

# ---------------------------
# ✅ SIDEBAR
user_email = st.session_state["email"]
if user_email in special_users:
    allowed = ["Current Stats / KPI", "Restaurant Profile"]
else:
    allowed = ["Current Stats / KPI", "Restaurant Profile"]

section = st.sidebar.radio("📁 Navigation", allowed)

# ---------------------------
# ✅ Welcome Page
if st.session_state.get("section") == "Welcome":
    st.title("Welcome to PRA Dashboard")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# ---------------------------
# ✅ KPI SECTION
if section == "Current Stats / KPI":
    st.title("📊 System KPI")

    st.markdown(f"<div class='metric-box kpi-blue'>📘 Total Restaurants: {len(treated)}</div>", unsafe_allow_html=True)

    if not tracking.empty:
        returned = tracking[tracking["delivery_status"].str.lower() == "returned"].shape[0]
        st.markdown(f"<div class='metric-box kpi-orange'>📦 Returned Notices: {returned}</div>", unsafe_allow_html=True)

    # Example: show per officer breakdown
    if "officer_id" in treated.columns:
        ids = sorted(treated["officer_id"].dropna().unique())
        for oid in ids:
            sub = treated[treated["officer_id"] == oid]
            with st.expander(f"👮 Officer ID {oid} — {len(sub)} Restaurants"):
                st.dataframe(sub[["id", "restaurant_name", "restaurant_address"]])

# ---------------------------
# ✅ Restaurant Profile
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")

    treated["label"] = treated["id"].astype(str) + " - " + treated["restaurant_name"].fillna("")
    selected = st.selectbox("Select Restaurant", sorted(treated["label"]))
    selected_id = selected.split(" - ")[0]
    selected_row = treated[treated["id"].astype(str) == selected_id].iloc[0]

    st.write(f"**Name:** {selected_row['restaurant_name']}")
    st.write(f"**Address:** {selected_row['restaurant_address']}")
    st.write(f"**Status:** {selected_row['compliance_status']}")

    # ✅ IMAGES
    imgs = images[images["restaurant_id"].astype(str) == selected_id]
    urls = [f"{url}/storage/v1/object/public/restaurant-images/{i['image_path']}" for _, i in imgs.iterrows()]
    if urls:
        idx = st.slider("Image", 0, len(urls)-1, 0)
        st.image(urls[idx])
    else:
        st.info("No images.")

    # ✅ COMMENTS
    these = comments[comments["restaurant_id"].astype(str) == selected_id]
    st.markdown("### 🗂 Comments")
    if not these.empty:
        st.dataframe(these[["officer_email", "comment", "timestamp"]])
    else:
        st.info("No comments yet.")

    # ✅ ADD COMMENT
    with st.form("add_comment"):
        txt = st.text_area("Add comment")
        if st.form_submit_button("Submit") and txt:
            supabase.table("officer_comments").insert({
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "comment": txt,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            st.success("Comment submitted.")
            st.rerun()

    # ✅ EXPORT PDF
    st.markdown("### 📥 Export Profile")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Restaurant: {selected_row['restaurant_name']}", ln=True)
    pdf.set_font("Arial", size=12)
    for col in ["restaurant_name", "restaurant_address", "compliance_status"]:
        pdf.multi_cell(0, 10, f"{col}: {selected_row[col]}")
    b = io.BytesIO()
    b.write(pdf.output(dest="S").encode("latin1"))
    st.download_button("⬇️ Download PDF", data=b.getvalue(), file_name=f"{selected_row['restaurant_name']}.pdf", mime="application/pdf")
