import pandas as pd
import infoprex_new_system

def detect_format_and_read(filepath_or_buffer) -> pd.DataFrame:
    """
    Detects if the Infoprex file is 'Sistema Antigo' or 'Sistema Novo'.
    Reads and normalizes the data accordingly.
    """
    header_df = None
    for enc in ['utf-16', 'utf-8', 'latin1']:
        try:
            if hasattr(filepath_or_buffer, 'seek'):
                filepath_or_buffer.seek(0)
            header_df = pd.read_csv(filepath_or_buffer, sep='\t', encoding=enc, nrows=0)
            if 'CPR' in header_df.columns:
                break
        except Exception:
            pass

    if header_df is None or 'CPR' not in header_df.columns:
        for enc in ['utf-16', 'utf-8', 'latin1']:
            try:
                if hasattr(filepath_or_buffer, 'seek'):
                    filepath_or_buffer.seek(0)
                header_df = pd.read_csv(filepath_or_buffer, sep=';', encoding=enc, nrows=0)
                if 'CPR' in header_df.columns:
                    break
            except Exception:
                pass

    if header_df is None or 'CPR' not in header_df.columns:
        return pd.DataFrame()

    is_new_system = 'DUV' in header_df.columns and 'LOCALIZACAO' in header_df.columns

    if is_new_system:
        if hasattr(filepath_or_buffer, 'seek'):
            filepath_or_buffer.seek(0)
        return infoprex_new_system.transform_new_system(filepath_or_buffer)
    
    # Legacy parsing
    df = None
    for sep in ['\t', ';']:
        for enc in ['utf-16', 'utf-8', 'latin1']:
            try:
                if hasattr(filepath_or_buffer, 'seek'):
                    filepath_or_buffer.seek(0)
                df = pd.read_csv(filepath_or_buffer, sep=sep, encoding=enc, on_bad_lines='skip', dtype=str)
                if not df.empty and 'CPR' in df.columns:
                    break
            except Exception:
                continue
        if df is not None and not df.empty and 'CPR' in df.columns:
            break

    if df is None or df.empty:
        return pd.DataFrame()

    # Remove quotes from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()

    # Apply location filtering
    if 'DUV' in df.columns and 'LOCALIZACAO' in df.columns:
        df['DUV_dt'] = pd.to_datetime(df['DUV'], dayfirst=True, errors='coerce')
        valid_dates = df.dropna(subset=['DUV_dt'])
        if not valid_dates.empty:
            max_date = valid_dates['DUV_dt'].max()
            rows_max_date = df[df['DUV_dt'] == max_date]
            if not rows_max_date.empty:
                localizacao_alvo = rows_max_date['LOCALIZACAO'].iloc[0]
                df = df[df['LOCALIZACAO'] == localizacao_alvo].copy()
        if 'DUV_dt' in df.columns:
            df.drop(columns=['DUV_dt'], inplace=True)

    for c in ['PVP', 'PCU', 'IVA', 'SAC']:
        if c in df.columns:
            # quotes are already removed
            df[c] = df[c].str.replace(',', '.', regex=False)
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    rename_dict = {
        'CPR': 'CNP',
        'NOM': 'Descrição',
        'SAC': 'Stock',
        'PCU': 'PC Atual'
    }
    df.rename(columns=rename_dict, inplace=True)
    
    return df

def process_infoprex_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the Stock > 0 filter and calculates the commercial margin.
    """
    if df.empty:
        return df

    # FR-IP-06: Stock filter
    if 'Stock' in df.columns:
        df = df[df['Stock'] > 0].copy()

    # FR-IP-07: Margin calculation
    if 'IVA' in df.columns and 'PVP' in df.columns and 'PC Atual' in df.columns:
        df['iva_divisor'] = 1 + (pd.to_numeric(df['IVA'], errors='coerce').fillna(0) / 100)
        df['PVP_sIVA'] = pd.to_numeric(df['PVP'], errors='coerce').fillna(0) / df['iva_divisor']
        pc_atual = pd.to_numeric(df['PC Atual'], errors='coerce').fillna(0)
        df['Margem'] = ((df['PVP_sIVA'] - pc_atual) / df['PVP_sIVA'].replace(0, pd.NA) * 100).fillna(0)
        df['Margem'] = pd.to_numeric(df['Margem'], errors='coerce').round(1)

    return df

def apply_ui_filters(df: pd.DataFrame, divergence_type: str, margin_threshold: bool) -> pd.DataFrame:
    """
    Applies the UI filters to the divergences DataFrame.
    """
    if df.empty:
        return df

    filtered_df = df.copy()

    # FR-IP-08: UI Filters
    if divergence_type == 'Infoprex < Master':
        if 'PVP_Infoprex' in filtered_df.columns and 'PVP Atual' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['PVP_Infoprex'] < filtered_df['PVP Atual']]
    elif divergence_type == 'Infoprex > Master':
        if 'PVP_Infoprex' in filtered_df.columns and 'PVP Atual' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['PVP_Infoprex'] > filtered_df['PVP Atual']]

    if margin_threshold:
        if 'Margem' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Margem'] > 30]

    return filtered_df

def compare_infoprex_master(df_infoprex: pd.DataFrame, final_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compares the Infoprex DataFrame with the Master Table (final_df).
    """
    if df_infoprex.empty or final_df.empty:
        return pd.DataFrame()

    df_infoprex['CNP'] = pd.to_numeric(df_infoprex['CNP'], errors='coerce')
    df_infoprex = df_infoprex.dropna(subset=['CNP'])
    df_infoprex['CNP'] = df_infoprex['CNP'].astype(int)

    if 'Stock' in df_infoprex.columns:
        df_infoprex['Stock'] = pd.to_numeric(df_infoprex['Stock'], errors='coerce')
        df_infoprex = df_infoprex.dropna(subset=['Stock'])
        df_infoprex['Stock'] = df_infoprex['Stock'].astype(int)

    merged_info = pd.merge(
        final_df,
        df_infoprex,
        on='CNP',
        how='inner'
    )

    if 'PVP Atual' in merged_info.columns and 'PVP' in merged_info.columns:
        merged_info['PVP Atual'] = pd.to_numeric(merged_info['PVP Atual'], errors='coerce').fillna(0).round(2)
        merged_info['PVP_Infoprex'] = pd.to_numeric(merged_info['PVP'], errors='coerce').fillna(0).round(2)
        diff_pvp = merged_info[merged_info['PVP Atual'] != merged_info['PVP_Infoprex']].copy()
        return diff_pvp
    
    return merged_info
