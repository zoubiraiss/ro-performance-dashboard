# RO Performance Dashboard

AI-powered monitoring system for Reverse Osmosis units.
Built for Sonatrach field operators.

## What it does
- Upload daily RO Excel data
- Automatic KPI calculation: recovery rate, salt rejection
- Trend charts with threshold lines
- Automatic anomaly detection
- AI assistant that answers operator questions from real data

## Tech stack
Python, Pandas, Streamlit, Plotly, Google Gemini API

## How to run
pip install -r requirements.txt
streamlit run ro_dashboard.py

## Data required
Excel file with columns:
date, Train, temperator, feed water, reject water,
permeate flow, pressur, conductivity, tds, ph, feed conductivity