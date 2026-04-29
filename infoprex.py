import pandas as pd

def process_data(file_sales):
    """
    Process Infoprex export data.
    """
    # --- A. VENDAS (INFOPREX) ---
    file_sales.seek(0)
    try:
        df_sales = pd.read_csv(
            file_sales, sep='\t', encoding='latin-1', on_bad_lines='skip', dtype=str)
    except:
        df_sales = pd.read_csv(
            file_sales, sep=';', encoding='latin-1', on_bad_lines='skip', dtype=str)

    # 1. Filtro Localização (Data mais recente)
    if 'DUV' in df_sales.columns and 'LOCALIZACAO' in df_sales.columns:
        df_sales['DUV_dt'] = pd.to_datetime(
            df_sales['DUV'], dayfirst=True, format='mixed', errors='coerce')
        valid = df_sales.dropna(subset=['DUV_dt'])
        if not valid.empty:
            max_loc = df_sales.loc[valid['DUV_dt'].idxmax(), 'LOCALIZACAO']
            df_sales = df_sales[df_sales['LOCALIZACAO'] == max_loc].copy()

    # 2. Limpeza Numérica (PVP, PCU, IVA e agora SAC para o stock)
    for c in ['PVP', 'PCU', 'IVA', 'SAC']:
        if c in df_sales.columns:
            # Remove aspas se existirem e troca vírgula por ponto
            df_sales[c] = df_sales[c].str.replace('"', '', regex=False).str.replace(',', '.', regex=False)
            df_sales[c] = pd.to_numeric(df_sales[c], errors='coerce').fillna(0.0)

    # 3. Filtro de Stock (SAC > 0)
    if 'SAC' in df_sales.columns:
        df_sales = df_sales[df_sales['SAC'] > 0].copy()

    # 4. Cálculo da Margem
    if 'IVA' in df_sales.columns and 'PVP' in df_sales.columns and 'PCU' in df_sales.columns:
        df_sales['iva_divisor'] = 1 + (df_sales['IVA'] / 100)
        df_sales['PVP_sIVA'] = df_sales['PVP'] / df_sales['iva_divisor']
        df_sales['Margem'] = ((df_sales['PVP_sIVA'] - df_sales['PCU']) / df_sales['PVP_sIVA'] * 100).fillna(0)
        df_sales['Margem'] = df_sales['Margem'].round(1)

    cols_to_return = ['CPR', 'NOM', 'PVP','SAC', 'Margem']
    existing_cols = [c for c in cols_to_return if c in df_sales.columns]
    return df_sales[existing_cols].copy()

def compare_infoprex_master(df_infoprex, final_df):
    """
    Compara o DataFrame do Infoprex com a Tabela Mestra (final_df).
    """
    # 2. Prepare for Merge
    df_infoprex['CPR'] = pd.to_numeric(df_infoprex['CPR'], errors='coerce')
    df_infoprex = df_infoprex.dropna(subset=['CPR'])
    df_infoprex['CPR'] = df_infoprex['CPR'].astype(int)

    if 'SAC' in df_infoprex.columns:
        df_infoprex['SAC'] = pd.to_numeric(df_infoprex['SAC'], errors='coerce')
        df_infoprex = df_infoprex.dropna(subset=['SAC'])
        df_infoprex['SAC'] = df_infoprex['SAC'].astype(int)

    # 3. Merge
    merged_info = pd.merge(
        final_df,
        df_infoprex,
        left_on='Codigo',
        right_on='CPR',
        how='inner'
    )

    # 4. Filter Differences
    merged_info['PVP Actual'] = merged_info['PVP Actual'].round(2)
    merged_info['PVP_Infoprex'] = merged_info['PVP'].round(2)

    diff_pvp = merged_info[merged_info['PVP Actual'] != merged_info['PVP_Infoprex']].copy()
    
    return diff_pvp