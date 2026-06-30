@echo off
echo Starting TelematicsPro...
echo Open http://localhost:8501 in your browser
echo Press Ctrl+C to stop
echo.
call venv\Scripts\activate.bat
streamlit run app.py
