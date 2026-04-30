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

# --- DESIGN SYSTEM ---
def inject_design_system():
    st.markdown("""
    <script src="https://cdn.tailwindcss.com/"></script>
    <script>
      tailwind.config = {
        corePlugins: { preflight: false }
      }
    </script>
    <script src="https://code.iconify.design/iconify-icon/1.0.7/iconify-icon.min.js"></script>
    <style>
        .stApp { font-family: 'Inter', sans-serif; background-color: #0a0a0a; color: #ffffff; }
        /* Componentes NexusFlow */
        .nf-card { background: rgba(24, 24, 27, 0.6); border: 1px solid rgba(255,255,255,0.05); border-radius: 0.75rem; padding: 1.5rem; }
        .nf-badge { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; }
        .nf-badge-primary { background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.3); color: #fb923c; }
        .nf-badge-error { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #f87171; }
        .nf-badge-warning { background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.3); color: #facc15; }
        .nf-badge-info { background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.3); color: #60a5fa; }
        .nf-badge-success { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); color: #4ade80; }
        .nf-alert { display: flex; align-items: center; gap: 0.75rem; padding: 1rem; border-radius: 0.75rem; font-size: 0.875rem; margin-bottom: 1rem; font-weight: 500; }
        .nf-alert-error { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #fca5a5; }
        .nf-alert-warning { background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.3); color: #fdba74; }
        .nf-alert-info { background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.3); color: #93c5fd; }
        .nf-alert-success { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); color: #86efac; }
        /* Typography overrides */
        h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 400 !important; letter-spacing: -0.025em; }
        hr { border-color: rgba(255,255,255,0.1) !important; }
        /* Tweak Streamlit inputs */
        div[data-baseweb="input"] > div { background-color: #161616 !important; border-color: #262626 !important; }
        div[data-baseweb="select"] > div { background-color: #161616 !important; border-color: #262626 !important; }
        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    </style>
    """, unsafe_allow_html=True)

def ui_alert(message, alert_type="info", icon=None):
    if not icon:
        icons = {
            "error": "lucide:alert-circle",
            "warning": "lucide:alert-triangle",
            "info": "lucide:info",
            "success": "lucide:check-circle-2"
        }
        icon = icons.get(alert_type, "lucide:info")
    
    html = f"""
    <div class="nf-alert nf-alert-{alert_type}">
        <iconify-icon icon="{icon}" class="text-xl"></iconify-icon>
        <span>{message}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def ui_header(title, subtitle=None, icon="lucide:layers"):
    html = f"""
    <div class="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-[0_0_15px_rgba(249,115,22,0.3)]">
            <iconify-icon icon="{icon}" class="text-white text-xl"></iconify-icon>
        </div>
        <div>
            <h2 class="text-2xl font-normal text-white tracking-tight m-0">{title}</h2>
            {f'<p class="text-sm text-neutral-400 font-light m-0 mt-1">{subtitle}</p>' if subtitle else ''}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def ui_sidebar_status(version="1.0.0", last_updated="Ainda não carregada", total_products=0):
    html = f"""
    <div class="nf-card flex flex-col gap-4 mt-4">
        <div class="flex items-center justify-between">
            <span class="text-sm text-neutral-400">Versão do Sistema</span>
            <span class="nf-badge nf-badge-primary">v{version}</span>
        </div>
        <div class="flex items-center justify-between border-t border-white/5 pt-3">
            <div class="flex items-center gap-2 text-sm text-neutral-400">
                <iconify-icon icon="lucide:database"></iconify-icon>
                <span>Produtos na Tabela Mestra</span>
            </div>
            <span class="text-sm text-white font-medium">{total_products}</span>
        </div>
        <div class="flex flex-col gap-1 border-t border-white/5 pt-3">
            <div class="flex items-center gap-2 text-sm text-neutral-400">
                <iconify-icon icon="lucide:clock"></iconify-icon>
                <span>Última Atualização</span>
            </div>
            <span class="text-xs text-neutral-500">{last_updated}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


inject_design_system()

# --- UI PRINCIPAL ---
ui_header("Verificador de Preços Farmácia", "Análise e correspondência de preços (Sifarma & Infoprex)")

sheet_id = None
if "GOOGLE_SHEET_ID" in st.secrets:
    sheet_id = st.secrets["GOOGLE_SHEET_ID"]
elif "GOOGLE_SHEET_ID" in os.environ:
    sheet_id = os.environ["GOOGLE_SHEET_ID"]

if not sheet_id:
    with st.sidebar:
        ui_alert("ID da Google Sheet não configurado.", "warning")
        sheet_id = st.text_input("Introduza o ID da Google Sheet (ou parte 2PACX...):")

if not sheet_id:
    ui_alert("Por favor, configure o ID da Google Sheet nas 'Secrets' ou introduza-o na barra lateral.", "info", "lucide:arrow-left-circle")
    st.stop()

sheet_url = build_google_sheet_url(sheet_id)

with st.sidebar:
    st.markdown("### Estado do Sistema")
    if st.button("🔄 Recarregar Tabela Mestra", type="primary"):
        fetch_and_process_master_table.clear()
        st.rerun()

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
            ui_sidebar_status(version="1.1.0", last_updated=last_updated, total_products=len(df_master))
            
    except Exception as e:
        status.update(label="❌ Erro ao carregar Tabela Mestra", state="error")
        ui_alert(f"Erro: {e}", "error")
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
            ui_alert(f"Vídeo '{video_file}' não encontrado na pasta.", "warning")

    uploaded_file = st.file_uploader("Carregar ficheiro Sifarma", type=['csv'], help="Certifique-se de que o separador é ';'", label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            df_sifarma = read_sifarma_csv(uploaded_file)
            df_sifarma_clean, critical_errors = deduplicate_sifarma_data(df_sifarma)
            
            st.divider()
            st.markdown("### 2. Resultados da Análise")
            
            if critical_errors:
                ui_alert(f"Erro Crítico: {len(critical_errors)} Linha(s) de bónus sem desconto 100% registado no Sifarma (PVF=0).", "error")
                st.dataframe(critical_errors, width='stretch')

            # Alert 1
            df_a1 = get_alert_1_high_cost(df_sifarma_clean, df_master)
            if not df_a1.empty:
                ui_alert(f"ALERTA CRÍTICO: {len(df_a1)} Produtos com PVF SUPERIOR ao previsto", "error")
                st.dataframe(df_a1, hide_index=True, width='stretch')
                st.download_button("📥 Exportar Alerta Custo Superior (.xlsx)", to_excel_bytes(df_a1, "Custo Superior"), get_export_filename("alerta_pvf_superior"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 2
            df_a2 = get_alert_2_low_cost(df_sifarma_clean, df_master)
            if not df_a2.empty:
                ui_alert(f"ALERTA DE VERIFICAÇÃO: {len(df_a2)} Produtos com PVF MUITO INFERIOR (>10%)", "warning")
                st.dataframe(df_a2, hide_index=True, width='stretch')
                st.download_button("📥 Exportar Alerta Custo Inferior (.xlsx)", to_excel_bytes(df_a2, "Custo Inferior"), get_export_filename("alerta_pvf_inferior"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 3
            df_a3 = get_alert_3_pvp_divergence(df_sifarma_clean, df_master)
            if not df_a3.empty:
                ui_alert(f"PVP a Atualizar: {len(df_a3)} Produtos", "info", "lucide:refresh-cw")
                st.dataframe(df_a3, hide_index=True, width='stretch')
                st.download_button("📥 Exportar Alerta PVP Divergente (.xlsx)", to_excel_bytes(df_a3, "PVP Divergente"), get_export_filename("alerta_pvp_divergente"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 4
            df_a4 = get_alert_4_missing_pc(df_sifarma_clean, df_invalid_pc)
            if not df_a4.empty:
                ui_alert(f"Tabela Mestra Incompleta — PC Atual ({len(df_a4)} Produtos)", "warning")
                st.dataframe(df_a4, hide_index=True, width='stretch')
                st.download_button("📥 Exportar Alerta PC Inválido (.xlsx)", to_excel_bytes(df_a4, "PC Inválido"), get_export_filename("alerta_pc_invalido"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 5
            df_a5 = get_alert_5_missing_pvp(df_sifarma_clean, df_invalid_pvp)
            if not df_a5.empty:
                ui_alert(f"Tabela Mestra Incompleta — PVP Atual ({len(df_a5)} Produtos)", "warning")
                st.dataframe(df_a5, hide_index=True, width='stretch')
                st.download_button("📥 Exportar Alerta PVP Inválido (.xlsx)", to_excel_bytes(df_a5, "PVP Inválido"), get_export_filename("alerta_pvp_invalido"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Alert 6
            df_a6 = get_alert_6_not_in_master(df_sifarma_clean, df_master, df_invalid_pc, df_invalid_pvp)
            if not df_a6.empty:
                with st.expander(f"❓ {len(df_a6)} Produtos não encontrados na Tabela Mestra", expanded=True):
                    st.dataframe(df_a6, hide_index=True, width='stretch')
                    st.download_button("📥 Exportar Produtos em Falta (.xlsx)", to_excel_bytes(df_a6, "Em Falta"), get_export_filename("produtos_em_falta_tabela"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            ui_alert(f"Erro ao processar ficheiro Sifarma: {e}", "error")

# === TAB 2: INFOPREX ===
with tab_infoprex:
    st.markdown("### Comparação Infoprex vs Tabela Mestra")
    
    uploaded_infoprex = st.file_uploader("Carregar ficheiro Infoprex", type=['txt', 'csv', 'tsv'], key="infoprex_uploader", label_visibility="collapsed")

    if uploaded_infoprex:
        try:
            df_info_raw = detect_format_and_read(uploaded_infoprex)
            df_info_proc = process_infoprex_data(df_info_raw)
            diff_pvp = compare_infoprex_master(df_info_proc, df_master)
            
            st.divider()
            
            if diff_pvp.empty:
                ui_alert("Todos os produtos correspondidos têm o PVP correto!", "success")
            else:
                col1, col2, col3 = st.columns([2, 0.8, 1.5])
                with col1:
                    ui_alert(f"Encontrados **{len(diff_pvp)}** produtos com PVP diferente.", "warning")
                with col2:
                    filter_margin = st.toggle("Margem > 30%", value=False)
                with col3:
                    filter_tipo = st.radio("Filtro de Divergência:", ["Todas", "Infoprex < Mestra", "Infoprex > Mestra"], horizontal=True)

                if filter_tipo == "Infoprex < Mestra":
                    tipo_param = "Infoprex < Master"
                elif filter_tipo == "Infoprex > Mestra":
                    tipo_param = "Infoprex > Master"
                else:
                    tipo_param = "Todas"

                final_view = apply_ui_filters(diff_pvp, tipo_param, filter_margin)
                
                show_cols = ['CNP', 'Descrição', 'Stock', 'PVP Atual', 'PVP_Infoprex', 'Margem']
                display_df = final_view[show_cols].rename(columns={
                    'PVP Atual': 'PVP Mestra',
                    'PVP_Infoprex': 'PVP Infoprex',
                    'Margem': 'Margem (%)'
                })

                edited_df = st.data_editor(display_df, width='stretch', hide_index=True, num_rows='dynamic')

                st.download_button(
                    label="📥 Descarregar Resultados (.xlsx)",
                    data=to_excel_bytes(edited_df, "Infoprex"),
                    file_name=get_export_filename("divergencias_infoprex"),
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

        except Exception as e:
            ui_alert(f"Erro ao processar ficheiro Infoprex: {e}", "error")
