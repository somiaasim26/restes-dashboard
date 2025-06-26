
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
def load_table(table_name):
    return pd.DataFrame(supabase.table(table_name).select("*").execute().data)

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
    user_email = st.session_state.get("email", "")

    # Officer Mapping
    officer_ids = {
        "Haali1@live.com": "3",
        "Kamranpra@gmail.com": "2",
        "Saudatiq90@gmail.com": "1"
    }

    officer_id = officer_ids.get(user_email)

    # Ensure string matching
    treated_df["officer_id"] = treated_df["officer_id"].astype(str)
    treated_df["id"] = treated_df["id"].astype(str)
    followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str)

    # PI/Admin Full View
    st.markdown("## 📋 Notice Follow-up & Latest Updates")

    for email, oid in officer_ids.items():
        assigned = treated_df[treated_df["officer_id"] == oid]
        assigned_ids = assigned["id"].tolist()
        followups = followup_df[followup_df["restaurant_id"].isin(assigned_ids)]

        returned_count = followups["delivery_status"].str.lower().eq("returned").sum()
        delivered_count = followups["delivery_status"].str.lower().eq("delivered").sum()

        to_resend = followups[
            (followups["delivery_status"].str.lower() == "returned") &
            (
                followups["correct_address"].fillna("").str.strip() != "" |
                followups["correct_name"].fillna("").str.strip() != ""
            )
        ]

        with st.expander(f"👮 Officer ID: {email} — Assigned Restaurants: {len(assigned)}"):
            st.markdown(f"<div style='padding-left:1rem'>📭 <b>Returned Notices:</b> <span style='color:#b91c1c'>{returned_count}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-left:1rem'>✅ <b>Delivered Notices:</b> <span style='color:#16a34a'>{delivered_count}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-left:1rem'>📦 <b>To Resend:</b> <span style='color:#d97706'>{len(to_resend)}</span></div>", unsafe_allow_html=True)

            preview_df = assigned[["id", "restaurant_name", "restaurant_address"]].head(10)
            st.dataframe(preview_df)

            if st.button(f"🔍 Load All Restaurants — Officer {oid}", key=f"load_all_{oid}"):
                st.dataframe(assigned[["id", "restaurant_name", "restaurant_address"]])

#------------------------------------------------------------------------------------------------------------------

# ✅ Updated Restaurant Profile Section (Supabase-based, optimized)

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

    # Apply filtering only for officers
    if officer_id:
        df = df[df["officer_id"] == officer_id]
        st.info(f"Showing restaurants for Officer {officer_id}")
    else:
        st.success("Showing all restaurants")

    # Filtering
    registered_df = df[df.get("compliance_status") == "Registered"]
    unregistered_df = df[df.get("compliance_status") != "Registered"]
    filers_df = df[df.get("ntn").notna() & (df.get("ntn").astype(str).str.strip() != "")]

    # Quick Buttons View
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

    # Dropdown selector
    rest_df = df[["id", "restaurant_name"]].dropna(subset=["id"]).copy()
    rest_df['id'] = rest_df['id'].astype(str)
    rest_df['label'] = rest_df['id'] + " - " + rest_df['restaurant_name'].fillna("")
    rest_df = rest_df.sort_values(by="id", key=lambda x: x.str.zfill(10))

    selected_label = st.selectbox("🔍 Search by ID or Name", rest_df['label'].tolist())
    selected_id = selected_label.split(" - ")[0]
    selected_name = selected_label.split(" - ")[1]

    st.subheader(f"🏪 {selected_name}")

    # Images
    st.markdown("### 🖼️ Restaurant Images")
    imgs = dfs["restaurant_images"]
    imgs = imgs[imgs["restaurant_id"].astype(str) == selected_id]
    image_type_map = {"front": "Front Image", "menu": "Menu Image", "receipt": "Receipt Image"}

    def get_supabase_url(filename):
        return f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}"

    def clean_filename(path):
        return os.path.basename(str(path)).strip('"').strip("'")

    if not imgs.empty:
        img_cols = st.columns(3)
        for i, img_type in enumerate(["front", "menu", "receipt"]):
            with img_cols[i]:
                subset = imgs[imgs["image_type"] == img_type]
                if not subset.empty:
                    st.image(get_supabase_url(clean_filename(subset.iloc[0]["image_path"])), caption=image_type_map[img_type])
                else:
                    st.info(f"No {image_type_map[img_type]} found.")
    else:
        st.info("No images available for this restaurant.")

    # Basic Info
    st.markdown("### 🗃️ Basic Info")
    row = df[df["id"].astype(str) == selected_id]
    if not row.empty:
        row = row.iloc[0]
        info_cols = ["restaurant_name", "restaurant_address", "compliance_status", "officer_id", "ntn", "latitude", "longitude"]
        info_df = pd.DataFrame([[col, row[col]] for col in info_cols if col in row], columns=["Field", "Value"])
        st.table(info_df)
    else:
        st.warning("Restaurant not found.")

    # Survey Info
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


        # --- Officer Comments Section ---
    st.markdown("### 📝 Reason for Not Sending Notice")

    # Safely pull skip reasons from Supabase
    try:
        skip_reason_df = pd.DataFrame(
            supabase.table("notice_skip_reasons").select("*").execute().data
        )
    except Exception as e:
        skip_reason_df = pd.DataFrame()
        st.warning(f"⚠️ Unable to load previous skip reasons: {e}")

    # Filter based on selected restaurant + logged-in officer
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

    # Display form if not already submitted
    if not already_submitted:
        reason = st.radio("Select reason:", [
            "Not Liable – Turnover < PKR 6M",
            "Not a Restaurant – Retail or Non-Food",
            "Already Registered with PRA",
            "Duplicate Entry / Already Covered",
            "Closed / Inactive Business",
            "Outside PRA Jurisdiction"
        ])

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


    # CSV Export
    st.markdown("### 📥 Export Restaurant Data as CSV")

    # Join treated + survey for full export
    csv_data = df.merge(survey_df, on="id", how="left") if not survey_df.empty else df

    if officer_id:  # Officer login - only his assigned restaurants
        if st.button("📤 Download Your Assigned Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, f"restaurants_officer_{officer_id}.csv", "text/csv")
    else:  # Full access user
        if st.button("📤 Download All Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "all_restaurants.csv", "text/csv")
