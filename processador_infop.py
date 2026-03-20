import pandas as pd

def process_data(file_sales):
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
    # Apenas comparamos produtos que temos fisicamente em stock
    if 'SAC' in df_sales.columns:
        df_sales = df_sales[df_sales['SAC'] > 0].copy()

    # 4. Cálculo da Margem
    # Transformar IVA (ex: 23) em divisor (ex: 1.23)
    df_sales['iva_divisor'] = 1 + (df_sales['IVA'] / 100)
    
    # PVP sem IVA
    df_sales['PVP_sIVA'] = df_sales['PVP'] / df_sales['iva_divisor']
    
    # Margem % = (PVPsIVA - PCU) / PVPsIVA
    # Usamos o fillna(0) para evitar problemas onde o PVP_sIVA é zero
    df_sales['Margem'] = ((df_sales['PVP_sIVA'] - df_sales['PCU']) / df_sales['PVP_sIVA'] * 100).fillna(0)
    df_sales['Margem'] = df_sales['Margem'].round(4)

    # Retornar apenas as colunas desejadas
    cols_to_return = ['CPR', 'NOM', 'PVP','SAC', 'Margem']
    return df_sales[cols_to_return].copy()
