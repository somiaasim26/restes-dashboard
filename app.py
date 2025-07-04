
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
import requests
from PIL import Image
from io import BytesIO
from PIL import Image, ExifTags
from io import StringIO


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
    "haali1@live.com": "123PRA**!",
    "kamranpra@gmail.com": "123PRA**!",
    "saudatiq90@gmail.com": "123PRA**!"
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
            st.session_state["section"] = "Restaurant Profile"
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
    "enhanced_treated_restaurants": "Updates in Treatment",
    "new_ntn_mappings": "New NTNs",
    "registered_ntn_data": "Officer-wise Registered Data",
    "s1_p1": "Survey 1 - P1", "s1_p2": "Survey 1 - P2", "s1_sec2": "Survey 1 - Sec2", "s1_sec3": "Survey 1 - Sec3",
    "s2_p1": "Survey 2 - P1", "s2_p2": "Survey 2 - P2", "s2_sec2": "Survey 2 - Sec2", "s2_sec3": "Survey 2 - Sec3"
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
    allowed_sections = ["Restaurant Profile"]
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
    followup_df["correct_name"] = followup_df.get("correct_name", "").astype(str).fillna("")

    officer_ids = sorted(treated_df["officer_id"].unique())

    for oid in officer_ids:
        officer_df = treated_df[treated_df["officer_id"] == oid]
        assigned_ids = officer_df["id"].tolist()
        total_restaurants = len(officer_df)

        officer_followups = followup_df[followup_df["restaurant_id"].isin(assigned_ids)]

        returned = officer_followups[officer_followups["delivery_status"].str.lower() == "returned"].copy()

        # Must have either corrected name or corrected address
        # Resend-worthy: must have either a non-empty correct name or correct address (not just 'None' or blank)
        resend_df = returned[
            (returned["correct_name"].fillna("").str.strip().str.lower() != "") &
            (returned["correct_name"].fillna("").str.strip().str.lower() != "none")
            |
            (returned["correct_address"].fillna("").str.strip().str.lower() != "") &
            (returned["correct_address"].fillna("").str.strip().str.lower() != "none")
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

        followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str).str.strip()
        treated_df["id"] = treated_df["id"].astype(str).str.strip()

        combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["latest_formality_status"] = combined["latest_formality_status"].fillna("").str.strip().str.lower()
        combined["compliance_status"] = combined["compliance_status"].fillna("").str.strip().str.lower()

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

    # --- Filing Status Summary (Compact View) ---
    st.markdown("## 🧾 Formality Change All Restaurants")

    try:
        followup_df = dfs["notice_followup_tracking"]
        treated_df = dfs["treated_restaurant_data"][["id", "restaurant_name", "restaurant_address", "compliance_status"]]

        followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str).str.strip()
        treated_df["id"] = treated_df["id"].astype(str).str.strip()

        combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["changed"] = combined["compliance_status"].fillna("").str.strip().str.lower() != combined["latest_formality_status"].fillna("").str.strip().str.lower()
        changed = combined[combined["changed"]].copy()

        total_changed = len(changed)
        st.markdown(f"### 🧾 Restaurants With Status Changes: <span style='background:#dcfce7;padding:5px 10px;border-radius:5px;font-weight:bold;'>{total_changed}</span>", unsafe_allow_html=True)

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
        st.error(f"❌ Could not load compact summary: {e}")

#------------------------------------------------------------------------------------------------------------------

#------ Data Browser ----

elif section == "Data Browser":
    st.title("📋 Database Browser")

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

    
############################################################

        # --- Choose Table ---
    tables = ["enhanced_treated_restaurants", "treated_restaurant_data", "new_ntn_mappings"]
    selected_table = st.selectbox("📄 Choose a table to explore", tables)

    # --- Sample columns for filtering ---
    sample = supabase.table(selected_table).select("*").limit(1).execute()
    columns = list(sample.data[0].keys()) if sample.data else []
    if not columns:
        st.warning("⚠️ This table has no data.")
        st.stop()

    # --- Load Full Table Option ---
    load_all = st.checkbox("⬇️ Load full table (ignores filters)", value=False)

    if not load_all:
        with st.expander("🔍 Add Filter Condition", expanded=True):
            selected_column = st.selectbox("Filter 1: Column (Required)", columns)
            operator = st.selectbox("Operator (Optional)", ["", "=", "!=", "ILIKE", "IS NULL", "IS NOT NULL"])
            value = ""
            if operator not in ["", "IS NULL", "IS NOT NULL"]:
                value = st.text_input("Value (Optional)")
    else:
        selected_column = None
        operator = None
        value = None

    # --- Query Builder ---
    query = supabase.table(selected_table).select("*")  # All fields

    if not load_all and selected_column:
        if operator == "IS NULL":
            query = query.filter(selected_column, "is", None)
        elif operator == "IS NOT NULL":
            query = query.not_(selected_column, "is", None)
        elif operator == "=":
            query = query.eq(selected_column, value)
        elif operator == "!=":
            query = query.neq(selected_column, value)
        elif operator == "ILIKE":
            query = query.ilike(selected_column, f"%{value}%")

    # --- Execute Query ---
    try:
        results = query.limit(1000).execute()
        df = pd.DataFrame(results.data)

        st.subheader("📊 Table Preview")
        st.dataframe(df, use_container_width=True)
        st.success(f"✅ {len(df)} records found")

        if not load_all and selected_column in df.columns:
            st.info(f"🧮 Unique {selected_column} values: {df[selected_column].nunique(dropna=True)}")

    except Exception as e:
        st.error(f"❌ Query failed: {e}")

    # --- View All NTNs by Officer ---
    with st.expander("👮 View NTNs by Officer ID", expanded=False):
        try:
            # ⚠️ Update this table name to your actual Supabase table
            correct_ntn_table = "your_actual_ntn_table_name"

            officer_ntn_query = supabase.table(correct_ntn_table).select("officer_id, ntn, restaurant_name, id, address").execute()
            officer_df = pd.DataFrame(officer_ntn_query.data)

            if not officer_df.empty:
                for officer_id in officer_df["officer_id"].dropna().unique():
                    with st.expander(f"Officer {officer_id} – NTNs", expanded=False):
                        st.dataframe(officer_df[officer_df["officer_id"] == officer_id], use_container_width=True)
            else:
                st.warning("⚠️ No NTN data available in the specified table.")

        except Exception as e:
            st.error(f"❌ Failed to fetch NTNs: {e}")


# ---------------------- Restaurant Profile Header ----------------------
elif section == "Restaurant Profile":

    st.title("📋 Restaurant Summary Profile")
    
    try:
        # 🚀 Load data from enhanced table
        raw_data = supabase.table("enhanced_treated_restaurants").select("*").limit(5000).execute().data
        df = pd.DataFrame(raw_data)

        # 🔍 Debug: show all available columns
        st.write("📋 Available Columns:", df.columns.tolist())

        # 🧠 Map officer
        officer_ids = {
            "haali1@live.com": "3",
            "kamranpra@gmail.com": "2",
            "saudatiq90@gmail.com": "1"
        }
        officer_id = officer_ids.get(user_email)

        if officer_id:
            df = df[df["officer_id"] == officer_id]
            st.info(f"Showing restaurants for Officer {officer_id}")
        else:
            st.info("Showing all restaurants (admin view)")

        # 🧾 Desired columns — try both capitalized and lowercase
        summary_cols = ["id", "restaurant_name", "restaurant_address", "all_ntns", "ntn", "New_NTN", "new_ntn"]
        lowercase_cols = [col.lower() for col in df.columns]
        display_cols = [col for col in summary_cols if col.lower() in lowercase_cols]

        # 🔁 Adjust column names if needed (case-insensitive mapping)
        matched_cols = []
        for col in display_cols:
            for real_col in df.columns:
                if real_col.lower() == col.lower():
                    matched_cols.append(real_col)
                    break

        st.write("✅ Columns that will display:", matched_cols)

        # 📊 Compliance groups
        registered_df = df[df["compliance_status"].str.lower() == "registered"]
        unregistered_df = df[df["compliance_status"].str.lower() == "unregistered"]
        filers_df = df[df["compliance_status"].str.lower() == "filed"]

        st.markdown("### 📊 Monthly Compliance Summary")
        # 🚨 TEMP DEBUGGING OUTPUT
        st.write("🧪 Officer ID:", officer_id)
        st.write("🧪 DataFrame shape after filtering:", df.shape)
        st.write("🧪 Sample of df:", df.head(3))
        st.write("🧪 Registered Count:", len(registered_df))
        st.write("🧪 Unregistered Count:", len(unregistered_df))
        st.write("🧪 Filers Count:", len(filers_df))


        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(f"✅ Registered ({len(registered_df)})"):
                if matched_cols:
                    st.dataframe(registered_df[matched_cols], use_container_width=True)
                else:
                    st.warning("No valid columns to display.")

        with col2:
            if st.button(f"❌ Unregistered ({len(unregistered_df)})"):
                if matched_cols:
                    st.dataframe(unregistered_df[matched_cols], use_container_width=True)
                else:
                    st.warning("No valid columns to display.")

        with col3:
            if st.button(f"🧾 Filers ({len(filers_df)})"):
                if matched_cols:
                    st.dataframe(filers_df[matched_cols], use_container_width=True)
                else:
                    st.warning("No valid columns to display.")

    except Exception as e:
        st.error(f"❌ Failed to load enhanced restaurant data: {e}")


    # --- Restaurant Selector ---
    # ---(Officer Filtered to Unregistered Only) ---
    if user_email in officer_ids:
        officer_id = officer_ids[user_email]
        officer_df = df[df["officer_id"] == officer_id]
        unregistered_df = officer_df[officer_df["compliance_status"].str.lower() == "unregistered"].copy()
        rest_df = unregistered_df[["id", "restaurant_name"]].dropna()
    else:
        # Admin/super user: show all restaurants
        rest_df = df[["id", "restaurant_name"]].dropna().copy()

    # Construct labels
    rest_df["id"] = rest_df["id"].astype(str)
    rest_df["label"] = rest_df["id"] + " - " + rest_df["restaurant_name"].fillna("")
    rest_df = rest_df.sort_values("id", key=lambda x: x.str.zfill(10))

    # Prevent errors if nothing found
    if rest_df.empty:
        st.warning("No restaurants available to display.")
        st.stop()

    # Display selection
    selected_label = st.selectbox("🔍 Search by ID or Name", rest_df["label"].tolist())
    selected_id = selected_label.split(" - ")[0].strip()
    selected_name = selected_label.split(" - ")[1].strip()

    st.subheader(f"🏪 {selected_name}")


    # ---------------------- IMAGE SECTION ----------------------
    from PIL import Image, ExifTags

    st.markdown("### 🖼️ Restaurant Images")

    @st.cache_resource(show_spinner=False)
    def load_image_from_supabase(filename):
        try:
            url = f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}"
            response = requests.get(url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))

                # Correct orientation using EXIF if available
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    exif = img._getexif()
                    if exif:
                        orientation_value = exif.get(orientation)
                        if orientation_value == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation_value == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation_value == 8:
                            img = img.rotate(90, expand=True)
                except Exception:
                    pass  # Skip orientation if EXIF not available

                return img
        except Exception:
            return None
        return None

    image_types = {
        "front": "📸 Front Image",
        "menu": "🍽️ Menu Image",
        "receipt": "🧾 Receipt Image"
    }

    cols = st.columns(3)
    for idx, (img_type, label) in enumerate(image_types.items()):
        with cols[idx]:
            st.markdown(f"#### {label}")
            filename = f"{selected_id}_{img_type}.jpg"
            image = load_image_from_supabase(filename)
            if image:
                st.image(image, use_container_width=True, caption=filename)
            else:
                st.info("Image not available.")


    # ---------------------- BASIC INFO ----------------------
    st.markdown("### 🗃️ Basic Info")
    row = df[df["id"].astype(str) == selected_id]
    if not row.empty:
        row = row.iloc[0]
        info_cols = ["id", "restaurant_name", "restaurant_address", "compliance_status", "officer_id", "ntn", "latitude", "longitude"]
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
            "ntn": "🔘 NTN", "pntn": "🔘 PNTN", "strn": "🔘 STRN", "type_of_the_restaurant": "🍱 Type of Restaurant",
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

                # Special formatting for long links
                if col.lower() == "link":
                    (col1 if i % 2 == 0 else col2).markdown(f"""
                        <div style='
                            background-color: #f1f5f9;
                            padding: 8px 12px;
                            border-radius: 6px;
                            margin-bottom: 8px;
                            border-left: 4px solid #2563eb;
                            word-break: break-word;
                            white-space: normal;
                            max-width: 100%;
                        '>
                            <strong>{label}:</strong><br>
                            <a href="{value}" target="_blank">{value}</a>
                        </div>
                    """, unsafe_allow_html=True)
                else:
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

    # Reason selection
    reason_options = [
        "Not Liable – turnover < 6M",
        "Not a Restaurant – Retail or Non-Food",
        "Already Registered with PRA",
        "Closed / Inactive Business"
    ]
    selected_reason = st.radio("Select reason for not sending notice:", reason_options, key=f"reason_radio_{selected_id}_{user_email}")

    ntn_input = None
    if selected_reason == "Already Registered with PRA":
        ntn_input = st.text_input("Enter NTN (if known):", placeholder="e.g. 1234567")

    # Submit to Supabase
    if st.button("✅ Submit Reason"):
        try:
            payload = {
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "reason": selected_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            if selected_reason == "Already Registered with PRA" and ntn_input:
                payload["NTN"] = ntn_input

            supabase.table("notice_skip_reasons").insert(payload).execute()
            st.success("✅ Reason submitted successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to submit reason: {e}")

    # ---------------------- EXPORT + TABLES ----------------------

    st.markdown("### 🧾 Export Restaurant Data as CSV")

    # Load data
    try:
        officer_id = officer_ids.get(user_email)
        if not officer_id:
            st.warning("⚠️ Officer not recognized.")
            st.stop()

        treated_data = supabase.table("treated_restaurant_data").select("id, restaurant_name, restaurant_address, latitude, longitude, officer_id").execute().data
        skip_data = supabase.table("notice_skip_reasons").select("restaurant_id, officer_email, reason, NTN, timestamp").execute().data

        treated_df = pd.DataFrame(treated_data)
        

        # Filter by officer
        treated_df = treated_df[treated_df["officer_id"] == officer_id].copy()
        # Define expected columns
        expected_cols = ["restaurant_id", "officer_email", "reason", "NTN", "timestamp"]

        # Safely create DataFrame
        skip_df = pd.DataFrame(skip_data)

        # Force expected schema if empty
        if skip_df.empty:
            skip_df = pd.DataFrame(columns=expected_cols)
        else:
            skip_df = skip_df[expected_cols]

        # Filter for current user
        skip_df = skip_df[skip_df["officer_email"] == user_email].copy()
        st.info(f"Skip Reasons Loaded: {len(skip_df)} rows")


        treated_df["id"] = treated_df["id"].astype(str)
        skip_df["restaurant_id"] = skip_df["restaurant_id"].astype(str)

        skipped_ids = skip_df["restaurant_id"].unique()

        # ---------- SKIPPED ----------
        skipped_df = treated_df[treated_df["id"].isin(skipped_ids)].copy()
        skipped_df = skipped_df.merge(skip_df, left_on="id", right_on="restaurant_id", how="left")
        skipped_df["timestamp"] = pd.to_datetime(skipped_df["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")

        display_skipped = skipped_df[[
            "restaurant_name", "restaurant_address", "latitude", "longitude", "reason", "NTN", "timestamp"
        ]].rename(columns={
            "restaurant_name": "Name", "restaurant_address": "Address", "latitude": "Latitude",
            "longitude": "Longitude", "reason": "Skip Reason", "NTN": "NTN", "timestamp": "Submitted At"
        })

        st.markdown("### ❌ Skipped Restaurants (Notice Not Sent)")
        if display_skipped.empty:
            st.info("✅ No skipped restaurants yet.")
        else:
            st.dataframe(display_skipped, use_container_width=True)
            csv_skipped = display_skipped.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Skipped Restaurants (CSV)", csv_skipped, file_name="skipped_restaurants.csv")

        # ---------- APPROVED ----------
        approved_df = treated_df[~treated_df["id"].isin(skipped_ids)].copy()
        display_approved = approved_df[[
            "restaurant_name", "restaurant_address", "latitude", "longitude"
        ]].rename(columns={
            "restaurant_name": "Name", "restaurant_address": "Address",
            "latitude": "Latitude", "longitude": "Longitude"
        })

        st.markdown("### ✅ Approved Restaurants (Send Notice)")
        if display_approved.empty:
            st.info("✅ No approved restaurants left (all skipped).")
        else:
            st.dataframe(display_approved, use_container_width=True)
            csv_approved = display_approved.to_csv(index=False).encode("utf-8")
            st.download_button("📤 Download Approved Notice List (CSV)", csv_approved, file_name="approved_notice.csv")

    except Exception as e:
        st.error(f"❌ Could not load exportable data: {e}")

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
