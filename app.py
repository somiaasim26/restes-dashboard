import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
body { background-color: #fcfbf5; }
.block-container { padding: 2rem 3rem; }
.st-emotion-cache-6qob1r, .css-1v0mbdj {
    background-color: #000000 !important;
    color: #ffffff !important;
    padding: 15px;
}
.st-emotion-cache-1d391kg {
    color: #ffffff !important;
}
h1, h2, h3, h4 { color: #1f2937; font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- AUTH ---
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!",
    "hamzaafsar94@gmail.com": "123PRA**!",
    "mcb2270@columbia.edu": "123PRA**!",
    "asad.sherafghan@gmail.com": "123PRA**!",
    "adnanqk@gmail.com": "123PRA**!",
    "anders_jensen@hks.harvard.edu": "123PRA**!",
    "amnanoorfatimalse@gmail.com": "123PRA**!",
    "s.s.shezreenshah@gmail.com": "123PRA**!"
}
special_access_users = {
    "salmanzafars@gmail.com": "123PRA**!",
    "Haali1@live.com": "123PRA**!",
    "Kamranpra@gmail.com": "123PRA**!",
    "Saudatiq90@gmail.com": "123PRA**!"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 PRA Dashboard Login")
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

# --- SUPABASE ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data
def load_table(name):
    return pd.DataFrame(supabase.table(name).select("*").execute().data)

# --- LOAD ---
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "officer_compliance_updates": "Officer Updates",
    "notice_followup_tracking": "Notice Followup Tracking",
    "restaurant_images": "Restaurant Images",
    "surveydata_treatmentgroup": "Survey Data",
    "officer_comments": "Officer Comments"
}
dfs = {k: load_table(k) for k in tables}

# --- WELCOME ---
if st.session_state.get("section") == "Welcome":
    st.title("👋 Welcome to PRA Dashboard")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# --- SIDEBAR ---
user_email = st.session_state["email"]
allowed = ["Current Stats / KPI"]
if user_email not in special_access_users:
    allowed += ["Restaurant Profile", "Data Browser"]

section = st.sidebar.radio("📁 Navigation", allowed)

def get_supabase_image_url(filename):
    return f"{url}/storage/v1/object/public/restaurant-images/{filename}"

# --- KPI ---
if section == "Current Stats / KPI":
    st.title("📊 System KPI")
    treated = dfs["treated_restaurant_data"]
    notices = dfs["notice_followup_tracking"]
    st.metric("Total Restaurants", len(treated))
    if not notices.empty:
        returned = notices[notices["delivery_status"].str.lower() == "returned"].shape[0]
        st.metric("Returned Notices", returned)

# --- PROFILE ---
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")
    df = dfs["treated_restaurant_data"]
    df["label"] = df["id"].astype(str) + " - " + df["restaurant_name"]
    selected = st.selectbox("Select Restaurant", df["label"])
    selected_id = selected.split(" - ")[0]
    row = df[df["id"].astype(str) == selected_id].iloc[0]
    st.write(f"**Name:** {row['restaurant_name']}")
    st.write(f"**Address:** {row['restaurant_address']}")
    st.write(f"**Status:** {row['compliance_status']}")

    # Images
    imgs = dfs["restaurant_images"]
    imgs = imgs[imgs["restaurant_id"].astype(str) == selected_id]
    urls = [get_supabase_image_url(i['image_path']) for _, i in imgs.iterrows()]
    if urls:
        idx = st.slider("Image", 0, len(urls)-1, 0)
        st.image(urls[idx])
    else:
        st.info("No images.")

    # Comments
    comments = dfs.get("officer_comments", pd.DataFrame())
    if "restaurant_id" in comments.columns:
        comments = comments[comments["restaurant_id"].astype(str) == selected_id]
    else:
        comments = pd.DataFrame()
    st.markdown("### Officer Comments")
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
            st.rerun()

# --- BROWSER ---
elif section == "Data Browser":
    st.title("📂 Data Browser")
    options = [
        ("treated_restaurant_data", "Treated Restaurants"),
        ("officer_compliance_updates", "Officer Updates"),
        ("surveydata_treatmentgroup", "Survey Data"),
    ]
    pick = st.selectbox("Select Table", [label for _, label in options])
    key = [k for k, v in options if v == pick][0]
    st.dataframe(dfs[key])
