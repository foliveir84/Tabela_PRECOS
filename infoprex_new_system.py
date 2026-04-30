import pandas as pd
from validators import to_float_safe, to_int_safe

def transform_new_system(filepath_or_buffer) -> pd.DataFrame:
    """
    Transforms data from the new Infoprex system into a normalized DataFrame.
    """
    # FR-IP-01: Memory Optimization
    colunas_alvo = ['CPR', 'NOM', 'LOCALIZACAO', 'SAC', 'PVP', 'PCU', 'IVA', 'DUV']
    
    def usecols_func(x):
        return x in colunas_alvo
    
    df = None
    for enc in ['utf-16', 'utf-8', 'latin1']:
        try:
            if hasattr(filepath_or_buffer, 'seek'):
                filepath_or_buffer.seek(0)
            df = pd.read_csv(filepath_or_buffer, sep='\t', encoding=enc, usecols=usecols_func, dtype=str)
            if 'CPR' in df.columns and 'DUV' in df.columns:
                break
        except Exception:
            continue
            
    if df is None or 'CPR' not in df.columns:
        return pd.DataFrame()

    # Remove quotes from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()

    # FR-IP-03, FR-IP-04: Dynamic row identification and location filtering
    df['DUV_dt'] = pd.to_datetime(df['DUV'], dayfirst=True, errors='coerce')
    valid_dates = df.dropna(subset=['DUV_dt'])
    
    if not valid_dates.empty:
        max_date = valid_dates['DUV_dt'].max()
        # Find rows with the max_date
        rows_max_date = df[df['DUV_dt'] == max_date]
        if not rows_max_date.empty:
            localizacao_alvo = rows_max_date['LOCALIZACAO'].iloc[0]
            df = df[df['LOCALIZACAO'] == localizacao_alvo].copy()

    # FR-IP-05: Clean numerical values
    for col in ['PVP', 'PCU', 'IVA']:
        if col in df.columns:
            df[col] = df[col].apply(to_float_safe)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    if 'SAC' in df.columns:
        df['SAC'] = df['SAC'].apply(to_int_safe)
        df['SAC'] = pd.to_numeric(df['SAC'], errors='coerce').fillna(0)
        
    # Rename columns to UI expectations
    rename_dict = {
        'CPR': 'CNP',
        'NOM': 'Descrição',
        'SAC': 'Stock',
        'PCU': 'PC Atual'
    }
    df.rename(columns=rename_dict, inplace=True)
    
    if 'DUV_dt' in df.columns:
        df.drop(columns=['DUV_dt'], inplace=True)
        
    return df
