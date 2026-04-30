# Verificador de Preços

## Project Overview

**Verificador de Preços** is a cloud-ready web application built with **Python** and **Streamlit**. It serves as an internal tool for pharmacies to validate and reconcile product prices across three data sources:
1. **Google Sheets (Master Table):** The canonical reference for Cost Price (`PC Atual`) and Retail Price (`PVP Atual`), organized by laboratory in multiple sheets.
2. **Sifarma (CSV):** The pharmacy's management system dump.
3. **Infoprex (TXT):** A secondary stock and price management system (Supports both 'Legacy' and 'New' formats).

The platform identifies price discrepancies, warns about critical financial risks (e.g., costs higher than expected), highlights data entry errors, calculates commercial margins, and generates remediation reports exportable as Excel files.

### Key Technologies
- **Python 3.x**
- **Streamlit** (UI/Frontend)
- **Pandas** (Data Manipulation)
- **OpenPyXL** (Excel Parsing/Exporting)

### Architecture
The system follows a strict modular architecture separating UI rendering from business logic (Version 3.0):
- `app.py`: Streamlit entry point. Contains ONLY UI layout and orchestration.
- `google_sheets.py`: Master table fetching, structural validation (A1='CNP'), and caching (60m TTL). Captures metadata (Last-Modified).
- `sifarma.py`: CSV parsing, PVF=0 deduplication, and all 6 discrepancy alert logic functions.
- `infoprex.py`: Format detection, margin calculation, and dynamic UI filtering.
- `infoprex_new_system.py`: Isolated logic for transforming the 'New System' format (external module integration).
- `exporters.py`: Centralized Excel generation utility.
- `validators.py`: Shared data validation helpers (`to_float_safe`, `to_int_safe`).

## Building and Running

To run the application locally:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

*Note: The `GOOGLE_SHEET_ID` should be configured in `.streamlit/secrets.toml` for local development or in Streamlit Community Cloud Secrets for deployment.*

## Development Conventions

This project enforces strict coding and architectural standards. Always adhere to the following rules:

### Code Style & Guidelines (Non-Negotiable)
- **Simplicity:** Keep functions small and focused on a single responsibility (maximum 40 lines suggested).
- **PEP 8:** Strictly adhere to PEP 8 formatting. The maximum line length is **88 characters** (compatible with Black).
- **Strings:** Always use **single quotes (`'`)** for Python strings, unless technically impossible (e.g., an f-string that contains single quotes inside).
- **Language Policy:**
  - **Code (100% English):** All variable names, functions, classes, and technical comments must be written in English.
  - **User Interface (pt-PT):** All text displayed to the user (labels, tooltips, `st.error` messages, success messages, UI headers) MUST be strictly in European Portuguese (pt-PT). Do not mix languages or use informal Portuguese.

### Data Handling & Error Management
- **No Silent Drops:** Never ignore data conversion failures silently. Do not use aggressive `dropna()` on key columns (like `CNP` or prices) without capturing and reporting the discarded rows to dedicated UI error views.
- **Robust Conversions:** Use the dedicated modules (e.g., `validators.py`) to safely convert currencies and numbers.
- **Floating Point Math:** When comparing prices, always round both sides to 2 decimal places before applying equality operators (`!=`).
- **Encoding Fallbacks:** Ensure robust file reading by chaining encodings: `utf-8` -> `utf-8-sig` -> `latin-1` (for Sifarma) and `utf-16` -> `utf-8` -> `latin-1` (for Infoprex).

### Core Business Rules
- **Sifarma Alert Thresholds:**
  - Alert 1 (High Cost): `pvf > pc_atual * 1.01`
  - Alert 2 (Low Cost): `pvf < pc_atual * 0.90` (10% gap).
- **Interactive Grids:** The Infoprex results must use `st.data_editor` with `num_rows='dynamic'` to allow users to manually delete rows before exporting. 
- **Stock Filtering:** Infoprex comparisons MUST enforce a mandatory `Stock > 0` filter before any logic is applied.

### Export Standards
- **Excel Only:** Exporting to `.csv` for user downloads is strictly prohibited. All exports must be generated as `.xlsx`.
- **Centralized Exporter:** Use the `to_excel_bytes` function from `exporters.py` for all file generations. Do not implement Excel writing logic directly in `app.py`.
- **Naming Conventions:** Downloaded files must include the current date (e.g., `alerta_pvf_superior_YYYYMMDD.xlsx`).
- **Accurate State:** The exported Excel MUST strictly reflect the currently visible filtered and manually edited state on the UI grid.

### UI & Design System
- The UI must strictly follow the visual guidelines documented in the `@design_system/design-system.html` file.
- Re-use the existing typography, colors, animations, gradients, and CSS classes (Tailwind CSS + Iconify) defined in the design system.
- **Do NOT invent new loose visual styles** or introduce new external CSS frameworks.