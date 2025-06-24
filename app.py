import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# ✅ Page Setup + Styling
st.set_page_config(page_title="PRA Dashboard", layout="wide")

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
.metric-box {
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
    transition: all 0.2s ease-in-out;
}
.metric-box:hover {
    transform: translateY(-3px);
    box-shadow: 0px 6px 14px rgba(0,0,0,0.3);
}
.kpi-blue { background-color: #2563eb; }
.kpi-green { background-color: #16a34a; }
.kpi-orange { background-color: #f59e0b; }
.kpi-gray { background-color: #6b7280; }
.form-box {
    background: #f3f4f6;
    padding: 1.5rem;
    border-radius: 0.5rem;
    border-left: 6px solid #2563eb;
    margin-top: 2rem;
}
/* Sidebar radio label text color */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    color: white !important;
    font-weight: 600;
}
/* Selected option styling */
section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {
    color: white !important;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ✅ Auth Setup
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!"
}
special_access_users = {
    "salmanzafars@gmail.com": "123PRA**!"
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

# ✅ Connect to Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data
def load_table(name):
    return pd.DataFrame(supabase.table(name).select("*").execute().data)

# ✅ Load only needed tables
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "officer_compliance_updates": "Officer Updates",
    "surveydata_treatmentgroup": "Survey Data",
    "restaurant_images": "Restaurant Images",
    "officer_comments": "Officer Comments",
    "notice_followup_tracking": "Notice Followup Tracking",
}

dfs = {k: load_table(k) for k in tables}

# ✅ Navigation
user_email = st.session_state["email"]
allowed = ["Current Stats / KPI"]
if user_email not in special_access_users:
    allowed += ["Restaurant Profile", "Data Browser"]

section = st.sidebar.radio("📁 Navigation", allowed)

def get_supabase_image_url(filename):
    return f"{url}/storage/v1/object/public/restaurant-images/{filename}"

# ✅ KPI
if section == "Current Stats / KPI":
    st.title("📊 System KPI")
    treated = dfs["treated_restaurant_data"]
    notices = dfs["notice_followup_tracking"]

    st.metric("Total Restaurants", len(treated))
    if not notices.empty:
        returned = notices[notices["delivery_status"].str.lower() == "returned"].shape[0]
        st.metric("Returned Notices", returned)

# ✅ Restaurant Profile
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")
    treated = dfs["treated_restaurant_data"]
    treated["label"] = treated["id"].astype(str) + " - " + treated["restaurant_name"]
    selected = st.selectbox("Select Restaurant", treated["label"])
    selected_id = selected.split(" - ")[0]

    row = treated[treated["id"].astype(str) == selected_id].iloc[0]
    st.write(f"**Name:** {row['restaurant_name']}")
    st.write(f"**Address:** {row['restaurant_address']}")
    st.write(f"**Status:** {row['compliance_status']}")

    imgs = dfs["restaurant_images"]
    imgs = imgs[imgs["restaurant_id"].astype(str) == selected_id]
    urls = [get_supabase_image_url(i['image_path']) for _, i in imgs.iterrows()]
    if urls:
        idx = st.slider("Image", 0, len(urls)-1, 0)
        st.image(urls[idx])
    else:
        st.info("No images.")

    comments = dfs["officer_comments"]
    comments = comments[comments["restaurant_id"].astype(str) == selected_id]
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

# ✅ Data Browser
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
