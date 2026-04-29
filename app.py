import streamlit as st
import pandas as pd
import io
import os

from google_sheets import get_sheet_url, load_google_sheet_data
from sifarma import process_sifarma
from infoprex import process_data, compare_infoprex_master

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Verificador de Preços",
                   page_icon="💊", layout="wide")

# --- UI PRINCIPAL ---
st.title("💊 Verificador de Preços Farmácia")

# Obter URL dinamicamente
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
        status.update(
            label=f"✅ Tabela Mestra Carregada ({len(final_df)} produtos)", state="complete", expanded=False)
    else:
        status.update(label="❌ Erro ao carregar Tabela Mestra", state="error")
        st.stop()

# --- TABS ---
tab_sifarma, tab_infoprex = st.tabs(["Sifarma (CSV)", "Infoprex (TXT)"])

# === TAB 1: SIFARMA ===
with tab_sifarma:
    st.markdown("### 1. Carregar Dados Sifarma")
    st.markdown(
        "Faça upload do ficheiro `export.csv` retirado da **Revisão de Preços** do Sifarma.")

    # Tutorial em vídeo
    with st.expander("🎥 Ver Tutorial: Como exportar o ficheiro?"):
        video_file = "ExportarFicheiro.mp4"
        if os.path.exists(video_file):
            st.video(video_file)
        else:
            st.warning(
                f"Vídeo '{video_file}' não encontrado na pasta do projeto.")

    uploaded_file = st.file_uploader("Upload do ficeiro do Sifarma",
                                     type=['csv'],
                                     help="Certifique-se que o separador é ';'",
                                     label_visibility="collapsed"
                                     )

    if uploaded_file is not None:
        try:
            csv_df = process_sifarma(uploaded_file)

            # --- ANÁLISE ---
            st.divider()
            st.markdown("### 2. Resultados da Análise")

            # Merge
            merged_df = pd.merge(
                final_df, csv_df, on='Codigo', how='inner')

            # --- ALERTA 1: PREÇO DE CUSTO (CRÍTICO - PVF SUPERIOR) ---
            # PVF > PC Actual * 1.01
            df_custo_alto = merged_df[merged_df['PVF_Sifarma'] > (
                merged_df['PC Actual'] * 1.01)].copy()

            if not df_custo_alto.empty:
                with st.container():
                    st.error(
                        f"🔴 **ALERTA CRÍTICO: {len(df_custo_alto)} Produtos com PVF SUPERIOR ao previsto**")
                    st.markdown(
                        "O Preço de Custo (PVF) no Sifarma é **mais de 1% superior** ao PC da Tabela Mestra. Prejuízo potencial.")

                    cols_custo = ['Codigo', 'DESIGNAÇÃO',
                                  'PC Actual', 'PVF_Sifarma']
                    st.dataframe(
                        df_custo_alto[cols_custo], use_container_width=True, hide_index=True)

            # --- ALERTA 2: POSSÍVEL ERRO TROCA PREÇO (PVF MUITO INFERIOR) ---
            # PVF < PC Actual * 0.95
            df_custo_baixo = merged_df[merged_df['PVF_Sifarma'] < (
                merged_df['PC Actual'] * 0.95)].copy()

            if not df_custo_baixo.empty:
                with st.container():
                    st.warning(
                        f"⚠️ **ALERTA DE VERIFICAÇÃO: {len(df_custo_baixo)} Produtos com PVF MUITO INFERIOR (>5%)**")
                    st.markdown(
                        "O PVF no Sifarma é **mais de 5% inferior** ao PC da Tabela. Possível erro de introdução (Troca com Preço Líquido?).")

                    cols_show = ['Codigo', 'DESIGNAÇÃO',
                                 'PC Actual', 'PVF_Sifarma']
                    if 'Liq_Sifarma' in df_custo_baixo.columns:
                        cols_show.append('Liq_Sifarma')

                    st.dataframe(
                        df_custo_baixo[cols_show], use_container_width=True, hide_index=True)

            # --- ALERTA 3: PVP DESATUALIZADO (AÇÃO) ---
            df_pvp_diff = merged_df[merged_df['PVP Actual'] != round(
                merged_df['PVP_Sifarma'], 2)].copy()

            if not df_pvp_diff.empty:
                st.info(
                    f"🔄 **Atualização Necessária: {len(df_pvp_diff)} Produtos com PVP incorreto**")

                cols_pvp = ['Codigo', 'DESIGNAÇÃO',
                            'PVP Actual', 'PVP_Sifarma']
                st.dataframe(
                    df_pvp_diff[cols_pvp], use_container_width=True, hide_index=True)

                st.download_button(
                    label="📥 Descarregar CSV para Atualização",
                    data=df_pvp_diff[['Codigo', 'DESIGNAÇÃO', 'PVP Actual']].to_csv(
                        index=False).encode('utf-8'),
                    file_name='atualizar_pvp_sifarma.csv',
                    mime='text/csv',
                    type="primary"
                )
            else:
                st.success("✅ Todos os PVPs estão atualizados!")

            # --- ALERTA 3: PRODUTOS EM FALTA (MISSING) ---
            df_missing = csv_df[~csv_df['Codigo'].isin(
                final_df['Codigo'])].copy()

            if not df_missing.empty:
                with st.expander(f"❓ **{len(df_missing)} Produtos não encontrados na Tabela Mestra**", expanded=True):
                    st.warning(
                        "Estes produtos constam no ficheiro do Sifarma mas **não existem** na Tabela Mestra da Google Sheet.")
                    st.dataframe(df_missing, hide_index=True,
                                 use_container_width=True)

                    # Excel buffer
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_missing.to_excel(
                            writer, index=False, sheet_name='Em Falta')

                    st.download_button(
                        label="📥 Descarregar Excel (Enviar para Seomara)",
                        data=buffer.getvalue(),
                        file_name='produtos_em_falta_tabela.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )

        except Exception as e:
            st.error(f"❌ Erro ao processar ficheiro: {e}")

# === TAB 2: INFOPREX ===
with tab_infoprex:
    st.markdown("### Comparação Infoprex vs Master")
    st.markdown(
        "Carregue o ficheiro `INFOPREX.TXT` para comparar preços e margens.")

    uploaded_infoprex = st.file_uploader("Carregar Infoprex", type=[
                                         'txt', 'csv'], key="infoprex_uploader")

    if uploaded_infoprex:
        try:
            # 1. Process Data
            df_infoprex = process_data(uploaded_infoprex)

            # 2. Compare Data
            diff_pvp = compare_infoprex_master(df_infoprex, final_df)

            # 3. UI & Filters
            st.divider()

            if diff_pvp.empty:
                st.success(
                    "✅ Todos os produtos correspondidos têm o PVP correto!")
            else:
                col1, col2, col3 = st.columns([2, 0.8, 1.5])
                with col1:
                    st.warning(
                        f"⚠️ Encontrados **{len(diff_pvp)}** produtos com PVP diferente.")
                with col2:
                    # Switch for Margin
                    filter_margin = st.toggle("Margem > 30%", value=False)
                with col3:
                    # Novo Filtro de Direção do Preço
                    filter_tipo = st.radio(
                        "Divergência:",
                        ["Todas", "Infoprex < Master", "Infoprex > Master"],
                        horizontal=True,
                        help="Filtra produtos onde o preço no sistema está abaixo ou acima da tabela mestra."
                    )

                # Apply Logic
                final_view = diff_pvp.copy()

                if filter_margin:
                    final_view = final_view[final_view["Margem"] > 30.0]

                if filter_tipo == "Infoprex < Master":
                    final_view = final_view[final_view["PVP_Infoprex"]
                                            < final_view["PVP Actual"]]
                    st.info(
                        f"🔍 Mostrando **{len(final_view)}** produtos onde o **PVP Infoprex < Master**.")
                elif filter_tipo == "Infoprex > Master":
                    final_view = final_view[final_view["PVP_Infoprex"]
                                            > final_view["PVP Actual"]]
                    st.info(
                        f"🔍 Mostrando **{len(final_view)}** produtos onde o **PVP Infoprex > Master**.")
                else:
                    st.info(
                        f"🔍 Mostrando **{len(final_view)}** produtos com divergência de preço.")

                if filter_margin:
                    st.caption(
                        "💡 *Filtro adicional: Apenas produtos com Margem > 30%.*")

                # Display Dataframe
                show_cols = ['Codigo', 'NOM', 'SAC',
                             'PVP Actual', 'PVP_Infoprex', 'Margem']

                # Rename for better display
                display_df = final_view[show_cols].rename(columns={
                    'NOM': 'Designação',
                    'SAC': 'Stock',
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
