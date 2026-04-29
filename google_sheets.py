import pandas as pd
import re
import os
import streamlit as st

def get_sheet_url():
    """
    Retrieves the Sheet URL from secrets, environment variables, or sidebar input.
    """
    sheet_id = None

    # 1. Try Streamlit Secrets
    if "GOOGLE_SHEET_ID" in st.secrets:
        sheet_id = st.secrets["GOOGLE_SHEET_ID"]

    # 2. Try Environment Variable
    elif "GOOGLE_SHEET_ID" in os.environ:
        sheet_id = os.environ["GOOGLE_SHEET_ID"]

    # 3. Fallback: Input in Sidebar (Debug/Manual)
    if not sheet_id:
        with st.sidebar:
            st.warning("⚠️ ID da Google Sheet não configurado.")
            sheet_id = st.text_input(
                "Introduza o ID da Google Sheet (ou parte 2PACX...):")

    if sheet_id:
        # Construct URL based on ID type
        if sheet_id.startswith("2PACX"):
            return f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=xlsx"
        else:
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    return None

def normalize_column_name(col_name):
    """Normalizes column names for comparison (lowercase, stripped)."""
    return str(col_name).strip().lower()

def find_target_columns(columns):
    """
    Finds the specific PVP and PC columns regardless of 'atual' or 'actual' spelling.
    Returns a dict with 'pvp' and 'pc' keys mapped to actual column names, or None if not found.
    """
    normalized_cols = {normalize_column_name(c): c for c in columns}

    # Regex patterns for flexible matching
    pvp_pattern = re.compile(r"^pvp\s*(atual|actual)$")
    pc_pattern = re.compile(r"^pc\s*(atual|actual)$")

    found_pvp = None
    found_pc = None

    for norm_col, original_col in normalized_cols.items():
        if pvp_pattern.match(norm_col):
            found_pvp = original_col
        if pc_pattern.match(norm_col):
            found_pc = original_col

    if found_pvp and found_pc:
        return {'pvp': found_pvp, 'pc': found_pc}
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_google_sheet_data(url):
    """Loads and processes the Google Sheet data, returning the consolidated DataFrame."""
    try:
        xls = pd.ExcelFile(url, engine='openpyxl')
        valid_dataframes = []

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)

            if df.empty:
                continue

            target_cols = find_target_columns(df.columns)

            if target_cols:
                first_col = df.columns[0]
                pvp_col = target_cols['pvp']
                pc_col = target_cols['pc']

                temp_df = df[[first_col, pvp_col, pc_col]].copy()
                temp_df.columns = ['Codigo', 'PVP Actual', 'PC Actual']

                valid_dataframes.append(temp_df)

        if valid_dataframes:
            final_df = pd.concat(valid_dataframes, ignore_index=True)
            final_df = final_df.dropna(how='all')

            for col in ['PVP Actual', 'PC Actual']:
                final_df[col] = final_df[col].astype(str).str.replace(',', '.', regex=False)
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')

            final_df['Codigo'] = pd.to_numeric(final_df['Codigo'], errors='coerce')
            final_df = final_df.dropna(subset=['Codigo', 'PVP Actual', 'PC Actual'])

            final_df['PVP Actual'] = final_df['PVP Actual'].round(2)
            final_df['Codigo'] = final_df['Codigo'].astype(int)

            return final_df
        return None

    except Exception as e:
        st.error(f"Erro ao carregar dados da Google Sheet: {e}")
        return None
