import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-Layer Process Log Engine")

st.title("Multi-Layer Process Log Engineering Framework")

# =========================================================
# FILE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls", "xlsb"]
)

if uploaded_file is not None:

    # File size protection (500MB)
    if uploaded_file.size > 500 * 1024 * 1024:
        st.error("File too large. Please upload file under 500MB.")
        st.stop()

    try:
        # =========================================================
        # LOAD FILE
        # =========================================================

        if uploaded_file.name.endswith(".csv"):

            raw_df = pd.read_csv(
                uploaded_file,
                low_memory=True,
                dtype=str
            )

        else:
            # Detect engine
            if uploaded_file.name.endswith(".xlsb"):
                try:
                    engine_type = "pyxlsb"
                except ImportError:
                    st.error("pyxlsb is not installed. Please add it to requirements.txt")
                    st.stop()
            else:
                engine_type = "openpyxl"

            excel_file = pd.ExcelFile(uploaded_file, engine=engine_type)
            sheet_names = excel_file.sheet_names

            selected_sheet = st.selectbox(
                "Select Sheet to Process",
                sheet_names
            )

            if st.button("Load Selected Sheet"):
                raw_df = pd.read_excel(
                    excel_file,
                    sheet_name=selected_sheet,
                    engine=engine_type,
                    dtype=str
                )
            else:
                st.stop()

        st.success("File Loaded Successfully")

    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # =========================================================
    # STANDARDIZE COLUMN NAMES
    # =========================================================

    raw_df.columns = (
        raw_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # =========================================================
    # REMOVE DUPLICATE INCIDENT
    # =========================================================

    disposition_col = None
    for col in raw_df.columns:
        if "disposition" in col:
            disposition_col = col
            break

    if disposition_col:
        raw_df = raw_df[
            ~raw_df[disposition_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains("duplicate incident", na=False)
        ]

    # =========================================================
    # SELECT DATA LAYER
    # =========================================================

    layer = st.radio(
        "Select Data Layer",
        ["SPF", "Closed", "Reopen"]
    )

    # =========================================================
    # CASE LOG CREATION
    # =========================================================

    if layer == "SPF":
        required_cols = [
            "incident_id",
            "incident_thread_id",
            "category_id",
            "status",
            "status_type",
            "sellerid",
            "disposition_id",
            "month",
            "partner",
            "tier",
            "domain",
            "spf_related_issues"
        ]

    elif layer == "Closed":
        required_cols = [
            "incident_id",
            "seller_id",
            "category_id",
            "count_of_inflow_seller_contacts",
            "status",
            "status_type",
            "count_of_solved_status",
            "disposition",
            "time_spent_in_wsa(days)",
            "time_spent_in_wsc(days)",
            "time_spent_in_l1(days)",
            "time_spent_inl2(days)",
            "time_spent_in_l3(days)",
            "closed_time_spent(days)",
            "time_spent_in_l1wsa(days)",
            "time_spent_in_l2wsa(days)",
            "month",
            "partner",
            "tier",
            "domain"
        ]

    else:  # Reopen
        required_cols = [
            "incident_id",
            "issue_type",
            "disposition",
            "seller_id",
            "status",
            "month",
            "partner",
            "tier",
            "count_repeat",
            "esc/non_esc",
            "domain"
        ]

    available_cols = [col for col in required_cols if col in raw_df.columns]

    if len(available_cols) == 0:
        st.error("Required columns not found in file.")
        st.stop()

    case_log = raw_df[available_cols].copy()

    if "incident_id" in case_log.columns:
        case_log.rename(columns={"incident_id": "case_id"}, inplace=True)

    if "case_id" in case_log.columns:
        case_log = case_log.drop_duplicates(subset=["case_id"])

    st.success("Case Log Generated Successfully")

    st.download_button(
        "Download Case Log",
        case_log.to_csv(index=False),
        f"{layer}_case_log.csv",
        "text/csv"
    )

    # =========================================================
    # EVENT LOG CREATION
    # =========================================================

    event_cols = [
        "incident_id",
        "incident_date_created",
        "l1_to_l2_modified_time",
        "escalated_to_l3_date",
        "incident_date_closed"
    ]

    available_event_cols = [col for col in event_cols if col in raw_df.columns]

    if len(available_event_cols) > 1:

        event_wide = raw_df[available_event_cols].copy()

        if "incident_id" in event_wide.columns:
            event_wide.rename(columns={"incident_id": "case_id"}, inplace=True)

        st.success("Event Wide Format Generated")

        st.download_button(
            "Download Event Wide Format",
            event_wide.to_csv(index=False),
            f"{layer}_event_wide.csv",
            "text/csv"
        )

        # Optional Long Format
        if st.checkbox("Generate Long Event Log (May exceed Excel row limit)"):

            event_df = event_wide.copy()

            timestamp_cols = [
                col for col in event_df.columns if col != "case_id"
            ]

            for col in timestamp_cols:
                event_df[col] = pd.to_datetime(event_df[col], errors="coerce")

            event_long = event_df.melt(
                id_vars=["case_id"],
                var_name="activity",
                value_name="timestamp"
            )

            event_long = event_long.dropna(subset=["timestamp"])
            event_long = event_long.sort_values(["case_id", "timestamp"])

            st.success("Long Event Log Generated")

            st.download_button(
                "Download Long Event Log",
                event_long.to_csv(index=False),
                f"{layer}_event_long.csv",
                "text/csv"
            )

    else:
        st.warning("Event timestamp columns not found.")
