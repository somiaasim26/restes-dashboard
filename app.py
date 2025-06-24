# -------------------- Imports --------------------
import streamlit as st
import pandas as pd
from supabase import create_client
import io
from fpdf import FPDF
from datetime import datetime

# -------------------- Page Config & Styling --------------------
st.set_page_config(page_title="PRA Restaurant Dashboard", layout="wide")

st.markdown("""
<style>
body { background-color: #fcfbf5; }
.block-container { padding: 2rem 3rem; }
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
</style>
""", unsafe_allow_html=True)

# -------------------- Auth Setup --------------------
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

# -------------------- Supabase Client --------------------
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Helper for images
def get_supabase_image_url(filename):
    return f"{url}/storage/v1/object/public/restaurant-images/{filename}"

# -------------------- Sidebar Navigation --------------------
st.sidebar.title("📁 PRA-System")
user_email = st.session_state.get("email")

if user_email in special_access_users:
    allowed_sections = ["Current Stats / KPI", "Restaurant Profile"]
else:
    allowed_sections = [
        "Current Stats / KPI",
        "Data Browser",
        "Survey Search",
        "Change Log",
        "Submit Form",
        "Restaurant Profile"
    ]
##############
section = st.sidebar.radio("Navigation", allowed_sections)

# -------------------- Load Tables from Supabase --------------------
@st.cache_data
def load_table(table_name):
    data = supabase.table(table_name).select("*").execute().data
    return pd.DataFrame(data)

# Tables you want:
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "officer_compliance_updates": "Officer Updates",
    "notice_followup_tracking": "Notice Followup Tracking",
    "surveydata_treatmentgroup": "Survey Data",
    "restaurant_images": "Restaurant Images",
    "officer_comments": "Officer Comments",
}

# Load them into a dict
dfs = {label: load_table(name) for name, label in tables.items()}
# -------------------- Welcome Page --------------------
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
                
                progress_bar.progress(i)
         
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# -------------------- KPI Section --------------------
if section == "Current Stats / KPI":
    st.title("📊 System KPI (Supabase)")

    treated_df = dfs["Treated Restaurants"]
    notices_df = dfs["Notice Followup Tracking"]

    st.metric("Total Restaurants", len(treated_df))

    if not notices_df.empty and "delivery_status" in notices_df.columns:
        returned = notices_df[notices_df["delivery_status"].str.lower() == "returned"].shape[0]
        st.metric("Returned Notices", returned)

    # By officer breakdown:
    officer_ids = treated_df["officer_id"].dropna().unique()
    for oid in sorted(officer_ids):
        off_df = treated_df[treated_df["officer_id"] == oid]
        with st.expander(f"👮 Officer ID: {oid} — Restaurants: {len(off_df)}"):
            st.dataframe(off_df[["id", "restaurant_name", "restaurant_address"]])
# -------------------- Data Browser --------------------
elif section == "Data Browser":
    st.header("📂 Explore Database Tables")
    group = st.radio("Choose Dataset", ["Core Tables", "Survey Tables"], horizontal=True)

    if group == "Core Tables":
        core_labels = [v for k, v in tables.items() if "treated" in k or "officer" in k or "pra_" in k or "notice" in k]
        selected_label = st.selectbox("Select Core Table", core_labels)
        df = dfs[selected_label]

        if not df.empty:
            col = st.radio("Search by", ["id", "restaurant_name"], horizontal=True)
            if col in df.columns:
                val = st.selectbox("Search Value", sorted(df[col].astype(str).dropna().unique()))
                st.dataframe(df[df[col].astype(str) == val])
            else:
                st.dataframe(df)
        else:
            st.warning("Table is empty.")

    else:
        survey_labels = [v for k, v in tables.items() if k.startswith("s1") or k.startswith("s2")]
        selected_label = st.selectbox("Select Survey Table", survey_labels)
        df = dfs[selected_label]

        if not df.empty:
            col = st.selectbox("Select Column to Filter", df.columns)
            vals = df[col].dropna().astype(str).unique()
            selected = st.multiselect("Filter Values", sorted(vals))
            if selected:
                df = df[df[col].astype(str).isin(selected)]
            st.dataframe(df)
        else:
            st.warning("Survey table is empty.")

# -------------------- Survey Search --------------------
elif section == "Survey Search":
    st.header("🔍 Search Survey Records")
    ids = pd.concat([
        dfs['Survey 1 - P1']['id'], dfs['Survey 2 - P1']['id']
    ]).astype(str).unique()
    names = pd.concat([
        dfs['Survey 1 - P1']['restaurant_name'],
        dfs['Survey 2 - P1']['restaurant_name']
    ]).dropna().unique()

    mode = st.radio("Search by", ["ID", "Restaurant Name"], horizontal=True)
    choice = st.selectbox("Search Value", sorted(ids if mode == "ID" else names))
    for label, df in dfs.items():
        if mode == "ID" and 'id' in df.columns:
            match = df[df['id'].astype(str) == choice]
        elif mode == "Restaurant Name" and 'restaurant_name' in df.columns:
            match = df[df['restaurant_name'] == choice]
        else:
            match = pd.DataFrame()
        if not match.empty:
            with st.expander(f"{label}"):
                st.dataframe(match)

# -------------------- Change Log --------------------
elif section == "Change Log":
    st.header("🕓 Change History Log")
    try:
        logs = dfs["PRA System"]  # assuming logs stored here
        if not logs.empty:
            st.dataframe(logs.sort_values("modified_at", ascending=False).head(200))
        else:
            st.info("No change logs found.")
    except Exception as e:
        st.warning(f"⚠️ Could not load log: {e}")
# -------------------- Restaurant Profile --------------------
elif section == "Restaurant Profile":
    st.title("📋 Restaurant Summary Profile")

    treated = dfs["Treated Restaurants"]
    survey = dfs["Survey Data"]

    registered_df = treated[treated["compliance_status"] == "Registered"]
    unregistered_df = treated[treated["compliance_status"] != "Registered"]
    filers_df = treated[treated["ntn"].notna() & (treated["ntn"].astype(str).str.strip() != "")]

    ac_df = survey[survey.get("air_conditioner") == "Yes"] if "air_conditioner" in survey.columns else pd.DataFrame()
    card_df = survey[survey.get("credit_debit_card_acceptance") == "Yes"] if "credit_debit_card_acceptance" in survey.columns else pd.DataFrame()
    foodcourt_df = survey[survey.get("food_court") == "Yes"] if "food_court" in survey.columns else pd.DataFrame()

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

    def join_survey_flags(flag_df, base_df):
        if flag_df.empty: return pd.DataFrame()
        return flag_df.merge(base_df[["id", "restaurant_name", "restaurant_address"]], on="id", how="left")

    ac_final = join_survey_flags(ac_df, treated)
    card_final = join_survey_flags(card_df, treated)
    foodcourt_final = join_survey_flags(foodcourt_df, treated)

    col4, col5, col6 = st.columns(3)
    with col4:
        with st.expander(f"❄ AC Present ({len(ac_final)})"):
            st.dataframe(ac_final if not ac_final.empty else pd.DataFrame({"Info": ["No data"]}))
    with col5:
        with st.expander(f"💳 Accept Card ({len(card_final)})"):
            st.dataframe(card_final if not card_final.empty else pd.DataFrame({"Info": ["No data"]}))
    with col6:
        with st.expander(f"🏢 In Food Court ({len(foodcourt_final)})"):
            st.dataframe(foodcourt_final if not foodcourt_final.empty else pd.DataFrame({"Info": ["No data"]}))

    # === Single Profile ===
    treated["label"] = treated["id"].astype(str) + " - " + treated["restaurant_name"]
    selected = st.selectbox("Search by ID or Name", treated["label"])
    selected_id = selected.split(" - ")[0]
    selected_name = selected.split(" - ")[1]

    st.subheader(f"🏪 {selected_name}")

    # === Images ===
    st.markdown("### 🖼️ Restaurant Images")
    imgs = dfs["Restaurant Images"]
    imgs = imgs[imgs["restaurant_id"].astype(str) == selected_id]

    image_types = ["front", "menu", "receipt"]
    cols = st.columns(3)
    for i, img_type in enumerate(image_types):
        subset = imgs[imgs["image_type"] == img_type]
        if not subset.empty:
            url = get_supabase_image_url(subset.iloc[0]["image_path"])
            cols[i].image(url, caption=f"{img_type.title()} Image")
        else:
            cols[i].info(f"No {img_type} image.")

    # === Basic Info ===
    st.markdown("### 🗃️ Basic Info")
    info_row = treated[treated["id"].astype(str) == selected_id]
    if not info_row.empty:
        fields = ['restaurant_name', 'restaurant_address', 'compliance_status', 'officer_id', 'ntn']
        info_df = info_row[fields].T.reset_index()
        info_df.columns = ["Field", "Value"]
        st.table(info_df)
    else:
        st.info("No info found.")

    # === Survey Info ===
    st.markdown("### 🏢 Survey Info")
    survey_row = survey[survey["id"].astype(str) == selected_id]
    if not survey_row.empty:
        row = survey_row.iloc[0]
        col1, col2 = st.columns(2)
        for i, col in enumerate(row.index):
            if col != "id" and pd.notna(row[col]) and str(row[col]).strip():
                label = col.replace("_", " ").capitalize()
                val = row[col]
                box = f"""
                <div style='background:#f9f9f9; border:1px solid #ddd; border-radius:5px; padding:10px; margin:5px;'>
                <strong>{label}:</strong> {val}
                </div>
                """
                (col1 if i % 2 == 0 else col2).markdown(box, unsafe_allow_html=True)

    # === Comments ===
    st.markdown("### 📝 Officer Comments")
    comments = dfs["Officer Comments"]
    comments = comments[comments["restaurant_id"].astype(str) == selected_id]
    if not comments.empty:
        st.dataframe(comments[["officer_email", "comment", "timestamp"]])
    with st.form("Add Comment"):
        c = st.text_area("Add comment:")
        if st.form_submit_button("Submit"):
            supabase.table("officer_comments").insert({
                "restaurant_id": selected_id,
                "officer_email": user_email,
                "comment": c,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            st.success("Comment added — refresh to view.")
