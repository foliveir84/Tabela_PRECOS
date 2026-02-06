# Project: Tabela_PRECOS

## Overview
This project is a **Streamlit application** designed to help pharmacy staff verify and update product prices. It acts as a bridge between the official price table (hosted on Google Sheets) and the pharmacy's internal system (Sifarma), identifying discrepancies in Cost Prices (PC) and Sales Prices (PVP).

## Key Features

### 1. Data Integration & Performance
- **Google Sheets**: Fetches the "Master Price Table" securely using a Sheet ID configured via Secrets or Environment Variables.
- **Smart Caching**: Uses `@st.cache_data` with a 1-hour TTL to prevent repetitive, slow downloads of the Excel file. Includes a manual "Reload" button.
- **Robust Cleaning**: Handles data type inconsistencies (mixed strings/floats with commas) to ensure no valid price data is lost during processing.

### 2. Analysis & Alerts
The app compares the Master Table against an uploaded `export.csv` from Sifarma and generates four specific alerts:
- 🔴 **Critical Cost Alert**: Flags products where the System Cost (PVF) is > 1% higher than the Master Table Cost (PC). *Action: Verify with supplier/Seomara.*
- ⚠️ **Data Entry Verification**: Flags products where the System PVF is > 5% lower than the Master Table PC. This often indicates the "Preço Líquido" was incorrectly entered into the PVF field. *Action: Confirm manual entry.*
- 🔵 **PVP Update Action**: Identifies products where the System PVP differs from the Master Table PVP. *Action: Update Sifarma.*
- 🟡 **Missing Products**: Lists products present in the System but missing from the Master Table. *Action: Request price table addition.*

### 3. User Experience
- **Video Tutorial**: Embedded "How-to" video (`ExportarFicheiro.mp4`) guiding users on how to export the CSV from Sifarma.
- **Smart Data Mapping**: Automatically captures the `LÍQ.` column from Sifarma exports when available to assist in discrepancy verification.
- **Visual Feedback**: Clear color-coded alerts (Red/Yellow/Blue) and dedicated download buttons for each issue type.

## Security & Deployment

This application is **Cloud-Ready** and avoids hardcoding sensitive links.

### Local Development
The Google Sheet ID is stored in `.streamlit/secrets.toml` (git-ignored):
```toml
GOOGLE_SHEET_ID = "2PACX-..."
```

### Cloud Deployment (Streamlit Community Cloud)
1. Push the code (including `ExportarFicheiro.mp4`) to GitHub.
2. In Streamlit Cloud **Settings > Secrets**, add:
   ```toml
   GOOGLE_SHEET_ID = "2PACX-1vQrUrwXhW10bnIWJzkTeCXLkrH7zvDh-CMQ-SAbvg2ocLSmBP09qmCpD6dkDf4rbg"
   ```

## Project Structure
- `app.py`: Main application logic.
- `requirements.txt`: Python dependencies (`streamlit`, `pandas`, `openpyxl`).
- `.streamlit/secrets.toml`: Local configuration (not in repo).
- `.gitignore`: Security rules.
- `ExportarFicheiro.mp4`: Tutorial video asset.
- `tabela_precos.ipynb`: Development sandbox.

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
