# === PRA DASHBOARD (STREAMLINED) ===
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config("📊 PRA Restaurant Dashboard", layout="wide")
st.markdown("""
    <style>
    body { background: #fcfbf5; }
    .block-container { padding: 2rem 3rem; }
    </style>
""", unsafe_allow_html=True)

# === DATABASE CONNECTION ===
engine = create_engine(
    f"postgresql://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@"
    f"{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/{st.secrets['postgres']['database']}"
)

# === SIMPLE AUTH ===
APPROVED_USERS = {
    "somiaasim26@gmail.com": "123PRA**!",
    "hamzaafsar94@gmail.com": "123PRA**!",
    "mcb2270@columbia.edu": "123PRA**!",
    "asad.sherafghan@gmail.com": "123PRA**!",
    "adnanqk@gmail.com": "123PRA**!",
    "anders_jensen@hks.harvard.edu": "123PRA**!",
    "amnanoorfatimalse@gmail.com": "123PRA**!",
    "s.s.shezreenshah@gmail.com": "123PRA**!"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 PRA Dashboard Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if APPROVED_USERS.get(email) == password:
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# === CACHED DATA ===
@st.cache_data(ttl=600)
def load_table(table):
    return pd.read_sql(f"SELECT * FROM {table}", engine)

treated = load_table("treated_restaurant_data")
officer_updates = load_table("officer_compliance_updates")
survey = load_table("surveydata_treatmentgroup")
returns = load_table("restaurant_return_data")

# === SIDEBAR ===
section = st.sidebar.radio("📁 Navigate", [
    "KPIs & Stats",
    "Restaurant Profile",
    "Return Summary"
])

# === 1️⃣ KPIs ===
if section == "KPIs & Stats":
    st.header("📊 PRA Restaurant KPIs")
    col1, col2, col3 = st.columns(3)

    total = len(treated)
    registered = len(treated[treated["compliance_status"] == "Registered"])
    unregistered = total - registered

    col1.metric("Total Restaurants", total)
    col2.metric("Registered", registered)
    col3.metric("Unregistered", unregistered)

    st.markdown("### 📈 Latest Officer Updates")
    st.dataframe(officer_updates.tail(50))

# === 2️⃣ RESTAURANT PROFILE ===
elif section == "Restaurant Profile":
    st.header("🏪 Restaurant Profile")

    # Dropdown: ID - Name
    options = treated[["id", "restaurant_name"]].dropna().astype(str)
    options["label"] = options["id"] + " — " + options["restaurant_name"]
    selected_label = st.selectbox("Select Restaurant", options["label"])
    selected_id = selected_label.split(" — ")[0]

    # Basic Info
    basic = treated[treated["id"] == selected_id]
    st.markdown("### 🗂️ Basic Information")
    st.table(basic.T.rename(columns={basic.index[0]: "Value"}))

    # Survey Info
    s_row = survey[survey["id"] == selected_id]
    if not s_row.empty:
        st.markdown("### 📝 Survey Data")
        st.table(s_row.T.rename(columns={s_row.index[0]: "Value"}))
    else:
        st.info("No survey data for this restaurant.")

# === 3️⃣ RETURN SUMMARY ===
elif section == "Return Summary":
    st.header("📄 Return Summary")

    years = sorted(returns["TAX_PERIOD_YEAR"].dropna().unique(), reverse=True)
    months = sorted(returns["TAX_PERIOD_MONTH"].dropna().unique(), reverse=True)
    col1, col2 = st.columns(2)
    selected_year = col1.selectbox("Year", years)
    selected_month = col2.selectbox("Month", months)

    filtered = returns[
        (returns["TAX_PERIOD_YEAR"] == selected_year) &
        (returns["TAX_PERIOD_MONTH"] == selected_month)
    ]

    st.markdown(f"## 📊 Returns for {selected_month}/{selected_year}")
    st.dataframe(filtered)

# === END ===
