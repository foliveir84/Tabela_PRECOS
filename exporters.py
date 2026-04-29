import io
import datetime
import pandas as pd

def to_excel_bytes(df: pd.DataFrame, sheet_name: str = 'Dados') -> bytes:
    """
    Converts a pandas DataFrame to an Excel file in memory and returns it as bytes.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

def get_export_filename(base_name: str) -> str:
    """
    Generates an export filename with the current date appended in YYYYMMDD format.
    Example: get_export_filename('report') -> 'report_20231027.xlsx'
    """
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    return f'{base_name}_{date_str}.xlsx'
