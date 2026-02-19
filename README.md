# **Multi-Strategy Quantitative Stock Selection Engine**

This project provides a robust, automated pipeline for identifies high-potential investment candidates (Growth, Dividend, and Turnaround) using SEC financial data and real-time market metrics.

## **Core Components**

1.  **SEC ETL Pipeline**: (`import_all_sec_data.py`) Fetches, parses, and archival of SEC company facts into a local MariaDB database.
2.  **Stock Selection Engine**: (`stock_selection_engine/`) A modular, vectorized processing engine that applies quantitative filters across multiple investment strategies.
3.  **Data Quality Tools**: (`check_data_quality.py`) Verification scripts to ensure integrity of critical financial columns (EPS, Revenue, etc.).

## **Documentation**

- **[Specification](file:///home/kay/workspace/stock-batch/Stock-Selection-Program-Specification.md)**: Detailed technical architecture, quantitative models, and selection logic.
- **[Engine Guide](file:///home/kay/workspace/stock-batch/stock_selection_engine_guide.md)**: Setup, configuration, and execution instructions for the selection engine.
- **[Import Guideline](file:///home/kay/workspace/stock-batch/import_all_sec_data-guideline.md)**: Instructions for running the SEC data import process.
- **[Data Mapping](file:///home/kay/workspace/stock-batch/import_all_sec_data_mapping.md)**: Technical details on SEC XBRL to Database column mapping.

## **Quick Start**

1.  **Import Data**:
    ```bash
    python3 import_all_sec_data.py --limit 100
    ```
2.  **Verify Quality**:
    ```bash
    python3 check_data_quality.py
    ```
3.  **Run Engine**:
    ```bash
    python3 -m stock_selection_engine.main --limit 50
    ```
