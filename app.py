
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


# --- Utility: Clean & Standardize IDs ---
def clean_ids(df, id_columns):
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df = df[df[col] != ""]
    return df

# --- Current Stats / KPI Section ---
if section == "Current Stats / KPI":
    is_special_user = user_email in special_access_users

    if is_special_user:
        st.title("📊 PRA System Status")

        # Load and clean Supabase data
        treated_df = clean_ids(load_table("treated_restaurant_data"), ["id", "officer_id"])
        tracking_df = clean_ids(load_table("enforcement_tracking"), ["restaurant_id"])

        total_restaurants = len(treated_df)

        st.markdown("""
            <style>
            .short-metric-box {
                padding: 1rem;
                border-radius: 10px;
                color: white;
                font-size: 1.2rem;
                font-weight: 600;
                background-color: #2563eb;
                box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
                text-align: center;
                width: fit-content;
                min-width: 200px;
                margin-bottom: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="short-metric-box">📘 Total Restaurants<br>{total_restaurants}</div>', unsafe_allow_html=True)

        # Clean and standardize officer IDs
        officer_ids = treated_df["officer_id"].dropna().unique()
        officer_ids = sorted(set([
            str(int(float(o))) if o.replace('.', '', 1).isdigit() else o
            for o in officer_ids
        ]))

        for oid in officer_ids:
            officer_df = treated_df[treated_df["officer_id"] == oid]

            with st.expander(f"👮 Officer ID: {oid} — Assigned Restaurants: {len(officer_df)}"):
                st.dataframe(officer_df[["id", "restaurant_name", "restaurant_address"]])

            if not tracking_df.empty and "restaurant_id" in tracking_df.columns:
                try:
                    tracking_data = tracking_df.merge(
                        treated_df[["id", "officer_id"]],
                        left_on="restaurant_id", right_on="id", how="inner"
                    )
                    officer_tracking = tracking_data[tracking_data["officer_id"] == oid]

                    with st.expander(f"📦 Enforcement Tracking — Officer {oid}"):
                        if not officer_tracking.empty:
                            st.dataframe(officer_tracking[[
                                "restaurant_id", "courier_status", "notice_status", "filing_status", "updated_at"
                            ]])
                        else:
                            st.info("No enforcement tracking records found.")
                except Exception as e:
                    st.warning(f"⚠️ Error loading tracking data: {e}")

    # --- Notice Follow-up Summary ---
    st.markdown("## 📋 Notice Follow-up & Latest Updates")

    try:
        followup_df = clean_ids(load_table("notice_followup_tracking"), ["restaurant_id"])
        treated_df = clean_ids(load_table("treated_restaurant_data"), ["id", "officer_id"])

        merged = pd.merge(followup_df, treated_df[["id", "officer_id"]], left_on="restaurant_id", right_on="id", how="left")
        merged.fillna("", inplace=True)

        officer_ids = sorted(merged["officer_id"].dropna().unique())

        for oid in officer_ids:
            off_df = merged[merged["officer_id"] == oid]
            total = len(off_df)
            returned = (off_df["delivery_status"].str.lower() == "returned").sum()
            corrected_names = (off_df["correct_name"].str.strip() != "").sum()
            corrected_address = (off_df["correct_address"].str.strip() != "").sum()

            with st.expander(f"🕵️ Officer ID {oid} — Restaurants: {total} — Notices Returned: {returned}"):
                col1, col2 = st.columns(2)
                col1.metric("📬 Notices Returned", returned)
                col2.metric("📛 Corrected Names", corrected_names)

                resend_df = off_df[
                    (off_df["delivery_status"].str.lower() == "returned") &
                    (
                        (off_df["correct_name"].fillna("").str.strip() != "") |
                        (off_df["correct_address"].fillna("").str.strip() != "")
                    )
                ]
                total_resends = len(resend_df)

                st.markdown(f"### 📨 Total Notices to Re-send: `{total_resends}`")

                if not resend_df.empty:
                    st.dataframe(resend_df[[
                        "restaurant_id", "delivery_status", "correct_address", "correct_name", "contact"
                    ]].reset_index(drop=True))
                else:
                    st.info("No returned notices for this officer.")
    except Exception as e:
        st.error(f"❌ Error loading Notice Follow-up: {e}")

    # --- Filing Status Summary ---
    st.markdown("## 🔄 Latest Formality Status")

    try:
        followup_df = clean_ids(load_table("notice_followup_tracking"), ["restaurant_id"])
        treated_df = clean_ids(load_table("treated_restaurant_data"), ["id", "restaurant_name", "restaurant_address", "compliance_status"])

        combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["latest_formality_status"] = combined["latest_formality_status"].fillna("None").str.strip()
        combined["compliance_status"] = combined["compliance_status"].fillna("None").str.strip()
        combined["changed"] = combined["latest_formality_status"].str.lower() != combined["compliance_status"].str.lower()
        changed = combined[combined["changed"]]

        st.markdown(f"### 📦 Status Change Summary — Total Changes: `{len(changed)}`")

        for status_key, group_df in changed.groupby("latest_formality_status"):
            display_label = {
                "filer": "🟢 Started Filing",
                "none": "⚪ No Change in Formality"
            }.get(status_key.lower(), status_key)

            with st.expander(f"{display_label} — {len(group_df)}"):
                st.dataframe(group_df[[
                    "restaurant_id", "restaurant_name", "restaurant_address", "compliance_status", "latest_formality_status"
                ]].reset_index(drop=True))
    except Exception as e:
        st.error(f"❌ Could not load filing status summary: {e}")

    # --- Compact Status View ---
    st.markdown("## 🔄 Filing Status Change Summary")

    try:
        followup_df = clean_ids(load_table("notice_followup_tracking"), ["restaurant_id"])
        treated_df = clean_ids(load_table("treated_restaurant_data"), ["id", "restaurant_name", "restaurant_address", "compliance_status"])

        combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["changed"] = combined["compliance_status"].fillna("").str.strip().str.lower() != combined["latest_formality_status"].fillna("").str.strip().str.lower()
        changed = combined[combined["changed"]].copy()

        total_changed = len(changed)
        st.markdown(f"### 🧾 Total Restaurants With Status Changes: <span style='background:#dcfce7;padding:5px 10px;border-radius:5px;font-weight:bold;'>{total_changed}</span>", unsafe_allow_html=True)

        restaurant_labels = changed.apply(lambda row: f"{row['restaurant_name']} ({row['id']})", axis=1).tolist()
        selected_label = st.selectbox("🔍 Select a Restaurant", restaurant_labels)

        selected_id = selected_label.split("(")[-1].replace(")", "").strip()
        row = changed[changed["id"] == selected_id].iloc[0]

        st.markdown(f"""
        <div style='
            border:1px solid #ddd;
            padding:10px;
            margin-top:10px;
            border-radius:6px;
            background-color:#f9f9f9;
        '>
            <b>🏪 {row['restaurant_name']}</b> <br>
            📍 <i>{row['restaurant_address']}</i> <br>
            🆔 ID: <code>{row['id']}</code> <br><br>
            <b>Previous Status:</b> <span style='color:#d97706;'>{row['compliance_status']}</span><br>
            <b>Latest Status:</b> <span style='color:#16a34a;'>{row['latest_formality_status']}</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Could not load filing status detail: {e}")

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

    # Compliance filtering
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

    # Dropdown selector
    rest_df = df[["id", "restaurant_name"]].dropna(subset=["id"]).copy()
    rest_df['id'] = rest_df['id'].astype(str)
    rest_df['label'] = rest_df['id'] + " - " + rest_df['restaurant_name'].fillna("")
    rest_df = rest_df.sort_values(by="id", key=lambda x: x.str.zfill(10))

    selected_label = st.selectbox("🔍 Search by ID or Name", rest_df['label'].tolist())
    selected_id = selected_label.split(" - ")[0].strip()
    selected_name = selected_label.split(" - ")[1].strip()

    st.subheader(f"🏪 {selected_name}")

    # -------------------- Image Display Section --------------------
    st.markdown("### 🖼️ Restaurant Images")
    imgs = dfs["restaurant_images"].copy()
    imgs["restaurant_id"] = imgs["restaurant_id"].astype(str).str.strip().str.replace('"', '').str.replace("'", '')
    selected_id = selected_id.strip()
    imgs = imgs[imgs["restaurant_id"] == selected_id]

    image_type_map = {"front": "Front Image", "menu": "Menu Image", "receipt": "Receipt Image"}

    def get_supabase_url(filename):
        return f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}"

    def clean_filename(path):
        if isinstance(path, str):
            return os.path.basename(path.strip().replace('"', '').replace("'", '').replace("\\", "/"))
        return ""

    if not imgs.empty:
        img_cols = st.columns(3)
        for i, img_type in enumerate(["front", "menu", "receipt"]):
            with img_cols[i]:
                subset = imgs[imgs["image_type"] == img_type]
                if not subset.empty:
                    image_path = clean_filename(subset.iloc[0]["image_path"])
                    image_url = get_supabase_url(image_path)
                    st.image(image_url, caption=image_type_map[img_type])
                    st.caption(f"[Debug] {image_url}")
                else:
                    st.info(f"No {image_type_map[img_type]} found.")
    else:
        st.info("No images available for this restaurant.")

    # -------------------- Basic Info --------------------
    st.markdown("### 🗃️ Basic Info")
    row = df[df["id"].astype(str) == selected_id]
    if not row.empty:
        row = row.iloc[0]
        info_cols = ["restaurant_name", "restaurant_address", "compliance_status", "officer_id", "ntn", "latitude", "longitude"]
        info_df = pd.DataFrame([[col, row[col]] for col in info_cols if col in row], columns=["Field", "Value"])
        st.table(info_df)
    else:
        st.warning("Restaurant not found.")

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
