import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import os
import io
from fpdf import FPDF
from sqlalchemy.sql import text
from datetime import datetime



# --- Page Setup ---
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

# --- Dark Mode Styling ---
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
        .survey-header {
        font-size: 1.1rem;
        background-color: #f8f9fa;
        padding: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        font-weight: 600;
        color: #1f2937;
    }
    .survey-entry {
        padding: 0.3rem 0.5rem;
        border-bottom: 1px solid #ddd;
    }
    .survey-entry strong {
        color: #1f2937;
    }


    </style>
""", unsafe_allow_html=True)


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

# --- Welcome Page ---
if st.session_state.get("section") == "Welcome":
    st.markdown("""
        <style>
        .title-fade {
            font-size: 50px;
            font-weight: 700;
            color: #1f2937;
            animation: fadeIn 1s ease-in-out;
            text-align: center;
            margin-bottom: 0px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='title-fade'>Restaurant Enforcement System Database</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👨‍🔬 Principal Investigators")
        st.markdown("- Michael Carlos Best\n- Anders Jensen\n- Adnan Khan\n- Sher Afghan Asad")
    with col2:
        st.markdown("### 🔬 Research Assistant Team")
        st.markdown("- Hamza Afsar\n- Amna\n- Somia\n- Shezreen Shah")

    if st.button("Enter Dashboard"):
        with st.spinner("Loading the PRA Dashboard..."):
            st.balloons()
            progress_bar = st.progress(0)
            for i in range(1, 101):
                time.sleep(0.015)  # slower, smoother
                progress_bar.progress(i)
            time.sleep(1)  # pause after loading finishes
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()


# --- DB Setup ---
# Build the connection string from Streamlit secrets
engine = create_engine(
    f"postgresql://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@"
    f"{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/"
    f"{st.secrets['postgres']['database']}"
)
#st.title("🔍 Debug: Database Check")

#try:
#    test_df = pd.read_sql("SELECT * FROM treated_restaurant_data", engine)
 #   st.success("✅ Connected to DB and retrieved records.")
 #   st.dataframe(test_df)
#except Exception as e:
 #   st.error(f"❌ Error pulling data: {e}")

def get_supabase_image_url(filename):
    base_url = "https://jrvvslujqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/"
    return f"{base_url}{filename}"


# --- Sidebar Navigation ---
st.sidebar.title("📁 PRA-System")
user_email = st.session_state.get("email")

# Check if this user has restricted access
if user_email in special_access_users:
    allowed_sections = ["Current Stats / KPI", "Restaurant Profile"]
else:
    allowed_sections = [
        "Current Stats / KPI", "Data Browser", "Survey Search", 
        "Change Log", "Submit Form", "Restaurant Profile", "Return Summary"
    ]

section = st.sidebar.radio("Navigation", allowed_sections)



tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "officer_compliance_updates": "Officer Updates",
    "pra_system_updates": "PRA System",
    "restaurant_return_data": "Return Data",  # ✅ ADD THIS
    "surveydata_treatmentgroup": "Survey Data",
    "s1_p1": "Survey 1 - P1", "s1_p2": "Survey 1 - P2", "s1_sec2": "Survey 1 - Sec2", "s1_sec3": "Survey 1 - Sec3",
    "s2_p1": "Survey 2 - P1", "s2_p2": "Survey 2 - P2", "s2_sec2": "Survey 2 - Sec2", "s2_sec3": "Survey 2 - Sec3",
    "notice_followup_tracking": "Notice Followup Tracking"

}

dataframes = {}
for sql_name, label in tables.items():
    try:
        df = pd.read_sql(f"SELECT * FROM {sql_name}", engine)
        dataframes[label] = df
    except Exception as e:
        st.warning(f"⚠ Failed to load `{sql_name}`: {e}")



# --- Current Stats / KPI (Special User Layout) ---
if section == "Current Stats / KPI":
    is_special_user = user_email in special_access_users

    if is_special_user:
        st.title("📊 PRA System Status")

        # Load required tables
        treated_df = dataframes["Treated Restaurants"]
        tracking_df = dataframes.get("Enforcement Tracking", pd.DataFrame())

        # Count
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

        officer_ids = treated_df["officer_id"].dropna().unique()
        officer_ids = sorted([int(o) for o in officer_ids if str(o).isdigit()])

        for oid in officer_ids:
            officer_df = treated_df[treated_df["officer_id"] == str(oid)]

            with st.expander(f"👮 Officer ID: {oid} — Assigned Restaurants: {len(officer_df)}"):
                st.dataframe(officer_df[["id", "restaurant_name", "restaurant_address"]])

            if not tracking_df.empty and "restaurant_id" in tracking_df.columns:
                try:
                    tracking_data = tracking_df.merge(
                        treated_df[["id", "officer_id"]],
                        left_on="restaurant_id", right_on="id", how="inner"
                    )
                    officer_tracking = tracking_data[tracking_data["officer_id"] == str(oid)]

                    with st.expander(f"📦 Enforcement Tracking — Officer {oid}"):
                        if not officer_tracking.empty:
                            st.dataframe(officer_tracking[[
                                "restaurant_id", "courier_status", "notice_status", "filing_status", "updated_at"
                            ]])
                        else:
                            st.info("No enforcement tracking records found.")
                except Exception as e:
                    st.warning(f"⚠️ Error loading tracking data: {e}")
    #else:
       # st.warning("You do not have permission to view this page.")

    # --- PI View (Slim) ---
    st.markdown("## 📋 Notice Follow-up & Latest Updates")

    try:
        df = dataframes["Notice Followup Tracking"]
        treated_df = dataframes["Treated Restaurants"]

        df["restaurant_id"] = df["restaurant_id"].astype(str)
        treated_df["id"] = treated_df["id"].astype(str)
        merged = pd.merge(df, treated_df[['id', 'officer_id']], left_on="restaurant_id", right_on="id", how="left")
        merged.fillna("", inplace=True)

        officer_ids = sorted(merged["officer_id"].dropna().unique())

        for oid in officer_ids:
            off_df = merged[merged["officer_id"] == oid]
            total = len(off_df)
            returned = (off_df["delivery_status"].str.lower() == "returned").sum()
            corrected_names = (off_df["correct_name"].str.strip() != "").sum()
            corrected_address = (off_df["correct_address"].str.strip() != "").sum()

            with st.expander(f"🕵️ Officer ID {oid} — Restaurants: {total} — Notices Returned: {returned}", expanded=False):
                col1, col2 = st.columns(2)
                col1.metric("📬 Notices Returned", returned)
                col2.metric("📛 Corrected Names", corrected_names)

                st.markdown("### 🗺️ Restaurants to Re-send Notice")
                # Only keep restaurants with returned notice AND corrected info
                resend_df = off_df[
                    (off_df["delivery_status"].str.lower() == "returned") &
                    (
                        (off_df["correct_name"].fillna("").str.strip() != "") |
                        (off_df["correct_address"].fillna("").str.strip() != "")
                    )
                ]

                if not resend_df.empty:
                    st.dataframe(resend_df[[
                        "restaurant_id", "delivery_status", "correct_address", "correct_name", "contact"
                    ]])
                else:
                    st.info("No returned notices for this officer.")

    except Exception as e:
        st.error(f"❌ Error loading PI View: {e}")

    # --- Filing Status Summary (Grouped Count with Drilldown) ---
    st.markdown("## 🔄 Latest Formality Status")

    try:
        df = dataframes["Notice Followup Tracking"]
        treated_df = dataframes["Treated Restaurants"][["id", "restaurant_name", "restaurant_address", "compliance_status"]]

        df["restaurant_id"] = df["restaurant_id"].astype(str)
        treated_df["id"] = treated_df["id"].astype(str)

        # Merge old and new status
        combined = pd.merge(df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["latest_formality_status"] = combined["latest_formality_status"].fillna("None").str.strip()
        combined["compliance_status"] = combined["compliance_status"].fillna("None").str.strip()

        # Only changed rows
        combined["changed"] = combined["latest_formality_status"].str.lower() != combined["compliance_status"].str.lower()
        changed = combined[combined["changed"]]

        st.markdown(f"### 📦 Status Change Summary — Total Changes: `{len(changed)}`")

        status_groups = changed.groupby("latest_formality_status")

        for status_key, group_df in status_groups:
            # Rename display labels
            display_label = status_key
            if status_key.lower() == "filer":
                display_label = "🟢 Started Filing"
            elif status_key.lower() == "none":
                display_label = "⚪ No Change in Formality"

            with st.expander(f"{display_label} — {len(group_df)}", expanded=False):
                st.dataframe(group_df[[
                    "restaurant_id", "restaurant_name", "restaurant_address", "compliance_status", "latest_formality_status"
                ]].reset_index(drop=True))


    except Exception as e:
        st.error(f"❌ Could not load summary: {e}")

    # --- Filing Status Summary (Compact View) ---
    st.markdown("## 🔄 Filing Status Change Summary")

    try:
        formality_df = dataframes["Notice Followup Tracking"]
        treated_df = dataframes["Treated Restaurants"][["id", "restaurant_name", "restaurant_address", "compliance_status"]]

        formality_df["restaurant_id"] = formality_df["restaurant_id"].astype(str)
        treated_df["id"] = treated_df["id"].astype(str)

        combined = pd.merge(formality_df, treated_df, left_on="restaurant_id", right_on="id", how="left")
        combined["changed"] = combined["compliance_status"].fillna("").str.strip().str.lower() != combined["latest_formality_status"].fillna("").str.strip().str.lower()
        changed = combined[combined["changed"]].copy()

        total_changed = len(changed)
        st.markdown(f"### 🧾 Total Restaurants With Status Changes: <span style='background:#dcfce7;padding:5px 10px;border-radius:5px;font-weight:bold;'>{total_changed}</span>", unsafe_allow_html=True)

        # Optional dropdown to filter or explore
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
        st.error(f"❌ Could not load filing status summary: {e}")

    
#----------------------------------------------------------------------------------------------------------------------------------

# --- Data Browser ---
elif section == "Data Browser":
    st.header("📂 Explore Database Tables")
    group = st.radio("Choose Dataset", ["Core Tables", "Survey Tables"], horizontal=True)

    if group == "Core Tables":
        core_labels = [v for k, v in tables.items() if "treated" in k or "officer" in k or "pra_" in k]
        selected_label = st.selectbox("Select Core Table", core_labels)

        selected_table = [k for k, v in tables.items() if v == selected_label][0]
        df = dataframes[selected_label]

        col = st.radio("Search by", ["id", "restaurant_name"], horizontal=True)
        if col in df.columns:
            val = st.selectbox("Search Value", sorted(df[col].astype(str).dropna().unique()))
            st.dataframe(df[df[col].astype(str) == val])
        else:
            st.dataframe(df)

    else:
        survey_labels = [v for k, v in tables.items() if k.startswith("s1") or k.startswith("s2")]
        selected_label = st.selectbox("Select Survey Table", survey_labels)
        df = dataframes[selected_label]

        col = st.selectbox("Select Column to Filter", df.columns)
        vals = df[col].dropna().astype(str).unique()
        selected = st.multiselect("Filter Values", sorted(vals))
        if selected:
            df = df[df[col].astype(str).isin(selected)]
        st.dataframe(df)


# --- Survey Search ---
elif section == "Survey Search":
    st.header("🔍 Search Survey Records")
    ids = pd.concat([
        dataframes['Survey 1 - P1']['id'], dataframes['Survey 2 - P1']['id']
    ]).astype(str).unique()
    names = pd.concat([
        dataframes['Survey 1 - P1']['restaurant_name'],
        dataframes['Survey 2 - P1']['restaurant_name']
    ]).dropna().unique()

    mode = st.radio("Search by", ["ID", "Restaurant Name"], horizontal=True)
    choice = st.selectbox("Search Value", sorted(ids if mode == "ID" else names))
    for label, df in dataframes.items():
        if mode == "ID" and 'id' in df.columns:
            match = df[df['id'].astype(str) == choice]
        elif mode == "Restaurant Name" and 'restaurant_name' in df.columns:
            match = df[df['restaurant_name'] == choice]
        else:
            match = pd.DataFrame()
        if not match.empty:
            with st.expander(f"{label}"):
                st.dataframe(match)

# --- Change Log ---
elif section == "Change Log":
    st.header("🕓 Change History Log")
    try:
        logs = pd.read_sql("SELECT * FROM column_change_log ORDER BY modified_at DESC LIMIT 200", engine)
        st.dataframe(logs)
    except:
        st.warning("No change logs found.")

# --- Form Link ---
elif section == "Submit Form":
    st.header("📥 Submit a Compliance Update")
    st.markdown("Click below to open the officer form.")
    st.link_button("Open Form in New Tab", "https://restes-dashboard-form.streamlit.app/")
    #st.link_button("Open Form in New Tab", "https://restes-dashboard-form.streamlit.app/")

    
# --- Restaurant Landing Page -----


elif section == "Restaurant Profile":
    st.title("📋 Restaurant Summary Profile")

    st.markdown("### 📊 Monthly Reporting Summary")

    df = dataframes["Treated Restaurants"]
    survey_df = dataframes["Survey Data"]

    # Core flags from Treated
    registered_df = df[df.get("compliance_status") == "Registered"]
    unregistered_df = df[df.get("compliance_status") != "Registered"]
    filers_df = df[df.get("ntn").notna() & (df.get("ntn").astype(str).str.strip() != "")]

    # Extra flags from Survey Data
    ac_df = survey_df[survey_df.get("air_conditioner") == "Yes"] if "air_conditioner" in survey_df.columns else pd.DataFrame()
    card_df = survey_df[survey_df.get("credit_debit_card_acceptance") == "Yes"] if "credit_debit_card_acceptance" in survey_df.columns else pd.DataFrame()
    foodcourt_df = survey_df[survey_df.get("food_court") == "Yes"] if "food_court" in survey_df.columns else pd.DataFrame()

    # Display Grid
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.expander(f"✅ Registered ({len(registered_df)})"):
            st.dataframe(registered_df[["id", "restaurant_name", "restaurant_address"]])

    with col2:
        with st.expander(f"❌ Unregistered ({len(unregistered_df)})"):
            st.dataframe(unregistered_df[["id", "restaurant_name", "restaurant_address"]])

    with col3:
        with st.expander(f"🧾 Filers ({len(filers_df)})"):
            st.dataframe(filers_df[["id", "restaurant_name", "restaurant_address"]])

    # --- Survey flag summaries with restaurant info merge ---
    def join_survey_flags(survey_flag_df, treated_df):
        if survey_flag_df.empty:
            return pd.DataFrame()
        return pd.merge(
            survey_flag_df[["id"]],
            treated_df[["id", "restaurant_name", "restaurant_address"]],
            on="id", how="left"
        )

    ac_df_final = join_survey_flags(ac_df, df)
    card_df_final = join_survey_flags(card_df, df)
    foodcourt_df_final = join_survey_flags(foodcourt_df, df)

    col4, col5, col6 = st.columns(3)

    with col4:
        with st.expander(f"❄ AC Present ({len(ac_df_final)})"):
            if not ac_df_final.empty:
                st.dataframe(ac_df_final)
            else:
                st.info("Missing data.")

    with col5:
        with st.expander(f"💳 Accept Card ({len(card_df_final)})"):
            if not card_df_final.empty:
                st.dataframe(card_df_final)
            else:
                st.info("Missing data.")

    with col6:
        with st.expander(f"🏢 In Food Court ({len(foodcourt_df_final)})"):
            if not foodcourt_df_final.empty:
                st.dataframe(foodcourt_df_final)
            else:
                st.info("Missing data.")



    # --- Select Restaurant ---

    rest_df = dataframes['Treated Restaurants'][["id", "restaurant_name"]].dropna(subset=["id"])
    rest_df['id'] = rest_df['id'].astype(str)
    rest_df['label'] = rest_df['id'] + " - " + rest_df['restaurant_name'].fillna("")
    rest_df = rest_df.sort_values(by="id", key=lambda x: x.str.zfill(10))  # or use the regex option above


    selected_label = st.selectbox("Search by ID or Name", rest_df['label'].tolist())
    selected_id = selected_label.split(" - ")[0]
    selected_name = selected_label.split(" - ")[1]

    restaurant = rest_df[rest_df['id'] == selected_id]
    st.subheader(f"🏪 {selected_name}")

    # --- Image Display ---
    import os

    # Helper to clean filename
    def clean_filename(path):
        return os.path.basename(str(path)).strip().strip('"').strip("'")

    # Helper to build public Supabase URL
    def get_supabase_image_url(filename):
        base_url = "https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/"
        return f"{base_url}{filename}"


    # --- Image Display ---
    st.markdown("### 🖼️  Restaurant Images")
    image_type_map = {"front": "Front Image", "menu": "Menu Image", "receipt": "Receipt Image"}

    try:
            img_df = pd.read_sql(f"""
                SELECT * FROM restaurant_images 
                WHERE restaurant_id = '{selected_id}' 
                ORDER BY 
                    image_type,
                    image_path
            """, engine)

            if not img_df.empty:
                def show_image_slider(img_type, container):
                    imgs = img_df[img_df["image_type"] == img_type]

                    if imgs is None or imgs.empty or len(imgs) == 0:
                        container.info(f"No {image_type_map[img_type]} available.")
                        return

                    # Always safe to proceed from here on
                    if len(imgs) == 1:
                        try:
                            filename = clean_filename(imgs.iloc[0]["image_path"])
                            url = get_supabase_image_url(filename)
                            container.image(url, caption=f"{image_type_map[img_type]} 1")
                        except Exception as e:
                            container.error(f"⚠️ Could not load image. {e}")
                        return

                    # Multiple images
                    if "img_idx" not in st.session_state:
                        st.session_state["img_idx"] = {}
                    if img_type not in st.session_state["img_idx"]:
                        st.session_state["img_idx"][img_type] = 0

                    idx = st.session_state["img_idx"][img_type]

                    try:
                        filename = clean_filename(imgs.iloc[idx]["image_path"])
                        url = get_supabase_image_url(filename)
                        container.image(url, caption=f"{image_type_map[img_type]} {idx+1} of {len(imgs)}")

                        left, right = container.columns([1, 1])
                        with left:
                            if st.button("⬅", key=f"{img_type}_prev") and idx > 0:
                                st.session_state["img_idx"][img_type] -= 1
                        with right:
                            if st.button("➡", key=f"{img_type}_next") and idx < len(imgs) - 1:
                                st.session_state["img_idx"][img_type] += 1

                    except Exception as e:
                        container.error(f"⚠️ Could not load image. {e}")


            img_cols = st.columns(3)
            any_images = False
            for i, img_type in enumerate(["front", "menu", "receipt"]):
                if not img_df[img_df["image_type"] == img_type].empty:
                    any_images = True
                    with img_cols[i]:
                        st.markdown(f"#### 📸 {image_type_map[img_type]}")
                        show_image_slider(img_type, st.container())

            if not any_images:
                st.warning("No images found for this restaurant.")

    except Exception as e:
        st.warning(f"Could not load images. Error: {e}")

    # --- Basic Info ---
    st.markdown("### 🗃️ Basic Info")
    treated_df = dataframes["Treated Restaurants"]

    if not treated_df.empty:
        restaurant_row = treated_df[treated_df['id'].astype(str) == selected_id]
        if not restaurant_row.empty:
            display_fields = ['restaurant_name', 'restaurant_address', 'compliance_status', 'officer_id', 'ntn', 'latitude', 'longitude', 'id']
            info_df = restaurant_row[display_fields].T.reset_index()
            info_df.columns = ['Field', 'Value']
            st.table(info_df)
        else:
            st.info("No basic info found for this restaurant.")
    else:
        st.warning("Treated restaurant data table is empty or not accessible.")

    # --- Survey Answers ---
    st.markdown("### 🏢 Restaurant Information")
    survey_df = dataframes["Survey Data"]

    if not survey_df.empty:
        survey_row = survey_df[survey_df["id"].astype(str) == selected_id]
        if not survey_row.empty:
            row = survey_row.iloc[0]
            # ... continue with the label_map and rendering as you already have ...
        else:
            st.info("No survey data found for this restaurant.")
    else:
        st.warning("Survey table is empty or not connected.")
        


    if not survey_df.empty:
        survey_row = survey_df[survey_df["id"].astype(str) == selected_id]
        if not survey_row.empty:
            row = survey_row.iloc[0]
            label_map = {
                "ntn": "🔘 NTN",
                "pntn": "🔘 PNTN",
                "strn": "🔘 STRN",
                "restaurant_type": "🍱 Restaurant Type",
                "cuisine": "🧑‍🍳 Cuisine",
                "number_of_customers": "🧑‍🤝‍🧑 Customers",
                "number_of_chairs": "🪑 Chairs",
                "number_of_floors": "🏢 Floors",
                "number_of_tables": "🛎️ Tables",
                "seating_arrangement": "🧍‍🪑 Seating Arrangement",
                "air_conditioner": "❄ Air Conditioning",
                "credit_debit_card_acceptance": "💳 Card Acceptance",
                "food_court": "🏬 Located in Food Court",
                "gst": "💸 GST Amount",
                "pre_tax_price": "💰 Pre-Tax Price",
                "post_tax_price": "💰 Post-Tax Price",
                "price_paid": "💸 Price Paid"
            }

            st.markdown("---")
            col1, col2 = st.columns(2)

            fields = [col for col in row.index if col != "id" and pd.notna(row[col]) and str(row[col]).strip() != ""]
            for i, col in enumerate(fields):
                label = label_map.get(col.lower(), col.replace("_", " ").capitalize())
                value = row[col]
                html_block = f"""
                    <div style='
                        background-color: #f9f9f9;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px 15px;
                        margin-bottom: 10px;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        max-width: 100%;
                        white-space: normal;
                    '>
                        <strong>{label}</strong><br>
                        <strong style='color:#333; word-break: break-word;'>{value}</strong>
                    </div>
                """

                (col1 if i % 2 == 0 else col2).markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("No survey data found for this restaurant.")
    else:
        st.warning("Survey table is empty or not connected.")
    

    # --- Officer Comment Section ---
    st.markdown("### 📝 Officer Comment (Why Notice Not Sent)")

    # Show previous comments for this restaurant
    existing_comments = pd.read_sql(f"""
        SELECT officer_email, comment, timestamp 
        FROM officer_comments 
        WHERE restaurant_id = '{selected_id}' 
        ORDER BY timestamp DESC
    """, engine)

    if not existing_comments.empty:
        st.markdown("#### 🗂 Previous Comments")
        st.dataframe(existing_comments)

    # Comment submission form
    with st.form(key="comment_form"):
        officer_comment = st.text_area("Enter your comment here:")
        submit_comment = st.form_submit_button("💬 Submit Comment")

        if submit_comment and officer_comment.strip():
            query = text("""
                INSERT INTO officer_comments (restaurant_id, officer_email, comment, timestamp)
                VALUES (:restaurant_id, :officer_email, :comment, :timestamp)
            """)
            values = {
                "restaurant_id": selected_id,
                "officer_email": st.session_state["email"],
                "comment": officer_comment.strip(),
                "timestamp": datetime.utcnow()
            }
            with engine.begin() as conn:
                conn.execute(query, values)
            st.success("✅ Comment submitted.")
            st.experimental_rerun()


    # ========== EXPORT SECTION ==========
    export_col1, export_col2 = st.columns(2)

    with export_col1:
        if st.button("📥 Download Profile as PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Add restaurant basic info
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, f"Restaurant Summary: {selected_name}", ln=True)
            pdf.ln(5)

            pdf.set_font("Arial", size=12)
            for i, row in info_df.iterrows():
                pdf.multi_cell(0, 10, f"{row['Field']}: {row['Value']}")

            pdf.ln(5)

            # Survey Info if available
            if not survey_df.empty:
                survey_row = survey_df[survey_df["id"].astype(str) == selected_id]
                if not survey_row.empty:
                    pdf.set_font("Arial", 'B', 13)
                    pdf.cell(200, 10, txt="Survey Information", ln=True)
                    pdf.ln(3)

                    row = survey_row.iloc[0]
                    for col in row.index:
                        val = str(row[col])
                        if val and col != "id":
                            pdf.set_font("Arial", size=12)
                            pdf.multi_cell(0, 10, f"{col}: {val}")

            # Export
            pdf_output = io.BytesIO()
            pdf_output.write(pdf.output(dest='S').encode('latin1'))
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_output.getvalue(),
                file_name=f"{selected_name}_profile.pdf",
                mime="application/pdf"
            )

    with export_col2:
        if st.button("📊 Download Profile as CSV"):
            full_csv_df = info_df.copy()
            if not survey_df.empty:
                survey_row = survey_df[survey_df["id"].astype(str) == selected_id]
                if not survey_row.empty:
                    survey_info = pd.DataFrame(survey_row.T).reset_index()
                    survey_info.columns = ['Field', 'Value']
                    full_csv_df = pd.concat([full_csv_df, survey_info], ignore_index=True)

            csv = full_csv_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"{selected_name}_profile.csv",
                mime="text/csv"
            )


# -- Return Data

elif section == "Return Summary":
    st.title("📊 Return Summary Viewer")

    treated_df = dataframes["Treated Restaurants"]
    return_df = dataframes["Return Data"] 
    treated_df = dataframes["treated_restaurant_data"]
    return_df = dataframes["restaurant_return_data"]  


    return_df.columns = return_df.columns.str.strip().str.upper().str.replace(" ", "_")

    if treated_df.empty or return_df.empty:
        st.warning("One or more required tables are empty.")
    else:
        treated_df["NTN"] = treated_df["ntn"].astype(str)

        # --- Filter by Year and Month First ---
        col1, col2 = st.columns(2)
        all_years = sorted(return_df["TAX_PERIOD_YEAR"].dropna().unique(), reverse=True)
        all_months = sorted(return_df["TAX_PERIOD_MONTH"].dropna().unique(), reverse=True)

        selected_year = col1.selectbox("📅 Filter by Tax YEAR", all_years)
        selected_month = col2.selectbox("📅 Filter by Tax MONTH", all_months)

        filtered_df = return_df[
            (return_df["TAX_PERIOD_YEAR"] == selected_year) &
            (return_df["TAX_PERIOD_MONTH"] == selected_month)
        ]

        if filtered_df.empty:
            st.info("No return records found for selected date.")
        else:
            st.markdown("### 📋 All Returns for Selected Month")
            st.dataframe(filtered_df.style.set_properties(**{'font-size': '14px'}))

            # --- Search by NTN within that Month ---
            ntn_list = sorted(filtered_df["NTN"].dropna().unique())
            selected_ntn = st.selectbox("🔍 Search by NTN (filtered)", ntn_list)

            # Step 1: Get all return entries for this NTN
            ntn_data = filtered_df[filtered_df["NTN"] == selected_ntn]

            if not ntn_data.empty:
                # Step 2: Get matching restaurant record
                matched_rest = treated_df[treated_df["NTN"] == selected_ntn]

                if not matched_rest.empty:
                    rid = matched_rest["id"].values[0]
                    rname = matched_rest["restaurant_name"].values[0]
                    st.markdown(f"### 🏪 Restaurant: **{rname}**  (ID: `{rid}`)")

                    # Show basic treated_restaurant_data
                    st.markdown("#### 🧾 Restaurant Profile (from TreatedRestaurants)")
                    st.dataframe(matched_rest.T.rename(columns={0: 'Value'}))

                else:
                    st.warning("No restaurant matched in Treated Restaurants table.")

                # Step 3: Filing Status (latest return)
                most_recent = return_df[return_df["NTN"] == selected_ntn].sort_values(
                    ["TAX_PERIOD_YEAR", "TAX_PERIOD_MONTH"], ascending=False
                ).head(1)

                current = f"{selected_year}-{selected_month:02}"
                last_filed = f"{most_recent['TAX_PERIOD_YEAR'].values[0]}-{int(most_recent['TAX_PERIOD_MONTH'].values[0]):02}"

                compliant = (current == last_filed)

                color = "green" if compliant else "red"
                status = "🟢 Filer (Up-to-date)" if compliant else "🔴 Late Filer (No return for current month)"

                st.markdown(
                    f"<div style='border:1px solid {color}; padding: 10px; border-radius:5px; background-color:#f7f7f7;'><b>Status:</b> <span style='color:{color}; font-weight:bold;'>{status}</span><br><b>Most Recent Return:</b> {last_filed}</div>",
                    unsafe_allow_html=True
                )

                # Step 4: Display the return data for that NTN
                st.markdown("### 📊 Return Records for this NTN (Selected Month)")
                st.dataframe(ntn_data.style.set_properties(**{'font-size': '14px'}))

            else:
                st.warning("No return record found for this NTN in the selected month.")


























