# app.py

import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import requests
from PIL import Image, ExifTags
from io import BytesIO
from functools import lru_cache

# ------------------- Streamlit Setup -------------------
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
    st.title("🔒 PRA Dashboard Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in approved_users and approved_users[email] == password:
            st.session_state.update(authenticated=True, email=email, section="Welcome")
            st.rerun()
        elif email in special_access_users and special_access_users[email] == password:
            st.session_state.update(authenticated=True, email=email, section="Restaurant Profile")
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# ------------------- Supabase Client -------------------
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ------------------- Caching Utilities -------------------
@st.cache_data
def load_table(table_name: str, batch_size=1000):
    all_data, offset = [], 0
    while True:
        res = supabase.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()
        data = res.data or []
        all_data.extend(data)
        if len(data) < batch_size:
            break
        offset += batch_size
    return pd.DataFrame(all_data)

@lru_cache(maxsize=500)
def fetch_image_from_supabase(filename):
    urls = [
        f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{filename}",
        f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/All_Images/{filename}"
    ]
    for url in urls:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    exif = img._getexif()
                    if exif:
                        val = exif.get(orientation)
                        if val == 3: img = img.rotate(180, expand=True)
                        elif val == 6: img = img.rotate(270, expand=True)
                        elif val == 8: img = img.rotate(90, expand=True)
                except: pass
                return img
        except: continue
    return None

@st.cache_data
def lazy_preload_images_subset(id_list, current_index, buffer=5):
    """
    Preloads a small buffer of images around the current index for smoother navigation.
    """
    preload_range = range(max(0, current_index - buffer), min(len(id_list), current_index + buffer + 1))
    preloaded_images = {}

    for i in preload_range:
        rest_id = id_list[i]
        for img_type in ["front", "menu", "receipt"]:
            key = (rest_id, img_type)
            preloaded_images[key] = fetch_image_from_supabase(f"{rest_id}_{img_type}.jpg")

    return preloaded_images



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
    "final_treatment": "final_treatment",
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

@st.cache_data
def load_final_treatment():
    df = load_table("final_treatment")
    df.columns = df.columns.str.strip().str.lower()
    df["id"] = df["id"].astype(str)
    df["restaurant_name"] = df["restaurant_name"].astype(str)
    df["label"] = df["id"] + " - " + df["restaurant_name"]
    df["formality_old"] = df["formality_old"].fillna("").str.strip().str.lower()
    df["ntn_final"] = df["ntn_final"].astype(str).str.strip()
    return df


# --- Sidebar Setup ---
user_email = st.session_state.get("email")
if user_email in special_access_users:
    allowed_sections = ["Restaurant Profile"]
else:
    allowed_sections = ["Restaurant Profile"]

section = st.sidebar.radio("📁 Navigate", allowed_sections)


# ---------------------- Current Stats / KPI ----------------------
if section == "Current Stats / KPI":

    st.title("📊 PRA System Status")

    # --- Load and Clean Treated and Follow-up Data ---
    treated_df = dfs.get("treated_restaurant_data", pd.DataFrame()).copy()
    followup_df = dfs.get("notice_followup_tracking", pd.DataFrame()).copy()

    # Drop nulls and clean ID fields
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
        officer_df = treated_df[treated_df["officer_id"] == oid].copy()
        assigned_ids = officer_df["id"].tolist()
        total_assigned = len(officer_df)

        officer_followups = followup_df[followup_df["restaurant_id"].isin(assigned_ids)].copy()
        returned = officer_followups[officer_followups["delivery_status"].str.lower() == "returned"].copy()

        # Resend-worthy = has valid corrected name or address
        resend_df = returned[
            ((returned["correct_name"].str.strip().str.lower() != "") & (returned["correct_name"].str.strip().str.lower() != "none")) |
            ((returned["correct_address"].str.strip().str.lower() != "") & (returned["correct_address"].str.strip().str.lower() != "none"))
        ].copy()

        st.markdown("---")
        with st.expander(f"🧑 Officer ID: {oid} — Assigned: {total_assigned}, Returned: {len(returned)}, Re-send: {len(resend_df)}", expanded=False):

            col1, col2, col3 = st.columns(3)
            col1.metric("📋 Assigned", total_assigned)
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

    # ---------------------- Status Change Section ----------------------
    st.markdown("## 🔄 Latest Formality Status")

    try:
        followup_df = dfs.get("notice_followup_tracking", pd.DataFrame()).copy()
        treated_df = dfs.get("treated_restaurant_data", pd.DataFrame())[["id", "restaurant_name", "restaurant_address", "compliance_status"]].copy()

        followup_df["restaurant_id"] = followup_df["restaurant_id"].astype(str).str.strip()
        treated_df["id"] = treated_df["id"].astype(str).str.strip()

        combined = pd.merge(followup_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["latest_formality_status"] = combined.get("latest_formality_status", "").fillna("").astype(str).str.strip().str.lower()
        combined["compliance_status"] = combined.get("compliance_status", "").fillna("").astype(str).str.strip().str.lower()

        combined["changed"] = (combined["latest_formality_status"] != combined["compliance_status"]) & (combined["latest_formality_status"] != "")
        changed = combined[combined["changed"]].copy()

        st.markdown(f"### 📦 Status Change Summary — Total Changes: {len(changed)}")

        for status_key, group_df in changed.groupby("latest_formality_status"):
            label = {
                "filed": "🟢 Started Filing",
                "registered": "🟠 Registered",
                "unregistered": "🔴 Unregistered"
            }.get(status_key.lower(), f"🔁 {status_key.title()}")

            with st.expander(f"{label} — {len(group_df)}", expanded=False):
                st.dataframe(group_df[[
                    "restaurant_id", "restaurant_name", "restaurant_address", "compliance_status", "latest_formality_status"
                ]].reset_index(drop=True))

    except Exception as e:
        st.error(f"❌ Could not load summary: {e}")

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
    # --- Officer Identity ---
    st.markdown(f"👮 Logged in as: `{user_email}`")


    # --- Officer Mapping ---
    officer_ids = {
        "haali1@live.com": "3",
        "kamranpra@gmail.com": "2",
        "saudatiq90@gmail.com": "1"
    }
    officer_id = officer_ids.get(user_email)

    # --- Load Final Treatment Data ---
    df_all = load_final_treatment().copy()
    if officer_id and user_email in special_access_users:
        df_all = df_all[df_all["officer_id"].astype(str) == officer_id]

    # --- Progress Counter ---
    total_assigned = df_all.shape[0]

    # Load issued + skipped restaurant IDs
    issued_ids = supabase.table("enforcement_tracking").select("restaurant_id").eq("officer_email", user_email).execute().data
    skip_ids = supabase.table("notice_skip_reasons").select("restaurant_id").eq("officer_email", user_email).execute().data

    issued_set = set([row["restaurant_id"] for row in issued_ids])
    skipped_set = set([row["restaurant_id"] for row in skip_ids])
    completed_ids = issued_set.union(skipped_set)

    completed = df_all[df_all["id"].isin(completed_ids)].shape[0]
    st.info(f"📈 You've completed **{completed} out of {total_assigned}** assigned restaurants.")


    # --- Session State Setup ---
    for key, default in {
        "profile_filter": "unregistered",
        "profile_index": 0,
        "selected_label": None
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # --- Filter Buttons ---
    st.markdown("### 🔍 Filter Restaurants by Status")
    filter_map = {
        "registered": "🟢 Registered",
        "unregistered": "❌ Unregistered",
        "filed": "✅ Filed",
        "ntn": "📄 With NTN"
    }
    btn_cols = st.columns(len(filter_map))
    for i, (key, label) in enumerate(filter_map.items()):
        if btn_cols[i].button(label):
            st.session_state.update(profile_filter=key, profile_index=0, selected_label=None)
            st.rerun()

    # --- Apply Filter ---
    filt = st.session_state["profile_filter"]
    if filt == "ntn":
        filtered_df = df_all[df_all["ntn_final"].notna() & (df_all["ntn_final"] != "")]
    else:
        filtered_df = df_all[df_all["formality_old"] == filt]
    filtered_df = filtered_df.reset_index(drop=True)
    if filtered_df.empty:
        st.warning("No restaurants match this filter.")
        st.stop()

    # --- Label Setup (ID + Name) ---
    filtered_df["label"] = filtered_df["id"].astype(str).str.strip() + " - " + filtered_df["restaurant_name"].astype(str).str.strip()
    label_map = dict(zip(filtered_df["label"], filtered_df["id"]))
    label_list = list(label_map.keys())

    # --- Restore Previous Selection ---
    selected_label = st.session_state.get("selected_label", label_list[0])
    if selected_label not in label_list:
        selected_label = label_list[0]
    selected_label = st.selectbox("🔎 Search by ID or Name", label_list, index=label_list.index(selected_label), key="restaurant_searchbox")

    # --- Sync Session State from Selection ---
    st.session_state["selected_label"] = selected_label
    selected_id = label_map[selected_label]
    current_index = filtered_df.index.get_loc(filtered_df[filtered_df["id"] == selected_id].index[0])
    st.session_state["profile_index"] = current_index
    current_row = filtered_df.iloc[current_index]

    # --- Navigation Buttons ---
    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("⏮ Back"):
            new_index = (current_index - 1) % len(filtered_df)
            st.session_state.update(
                profile_index=new_index,
                selected_label=filtered_df.iloc[new_index]["label"]
            )
            st.rerun()
    with nav2:
        if st.button("⏭ Next"):
            new_index = (current_index + 1) % len(filtered_df)
            st.session_state.update(
                profile_index=new_index,
                selected_label=filtered_df.iloc[new_index]["label"]
            )
            st.rerun()

    # --- Notice & Follow-up Section ---
    st.markdown("### 📩 Notice & Follow-up")

    # Load issued notices for this restaurant
    try:
        issued_data = supabase.table("enforcement_tracking") \
            .select("reason, issued, issued_at") \
            .eq("restaurant_id", selected_id) \
            .order("issued_at", desc=True) \
            .limit(1).execute().data

        has_notice = False
        notice_reason = ""
        if issued_data and issued_data[0].get("issued") == True:
            has_notice = True
            notice_reason = issued_data[0].get("reason", "Notice Issued")
            issued_time = pd.to_datetime(issued_data[0]["issued_at"]).strftime("%d %b %Y")

            st.markdown(f"""
            <div style='background-color: #fef3c7; border-left: 6px solid #f59e0b;
                padding: 10px 15px; border-radius: 6px; margin-bottom: 10px;'>
                <strong>📌 Notice Already Issued</strong><br>
                Reason: <em>{notice_reason}</em><br>
                Issued on: {issued_time}
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Could not check notice status: {e}")
        has_notice = False

    # Buttons
    b1, b2, b3 = st.columns(3)
    with b1:
        st.button("📬 Notice Sent", disabled=False)

    with b2:
        st.button("📅 Compliance Due", disabled=False)  # logic to be added later

    with b3:
        st.button("⏰ Follow-up Due", disabled=False)  # logic to be added later


    # --- Restaurant Name Header ---
    st.subheader(f"🏪 {current_row['restaurant_name']}")
    st.markdown(f"**Restaurant {current_index + 1} of {len(filtered_df)}**")

    # --- Restaurant Images ---
    st.markdown("### 🖼️ Restaurant Images")
    cols = st.columns(3)
    for i, img_type in enumerate(["front", "menu", "receipt"]):
        with cols[i]:
            st.markdown(f"#### {img_type.title()} Image")
            img = fetch_image_from_supabase(f"{selected_id}_{img_type}.jpg")
            if img:
                st.image(img, use_container_width=True)
            else:
                st.info("Image not available.")


    # --- Basic Info ---
    st.markdown("### 🗃️ Basic Info")
    info_df = pd.DataFrame([
        ["id", current_row.get("id", "")],
        ["restaurant_name", current_row.get("restaurant_name", "")],
        ["restaurant_address", current_row.get("restaurant_address", "")],
        ["ntn", current_row.get("ntn_final", "")],
        ["Compliance Status", current_row.get("formality_old", "")],
        ["officer_id", current_row.get("officer_id", "")],
        ["latitude", current_row.get("latitude", "")],
        ["longitude", current_row.get("longitude", "")]
    ], columns=["Field", "Value"])
    st.table(info_df)
####
    # --- Survey Info (from final_treatment) ---
    st.markdown("### 🏢 Survey Information")
    label_map = {
        "type_of_the_restaurant": "🍱 Type of Restaurant",
        "cuisine": "🧑‍🍳 Cuisine",
        "number_of_customers": "🧑‍🤝‍🧑 Customers",
        "number_of_chairs": "🪑 Chairs",
        "number_of_floors": "🏢 Floors",
        "number_of_tables": "🛎️ Tables",
        "seating_arrangement": "🧍‍🪑 Seating Arrangement",
        "air_conditioner": "❄ Air Conditioning",
        "credit_debit_card_acceptance": "💳 Card Acceptance",
        "food_court": "🏬 In Food Court",
        "gst": "💸 GST Amount",
        #"pre_tax_price": "💰 Pre-Tax Price",
        #"post_tax_price": "💰 Post-Tax Price",
        #"price_paid": "💸 Price Paid",
        "link": "🔗 Link",
        "contact_number": "📞 Contact Info"
    }

    row = current_row
    col1, col2 = st.columns(2)
    # List of allowed fields for survey info
    survey_fields = {
        "type_of_the_restaurant", "cuisine", "number_of_customers", "number_of_chairs",
        "number_of_floors", "number_of_tables", "seating_arrangement", "air_conditioner",
        "credit_debit_card_acceptance", "food_court", "link", "contact_number"
    }

    for i, col in enumerate(row.index):
        if col.lower() in survey_fields and pd.notna(row[col]):

            label = label_map.get(col.lower(), col.replace("_", " ").title())
            value = row[col]
            if col.lower() == "link":
                (col1 if i % 2 == 0 else col2).markdown(f"""
                    <div style='background-color: #f1f5f9; padding: 8px 12px;
                    border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;
                    word-break: break-word; white-space: normal; max-width: 100%;'>
                        <strong>{label}:</strong><br><a href="{value}" target="_blank">{value}</a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                (col1 if i % 2 == 0 else col2).markdown(f"""
                    <div style='background-color: #f1f5f9; padding: 8px 12px;
                    border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;'>
                        <strong>{label}:</strong> {value}
                    </div>
                """, unsafe_allow_html=True)


##########################################################
    # ---------------- Issue Notice + Reason Selection ----------------

    status = current_row.get("formality_old", "").strip().lower()
    st.markdown("### 📤 Issue Notice")

    notice_reasons = {
        "unregistered": [
            "To enforce registration with PRA",
            "Repeated refusal to register despite visits",
            "High turnover suspected, still unregistered"
        ],
        "registered": [
            "Not filing despite being registered",
            "Filing inconsistently (1 or 2 months)",
            "No filing for past 3 months"
        ],
        "filed": [
            "Stopped filing recently (penalty applicable)",
            "Late filing for multiple months",
            "Tax filing seems inaccurate"
        ]
    }

    status_label = {
        "unregistered": "🔴 Unregistered",
        "registered": "🟢 Registered",
        "filed": "✅ Filing"
    }

    if status in notice_reasons:
        st.success(f"This restaurant is **{status_label[status]}**")

        selected_reason = st.selectbox("📌 Select reason for issuing notice:", notice_reasons[status], key=f"notice_reason_{selected_id}")
        if st.button("🚀 Issue Notice", key=f"issue_notice_btn_{selected_id}"):
            try:
                supabase.table("enforcement_tracking").insert({
                    "restaurant_id": selected_id,
                    "officer_email": user_email,
                    "issued": True,
                    "status": status,
                    "reason": selected_reason,
                    "issued_at": datetime.utcnow().isoformat()
                }).execute()
                st.success("✅ Notice issued successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to issue notice: {e}")
        
    else:
        st.warning("⚠️ Unknown formality status")

    # Log this action
    supabase.table("activity_log").insert({
        "restaurant_id": selected_id,
        "officer_email": user_email,
        "action": "Issue Notice",
        "result": selected_reason
    }).execute()



    # --- Skip Reason ---
    st.markdown("### 📝 Reason for Not Sending Notice")
    reason_options = [
        "Not Liable – turnover < 6M",
        "Not a Restaurant – Retail or Non-Food",
        "Already Registered with PRA",
        "Closed / Inactive Business"
    ]
    selected_reason = st.radio("Select reason:", reason_options, key=f"reason_radio_{selected_id}_{user_email}")
    ntn_input = None
    if selected_reason == "Already Registered with PRA":
        ntn_input = st.text_input("Enter NTN (if known):", placeholder="e.g. 1234567")

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

        supabase.table("activity_log").insert({
        "restaurant_id": selected_id,
        "officer_email": user_email,
        "action": "Skip Reason",
        "result": selected_reason
    }).execute()

    #-------------------------------------------------------------

    # -------------------- TRACKER: Issued Notices by Officer --------------------

    st.markdown("### 📊 Issued Notices Tracker (Officer-wise)")

    try:
        notice_data = supabase.table("enforcement_tracking").select("*").execute().data
        df_notices = pd.DataFrame(notice_data)

        if df_notices.empty:
            st.info("No issued notices found.")
        else:
            df_notices["issued_at"] = pd.to_datetime(df_notices["issued_at"]).dt.strftime("%Y-%m-%d %H:%M")
            df_notices = df_notices.rename(columns={
                "restaurant_id": "Restaurant ID",
                "officer_email": "Officer",
                "status": "Formality Status",
                "reason": "Notice Reason",
                "issued_at": "Issued At"
            })

            # Filter UI
            officer_filter = st.selectbox("👮 Filter by Officer", ["All"] + sorted(df_notices["Officer"].unique().tolist()))
            status_filter = st.selectbox("📄 Filter by Formality Status", ["All"] + sorted(df_notices["Formality Status"].unique().tolist()))

            filtered_df = df_notices.copy()
            if officer_filter != "All":
                filtered_df = filtered_df[filtered_df["Officer"] == officer_filter]
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df["Formality Status"] == status_filter]

            st.dataframe(filtered_df, use_container_width=True)

            # Export button
            csv_export = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV of Issued Notices", csv_export, file_name="issued_notices.csv")

    except Exception as e:
        st.error(f"❌ Could not load issued notices: {e}")


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

        with st.expander("❌ Skipped Restaurants (Notice Not Sent)", expanded=False):
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

        with st.expander("✅ Approved Restaurants (Send Notice)", expanded=False):
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

    # Use the filtered and officer-scoped df directly
    csv_data = df_all.copy()

    if officer_id:
        if st.button("📤 Download Your Assigned Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, f"restaurants_officer_{officer_id}.csv", "text/csv")
    else:
        if st.button("📤 Download All Restaurants (CSV)"):
            csv = csv_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "all_restaurants.csv", "text/csv")

    # --- Officer Activity Log ---
    with st.expander("🗂️ View Your Activity Log", expanded=False):
        try:
            logs = supabase.table("activity_log").select("*").eq("officer_email", user_email).order("timestamp", desc=True).execute().data
            if not logs:
                st.info("No activity recorded yet.")
            else:
                log_df = pd.DataFrame(logs)
                log_df["timestamp"] = pd.to_datetime(log_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
                log_df = log_df.rename(columns={
                    "timestamp": "Date",
                    "action": "Action",
                    "restaurant_id": "Restaurant",
                    "result": "Result"
                })
                st.dataframe(log_df[["Date", "Action", "Restaurant", "Result"]], use_container_width=True)
        except Exception as e:
            st.error(f"❌ Failed to load activity log: {e}")


