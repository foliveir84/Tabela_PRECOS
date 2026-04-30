import io
import re
import requests
import pandas as pd
import streamlit as st
from typing import Dict, Any, List

from validators import to_float_safe, to_int_safe


def build_google_sheet_url(sheet_id: str) -> str:
    """
    Build the appropriate download URL for a Google Sheet based on its ID format.
    """
    if sheet_id.startswith('2PACX'):
        return f'https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=xlsx'
    else:
        return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'


@st.cache_data(ttl=3600)
def fetch_and_process_master_table(url: str) -> Dict[str, Any]:
    """
    Fetches the Excel file from Google Sheets, processes valid sheets,
    and identifies data anomalies.
    Returns a dictionary containing:
    - 'df_master': The consolidated valid DataFrame
    - 'df_invalid_pc': DataFrame with invalid PC Atual
    - 'df_invalid_pvp': DataFrame with invalid PVP Atual
    - 'corrupt_sheets': List of skipped sheets
    - 'last_updated': String representing the last modification date
    """
    response = requests.get(url)
    response.raise_for_status()
    
    # Capture the Last-Modified or Date header
    last_updated = response.headers.get('Last-Modified') or response.headers.get('Date', 'Unknown')
    
    corrupt_sheets: List[str] = []
    valid_dfs = []
    
    xls = pd.ExcelFile(io.BytesIO(response.content))
    
    pc_regex = re.compile(r'^pc\s*(atual|actual)$', re.IGNORECASE)
    pvp_regex = re.compile(r'^pvp\s*(atual|actual)$', re.IGNORECASE)
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Check if dataframe is completely empty
        if df.empty or len(df.columns) == 0:
            corrupt_sheets.append(sheet_name)
            continue
            
        # Check if cell A1 (first column name) is exactly 'CNP'
        first_col = str(df.columns[0]).strip().upper()
        if first_col != 'CNP':
            corrupt_sheets.append(sheet_name)
            continue
            
        pc_col_name = None
        pvp_col_name = None
        
        for col in df.columns:
            col_str = str(col).strip()
            if pc_regex.match(col_str):
                pc_col_name = col
            if pvp_regex.match(col_str):
                pvp_col_name = col
                
        if not pc_col_name or not pvp_col_name:
            corrupt_sheets.append(sheet_name)
            continue
            
        # Select and rename columns
        df_valid = df[[df.columns[0], pc_col_name, pvp_col_name]].copy()
        df_valid.columns = ['CNP', 'PC Atual', 'PVP Atual']
        
        valid_dfs.append(df_valid)
        
    if not valid_dfs:
        return {
            'df_master': pd.DataFrame(columns=['CNP', 'PC Atual', 'PVP Atual']),
            'df_invalid_pc': pd.DataFrame(columns=['CNP', 'PC Atual', 'PVP Atual']),
            'df_invalid_pvp': pd.DataFrame(columns=['CNP', 'PC Atual', 'PVP Atual']),
            'corrupt_sheets': corrupt_sheets,
            'last_updated': last_updated
        }
        
    df_consolidated = pd.concat(valid_dfs, ignore_index=True)
    df_consolidated.dropna(how='all', inplace=True)
    
    # Clean and cast using validators
    df_consolidated['CNP'] = df_consolidated['CNP'].apply(to_int_safe)
    df_consolidated.dropna(subset=['CNP'], inplace=True)
    df_consolidated['CNP'] = df_consolidated['CNP'].astype(int)
    
    df_consolidated['PC Atual'] = df_consolidated['PC Atual'].apply(to_float_safe)
    df_consolidated['PVP Atual'] = df_consolidated['PVP Atual'].apply(to_float_safe)
    
    # Round PVP to 2 decimals
    df_consolidated['PVP Atual'] = df_consolidated['PVP Atual'].round(2)
    
    # Identify invalid PC
    invalid_pc_mask = df_consolidated['PC Atual'].isna() | (df_consolidated['PC Atual'] <= 0)
    df_invalid_pc = df_consolidated[invalid_pc_mask].copy()
    
    # Identify invalid PVP
    invalid_pvp_mask = df_consolidated['PVP Atual'].isna() | (df_consolidated['PVP Atual'] <= 0)
    df_invalid_pvp = df_consolidated[invalid_pvp_mask].copy()
    
    # Clean master
    df_master = df_consolidated[~invalid_pc_mask & ~invalid_pvp_mask].copy()
    
    return {
        'df_master': df_master,
        'df_invalid_pc': df_invalid_pc,
        'df_invalid_pvp': df_invalid_pvp,
        'corrupt_sheets': corrupt_sheets,
        'last_updated': last_updated
    }
