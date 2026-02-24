import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Multi-Layer Process Log Engine")

st.title("Multi-Layer Process Log Engineering Framework")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:

    # Load file
    if uploaded_file.name.endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    st.success("File loaded successfully")

    # Standardize columns
    raw_df.columns = (
        raw_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Remove Duplicate Incident
    disposition_col = None
    for col in raw_df.columns:
        if "disposition" in col:
            disposition_col = col
            break

    if disposition_col:
        before = len(raw_df)

        raw_df = raw_df[
            ~raw_df[disposition_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains("duplicate incident", na=False)
        ]

        removed = before - len(raw_df)
        st.info(f"Duplicate Incident rows removed: {removed}")

    # Case Log
    case_cols = [
        "incident_id",
        "incident_thread_id",
        "category_id",
        "status",
        "status_type",
        "seller_id",
        "sellerid",
        "disposition_id",
        "disposition",
        "month",
        "partner",
        "tier",
        "domain"
    ]

    case_cols = [c for c in case_cols if c in raw_df.columns]
    case_log = raw_df[case_cols].copy()

    if "incident_id" in case_log.columns:
        case_log.rename(columns={"incident_id": "case_id"}, inplace=True)

    case_log = case_log.drop_duplicates(subset=["case_id"])

    # Event Log
    event_cols = [
        "incident_id",
        "incident_date_created",
        "l1_to_l2_modified_time",
        "escalated_to_l3_date",
        "incident_date_closed"
    ]

    event_cols = [c for c in event_cols if c in raw_df.columns]
    event_df = raw_df[event_cols].copy()

    if "incident_id" in event_df.columns:
        event_df.rename(columns={"incident_id": "case_id"}, inplace=True)

    for col in event_df.columns:
        if col != "case_id":
            event_df[col] = pd.to_datetime(event_df[col], errors="coerce")

    event_log = event_df.melt(
        id_vars=["case_id"],
        var_name="activity",
        value_name="timestamp"
    )

    event_log = event_log.dropna(subset=["timestamp"])
    event_log = event_log.sort_values(["case_id", "timestamp"])

    # Variant
    variant_df = event_log.groupby("case_id")["activity"].apply(
        lambda x: " > ".join(x)
    ).reset_index()

    variant_df.rename(columns={"activity": "variant"}, inplace=True)
    case_log = case_log.merge(variant_df, on="case_id", how="left")

    st.success("Case Log and Event Log generated successfully")

    st.download_button(
        "Download Case Log",
        case_log.to_csv(index=False),
        "final_case_log.csv",
        "text/csv"
    )

    st.download_button(
        "Download Event Log",
        event_log.to_csv(index=False),
        "final_event_log.csv",
        "text/csv"
    )