DEMO – Backtesting & Reporting Engine
------------------------------------

This demo shows the workflow of the monthly backtesting system built in Python. 
It includes both manual user-driven evaluation and automated algorithmic testing.

1. Manual Backtest (Interactive PDF)
   - A PDF is generated containing CE/PE selection and SL/Target radio buttons.
   - The user marks sample trades manually in the PDF.
   - The tool reads the filled PDF and calculates accuracy and trade statistics.

2. Automated Backtest (Logic-Based PDF)
   - The system generates an automated backtest PDF from synthetic data.
   - It includes:
        • Accuracy summary
        • Win/Loss breakdown
        • Sample rows of trade decisions

3. What This Demonstrates
   - PDF generation with ReportLab
   - Form fields (AcroForm radio buttons)
   - PDF parsing using PyPDF2
   - ETL of synthetic OHLC-style datasets
   - Multi-strategy support structure
   - Reporting layer for trading workflows

Note:
This demo uses publicly available historical market data and complies with SEBI guidelines.
All strategy logic, proprietary formulas, and sensitive trading mechanisms are intentionally excluded.
