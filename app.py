# PRA Dashboard (Supabase ONLY, Clean Full Version)

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import io
from fpdf import FPDF

# ------------------------------------
# CONFIG
st.set_page_config(page_title="PRA Dashboard", layout="wide")

# --- Connect to Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ------------------------------------
# Auth
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!",
    "hamzaafsar94@gmail.com": "123PRA**!"
}
special_access_users = {
    "salmanzafars@gmail.com": "123PRA**!"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 PRA Dashboard Login")
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
            st.error("❌ Invalid credentials.")
    st.stop()

# ------------------------------------
# Cache for Supabase tables
@st.cache_data
def load_table(name):
    return pd.DataFrame(supabase.table(name).select("*").execute().data)

tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "notice_followup_tracking": "Notice Tracking",
    "officer_comments": "Officer Comments",
    "restaurant_images": "Restaurant Images",
    "surveydata_treatmentgroup": "Survey Data"
}

dfs = {k: load_table(k) for k in tables}

# ------------------------------------
# Sidebar Navigation
user_email = st.session_state["email"]
allowed = ["Current Stats / KPI"]
if user_email not in special_access_users:
    allowed += ["Restaurant Profile"]
section = st.sidebar.radio("📁 Navigate", allowed)

# ------------------------------------
# KPI SECTION
if section == "Current Stats / KPI":
    st.title("📊 System KPI Overview")

    treated = dfs["treated_restaurant_data"]
    notices = dfs["notice_followup_tracking"]

    st.metric("Total Restaurants", len(treated))
    if not notices.empty and "delivery_status" in notices:
        returned = notices[notices["delivery_status"].str.lower() == "returned"].shape[0]
        st.metric("Returned Notices", returned)

    st.dataframe(
        treated[["id", "restaurant_name", "restaurant_address"]]
    )

# ------------------------------------
# RESTAURANT PROFILE SECTION
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")

    treated = dfs["treated_restaurant_data"]
    treated["label"] = treated["id"].astype(str) + " - " + treated["restaurant_name"]
    selected = st.selectbox("Select Restaurant", treated["label"])
    selected_id = selected.split(" - ")[0]

    row = treated[treated["id"].astype(str) == selected_id].iloc[0]
    st.subheader(row["restaurant_name"])
    st.write(f"**Address:** {row['restaurant_address']}")
    st.write(f"**Compliance Status:** {row['compliance_status']}")

    # === IMAGES ===
    st.markdown("### 📸 Images")
    imgs = dfs["restaurant_images"]
    imgs = imgs[imgs["restaurant_id"].astype(str) == selected_id]
    urls = [
        f"{url}/storage/v1/object/public/restaurant-images/{i['image_path']}"
        for _, i in imgs.iterrows()
    ]
    if urls:
        idx = st.slider("Image Index", 0, len(urls)-1, 0)
        st.image(urls[idx])
    else:
        st.info("No images found for this restaurant.")

    # === SURVEY INFO ===
    st.markdown("### 📋 Survey Data")
    survey = dfs["surveydata_treatmentgroup"]
    s_row = survey[survey["id"].astype(str) == selected_id]
    if not s_row.empty:
        st.dataframe(s_row)
    else:
        st.info("No survey data available.")

    # === OFFICER COMMENTS ===
    st.markdown("### 📝 Officer Comments")
    comments = dfs["officer_comments"]
    comments = comments[comments["restaurant_id"].astype(str) == selected_id] if "restaurant_id" in comments.columns else pd.DataFrame()
    if not comments.empty:
        st.dataframe(comments[["officer_email", "comment", "timestamp"]])
    else:
        st.info("No comments yet.")

    with st.form("Add Comment"):
        comment = st.text_area("Add a comment")
        if st.form_submit_button("Submit") and comment.strip():
            supabase.table("officer_comments").insert({
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "comment": comment.strip(),
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            st.success("✅ Comment added. Please refresh to see it!")

    # === EXPORT PDF ===
    if st.button("📄 Download Profile as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Restaurant Profile: {row['restaurant_name']}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Address: {row['restaurant_address']}", ln=True)
        pdf.cell(0, 10, f"Compliance Status: {row['compliance_status']}", ln=True)
        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        st.download_button("Download PDF", buf, f"{row['restaurant_name']}_profile.pdf")

# ------------------------------------
# End.
