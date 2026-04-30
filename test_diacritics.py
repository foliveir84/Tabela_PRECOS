import pandas as pd
from exporters import to_excel_bytes

df = pd.DataFrame({
    'Descrição com Diacríticos': ['Atenção', 'Coração', 'Farmácia', 'Bónus', 'Álcool', 'Açúcar']
})

try:
    b = to_excel_bytes(df, "Teste")
    print(f"Success! Bytes written: {len(b)}")
except Exception as e:
    print(f"Error: {e}")