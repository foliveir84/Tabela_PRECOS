# Project: Tabela_PRECOS

## Overview
This project is a Streamlit application designed to fetch, consolidate, and analyze price lists. It merges data from a Google Sheets document (containing "Actual" prices) with an exported CSV file (containing "Current System" prices) to identify discrepancies and missing items.

## Security & Deployment
This application avoids hardcoding sensitive links using **Streamlit Secrets**.

### Local Development
To run locally, the Google Sheet ID is stored in `.streamlit/secrets.toml`:
```toml
GOOGLE_SHEET_ID = "2PACX-..."
```
*Note: This file is ignored by git to protect your privacy.*

### Cloud Deployment (Streamlit Community Cloud)
1. Push your code to GitHub.
2. Connect your repository to Streamlit Cloud.
3. In the App Settings, go to **Secrets**.
4. Add the following key-value pair:
   ```toml
   GOOGLE_SHEET_ID = "2PACX-1vQrUrwXhW10bnIWJzkTeCXLkrH7zvDh-CMQ-SAbvg2ocLSmBP09qmCpD6dkDf4rbg"
   ```
5. Deploy. The app will automatically read this value.

## Features
- **Google Sheets Integration**: 
    - Fetches data using the ID configured in Secrets.
    - **Caching**: Implements `@st.cache_data` (1 hour TTL).
    - Cleans data: Removes empty rows, standardizes "Codigo" to integer, and prices to float.
    - **Fixes**: Handles mixed-type columns safely (string conversion before replacement).

- **CSV Import & Analysis**:
    - Upload `export.csv` (Sifarma).
    - Parses CSV with `;` separator.

- **Alerts**:
    1.  🔴 **Cost Price Alert**: PVF (System) > PC (Sheet) + 1%.
    2.  🔵 **Sales Price Update**: PVP (Sheet) != PVP (System).
    3.  🟡 **Missing Products**: Products in System but not in Sheet.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```