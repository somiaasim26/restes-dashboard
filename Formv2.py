# --- 📦 Required Libraries ---
import streamlit as st
import datetime
import pandas as pd
from sqlalchemy import create_engine

# --- 🔧 Page Configuration ---
st.set_page_config(page_title="PRA Compliance Interface", layout="centered")

# --- 🛠️ Database Connection ---
from sqlalchemy import create_engine
import streamlit as st

engine = create_engine(
    f"postgresql://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@"
    f"{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/"
    f"{st.secrets['postgres']['database']}"
)


# --- 📑 Sidebar Navigation ---
page = st.sidebar.radio("Select Page", ["Officer Updates", "PRA System Data"])

# --- 🍽️ Utility Function ---
def get_restaurant_info(rest_id):
    query = f"SELECT * FROM treated_restaurant_data WHERE ID = '{rest_id}'"
    df = pd.read_sql(query, engine)
    return df.iloc[0] if not df.empty else None

# ------------------- PAGE 1: OFFICER UPDATES -------------------
if page == "Officer Updates":
    st.title("📝 Enforcement Officer Weekly Update Form")

    # Section 1 – Officer Info
    st.header("1. Enforcement Officer Information")
    officer_name = st.text_input("Enforcement Officer Name")
    officer_id = st.text_input("Enforcement Officer ID")
    interview_date = st.date_input("Interview Date", datetime.date.today())
    interview_method = st.radio("Interview Method", ["Call", "In-Person", "Other (Specify)"])

    # Section 2 – Restaurant Info
    st.header("2. Restaurant Information")
    restaurant_df = pd.read_sql("SELECT id, restaurant_name FROM treated_restaurant_data", engine)

    search_mode = st.radio("Search Restaurant By", ["ID", "Name"], horizontal=True)

    if search_mode == "ID":
        sorted_ids = sorted(restaurant_df["id"].unique())
        selected_id = st.selectbox("Select Restaurant ID", sorted_ids)
        restaurant_id = str(selected_id)
        selected_name = restaurant_df.loc[restaurant_df["id"] == selected_id, "restaurant_name"].values[0]
    else:
        sorted_names = sorted(restaurant_df["restaurant_name"].unique())
        selected_name = st.selectbox("Select Restaurant Name", sorted_names)
        restaurant_id = str(restaurant_df.loc[restaurant_df["restaurant_name"] == selected_name, "id"].values[0])

    st.markdown(f"**Selected Restaurant:** {selected_name} (ID: {restaurant_id})")

    restaurant_info = get_restaurant_info(restaurant_id)

    st.markdown(f"**Restaurant Name:** {restaurant_info['restaurant_name']}")
    st.markdown(f"**Address:** {restaurant_info['restaurant_address']}")
    st.markdown(f"**Latitude:** {restaurant_info['latitude']}")
    st.markdown(f"**Longitude:** {restaurant_info['longitude']}")

    # Section 3 – Formality & Compliance History
    st.header("3. Compliance Status History & Formality Status")
    initial_compliance = restaurant_info.get("compliance_status", "Unknown")
    st.markdown(f"**Compliance Status (24th March):** {initial_compliance}")

    formality_options = [
        "Unregistered (No record with PRA)",
        "Registered but Not Filing",
        "Registered & Filing"
    ]
    formality_status = st.radio("Formality Status", options=formality_options)

    compliance_status = ""
    if formality_status == "Registered & Filing":
        compliance_status = st.radio("Compliance Status with PRA", [
            "Active Filer", "Late Filer", "Filing with Errors", "Other (Specify)"
        ])

    # Section 4 – Existence & Operational Status
    st.header("4. Existence & Operational Status")
    status_today = st.radio("Status Today", ["Open", "Closed"],
                            index=["Open", "Closed"].index(restaurant_info.get("status_today", "Open")))
    closure_reason = ""
    if status_today == "Closed":
        closure_reason = st.radio("If Closed, Reason", ["Temporary Closure", "Permanent Closure", "Relocated", "Unknown"])

    # Conditional Sections
    ur_data, rnf_data, rf_data = {}, {}, {}

    if formality_status == "Unregistered (No record with PRA)":
        st.header("5. For Unregistered Businesses")
        ur_data["LastContact"] = st.date_input("Date of Last Contact", datetime.date.today())
        ur_data["NoticesSent"] = st.radio("Notices Sent", ["Yes", "No"])
        ur_data["NoticeType"] = st.selectbox("Type of Notice", ["Voluntary Compliance", "Advance Notice-CR", "Compulsory Registration", "Other (Specify)"])
        ur_data["OtherContact"] = st.radio("Any Other Contacts?", ["Yes", "No"])
        ur_data["ContactMethod"] = st.multiselect("Nature of Contact", ["Call", "Field Visit", "Email", "In-Person Meeting", "Other (Specify)"])
        ur_data["InteractionSummary"] = st.text_area("Interaction Summary")
        ur_data["ResponseReceived"] = st.radio("Response Received?", ["Yes", "No"])
        if ur_data["ResponseReceived"] == "Yes":
            ur_data["ResponseDate"] = st.date_input("Response Date", datetime.date.today())
            ur_data["ResponseMethod"] = st.multiselect("Nature of Response", ["Call", "Field Visit", "Letter", "Email", "In-Person Meeting", "Other (Specify)"])
            ur_data["ResponseSummary"] = st.text_area("Response Summary")
        else:
            ur_data["ResponseDate"] = None
            ur_data["ResponseMethod"] = []
            ur_data["ResponseSummary"] = ""
        ur_data["NextStep"] = st.selectbox("Next Step", ["Send Awareness Material", "Schedule Field Visit", "Issue Notice", "Escalate to Higher Authority", "No Further Action Needed"])
        ur_data["Comments"] = st.text_area("Comments")

    elif formality_status == "Registered but Not Filing":
        st.header("6. For Registered but Not Filing Businesses")
        rnf_data["Filed"] = st.radio("Filed Since Last Survey?", ["Yes", "No"])
        rnf_data["LastContact"] = st.date_input("Date of Last Contact", datetime.date.today())
        rnf_data["NoticesSent"] = st.radio("Notices Sent", ["Yes", "No"])
        rnf_data["NoticeType"] = st.selectbox("Type of Notice", ["Non-Filing Notice", "Non-Filing Penalty", "Other (Specify)"])
        rnf_data["Contact"] = st.multiselect("Nature of Contact", ["Call", "Field Visit", "Email", "In-Person Meeting", "Other (Specify)"])
        rnf_data["Interaction"] = st.text_area("Interaction Summary")
        rnf_data["ResponseReceived"] = st.radio("Response Received?", ["Yes", "No"])
        if rnf_data["ResponseReceived"] == "Yes":
            rnf_data["ResponseDate"] = st.date_input("Response Date", datetime.date.today())
            rnf_data["ResponseMethod"] = st.multiselect("Nature of Response", ["Call", "Field Visit", "Letter", "Email", "In-Person Meeting", "Other (Specify)"])
            rnf_data["ResponseSummary"] = st.text_area("Response Summary")
        else:
            rnf_data["ResponseDate"] = None
            rnf_data["ResponseMethod"] = []
            rnf_data["ResponseSummary"] = ""
        rnf_data["ReasonNonFiling"] = st.text_input("Reason for Non-Filing")
        rnf_data["NextStep"] = st.selectbox("Next Step", ["Send Reminder", "Offer Assistance", "Conduct Field Visit", "Issue Penalty", "Escalate", "No Action"])
        rnf_data["Comments"] = st.text_area("Comments")

    elif formality_status == "Registered & Filing":
        st.header("7. For Registered & Filing Businesses")
        rf_data["FiledLastMonth"] = st.radio("Filed Last Month?", ["Yes", "No"])
        rf_data["LastContact"] = st.date_input("Date of Last Contact", datetime.date.today())
        filed_own_accord = st.radio("Filed of Own Accord?", ["Yes", "No"])
        if rf_data["FiledLastMonth"] == "No" or filed_own_accord == "No":
            rf_data["NoticesSent"] = st.radio("Notices Sent", ["Yes", "No"])
            rf_data["NoticeType"] = st.selectbox("Type of Notice", ["Non-Filing Notice", "Non-Filing Penalty", "Other (Specify)"])
            rf_data["Contact"] = st.multiselect("Nature of Contact", ["Call", "Field Visit", "Email", "In-Person Meeting", "Other (Specify)"])
            rf_data["Interaction"] = st.text_area("Interaction Summary")
            rf_data["ResponseReceived"] = st.radio("Response Received?", ["Yes", "No"])
            if rf_data["ResponseReceived"] == "Yes":
                rf_data["ResponseDate"] = st.date_input("Response Date", datetime.date.today())
                rf_data["ResponseMethod"] = st.multiselect("Nature of Response", ["Call", "Field Visit", "Letter", "Email", "In-Person Meeting", "Other (Specify)"])
                rf_data["ResponseSummary"] = st.text_area("Response Summary")
            else:
                rf_data["ResponseDate"] = None
                rf_data["ResponseMethod"] = []
                rf_data["ResponseSummary"] = ""
        else:
            rf_data["NoticesSent"] = ""
            rf_data["NoticeType"] = ""
            rf_data["Contact"] = []
            rf_data["Interaction"] = ""
            rf_data["ResponseReceived"] = "No"
            rf_data["ResponseDate"] = None
            rf_data["ResponseMethod"] = []
            rf_data["ResponseSummary"] = ""
        rf_data["Comments"] = st.text_area("Comments")

    # Final Surveyor Details
    st.header("Surveyor Follow-up")
    survey_date = st.date_input("Survey Date", datetime.date.today())
    survey_followup_required = st.radio("Follow-up Action Needed?", ["Yes", "No"])
    survey_followup_date = st.date_input("Next Follow-up Date", datetime.date.today())

    # Submit Entry
    if st.button("Submit Entry"):
        entry = {
            "officername": officer_name,
            "officerid": officer_id,
            "interviewdate": interview_date,
            "interviewmethod": interview_method,
            "restaurantid": restaurant_id,
            "formalitystatus": formality_status,
            "compliancestatus": compliance_status,
            "compliancestatus_24march": initial_compliance,
            "statustoday": status_today,
            "closurereason": closure_reason,
            "surveydate": survey_date,
            "surveyfollowup": survey_followup_required,
            "surveyfollowupdate": survey_followup_date,
            **{f"ur_{k.lower()}": v for k, v in ur_data.items()},
            **{f"rnf_{k.lower()}": v for k, v in rnf_data.items()},
            **{f"rf_{k.lower()}": v for k, v in rf_data.items()},
        }

        pd.DataFrame([entry]).to_sql("officer_compliance_updates", engine, if_exists="append", index=False)
        st.success("✅ Entry submitted successfully!")


# ------------------- PAGE 2: PRA SYSTEM DATA -------------------
elif page == "PRA System Data":
    st.title("📦 PRA Centralized System Data Panel")

    # Load existing data
    try:
        pra_df = pd.read_sql("SELECT * FROM pra_system_updates", engine)
    except:
        pra_df = pd.DataFrame()

    # --- Upload PRA CSV ---
    st.subheader("📤 Upload Latest PRA Data (CSV)")
    uploaded_file = st.file_uploader("Upload PRA CSV", type="csv")

    if uploaded_file:
        new_data = pd.read_csv(uploaded_file)
        new_data.to_sql("pra_system_updates", engine, if_exists="replace", index=False)
        st.success("✅ PRA system table successfully updated with CSV data!")

    # --- View Existing Record ---
    st.markdown("---")
    if pra_df.empty:
        st.warning("⚠️ No PRA data available. Please upload a CSV or manually enter below.")
    else:
        selected_rest = st.selectbox("Select Restaurant ID", pra_df['restaurantid'].unique().tolist())
        matching = pra_df[pra_df['restaurantid'] == selected_rest]

        if not matching.empty:
            pra_info = matching.iloc[0]
            st.markdown(f"**Taxpayer Name:** {pra_info['taxpayer_name']}")
            st.markdown(f"**NTN:** {pra_info['ntn']}")
            st.markdown(f"**Filing Status:** {pra_info['filing_status']}")
            st.markdown(f"**Total Tax Amount:** Rs. {pra_info['total_tax_amount']}")
            st.markdown(f"**Months Filed:** {pra_info['months_filed']}")
            st.markdown(f"**Tax Paid:** Rs. {pra_info['tax_paid']}")
            st.markdown(f"**POS Device Linked:** {pra_info['pos_device']}")
            st.markdown(f"**EMIS Registered:** {pra_info['emis_registered']}")
            st.markdown(f"**Invoice Available (EMIS):** {pra_info['emis_invoice_available']}")
            st.markdown(f"**IRIS Officer Assigned:** {pra_info['iris_officer_assigned']}")
            st.markdown(f"**Notice Sent (IRIS):** {pra_info['iris_notice_sent']}")
            st.markdown(f"**Notice Issued (IRIS):** {pra_info['iris_notice_issued']}")

    # --- Manual Entry Form ---
    st.markdown("---")
    st.subheader("📝 Manually Add PRA Record")

    col1, col2 = st.columns(2)
    with col1:
        restaurantid = st.text_input("Restaurant ID")
        taxpayer_name = st.text_input("Taxpayer Name")
        ntn = st.text_input("NTN")
        total_tax_amount = st.number_input("Total Tax Amount", min_value=0.0, step=100.0)
        months_filed = st.number_input("Months Filed", min_value=0, step=1)
        emis_registered = st.selectbox("EMIS Registered", ["Yes", "No"])
        emis_invoice_available = st.selectbox("Invoice Available in EMIS", ["Yes", "No"])
    with col2:
        filing_status = st.selectbox("Filing Status", ["Filed", "Registered", "Unregistered"])
        tax_paid = st.number_input("Tax Paid (PKR)", min_value=0.0, step=100.0)
        pos_device = st.selectbox("POS Device Linked", ["Yes", "No"])
        iris_officer_assigned = st.text_input("IRIS Officer Assigned")
        iris_notice_sent = st.date_input("IRIS Notice Sent")
        iris_notice_issued = st.date_input("IRIS Notice Issued")

    if st.button("Submit PRA Record"):
        manual_entry = pd.DataFrame([{
            "restaurantid": restaurantid,
            "taxpayer_name": taxpayer_name,
            "ntn": ntn,
            "filing_status": filing_status,
            "total_tax_amount": total_tax_amount,
            "months_filed": months_filed,
            "tax_paid": tax_paid,
            "pos_device": pos_device,
            "emis_registered": emis_registered,
            "emis_invoice_available": emis_invoice_available,
            "iris_officer_assigned": iris_officer_assigned,
            "iris_notice_sent": iris_notice_sent,
            "iris_notice_issued": iris_notice_issued
        }])
        manual_entry.to_sql("pra_system_updates", engine, if_exists="append", index=False)
        st.success("✅ Manual PRA record submitted successfully!")
