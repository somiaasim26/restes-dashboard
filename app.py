
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
#from fpdf import FPDF

# --- Page Setup ---
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

# --- Styling ---
st.markdown("""<style>
    body { background-color: #fcfbf5; }
    .block-container { padding: 2rem 3rem; }
    .st-emotion-cache-6qob1r, .css-1v0mbdj {
        background-color: #000000 !important;
        color: #ffffff !important;
        padding: 15px;
    }
    h1, h2, h3, h4 { color: #1f2937; font-family: 'Segoe UI', sans-serif; }
    .metric-box { padding: 1.5rem; border-radius: 10px; color: white;
        font-size: 1.3rem; font-weight: 600; margin-bottom: 1rem;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.2); transition: all 0.2s ease-in-out; }
    .metric-box:hover { transform: translateY(-3px); box-shadow: 0px 6px 14px rgba(0,0,0,0.3); }
    .form-box { background: #f3f4f6; padding: 1.5rem; border-radius: 0.5rem;
        border-left: 6px solid #2563eb; margin-top: 2rem; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        color: white !important; font-weight: 600; }
    section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {
        color: white !important; font-weight: 700; }
</style>""", unsafe_allow_html=True)

# --- Auth Setup ---
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
    st.title("🔒 PRA Restaurant Enforcement Dashboard Login")
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
            st.error("Invalid credentials or unauthorized email.")
    st.stop()

# --- Supabase Client ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.cache_data
def load_table(table_name: str, columns: list = None, order_by: str = None):
    try:
        query = supabase.table(table_name).select("*" if columns is None else ",".join(columns))
        if order_by:
            query = query.order(order_by)
        response = query.execute()
        data = response.data
        if not data:
            st.warning(f"⚠️ No data returned from Supabase table: {table_name}")
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Supabase error loading '{table_name}': {e}")
        return pd.DataFrame()

# --- Table Mapping ---
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "notice_followup_tracking": "Notice Followup Tracking",
    "surveydata_treatmentgroup": "Survey Data",
    "restaurant_images": "Restaurant Images",
    "officer_comments": "Officer Comments",
    "enforcement_tracking": "Enforcement Tracking",
    "officer_compliance_updates": "Officer Updates",
    "notice_skip_reasons": "Notice Skip Reasons",
    "s1_p1": "Survey 1 - P1", "s1_p2": "Survey 1 - P2", "s1_sec2": "Survey 1 - Sec2", "s1_sec3": "Survey 1 - Sec3",
    "s2_p1": "Survey 2 - P1", "s2_p2": "Survey 2 - P2", "s2_sec2": "Survey 2 - Sec2", "s2_sec3": "Survey 2 - Sec3",
}
dfs = {k: load_table(k) for k in tables}

####
# --- Welcome Page ---
if st.session_state.get("section") == "Welcome":
    st.title("📊 PRA Restaurant Enforcement Dashboard")
    st.markdown("Welcome to the dashboard.")
    st.link_button("📝 Submit Compliance Update", "https://restes-dashboard-form.streamlit.app/")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# --- Sidebar Setup ---
user_email = st.session_state.get("email")
if user_email in special_access_users:
    allowed_sections = ["Current Stats / KPI", "Restaurant Profile"]
else:
    allowed_sections = ["Current Stats / KPI", "Data Browser", "Restaurant Profile", "Enforcement Tracking"]

section = st.sidebar.radio("📁 Navigate", allowed_sections)


# ---------------------- Current Stats / KPI ----------------------
if section == "Current Stats / KPI":
    st.title("📊 PRA System Status")

    treated_df = dfs["treated_restaurant_data"]
    followup_df = dfs["notice_followup_tracking"]

    # Ensure columns are strings
    treated_df["id"] = treated_df["id"].astype(str)
    treated_df["officer_id"] = treated_df["officer_id"].astype(str)
    followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str)
    followup_df["delivery_status"] = followup_df["delivery_status"].fillna("").astype(str)

    # Merge follow-ups with treated restaurants using ID
    merged = pd.merge(
        treated_df,
        followup_df,
        left_on="id",
        right_on="restaurant_id",
        how="left"
    )

    officer_ids = sorted(treated_df["officer_id"].dropna().unique())

    for oid in officer_ids:
        assigned = treated_df[treated_df["officer_id"] == oid]
        total_restaurants = len(assigned)

        officer_followups = merged[merged["officer_id"] == oid]
        returned_notices = officer_followups[
            officer_followups["delivery_status"].str.lower() == "returned"
        ]

        st.markdown("---")
        with st.expander(f"🧑 Officer ID: {oid} — Assigned Restaurants: {total_restaurants}", expanded=False):
            st.markdown(f"""
                - 🧾 **Total Assigned Restaurants**: `{total_restaurants}`  
                - 🔁 **Returned Notices**: `{len(returned_notices)}`
            """)

            st.markdown("### 📬 Returned Notices Details")
            if not returned_notices.empty:
                st.dataframe(returned_notices[[
                    "restaurant_name", "restaurant_address", "delivery_status", "correct_address", "correct_name"
                ]].reset_index(drop=True))
            else:
                st.info("No returned notices for this officer.")

#------------------------------------------------------------------------------------------------------------------

# ✅ Updated Restaurant Profile Section
# Ensure correct location
elif section == "Restaurant Profile":
    st.title("📋 Restaurant Summary Profile")

    df = dfs["treated_restaurant_data"]
    survey_df = dfs["surveydata_treatmentgroup"]
    officer_ids = {
        "Haali1@live.com": "3",
        "Kamranpra@gmail.com": "2",
        "Saudatiq90@gmail.com": "1"
    }
    officer_id = officer_ids.get(user_email)

    if officer_id:
        df = df[df["officer_id"] == officer_id]
        st.info(f"Showing restaurants for Officer {officer_id}")
    else:
        st.success("Showing all restaurants")

    # Filtering
    registered_df = df[df.get("compliance_status") == "Registered"]
    unregistered_df = df[df.get("compliance_status") != "Registered"]
    filers_df = df[df.get("ntn").notna() & (df.get("ntn").astype(str).str.strip() != "")]

    # Compliance Summary Buttons
    st.markdown("### 📊 Monthly Compliance Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"✅ Registered ({len(registered_df)})"):
            st.dataframe(registered_df[["id", "restaurant_name", "restaurant_address"]])
    with col2:
        if st.button(f"❌ Unregistered ({len(unregistered_df)})"):
            st.dataframe(unregistered_df[["id", "restaurant_name", "restaurant_address"]])
    with col3:
        if st.button(f"🧾 Filers ({len(filers_df)})"):
            st.dataframe(filers_df[["id", "restaurant_name", "restaurant_address"]])

    # Dropdown
    rest_df = df[["id", "restaurant_name"]].dropna(subset=["id"]).copy()
    rest_df["id"] = rest_df["id"].astype(str)
    rest_df["label"] = rest_df["id"] + " - " + rest_df["restaurant_name"].fillna("")
    rest_df = rest_df.sort_values(by="id", key=lambda x: x.str.zfill(10))

    selected_label = st.selectbox("🔍 Search by ID or Name", rest_df["label"].tolist())
    selected_id = selected_label.split(" - ")[0].strip()
    selected_name = selected_label.split(" - ")[1].strip()

    st.subheader(f"🏪 {selected_name}")

    # -------------------- Restaurant Images --------------------
    st.markdown("### 🖼️ Restaurant Images")

    import requests
    from PIL import Image
    from io import BytesIO

    def get_supabase_image_url(filename):
        return f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}"

    image_types = {
        "front": "📸 Front Image",
        "menu": "🍽️ Menu Image",
        "receipt": "🧾 Receipt Image"
    }

    for img_type, label in image_types.items():
        filename = f"{selected_id}_{img_type}.jpg"
        url = get_supabase_image_url(filename)

        st.markdown(f"#### {label}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                st.image(image, caption=filename, use_column_width="always")
            else:
                st.warning(f"No {img_type} image found.")
        except Exception as e:
            st.warning(f"Error loading image: {e}")

    # -------------------- Basic Info --------------------
    st.markdown("### 🗃️ Basic Info")
    row = df[df["id"].astype(str) == selected_id]
    if not row.empty:
        row = row.iloc[0]
        info_cols = ["restaurant_name", "restaurant_address", "compliance_status", "officer_id", "ntn", "latitude", "longitude"]
        info_df = pd.DataFrame([[col, row[col]] for col in info_cols if col in row], columns=["Field", "Value"])
        st.table(info_df)

    # -------------------- Survey Info --------------------
    st.markdown("### 🏢 Survey Information")
    survey_row = survey_df[survey_df["id"].astype(str) == selected_id]
    if not survey_row.empty:
        row = survey_row.iloc[0]
        label_map = {
            "ntn": "🔘 NTN", "pntn": "🔘 PNTN", "strn": "🔘 STRN", "restaurant_type": "🍱 Restaurant Type",
            "cuisine": "🧑‍🍳 Cuisine", "number_of_customers": "🧑‍🤝‍🧑 Customers", "number_of_chairs": "🪑 Chairs",
            "number_of_floors": "🏢 Floors", "number_of_tables": "🛎️ Tables", "seating_arrangement": "🧍‍🪑 Seating Arrangement",
            "air_conditioner": "❄ Air Conditioning", "credit_debit_card_acceptance": "💳 Card Acceptance",
            "food_court": "🏬 In Food Court", "gst": "💸 GST Amount", "pre_tax_price": "💰 Pre-Tax Price",
            "post_tax_price": "💰 Post-Tax Price", "price_paid": "💸 Price Paid"
        }

        col1, col2 = st.columns(2)
        for i, col in enumerate(row.index):
            if pd.notna(row[col]) and col != "id":
                label = label_map.get(col.lower(), col.replace("_", " ").title())
                value = row[col]
                (col1 if i % 2 == 0 else col2).markdown(f"""
                    <div style='
                        background-color: #f1f5f9;
                        padding: 8px 12px;
                        border-radius: 6px;
                        margin-bottom: 8px;
                        border-left: 4px solid #2563eb;
                    '>
                        <strong>{label}:</strong> {value}
                    </div>
                """, unsafe_allow_html=True)

    # -------------------- Skip Reason Section --------------------
    st.markdown("### 📝 Reason for Not Sending Notice")

    try:
        skip_reason_df = pd.DataFrame(supabase.table("notice_skip_reasons").select("*").execute().data)
    except Exception as e:
        skip_reason_df = pd.DataFrame()
        st.warning(f"⚠️ Unable to load previous skip reasons: {e}")

    already_submitted = False
    if not skip_reason_df.empty and "restaurant_id" in skip_reason_df.columns:
        skip_reason_df["restaurant_id"] = skip_reason_df["restaurant_id"].astype(str)
        submitted = skip_reason_df[
            (skip_reason_df["restaurant_id"] == selected_id) &
            (skip_reason_df["officer_email"] == user_email)
        ]
        if not submitted.empty:
            st.success(f"✅ Already submitted: {submitted.iloc[0]['reason']}")
            already_submitted = True

    if not already_submitted:
        reason = st.radio("Select reason:", [
            "Not Liable – Turnover < PKR 6M",
            "Not a Restaurant – Retail or Non-Food",
            "Already Registered with PRA",
            "Duplicate Entry / Already Covered",
            "Closed / Inactive Business",
            "Outside PRA Jurisdiction"
        ], key=f"reason_radio_{selected_id}_{user_email}")

        if st.button("✅ Submit Reason"):
            try:
                from datetime import datetime
                supabase.table("notice_skip_reasons").insert({
                    "restaurant_id": selected_id,
                    "officer_email": user_email,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()
                st.success("Reason submitted.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Submission failed: {e}")

    # -------------------- CSV Export --------------------
    st.markdown("### 📥 Export Restaurant Data as CSV")
    csv_data = df.merge(survey_df, on="id", how="left") if not survey_df.empty else df

    if officer_id:
        if st.button("📤 Download Your Assigned Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, f"restaurants_officer_{officer_id}.csv", "text/csv")
    else:
        if st.button("📤 Download All Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "all_restaurants.csv", "text/csv")
