# Project: Tabela_PRECOS

## Overview
This project is a **Streamlit application** designed to help pharmacy staff verify and update product prices. It acts as a bridge between the official price table (hosted on Google Sheets) and the pharmacy's internal systems (Sifarma and INFOPREX), identifying discrepancies in Cost Prices (PC), Sales Prices (PVP), and analyzing commercial margins.

## Key Features

### 1. Data Integration & Performance
- **Google Sheets**: Fetches the "Master Price Table" securely using a Sheet ID configured via Secrets or Environment Variables.
- **Multi-Source Support**: Analyzes both Sifarma (CSV) and INFOPREX (TXT/CSV) exports.
- **Smart Caching**: Uses `@st.cache_data` with a 1-hour TTL to prevent repetitive, slow downloads of the Excel file. Includes a manual "Reload" button.
- **Robust Cleaning**: Handles data type inconsistencies (mixed strings/floats with commas, quotes in INFOPREX) to ensure precision.

### 2. Analysis & Alerts (Sifarma Tab)
Compares the Master Table against Sifarma's `export.csv`:
- 🔴 **Critical Cost Alert**: Flags products where PVF > 1% higher than Master PC.
- ⚠️ **Data Entry Verification**: Flags products where PVF > 5% lower than Master PC (possible entry error).
- 🔵 **PVP Update Action**: Identifies PVP differences for immediate update.
- 🟡 **Missing Products**: Lists products in the system but missing from the Master Table.

### 3. Database Skeleton Analysis (Infoprex Tab)
Uses the INFOPREX file as the core database skeleton for global price verification:
- **Location Filtering**: Automatically identifies the pharmacy's main location based on the most recent sale date (`DUV`).
- **Stock Validation**: Only processes products with active stock (`SAC > 0`).
- **Commercial Margin Calculation**:
  - Calculates Net PVP (removing VAT/IVA: 6%, 23%, etc.).
  - Calculates real margin percentage: `((PVP_net - PCU) / PVP_net) * 100`.
- **Divergence Logic**:
  - Lists all products where INFOPREX PVP differs from Master Table.
  - **Price Direction Filter**: Radio buttons to isolate products where system price is either lower (`Infoprex < Master`) or higher (`Infoprex > Master`) than the official table.
  - **High Margin Switch**: Toggle to view only divergences where the margin is > 30% (indicative of products that should be perfectly aligned with the table).

### 4. User Experience
- **Tabbed Interface**: Clean separation between Sifarma and Infoprex workflows.
- **Video Tutorial**: Embedded "How-to" video for Sifarma exports.
- **Visual Feedback**: Color-coded alerts and formatted data tables (Currency and Percentage symbols).

## Security & Deployment
This application is **Cloud-Ready**.

### Local Development
The Google Sheet ID is stored in `.streamlit/secrets.toml` (git-ignored).

### Cloud Deployment (Streamlit Community Cloud)
1. Push code to GitHub.
2. Configure `GOOGLE_SHEET_ID` in Streamlit Cloud Secrets.

## Project Structure
- `app.py`: Main Streamlit application and UI logic.
- `processador_infop.py`: Specialized module for INFOPREX parsing, filtering, and margin calculations.
- `requirements.txt`: Python dependencies (`streamlit`, `pandas`, `openpyxl`).
- `ExportarFicheiro.mp4`: Tutorial video asset.
- `INFOPREX202602061456.TXT`: Sample data for testing.

## How to Run Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `streamlit run app.py`