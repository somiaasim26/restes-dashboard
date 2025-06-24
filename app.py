import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
from fpdf import FPDF

# ---------------------------
# ✅ CONFIG
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

# ✅ STYLE (your exact CSS)
st.markdown("""<style>/* your CSS here exactly */</style>""", unsafe_allow_html=True)

# ---------------------------
# ✅ AUTH
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!",
    "hamzaafsar94@gmail.com": "123PRA**!",
    "mcb2270@columbia.edu": "123PRA**!"
}
special_access_users = {
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
        elif email in special_access_users and special_access_users[email] == password:
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            st.session_state["section"] = "Current Stats / KPI"
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# ---------------------------
# ✅ SUPABASE CONNECTION
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data(ttl=600)
def load_table(table):
    return pd.DataFrame(supabase.table(table).select("*").execute().data)

treated_df = load_table("treated_restaurant_data")
tracking_df = load_table("notice_followup_tracking")
survey_df = load_table("surveydata_treatmentgroup")
images_df = load_table("restaurant_images")
comments_df = load_table("officer_comments")
returns_df = load_table("restaurant_return_data")

# ---------------------------
# ✅ SIDEBAR
user_email = st.session_state["email"]
allowed = ["Current Stats / KPI", "Restaurant Profile"] if user_email in special_access_users else [
    "Current Stats / KPI", "Restaurant Profile", "Return Summary"
]
section = st.sidebar.radio("Navigation", allowed)

# ---------------------------
# ✅ Welcome Page
if st.session_state.get("section") == "Welcome":
    st.title("Welcome to PRA Dashboard")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# ---------------------------
# ✅ KPI
if section == "Current Stats / KPI":
    st.title("📊 PRA System KPI")
    st.markdown(f"<div class='metric-box kpi-blue'>📘 Total Restaurants: {len(treated_df)}</div>", unsafe_allow_html=True)

    if not tracking_df.empty:
        returned = tracking_df[tracking_df["delivery_status"].str.lower() == "returned"].shape[0]
        st.markdown(f"<div class='metric-box kpi-orange'>📦 Returned Notices: {returned}</div>", unsafe_allow_html=True)

    if "officer_id" in treated_df.columns:
        ids = sorted(treated_df["officer_id"].dropna().unique())
        for oid in ids:
            sub = treated_df[treated_df["officer_id"] == oid]
            with st.expander(f"👮 Officer ID {oid} — {len(sub)} Restaurants"):
                st.dataframe(sub[["id", "restaurant_name", "restaurant_address"]])

# ---------------------------
# ✅ Restaurant Profile
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")

    treated_df["label"] = treated_df["id"].astype(str) + " - " + treated_df["restaurant_name"]
    selected = st.selectbox("Select Restaurant", sorted(treated_df["label"]))
    selected_id = selected.split(" - ")[0]
    selected_row = treated_df[treated_df["id"].astype(str) == selected_id].iloc[0]

    st.write(f"**Name:** {selected_row['restaurant_name']}")
    st.write(f"**Address:** {selected_row['restaurant_address']}")
    st.write(f"**Status:** {selected_row['compliance_status']}")

    # Images
    img_data = images_df[images_df["restaurant_id"].astype(str) == selected_id]
    img_urls = [
        f"{url}/storage/v1/object/public/restaurant-images/{row['image_path']}"
        for _, row in img_data.iterrows()
    ]
    if img_urls:
        idx = st.slider("Image", 0, len(img_urls)-1, 0)
        st.image(img_urls[idx])
    else:
        st.info("No images found.")

    # Comments
    sub_comments = comments_df[comments_df["restaurant_id"].astype(str) == selected_id]
    st.markdown("### 🗂 Comments")
    if not sub_comments.empty:
        st.dataframe(sub_comments[["officer_email", "comment", "timestamp"]])
    else:
        st.info("No comments yet.")

    # Add comment
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

    # Export PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Restaurant: {selected_row['restaurant_name']}", ln=True)
    pdf.cell(200, 10, f"Address: {selected_row['restaurant_address']}", ln=True)
    pdf.cell(200, 10, f"Status: {selected_row['compliance_status']}", ln=True)
    b = io.BytesIO()
    b.write(pdf.output(dest="S").encode("latin1"))
    st.download_button("⬇️ Download PDF", data=b.getvalue(), file_name=f"{selected_row['restaurant_name']}.pdf", mime="application/pdf")

# ---------------------------
# ✅ Return Summary
elif section == "Return Summary":
    st.title("📊 Return Summary")

    treated_df["NTN"] = treated_df["ntn"].astype(str)
    returns_df.columns = returns_df.columns.str.upper().str.replace(" ", "_")

    col1, col2 = st.columns(2)
    all_years = sorted(returns_df["TAX_PERIOD_YEAR"].dropna().unique(), reverse=True)
    all_months = sorted(returns_df["TAX_PERIOD_MONTH"].dropna().unique(), reverse=True)
    selected_year = col1.selectbox("Tax Year", all_years)
    selected_month = col2.selectbox("Tax Month", all_months)

    month_df = returns_df[
        (returns_df["TAX_PERIOD_YEAR"] == selected_year) &
        (returns_df["TAX_PERIOD_MONTH"] == selected_month)
    ]
    st.dataframe(month_df)

    if not month_df.empty:
        ntns = sorted(month_df["NTN"].dropna().unique())
        selected_ntn = st.selectbox("Select NTN", ntns)
        ntn_data = month_df[month_df["NTN"] == selected_ntn]

        matched = treated_df[treated_df["NTN"] == selected_ntn]
        if not matched.empty:
            st.dataframe(matched.T)

        latest = returns_df[returns_df["NTN"] == selected_ntn].sort_values(
            ["TAX_PERIOD_YEAR", "TAX_PERIOD_MONTH"], ascending=False
        ).head(1)
        compliant = (latest["TAX_PERIOD_YEAR"].values[0] == selected_year) and (latest["TAX_PERIOD_MONTH"].values[0] == selected_month)
        st.success(f"Status: {'Filer' if compliant else 'Late'}")

        st.dataframe(ntn_data)

