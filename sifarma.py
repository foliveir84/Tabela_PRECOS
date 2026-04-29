import pandas as pd

def process_sifarma(uploaded_file):
    """
    Reads and processes Sifarma exported CSV data.
    Returns processed DataFrame or raises an error if required columns are missing.
    """
    # Ler CSV com separador ;
    csv_df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

    # Selecionar apenas colunas relevantes
    required_columns = ['CNP', 'DESIGNAÇÃO', 'PVF', 'PVP']

    if all(col in csv_df.columns for col in required_columns):
        # Verificar se existe coluna LÍQ. (opcional mas útil para a validação)
        has_liq = 'LÍQ.' in csv_df.columns
        cols_to_keep = required_columns + (['LÍQ.'] if has_liq else [])

        csv_df = csv_df[cols_to_keep]

        # Renomear e limpar
        rename_map = {'CNP': 'Codigo', 'PVP': 'PVP_Sifarma', 'PVF': 'PVF_Sifarma'}
        if has_liq:
            rename_map['LÍQ.'] = 'Liq_Sifarma'

        csv_df = csv_df.rename(columns=rename_map)
        csv_df['Codigo'] = pd.to_numeric(csv_df['Codigo'], errors='coerce')
        csv_df = csv_df.dropna(subset=['Codigo'])
        csv_df['Codigo'] = csv_df['Codigo'].astype(int)

        cols_to_numeric = ['PVF_Sifarma', 'PVP_Sifarma']
        if has_liq:
            cols_to_numeric.append('Liq_Sifarma')

        for col in cols_to_numeric:
            if csv_df[col].dtype == 'object':
                csv_df[col] = csv_df[col].str.replace(',', '.', regex=False)
            csv_df[col] = pd.to_numeric(csv_df[col], errors='coerce')
        
        return csv_df
    else:
        raise ValueError(f"O CSV carregado não tem as colunas obrigatórias: {', '.join(required_columns)}")
