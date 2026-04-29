import streamlit as st
import pandas as pd
import io
import os

from google_sheets import build_google_sheet_url, fetch_and_process_master_table
from sifarma import (
    read_sifarma_csv, deduplicate_sifarma_data, 
    get_alert_1_high_cost, get_alert_2_low_cost, get_alert_3_pvp_divergence,
    get_alert_4_missing_pc, get_alert_5_missing_pvp, get_alert_6_not_in_master
)
from infoprex import detect_format_and_read, process_infoprex_data, apply_ui_filters, compare_infoprex_master
from exporters import to_excel_bytes, get_export_filename

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Verificador de Preços", page_icon="💊", layout="wide")

# --- UI PRINCIPAL ---
st.title("💊 Verificador de Preços Farmácia")

sheet_id = None
if "GOOGLE_SHEET_ID" in st.secrets:
    sheet_id = st.secrets["GOOGLE_SHEET_ID"]
elif "GOOGLE_SHEET_ID" in os.environ:
    sheet_id = os.environ["GOOGLE_SHEET_ID"]

if not sheet_id:
    with st.sidebar:
        st.warning("⚠️ ID da Google Sheet não configurado.")
        sheet_id = st.text_input("Introduza o ID da Google Sheet (ou parte 2PACX...):")

if not sheet_id:
    st.info("👈 Por favor configure o ID da Google Sheet nas 'Secrets' ou introduza na barra lateral.")
    st.stop()

sheet_url = build_google_sheet_url(sheet_id)

with st.sidebar:
    st.header("Estado do Sistema")
    if st.button("🔄 Recarregar Tabela Mestra"):
        fetch_and_process_master_table.clear()
        st.rerun()
    st.markdown("---")

# 1. Carregamento da Tabela Mestra
with st.status("A ligar à Tabela de Preços Mestra...", expanded=False) as status:
    try:
        master_data = fetch_and_process_master_table(sheet_url)
        df_master = master_data['df_master']
        df_invalid_pc = master_data['df_invalid_pc']
        df_invalid_pvp = master_data['df_invalid_pvp']
        corrupt_sheets = master_data['corrupt_sheets']
        last_updated = master_data['last_updated']
        
        status.update(label="✅ Tabela Mestra Carregada", state="complete", expanded=False)
        
        with st.sidebar:
            st.success(f"📦 {len(df_master)} produtos em memória")
            st.info(f"📅 Tabela actualizada em: {last_updated}")
            st.caption("🕐 Cache válido até: 1 hora")
            
    except Exception as e:
        status.update(label="❌ Erro ao carregar Tabela Mestra", state="error")
        st.error(f"Erro: {e}")
        st.stop()

if corrupt_sheets:
    with st.expander(f"⚠️ Laboratórios não processados — {len(corrupt_sheets)} abas com estrutura inválida"):
        st.write(corrupt_sheets)

# --- TABS ---
tab_sifarma, tab_infoprex = st.tabs(["Sifarma (CSV)", "Infoprex (TXT)"])

# === TAB 1: SIFARMA ===
with tab_sifarma:
    st.markdown("### 1. Carregar Dados Sifarma")
    
    with st.expander("🎥 Ver Tutorial: Como exportar o ficheiro?"):
        video_file = "ExportarFicheiro.mp4"
        if os.path.exists(video_file):
            st.video(video_file)
        else:
            st.warning(f"Vídeo '{video_file}' não encontrado na pasta.")

    uploaded_file = st.file_uploader("Upload do ficheiro Sifarma", type=['csv'], help="Certifique-se que o separador é ';'", label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            df_sifarma = read_sifarma_csv(uploaded_file)
            df_sifarma_clean, critical_errors = deduplicate_sifarma_data(df_sifarma)
            
            st.divider()
            st.markdown("### 2. Resultados da Análise")
            
            if critical_errors:
                st.error(f"🔴 Erro Crítico: {len(critical_errors)} Linha(s) de bónus sem desconto 100% registado no Sifarma (PVF=0).")
                st.dataframe(critical_errors)

            # Alert 1
            df_a1 = get_alert_1_high_cost(df_sifarma_clean, df_master)
            if not df_a1.empty:
                st.error(f"🔴 ALERTA CRÍTICO: {len(df_a1)} Produtos com PVF SUPERIOR ao previsto")
                st.dataframe(df_a1, hide_index=True)
                st.download_button("📥 Exportar Alerta Custo Superior", to_excel_bytes(df_a1, "Custo Superior"), get_export_filename("alerta_pvf_superior"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 2
            df_a2 = get_alert_2_low_cost(df_sifarma_clean, df_master)
            if not df_a2.empty:
                st.warning(f"⚠️ ALERTA DE VERIFICAÇÃO: {len(df_a2)} Produtos com PVF MUITO INFERIOR (>10%)")
                st.dataframe(df_a2, hide_index=True)
                st.download_button("📥 Exportar Alerta Custo Inferior", to_excel_bytes(df_a2, "Custo Inferior"), get_export_filename("alerta_pvf_inferior"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 3
            df_a3 = get_alert_3_pvp_divergence(df_sifarma_clean, df_master)
            if not df_a3.empty:
                st.info(f"🔄 PVP a Actualizar: {len(df_a3)} Produtos")
                st.dataframe(df_a3, hide_index=True)
                st.download_button("📥 Exportar Alerta PVP Divergente", to_excel_bytes(df_a3, "PVP Divergente"), get_export_filename("alerta_pvp_divergente"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 4
            df_a4 = get_alert_4_missing_pc(df_sifarma_clean, df_invalid_pc)
            if not df_a4.empty:
                st.warning(f"⚠️ Tabela Mestra Incompleta — PC Atual ({len(df_a4)} Produtos)")
                st.dataframe(df_a4, hide_index=True)
                st.download_button("📥 Exportar Alerta PC Inválido", to_excel_bytes(df_a4, "PC Inválido"), get_export_filename("alerta_pc_invalido"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 5
            df_a5 = get_alert_5_missing_pvp(df_sifarma_clean, df_invalid_pvp)
            if not df_a5.empty:
                st.warning(f"⚠️ Tabela Mestra Incompleta — PVP Atual ({len(df_a5)} Produtos)")
                st.dataframe(df_a5, hide_index=True)
                st.download_button("📥 Exportar Alerta PVP Inválido", to_excel_bytes(df_a5, "PVP Inválido"), get_export_filename("alerta_pvp_invalido"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 6
            df_a6 = get_alert_6_not_in_master(df_sifarma_clean, df_master)
            if not df_a6.empty:
                with st.expander(f"❓ {len(df_a6)} Produtos não encontrados na Tabela Mestra", expanded=True):
                    st.dataframe(df_a6, hide_index=True)
                    st.download_button("📥 Exportar Excel (Enviar para Gilda)", to_excel_bytes(df_a6, "Em Falta"), get_export_filename("produtos_em_falta_tabela"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            st.error(f"❌ Erro ao processar ficheiro Sifarma: {e}")

# === TAB 2: INFOPREX ===
with tab_infoprex:
    st.markdown("### Comparação Infoprex vs Master")
    
    uploaded_infoprex = st.file_uploader("Carregar Infoprex", type=['txt', 'csv', 'tsv'], key="infoprex_uploader", label_visibility="collapsed")

    if uploaded_infoprex:
        try:
            df_info_raw = detect_format_and_read(uploaded_infoprex)
            df_info_proc = process_infoprex_data(df_info_raw)
            diff_pvp = compare_infoprex_master(df_info_proc, df_master)
            
            st.divider()
            
            if diff_pvp.empty:
                st.success("✅ Todos os produtos correspondidos têm o PVP correto!")
            else:
                col1, col2, col3 = st.columns([2, 0.8, 1.5])
                with col1:
                    st.warning(f"⚠️ Encontrados **{len(diff_pvp)}** produtos com PVP diferente.")
                with col2:
                    filter_margin = st.toggle("Margem > 30%", value=False)
                with col3:
                    filter_tipo = st.radio("Divergência:", ["Todas", "Infoprex < Master", "Infoprex > Master"], horizontal=True)

                final_view = apply_ui_filters(diff_pvp, filter_tipo, filter_margin)
                
                show_cols = ['CNP', 'Descrição', 'Stock', 'PVP Atual', 'PVP_Infoprex', 'Margem']
                display_df = final_view[show_cols].rename(columns={
                    'PVP Atual': 'PVP Master',
                    'PVP_Infoprex': 'PVP Infoprex',
                    'Margem': 'Margem (%)'
                })

                edited_df = st.data_editor(display_df, use_container_width=True, hide_index=True, num_rows='dynamic')

                st.download_button(
                    label="📥 Descarregar Resultados (.xlsx)",
                    data=to_excel_bytes(edited_df, "Infoprex"),
                    file_name=get_export_filename("divergencias_infoprex"),
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

        except Exception as e:
            st.error(f"❌ Erro ao processar ficheiro Infoprex: {e}")
