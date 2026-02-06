import streamlit as st
import pandas as pd
import re
import io
import os
from processador_infop import process_data

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Verificador de Preços", page_icon="💊", layout="wide")

# --- FUNÇÕES AUXILIARES ---
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
            sheet_id = st.text_input("Introduza o ID da Google Sheet (ou parte 2PACX...):")

    if sheet_id:
        # Construct URL based on ID type
        # If it starts with 2PACX, it's a "Published to Web" link
        if sheet_id.startswith("2PACX"):
             return f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=xlsx"
        # Otherwise assume standard ID
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
        # Use openpyxl engine for .xlsx
        xls = pd.ExcelFile(url, engine='openpyxl')
        
        valid_dataframes = []
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            if df.empty:
                continue
                
            # Find target columns
            target_cols = find_target_columns(df.columns)
            
            if target_cols:
                # Extract columns: 1st column (Code), PVP, PC
                first_col = df.columns[0]
                pvp_col = target_cols['pvp']
                pc_col = target_cols['pc']
                
                # Create a subset dataframe
                temp_df = df[[first_col, pvp_col, pc_col]].copy()
                
                # Rename for consistency
                temp_df.columns = ['Codigo', 'PVP Actual', 'PC Actual']
                
                valid_dataframes.append(temp_df)
        
        if valid_dataframes:
            final_df = pd.concat(valid_dataframes, ignore_index=True)
            
            # 1. Remover linhas onde todas as colunas estão vazias
            final_df = final_df.dropna(how='all')
            
            # 2. Converter colunas para float e remover linhas inválidas
            for col in ['PVP Actual', 'PC Actual']:
                # Convert to string first to ensure .str.replace works on all values (handling mixed types)
                final_df[col] = final_df[col].astype(str).str.replace(',', '.', regex=False)
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            
            # 3. Converter Coluna Codigo para int
            final_df['Codigo'] = pd.to_numeric(final_df['Codigo'], errors='coerce')
            
            # 4. Remover linhas onde PVP, PC ou Codigo não puderam ser convertidos (NaN)
            final_df = final_df.dropna(subset=['Codigo', 'PVP Actual', 'PC Actual'])
            
            # Arredondar PVP Actual a 2 casas decimais
            final_df['PVP Actual'] = final_df['PVP Actual'].round(2)
            
            # Converter Codigo para int64 após limpar NaNs
            final_df['Codigo'] = final_df['Codigo'].astype(int)
            
            return final_df
        return None

    except Exception as e:
        st.error(f"Erro ao carregar dados da Google Sheet: {e}")
        return None

# --- UI PRINCIPAL ---

st.title("💊 Verificador de Preços Farmácia")

# Obter URL dinamicamente (Secrets > Env > Input)
sheet_url = get_sheet_url()

# Sidebar com Status e Ações
with st.sidebar:
    st.header("Estado do Sistema")
    if st.button("🔄 Recarregar Tabela Mestra"):
        load_google_sheet_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("ℹ️ **Versão:** 1.5")

if not sheet_url:
    st.info("👈 Por favor configure o ID da Google Sheet nas 'Secrets' ou introduza na barra lateral.")
    st.stop()

# 1. Carregamento da Tabela Mestra (Fundo)
with st.status("A ligar à Tabela de Preços Mestra...", expanded=False) as status:
    final_df = load_google_sheet_data(sheet_url)
    if final_df is not None:
        status.update(label=f"✅ Tabela Mestra Carregada ({len(final_df)} produtos)", state="complete", expanded=False)
    else:
        status.update(label="❌ Erro ao carregar Tabela Mestra", state="error")
        st.stop()

# --- TABS ---
tab_sifarma, tab_infoprex = st.tabs(["Sifarma (CSV)", "Infoprex (TXT)"])

# === TAB 1: SIFARMA ===
with tab_sifarma:
    st.markdown("### 1. Carregar Dados Sifarma")
    st.markdown("Faça upload do ficheiro `export.csv` retirado da **Revisão de Preços** do Sifarma.")

    # Tutorial em vídeo
    with st.expander("🎥 Ver Tutorial: Como exportar o ficheiro?"):
        video_file = "ExportarFicheiro.mp4"
        if os.path.exists(video_file):
            st.video(video_file)
        else:
            st.warning(f"Vídeo '{video_file}' não encontrado na pasta do projeto.")

    uploaded_file = st.file_uploader("", type=['csv'], help="Certifique-se que o separador é ';'")

    if uploaded_file is not None:
        try:
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
                
                # --- ANÁLISE ---
                st.divider()
                st.markdown("### 2. Resultados da Análise")
                
                # Merge
                merged_df = pd.merge(final_df, csv_df, on='Codigo', how='inner')
                
                # --- ALERTA 1: PREÇO DE CUSTO (CRÍTICO - PVF SUPERIOR) ---
                # PVF > PC Actual * 1.01
                df_custo_alto = merged_df[merged_df['PVF_Sifarma'] > (merged_df['PC Actual'] * 1.01)].copy()
                
                if not df_custo_alto.empty:
                    with st.container():
                        st.error(f"🔴 **ALERTA CRÍTICO: {len(df_custo_alto)} Produtos com PVF SUPERIOR ao previsto**")
                        st.markdown("O Preço de Custo (PVF) no Sifarma é **mais de 1% superior** ao PC da Tabela Mestra. Prejuízo potencial.")
                        
                        cols_custo = ['Codigo', 'DESIGNAÇÃO', 'PC Actual', 'PVF_Sifarma']
                        st.dataframe(df_custo_alto[cols_custo], use_container_width=True, hide_index=True)

                # --- ALERTA 2: POSSÍVEL ERRO TROCA PREÇO (PVF MUITO INFERIOR) ---
                # PVF < PC Actual * 0.95
                df_custo_baixo = merged_df[merged_df['PVF_Sifarma'] < (merged_df['PC Actual'] * 0.95)].copy()

                if not df_custo_baixo.empty:
                    with st.container():
                        st.warning(f"⚠️ **ALERTA DE VERIFICAÇÃO: {len(df_custo_baixo)} Produtos com PVF MUITO INFERIOR (>5%)**")
                        st.markdown("O PVF no Sifarma é **mais de 5% inferior** ao PC da Tabela. Possível erro de introdução (Troca com Preço Líquido?).")
                        
                        cols_show = ['Codigo', 'DESIGNAÇÃO', 'PC Actual', 'PVF_Sifarma']
                        if 'Liq_Sifarma' in df_custo_baixo.columns:
                            cols_show.append('Liq_Sifarma')
                        
                        st.dataframe(df_custo_baixo[cols_show], use_container_width=True, hide_index=True)
                
                # --- ALERTA 3: PVP DESATUALIZADO (AÇÃO) ---
                df_pvp_diff = merged_df[merged_df['PVP Actual'] != round(merged_df['PVP_Sifarma'], 2)].copy()
                
                if not df_pvp_diff.empty:
                    st.info(f"🔄 **Atualização Necessária: {len(df_pvp_diff)} Produtos com PVP incorreto**")
                    
                    cols_pvp = ['Codigo', 'DESIGNAÇÃO', 'PVP Actual', 'PVP_Sifarma']
                    st.dataframe(df_pvp_diff[cols_pvp], use_container_width=True, hide_index=True)
                    
                    st.download_button(
                        label="📥 Descarregar CSV para Atualização",
                        data=df_pvp_diff[['Codigo', 'DESIGNAÇÃO', 'PVP Actual']].to_csv(index=False).encode('utf-8'),
                        file_name='atualizar_pvp_sifarma.csv',
                        mime='text/csv',
                        type="primary"
                    )
                else:
                    st.success("✅ Todos os PVPs estão atualizados!")

                # --- ALERTA 3: PRODUTOS EM FALTA (MISSING) ---
                df_missing = csv_df[~csv_df['Codigo'].isin(final_df['Codigo'])].copy()
                
                if not df_missing.empty:
                    with st.expander(f"❓ **{len(df_missing)} Produtos não encontrados na Tabela Mestra**", expanded=True):
                        st.warning("Estes produtos constam no ficheiro do Sifarma mas **não existem** na Tabela Mestra da Google Sheet.")
                        st.dataframe(df_missing, hide_index=True, use_container_width=True)
                        
                        # Excel buffer
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_missing.to_excel(writer, index=False, sheet_name='Em Falta')
                        
                        st.download_button(
                            label="📥 Descarregar Excel (Enviar para Seomara)",
                            data=buffer.getvalue(),
                            file_name='produtos_em_falta_tabela.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
            
            else:
                st.error(f"❌ O CSV carregado não tem as colunas obrigatórias: {', '.join(required_columns)}")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar ficheiro: {e}")

# === TAB 2: INFOPREX ===
with tab_infoprex:
    st.markdown("### Comparação Infoprex vs Master")
    st.markdown("Carregue o ficheiro `INFOPREX.TXT` para comparar preços e margens.")
    
    uploaded_infoprex = st.file_uploader("Carregar Infoprex", type=['txt', 'csv'], key="infoprex_uploader")
    
    if uploaded_infoprex:
        try:
            # 1. Process Data
            df_infoprex = process_data(uploaded_infoprex)
            
            # 2. Prepare for Merge
            # Convert CPR to int to match Codigo from Master
            df_infoprex['CPR'] = pd.to_numeric(df_infoprex['CPR'], errors='coerce')
            df_infoprex = df_infoprex.dropna(subset=['CPR'])
            df_infoprex['CPR'] = df_infoprex['CPR'].astype(int)
            
            # 3. Merge
            # Master: Codigo, PVP Actual, PC Actual
            # Infoprex: CPR, NOM, PVP, Margem
            merged_info = pd.merge(
                final_df, 
                df_infoprex, 
                left_on='Codigo', 
                right_on='CPR', 
                how='inner'
            )
            
            # 4. Filter Differences
            # Rounding to 2 decimal places to avoid float precision issues
            merged_info['PVP Actual'] = merged_info['PVP Actual'].round(2)
            merged_info['PVP_Infoprex'] = merged_info['PVP'].round(2)
            
            # Comparison
            diff_pvp = merged_info[merged_info['PVP Actual'] != merged_info['PVP_Infoprex']].copy()
            
            # 5. UI & Filters
            st.divider()
            
            if diff_pvp.empty:
                st.success("✅ Todos os produtos correspondidos têm o PVP correto!")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.warning(f"⚠️ Encontrados **{len(diff_pvp)}** produtos com PVP diferente da Tabela Master.")
                with col2:
                    # Switch for Margin
                    filter_margin = st.toggle("Apenas Margem > 30%", value=False)
                
                # Apply Logic
                if filter_margin:
                    # Filter: Diff AND Margin > 30
                    final_view = diff_pvp[diff_pvp['Margem'] > 30.0].copy()
                    st.info(f"Mostrando **{len(final_view)}** produtos com diferença de preço E Margem > 30%.")
                    st.caption("Estes produtos têm margem suficiente para estar alinhados com a tabela, mas não estão.")
                else:
                    final_view = diff_pvp
                    st.info("Mostrando **todos** os produtos com diferença de preço (qualquer margem).")
                    st.caption("Produtos com margem < 30% podem ter preços diferentes justificadamente (compras sem desconto).")
                
                # Display Dataframe
                show_cols = ['Codigo', 'NOM', 'PVP Actual', 'PVP_Infoprex', 'Margem']
                
                # Rename for better display
                display_df = final_view[show_cols].rename(columns={
                    'NOM': 'Designação',
                    'PVP Actual': 'PVP Master',
                    'PVP_Infoprex': 'PVP Infoprex'
                })
                
                st.dataframe(
                    display_df.style.format({
                        'PVP Master': '{:.2f} €',
                        'PVP Infoprex': '{:.2f} €',
                        'Margem': '{:.1f} %'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download Button
                st.download_button(
                    label="📥 Descarregar Resultados (CSV)",
                    data=display_df.to_csv(index=False).encode('utf-8'),
                    file_name='divergencias_infoprex.csv',
                    mime='text/csv'
                )

        except Exception as e:
            st.error(f"❌ Erro ao processar ficheiro Infoprex: {e}")
