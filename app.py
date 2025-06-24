# Dashboard_New.py
import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- CONFIG ---
st.set_page_config(page_title="PRA Dashboard", layout="wide")

# --- SUPABASE CLIENT ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# --- CACHED LOAD ---
@st.cache_data
def load_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

# --- AUTH ---
approved_users = {
    "somiaasim26@gmail.com": "123PRA**!"
    # Add more if needed
}

special_access_users = {
    "salmanzafars@gmail.com": "123PRA**!"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 PRA Dashboard Login")
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

# --- SIDEBAR ---
user_email = st.session_state["email"]
if user_email in special_access_users:
    allowed_sections = ["Current Stats / KPI"]
else:
    allowed_sections = [
        "Current Stats / KPI", "Data Browser", "Restaurant Profile"
    ]

section = st.sidebar.radio("📂 Navigate", allowed_sections)

# --- LOAD TABLES ---
tables = {
    "treated_restaurant_data": "Treated Restaurants",
    "officer_compliance_updates": "Officer Updates",
    "pra_system_updates": "PRA System",
    "restaurant_images": "Restaurant Images",
    "restaurant_return_data": "Return Data",
    "surveydata_treatmentgroup": "Survey Data",
}

dfs = {}
for key in tables:
    try:
        dfs[key] = load_table(key)
    except Exception as e:
        st.warning(f"Could not load {key}: {e}")

# --- WELCOME ---
if st.session_state["section"] == "Welcome":
    st.title("👋 Welcome to PRA Dashboard")
    if st.button("Enter Dashboard"):
        st.session_state["section"] = "Current Stats / KPI"
        st.rerun()
    st.stop()

# --- CURRENT STATS ---
if section == "Current Stats / KPI":
    st.title("📊 PRA System Status")
    treated_df = dfs["treated_restaurant_data"]

    st.metric("Total Restaurants", len(treated_df))

    st.dataframe(
        treated_df[["id", "restaurant_name", "restaurant_address"]]
    )

# --- DATA BROWSER ---
elif section == "Data Browser":
    st.title("📂 Browse Tables")
    table = st.selectbox("Select Table", list(tables.values()))
    table_key = [k for k, v in tables.items() if v == table][0]
    st.dataframe(dfs[table_key])

#
# --- RESTAURANT PROFILE ---
elif section == "Restaurant Profile":
    st.title("🏪 Restaurant Profile")
    df = dfs["treated_restaurant_data"]
    df['label'] = df['id'].astype(str) + " - " + df['restaurant_name']
    selected = st.selectbox("Select Restaurant", df['label'])
    selected_id = selected.split(" - ")[0]

    row = df[df['id'].astype(str) == selected_id].iloc[0]
    st.write(f"**Name:** {row['restaurant_name']}")
    st.write(f"**Address:** {row['restaurant_address']}")
    st.write(f"**Status:** {row['compliance_status']}")

    # Images
    img_df = dfs["restaurant_images"]
    imgs = img_df[img_df['restaurant_id'].astype(str) == selected_id]
    for _, img in imgs.iterrows():
        st.image(f"https://ivresluijqsbmylqwolz.supabase.co/storage/v1/object/public/restaurant-images/{img['image_path']}")

