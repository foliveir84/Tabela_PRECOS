import pandas as pd
from validators import to_float_safe

def read_sifarma_csv(filepath_or_buffer) -> pd.DataFrame:
    """
    Ingest CSV with ';' separator. Try utf-8, fallback to utf-8-sig, fallback to latin-1.
    Ensure columns CNP, DESIGNAÇÃO, PVF, PVP exist (raise ValueError if not).
    Rename them to CNP, description, pvf, pvp_sifarma.
    Clean PVF and PVP using validators.to_float_safe.
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
    df = None
    
    for enc in encodings:
        try:
            if hasattr(filepath_or_buffer, 'seek'):
                filepath_or_buffer.seek(0)
            df = pd.read_csv(filepath_or_buffer, sep=';', encoding=enc)
            break
        except UnicodeDecodeError:
            continue
            
    if df is None:
        raise ValueError('Could not read the CSV file with any of the supported encodings.')

    required_cols = ['CNP', 'DESIGNAÇÃO', 'PVF', 'PVP']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
    rename_map = {
        'CNP': 'CNP',
        'DESIGNAÇÃO': 'description',
        'PVF': 'pvf',
        'PVP': 'pvp_sifarma'
    }
    
    cols_to_keep = required_cols.copy()
    if 'LÍQ.' in df.columns:
        cols_to_keep.append('LÍQ.')
        
    df = df[cols_to_keep].rename(columns=rename_map)
    
    df['CNP'] = pd.to_numeric(df['CNP'], errors='coerce')
    df = df.dropna(subset=['CNP'])
    df['CNP'] = df['CNP'].astype(int)
    
    df['pvf'] = df['pvf'].apply(to_float_safe)
    df['pvp_sifarma'] = df['pvp_sifarma'].apply(to_float_safe)
    
    if 'LÍQ.' in df.columns:
        df['LÍQ.'] = df['LÍQ.'].apply(to_float_safe)
        
    return df

def deduplicate_sifarma_data(df_sifarma: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Handle PVF=0. If duplicate CNP and one has PVF>0 and other PVF=0, drop the PVF=0 one.
    If CNP is unique and PVF=0, return it in a separate list of critical bonus errors.
    """
    # Sort by 'pvf' descending so that >0 comes before 0
    df_sorted = df_sifarma.sort_values(by='pvf', ascending=False)
    
    # Drop duplicates by CNP, keeping the first (the one with the highest PVF)
    df_dedup = df_sorted.drop_duplicates(subset=['CNP'], keep='first').copy()
    
    # Identify unique CNPs that still have PVF == 0
    mask_zero_pvf = df_dedup['pvf'] == 0
    df_critical = df_dedup[mask_zero_pvf].copy()
    
    # Clean DataFrame without the zero PVF cases
    df_clean = df_dedup[~mask_zero_pvf].copy()
    
    # Convert critical errors to a list of dictionaries
    critical_errors = df_critical.to_dict('records')
    
    return df_clean, critical_errors

def get_alert_1_high_cost(df_sifarma: pd.DataFrame, df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 1: PVF > PC Atual * 1.01
    """
    df_merged = pd.merge(df_sifarma, df_master, on='CNP', how='inner')
    mask = df_merged['pvf'] > (df_merged['PC Atual'] * 1.01)
    df_alert = df_merged[mask].copy()
    
    df_alert = df_alert.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF',
        'pvp_sifarma': 'PVP Sifarma'
    })
    
    return df_alert[['CNP', 'Descrição', 'PC Atual', 'PVF', 'PVP Sifarma', 'PVP Atual']]

def get_alert_2_low_cost(df_sifarma: pd.DataFrame, df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 2: PVF < PC Atual * 0.90
    Includes 'LÍQ.' if it exists in df_sifarma.
    """
    df_merged = pd.merge(df_sifarma, df_master, on='CNP', how='inner')
    mask = df_merged['pvf'] < (df_merged['PC Atual'] * 0.90)
    df_alert = df_merged[mask].copy()
    
    df_alert = df_alert.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF',
        'pvp_sifarma': 'PVP Sifarma'
    })
    
    cols_to_return = ['CNP', 'Descrição', 'PC Atual', 'PVF', 'PVP Sifarma', 'PVP Atual']
    if 'LÍQ.' in df_alert.columns:
        cols_to_return.append('LÍQ.')
        
    return df_alert[cols_to_return]

def get_alert_3_pvp_divergence(df_sifarma: pd.DataFrame, df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 3: round(pvp_sifarma, 2) != round(pvp_atual, 2)
    """
    df_merged = pd.merge(df_sifarma, df_master, on='CNP', how='inner')
    mask = df_merged['pvp_sifarma'].round(2) != df_merged['PVP Atual'].round(2)
    df_alert = df_merged[mask].copy()
    
    df_alert = df_alert.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF',
        'pvp_sifarma': 'PVP Sifarma'
    })
    
    return df_alert[['CNP', 'Descrição', 'PC Atual', 'PVF', 'PVP Sifarma', 'PVP Atual']]

def get_alert_4_missing_pc(df_sifarma: pd.DataFrame, df_invalid_pc_from_master: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 4: CNP in Sifarma is in the invalid PC list
    """
    df_merged = pd.merge(df_sifarma, df_invalid_pc_from_master, on='CNP', how='inner')
    
    df_alert = df_merged.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF',
        'pvp_sifarma': 'PVP Sifarma'
    })
    
    return df_alert[['CNP', 'Descrição', 'PC Atual', 'PVF', 'PVP Sifarma', 'PVP Atual']]

def get_alert_5_missing_pvp(df_sifarma: pd.DataFrame, df_invalid_pvp_from_master: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 5: CNP in Sifarma is in the invalid PVP list
    """
    df_merged = pd.merge(df_sifarma, df_invalid_pvp_from_master, on='CNP', how='inner')
    
    df_alert = df_merged.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF',
        'pvp_sifarma': 'PVP Sifarma'
    })
    
    return df_alert[['CNP', 'Descrição', 'PC Atual', 'PVF', 'PVP Sifarma', 'PVP Atual']]

def get_alert_6_not_in_master(df_sifarma: pd.DataFrame, df_master: pd.DataFrame, df_invalid_pc: pd.DataFrame, df_invalid_pvp: pd.DataFrame) -> pd.DataFrame:
    """
    Alert 6: CNP in Sifarma missing from Master entirely.
    It should NOT trigger for CNPs that are in Master but have invalid PC/PVP.
    It should ONLY trigger if the product in Sifarma has a valid PVP (> 0).
    Returns ONLY CNP, Descrição, PVF.
    """
    all_master_cnps = pd.concat([df_master['CNP'], df_invalid_pc['CNP'], df_invalid_pvp['CNP']]).unique()
    
    mask = (~df_sifarma['CNP'].isin(all_master_cnps)) & (df_sifarma['pvp_sifarma'] > 0)
    df_alert = df_sifarma[mask].copy()
    
    df_alert = df_alert.rename(columns={
        'description': 'Descrição',
        'pvf': 'PVF'
    })
    
    return df_alert[['CNP', 'Descrição', 'PVF']]
