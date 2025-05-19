# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install dependencies: `pip install -r requirements.txt` or `pip install pandas numpy sqlalchemy psycopg2-binary matplotlib seaborn plotly geopandas difflib fuzzywuzzy ipywidgets`
- Run Jupyter Notebook: `jupyter notebook LISWMC_ANALYTICS.ipynb`
- Export data: Check CSV files in the output directory

## Style Guidelines
- Use pandas for data processing and SQLAlchemy for database interactions
- Import order: standard libraries → third-party packages → local modules
- Use snake_case for variables and functions
- Document functions with docstrings describing purpose, parameters, and return values
- Handle database connections with try/except blocks and proper connection closing
- Use consistent 4-space indentation
- Wrap SQLAlchemy transactions in context managers
- For data manipulation, prefer pandas methods over Python loops
- When using regex patterns, document the pattern's purpose