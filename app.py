import streamlit as st
from supabase import create_client
import pandas as pd
import io
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="PRA Dashboard", layout="wide")

# -- Connect to Supabase --
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data
def load_table(name):
    return pd.DataFrame(supabase.table(name).select("*").execute().data)

approved_users = {"somiaasim26@gmail.com": "123PRA**!"}
special_access_users = {"salmanzafars@gmail.com": "123PRA**!"}

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
            st.error("Invalid credentials.")
    st.stop()

user_email = st.session_state["email"]
allowed = ["Current Stats / KPI"] if user_email in special_access_users else ["Current Stats / KPI", "Data Browser", "Restaurant Profile"]
section = st.sidebar.radio("📂 Navigate", allowed)

# -- Load all --
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "notice_followup_tracking": "Notice Tracking",
    "officer_comments": "Officer Comments",
    "restaurant_images": "Restaurant Images",
    "surveydata_treatmentgroup": "Survey Data",
}
dfs = {k: load_table(k) for k in tables}

# -- Welcome --
if st.session_state["section"] == "Welcome":
    st.title("👋 Welcome")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# -- KPI --
if section == "Current Stats / KPI":
    st.title("📊 KPI Overview")
    treated = dfs["treated_restaurant_data"]
    notices = dfs["notice_followup_tracking"]
    st.metric("Total Restaurants", len(treated))
    st.metric("Returned Notices", notices[notices["delivery_status"].str.lower() == "returned"].shape[0])
    st.dataframe(treated[["id", "restaurant_name", "restaurant_address"]])

# -- Data Browser --
elif section == "Data Browser":
    st.title("📂 Browse")
    pick = st.selectbox("Select Table", list(tables.values()))
    key = [k for k, v in tables.items() if v == pick][0]
    st.dataframe(dfs[key])

# -- Restaurant Profile --
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")
    df = dfs["treated_restaurant_data"]
    df["label"] = df["id"].astype(str) + " - " + df["restaurant_name"]
    selected = st.selectbox("Select Restaurant", df["label"])
    selected_id = selected.split(" - ")[0]
    row = df[df["id"].astype(str) == selected_id].iloc[0]

    st.subheader(row["restaurant_name"])
    st.write(f"**Address:** {row['restaurant_address']}")
    st.write(f"**Status:** {row['compliance_status']}")

    # ✅ Images (safe fallback)
    img_df = dfs["restaurant_images"]
    if "restaurant_id" in img_df.columns:
        imgs = img_df[img_df["restaurant_id"].astype(str) == selected_id]
    else:
        imgs = pd.DataFrame()
    urls = [f"{url}/storage/v1/object/public/restaurant-images/{i['image_path']}" for _, i in imgs.iterrows()]
    if urls:
        idx = st.slider("Image", 0, len(urls)-1, 0)
        st.image(urls[idx])
    else:
        st.info("No images found.")

    # ✅ Survey
    s_df = dfs["surveydata_treatmentgroup"]
    s_row = s_df[s_df["id"].astype(str) == selected_id]
    if not s_row.empty:
        st.subheader("📋 Survey Info")
        st.dataframe(s_row)
    else:
        st.info("No survey data.")

    # ✅ Comments (robust)
    c_df = dfs["officer_comments"]
    if "restaurant_id" in c_df.columns:
        comments = c_df[c_df["restaurant_id"].astype(str) == selected_id]
    else:
        comments = pd.DataFrame()
    st.subheader("🗒 Officer Comments")
    if not comments.empty:
        st.dataframe(comments)
    else:
        st.info("No comments yet.")

    with st.form("Add Comment"):
        comment = st.text_area("New Comment")
        if st.form_submit_button("Submit") and comment:
            supabase.table("officer_comments").insert({
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "comment": comment,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            st.success("Submitted.")
            st.experimental_rerun()

    # ✅ Export PDF
    if st.button("📄 Download PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Restaurant Profile: {row['restaurant_name']}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Address: {row['restaurant_address']}", ln=True)
        pdf.cell(0, 10, f"Status: {row['compliance_status']}", ln=True)
        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        st.download_button("Download PDF", buf, f"{row['restaurant_name']}.pdf")

################