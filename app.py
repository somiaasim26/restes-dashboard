
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
import requests
from PIL import Image
from io import BytesIO
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

# --- Supabase Client Setup ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# --- Supabase Load with Pagination ---
@st.cache_data
def load_table(table_name: str, columns: list = None, batch_size: int = 1000):
    try:
        offset = 0
        all_data = []
        while True:
            query = supabase.table(table_name).select("*" if columns is None else ",".join(columns)).range(offset, offset + batch_size - 1)
            response = query.execute()
            data = response.data or []
            all_data.extend(data)
            if len(data) < batch_size:
                break
            offset += batch_size
        return pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"❌ Failed to load `{table_name}`: {e}")
        return pd.DataFrame()

# --- Utility: Clean ID Columns ---
def clean_ids(df, id_cols):
    for col in id_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", "")
    return df.dropna(subset=id_cols)


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
# ---------------------- Officer-Wise Compliance Summary ----------------------
if section == "Current Stats / KPI":

        st.title("📊 PRA System Status")

        treated_df = dfs["treated_restaurant_data"].copy()
        followup_df = dfs["notice_followup_tracking"].copy()

        # Clean IDs and types
        treated_df = treated_df.dropna(subset=["id", "officer_id"])
        treated_df["id"] = treated_df["id"].astype(str).str.strip()
        treated_df["officer_id"] = treated_df["officer_id"].astype(str).str.strip()

        followup_df = followup_df.dropna(subset=["restaurant_id"])
        followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str).str.strip()
        followup_df["delivery_status"] = followup_df["delivery_status"].fillna("").astype(str)
        followup_df["reason"] = followup_df.get("reason", "").astype(str).fillna("")
        followup_df["correct_address"] = followup_df.get("correct_address", "").astype(str).fillna("")

        officer_ids = sorted(treated_df["officer_id"].unique())

        for oid in officer_ids:
            officer_df = treated_df[treated_df["officer_id"] == oid]
            assigned_ids = officer_df["id"].tolist()
            total_restaurants = len(officer_df)

            # Filter only those follow-up records related to this officer’s assigned restaurants
            officer_followups = followup_df[followup_df["restaurant_id"].isin(assigned_ids)]

            # Returned notices
            returned = officer_followups[officer_followups["delivery_status"].str.lower() == "returned"]

            # Resend-worthy: returned AND corrected address or reason
            resend_df = returned[
                (returned["correct_address"].str.strip() != "") |
                (returned["reason"].str.strip() != "")
            ]

            st.markdown("---")
            with st.expander(f"🧑 Officer ID: {oid} — Assigned: {total_restaurants}, Returned: {len(returned)}, Re-send: {len(resend_df)}", expanded=False):

                col1, col2, col3 = st.columns(3)
                col1.metric("📋 Assigned", total_restaurants)
                col2.metric("📬 Returned Notices", len(returned))
                col3.metric("📨 To Re-send", len(resend_df))

                if not resend_df.empty:
                    resend_df = resend_df.merge(
                        officer_df[["id", "restaurant_name", "restaurant_address"]],
                        left_on="restaurant_id", right_on="id", how="left"
                    )
                    st.markdown("### 🗺️ Restaurants to Re-send Notice")
                    st.dataframe(resend_df[[
                        "restaurant_id", "restaurant_name", "restaurant_address", "delivery_status", "correct_address", "reason"
                    ]].reset_index(drop=True))
                else:
                    st.info("✅ No returned notices requiring correction.")


    # --- Filing Status Summary (Grouped Count with Drilldown) ---
        st.markdown("## 🔄 Latest Formality Status")

        try:
            followup_df = dfs["notice_followup_tracking"].copy()
            treated_df = dfs["treated_restaurant_data"][["id", "restaurant_name", "restaurant_address", "compliance_status"]].copy()

            # Clean IDs
            followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str).str.strip()
            treated_df["id"] = treated_df["id"].astype(str).str.strip()

            # Merge with treated to compare status
            combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")

            # Normalize status fields
            combined["latest_formality_status"] = combined["latest_formality_status"].fillna("").str.strip().str.lower()
            combined["compliance_status"] = combined["compliance_status"].fillna("").str.strip().str.lower()

            # Only keep those where statuses differ
            combined["changed"] = combined["latest_formality_status"] != combined["compliance_status"]
            changed = combined[combined["changed"] & (combined["latest_formality_status"] != "")]

            st.markdown(f"### 📦 Status Change Summary — Total Changes: `{len(changed)}`")

            for status_key, group_df in changed.groupby("latest_formality_status"):
                label = {
                    "filer": "🟢 Started Filing",
                    "none": "⚪ No Change"
                }.get(status_key.lower(), f"🔄 {status_key.title()}")

                with st.expander(f"{label} — {len(group_df)}"):
                    st.dataframe(group_df[[
                        "restaurant_id", "restaurant_name", "restaurant_address", "compliance_status", "latest_formality_status"
                    ]].reset_index(drop=True))

        except Exception as e:
            st.error(f"❌ Could not load summary: {e}")

#------------------------------------------------------------------------------------------------------------------

#------ Data Browser ----

elif section == "Data Browser":
    st.title("📋 Supabase Data Browser")

    table_names = list(tables.keys())
    readable_names = [tables[t] for t in table_names]
    selected_table_name = st.selectbox("📁 Choose a Table to View", options=table_names, format_func=lambda x: tables[x])

    # Sample fetch (first 5 rows only)
    @st.cache_data
    def get_sample_data(table_name):
        try:
            return pd.DataFrame(supabase.table(table_name).select("*").limit(5).execute().data)
        except Exception as e:
            st.error(f"Error fetching sample: {e}")
            return pd.DataFrame()

    # Full fetch (on demand)
    @st.cache_data
    def get_full_data(table_name):
        try:
            return pd.DataFrame(supabase.table(table_name).select("*").execute().data)
        except Exception as e:
            st.error(f"Error fetching full data: {e}")
            return pd.DataFrame()

    st.markdown(f"### 🧾 Preview: {tables[selected_table_name]}")
    sample_df = get_sample_data(selected_table_name)

    if not sample_df.empty:
        st.dataframe(sample_df)
    else:
        st.info("No sample data available or table is empty.")

    if st.button("🔄 Load Full Table"):
        full_df = get_full_data(selected_table_name)
        st.markdown(f"### 📊 Full Dataset: {tables[selected_table_name]} ({len(full_df)} rows)")
        st.dataframe(full_df)


# ---------------------- Restaurant Profile Header ----------------------
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

    # Filter for officer
    if officer_id:
        df = df[df["officer_id"] == officer_id]
        st.info(f"Showing restaurants for Officer {officer_id}")
    else:
        st.success("Showing all restaurants")

    # --- Compliance Summary Buttons ---
    registered_df = df[df["compliance_status"] == "Registered"]
    unregistered_df = df[df["compliance_status"] != "Registered"]
    filers_df = df[df["ntn"].notna() & (df["ntn"].astype(str).str.strip() != "")]

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

    # --- Restaurant Selector ---
    rest_df = df[["id", "restaurant_name"]].dropna().copy()
    rest_df["id"] = rest_df["id"].astype(str)
    rest_df["label"] = rest_df["id"] + " - " + rest_df["restaurant_name"].fillna("")
    rest_df = rest_df.sort_values("id", key=lambda x: x.str.zfill(10))

    selected_label = st.selectbox("🔍 Search by ID or Name", rest_df["label"].tolist())
    selected_id = selected_label.split(" - ")[0].strip()
    selected_name = selected_label.split(" - ")[1].strip()

    st.subheader(f"🏪 {selected_name}")

    # ---------------------- IMAGE SECTION ----------------------
    st.markdown("### 🖼️ Restaurant Images")

    def get_supabase_image_url(filename):
        return f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}"

    image_types = {
        "front": "📸 Front Image",
        "menu": "🍽️ Menu Image",
        "receipt": "🧾 Receipt Image"
    }

    cols = st.columns(3)
    for idx, (img_type, title) in enumerate(image_types.items()):
        with cols[idx]:
            st.markdown(f"#### {title}")
            filename = f"{selected_id}_{img_type}.jpg"
            url = get_supabase_image_url(filename)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True, caption=filename)
                else:
                    st.info("Image not available.")
            except Exception:
                st.info("Image load error.")

    # ---------------------- BASIC INFO ----------------------
    st.markdown("### 🗃️ Basic Info")
    row = df[df["id"].astype(str) == selected_id]
    if not row.empty:
        row = row.iloc[0]
        info_cols = ["restaurant_name", "restaurant_address", "compliance_status", "officer_id", "ntn", "latitude", "longitude"]
        info_df = pd.DataFrame([[col, row[col]] for col in info_cols if col in row], columns=["Field", "Value"])
        st.table(info_df)
    else:
        st.warning("Restaurant not found.")

    # ---------------------- SURVEY INFO ----------------------
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
            "post_tax_price": "💰 Post-Tax Price", "price_paid": "💸 Price Paid", "link": "🔗 Link", "contact": "📞 Contact Info"
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

    # ---------------------- SKIP REASON ----------------------
    st.markdown("### 📝 Reason for Not Sending Notice")

    # Reason Options
    reason_options = [
        "Not Liable – turnover < 6M or not a restaurant",
        "Already Registered on FBR",
        "Inaccessible / Demolished",
        "Duplicate / Error in Listing"
    ]

    # Selection UI
    selected_reason = st.radio("Select reason for not sending notice:", reason_options, key=f"skip_{selected_id}_{user_email}")

    # Submission Button
    if st.button("✅ Submit Reason to Supabase"):
        try:
            from datetime import datetime
            insert_payload = {
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "reason": selected_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            supabase.table("notice_skip_reasons").insert(insert_payload).execute()
            st.success("✅ Reason submitted successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to submit reason: {e}")

    # ---------------------- CSV EXPORT ----------------------
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
