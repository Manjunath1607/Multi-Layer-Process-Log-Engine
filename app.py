import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Multi-Layer Process Log Engine")
st.title("Multi-Layer Process Log Engineering Framework")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls", "xlsb"]
)

# ---------------------------------------------------------
# FAST LOADER WITH CACHE
# ---------------------------------------------------------

@st.cache_data(show_spinner=True)
def load_data(file_bytes, file_name, sheet_name=None):

    file_buffer = io.BytesIO(file_bytes)

    # CSV → fastest path
    if file_name.endswith(".csv"):
        return pd.read_csv(file_buffer, dtype=str, low_memory=True)

    # Excel → read once
    if file_name.endswith(".xlsb"):
        engine_type = "pyxlsb"
    else:
        engine_type = "openpyxl"

    df = pd.read_excel(
        file_buffer,
        sheet_name=sheet_name,
        engine=engine_type,
        dtype=str
    )

    return df


if uploaded_file is not None:

    if uploaded_file.size > 500 * 1024 * 1024:
        st.error("File too large (limit 500MB).")
        st.stop()

    try:
        file_bytes = uploaded_file.read()

        # Excel → sheet selection
        if uploaded_file.name.endswith((".xlsx", ".xls", ".xlsb")):

            # Determine engine
            if uploaded_file.name.endswith(".xlsb"):
                engine_type = "pyxlsb"
            else:
                engine_type = "openpyxl"

            # Read sheet names
            excel_file = pd.ExcelFile(
                io.BytesIO(file_bytes),
                engine=engine_type
            )

            selected_sheet = st.selectbox(
                "Select Sheet to Process",
                excel_file.sheet_names
            )

            if st.button("Load Selected Sheet"):
                raw_df = load_data(
                    file_bytes,
                    uploaded_file.name,
                    selected_sheet
                )
            else:
                st.stop()

        else:
            raw_df = load_data(
                file_bytes,
                uploaded_file.name
            )

        st.success("File Loaded Successfully")
        st.write("Rows:", len(raw_df))
        st.write("Columns:", len(raw_df.columns))

    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # ---------------------------------------------------------
    # STANDARDIZE COLUMNS
    # ---------------------------------------------------------

    raw_df.columns = (
        raw_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # ---------------------------------------------------------
    # REMOVE DUPLICATE INCIDENT
    # ---------------------------------------------------------

    disposition_col = next(
        (col for col in raw_df.columns if "disposition" in col),
        None
    )

    if disposition_col:
        raw_df = raw_df[
            ~raw_df[disposition_col]
            .astype(str)
            .str.lower()
            .str.contains("duplicate incident", na=False)
        ]

    # ---------------------------------------------------------
    # SELECT LAYER
    # ---------------------------------------------------------

    layer = st.radio(
        "Select Data Layer",
        ["SPF", "Closed", "Reopen"]
    )

    layer_columns = {
        "SPF": [
            "incident_id","incident_thread_id","category_id","status",
            "status_type","sellerid","disposition_id","month",
            "partner","tier","domain","spf_related_issues"
        ],
        "Closed": [
            "incident_id","seller_id","category_id",
            "count_of_inflow_seller_contacts","status","status_type",
            "count_of_solved_status","disposition",
            "time_spent_in_wsa(days)","time_spent_in_wsc(days)",
            "time_spent_in_l1(days)","time_spent_inl2(days)",
            "time_spent_in_l3(days)","closed_time_spent(days)",
            "time_spent_in_l1wsa(days)","time_spent_in_l2wsa(days)",
            "month","partner","tier","domain"
        ],
        "Reopen": [
            "incident_id","issue_type","disposition","seller_id",
            "status","month","partner","tier",
            "count_repeat","esc/non_esc","domain"
        ]
    }

    required_cols = layer_columns[layer]
    available_cols = [col for col in required_cols if col in raw_df.columns]

    if not available_cols:
        st.error("Required columns not found in file.")
        st.stop()

    case_log = raw_df[available_cols].copy()

    if "incident_id" in case_log.columns:
        case_log.rename(columns={"incident_id": "case_id"}, inplace=True)

    if "case_id" in case_log.columns:
        case_log = case_log.drop_duplicates(subset=["case_id"])

    st.success("Case Log Generated")

    st.download_button(
        "Download Case Log",
        case_log.to_csv(index=False),
        f"{layer}_case_log.csv",
        "text/csv"
    )

    # ---------------------------------------------------------
    # EVENT LOG
    # ---------------------------------------------------------

    event_cols = [
        "incident_id",
        "incident_date_created",
        "l1_to_l2_modified_time",
        "escalated_to_l3_date",
        "incident_date_closed"
    ]

    available_event_cols = [
        col for col in event_cols if col in raw_df.columns
    ]

    if len(available_event_cols) > 1:

        event_df = raw_df[available_event_cols].copy()

        if "incident_id" in event_df.columns:
            event_df.rename(columns={"incident_id": "case_id"}, inplace=True)

        st.success("Event Wide Format Generated")

        st.download_button(
            "Download Event Wide Format",
            event_df.to_csv(index=False),
            f"{layer}_event_wide.csv",
            "text/csv"
        )

        if st.checkbox("Generate Long Event Log"):

            timestamp_cols = [
                col for col in event_df.columns
                if col != "case_id"
            ]

            for col in timestamp_cols:
                event_df[col] = pd.to_datetime(
                    event_df[col],
                    errors="coerce"
                )

            event_long = event_df.melt(
                id_vars=["case_id"],
                var_name="activity",
                value_name="timestamp"
            )

            event_long = event_long.dropna(subset=["timestamp"])
            event_long = event_long.sort_values(
                ["case_id", "timestamp"]
            )

            st.success("Long Event Log Generated")

            st.download_button(
                "Download Long Event Log",
                event_long.to_csv(index=False),
                f"{layer}_event_long.csv",
                "text/csv"
            )

    else:
        st.warning("Event timestamp columns not found.")
