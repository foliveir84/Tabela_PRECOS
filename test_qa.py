import pandas as pd
from sifarma import read_sifarma_csv, deduplicate_sifarma_data, get_alert_1_high_cost, get_alert_2_low_cost, get_alert_3_pvp_divergence
from infoprex import detect_format_and_read, process_infoprex_data, compare_infoprex_master

# Mock df_master, df_invalid_pc, df_invalid_pvp for testing
df_master = pd.DataFrame({
    'CNP': [7753194, 1234567, 7654321],
    'PC Atual': [10.0, 5.0, 20.0],
    'PVP Atual': [15.0, 7.5, 30.0]
})
df_invalid_pc = pd.DataFrame(columns=['CNP', 'PC Atual', 'PVP Atual'])
df_invalid_pvp = pd.DataFrame(columns=['CNP', 'PC Atual', 'PVP Atual'])

print('--- QA SIFARMA ---')
try:
    df_sifarma = read_sifarma_csv('export.csv')
    df_sifarma_clean, critical_errors = deduplicate_sifarma_data(df_sifarma)
    a1 = get_alert_1_high_cost(df_sifarma_clean, df_master)
    a2 = get_alert_2_low_cost(df_sifarma_clean, df_master)
    a3 = get_alert_3_pvp_divergence(df_sifarma_clean, df_master)
    print(f'Sifarma Clean length: {len(df_sifarma_clean)}')
    print(f'Alert 1 length: {len(a1)}')
    print(f'Alert 2 length: {len(a2)}')
    print(f'Alert 3 length: {len(a3)}')
    print('Sifarma QA Passed')
except Exception as e:
    print(f'Sifarma Error: {e}')

print('--- QA INFOPREX NOVO ---')
try:
    with open('NOVO.txt', 'rb') as f:
        df_novo = detect_format_and_read(f)
    if df_novo is not None and not df_novo.empty:
        df_novo_proc = process_infoprex_data(df_novo)
        diff_novo = compare_infoprex_master(df_novo_proc, df_master)
        print(f'Infoprex NOVO Clean length: {len(df_novo_proc)}')
        print(f'Infoprex NOVO Diff length: {len(diff_novo)}')
        print('Infoprex NOVO QA Passed')
    else:
        print('Infoprex NOVO empty')
except Exception as e:
    print(f'Infoprex NOVO Error: {e}')

print('--- QA INFOPREX VELHO ---')
try:
    with open('Velho.TXT', 'rb') as f:
        df_velho = detect_format_and_read(f)
    if df_velho is not None and not df_velho.empty:
        df_velho_proc = process_infoprex_data(df_velho)
        diff_velho = compare_infoprex_master(df_velho_proc, df_master)
        print(f'Infoprex VELHO Clean length: {len(df_velho_proc)}')
        print(f'Infoprex VELHO Diff length: {len(diff_velho)}')
        print('Infoprex VELHO QA Passed')
    else:
        print('Infoprex VELHO empty')
except Exception as e:
    print(f'Infoprex VELHO Error: {e}')
