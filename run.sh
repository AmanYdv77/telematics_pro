#!/bin/bash
echo "Starting TelematicsPro..."
echo "Open http://localhost:8501 in your browser"
echo "Press Ctrl+C to stop"
echo ""
source venv/bin/activate
streamlit run app.py
