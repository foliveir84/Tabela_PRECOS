# Project: Tabela_PRECOS

## Overview
This project is a Streamlit application designed to fetch, consolidate, and analyze price lists. It merges data from a Google Sheets document (containing "Actual" prices) with an exported CSV file (containing "Current System" prices) to identify discrepancies and missing items.

## Features
- **Google Sheets Integration**: 
    - Fetches data from a public Google Sheet without API keys.
    - **Caching**: Implements `@st.cache_data` (1 hour TTL) to load and process the heavy Excel file only once per session/hour, significantly improving performance. Includes a manual "Reload" button.
    - Iterates through all sheets.
    - Filters for sheets with "PVP" and "PC" columns (handling "atual"/"actual").
    - Cleans data: Removes empty rows, standardizes "Codigo" to integer, and prices to float.

- **CSV Import & Analysis**:
    - Upload functionality for `export.csv` (exported from Sifarma).
    - Parses CSV with semicolon (`;`) separator.
    - Extracts `CNP`, `DESIGNACAO`, `PVF`, `PVP`.

- **Automated Comparisons**:
    1.  **Cost Price Check**: Identifies products where the System Cost Price (`PVF`) is significantly higher (>1%) than the Sheet Cost Price (`PC Actual`).
        - *Goal*: Flag potentially incorrect cost prices for review ("Verificar com a Seomara").
    2.  **Sales Price Check**: Identifies products where the Sheet Sales Price (`PVP Actual`) differs from the System Sales Price (`PVP`).
        - *Goal*: Generate a list of products requiring price updates in the system ("Produtos que necessitam de PVP actualizado").
    3.  **Missing Products Check**: Identifies products present in the CSV export but missing from the Google Sheets Price Table.
        - *Goal*: Flag products that need to be added to the official price table ("Enviar para a Seomara").
        - *Output*: Exportable Excel file.

## Structure
- `app.py`: The main Streamlit application containing all logic.
- `requirements.txt`: Project dependencies (`streamlit`, `pandas`, `openpyxl`, `requests`).
- `tabela_precos.ipynb`: Original notebook (development sandbox).

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Development Conventions
- **Data Types**: 'Codigo' is always `int`. Prices are `float`.
- **Merge Strategy**: Inner join on 'Codigo' (CNP). Only products present in BOTH sources are analyzed.
- **Error Handling**: Rows with non-numeric price data in critical columns are discarded to ensure analysis stability.
