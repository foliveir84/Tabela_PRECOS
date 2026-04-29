# Verificador de Preços

## Project Overview

**Verificador de Preços** is a cloud-ready web application built with **Python** and **Streamlit**. It serves as an internal tool for pharmacies to validate and reconcile product prices across three data sources:
1. **Google Sheets (Master Table):** The canonical reference for Cost Price (`PC Atual`) and Retail Price (`PVP Atual`).
2. **Sifarma (CSV):** The pharmacy's management system dump.
3. **Infoprex (TXT):** A secondary stock and price management system.

The platform identifies price discrepancies, warns about critical financial risks (e.g., costs higher than expected), highlights data entry errors, calculates commercial margins, and generates remediation reports exportable as Excel files.

### Key Technologies
- **Python 3.x**
- **Streamlit** (UI/Frontend)
- **Pandas** (Data Manipulation)
- **OpenPyXL** (Excel Parsing/Exporting)

### Architecture
The system follows a strict modular architecture separating UI rendering from business logic:
- `app.py`: Streamlit entry point. Contains ONLY UI layout and orchestration.
- `google_sheets.py`: Master table fetching, validation, and caching.
- `sifarma.py`: CSV parsing and discrepancy alert logic.
- `infoprex.py` / `infoprex_new_system.py`: TXT parsing, margin calculation, and dynamic filtering.
- `exporters.py`: Centralized Excel generation utility.
- `validators.py`: Shared data validation helpers.

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
- **No Silent Drops:** Never ignore data conversion failures silently. Do not use aggressive `dropna()` on key columns (like `CNP` or prices) without capturing and reporting the discarded rows.
- **Robust Conversions:** Use the dedicated modules (e.g., `validators.py`) to safely convert currencies and numbers.
- **Floating Point Math:** When comparing prices, always round both sides to 2 decimal places before applying equality operators (`!=`).
- **Encoding Fallbacks:** Ensure robust file reading by chaining encodings: `utf-16` / `utf-8` -> `utf-8-sig` -> `latin-1`.

### Export Standards
- **Excel Only:** Exporting to `.csv` for user downloads is strictly prohibited. All exports must be generated as `.xlsx`.
- **Centralized Exporter:** Use the `to_excel_bytes` function from `exporters.py` for all file generations. Do not implement Excel writing logic directly in `app.py`.
- **Naming Conventions:** Downloaded files must include the current date (e.g., `alerta_pvf_superior_YYYYMMDD.xlsx`).

### UI & Design System
- The UI must strictly follow the visual guidelines documented in the `@design_system/design-system.html` file.
- Re-use the existing typography, colors, animations, gradients, and CSS classes (Tailwind CSS + Iconify) defined in the design system.
- **Do NOT invent new loose visual styles** or introduce new external CSS frameworks.