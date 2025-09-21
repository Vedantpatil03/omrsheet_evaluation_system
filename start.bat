@echo off
echo Starting OMR Evaluation System...
cd /d "C:\Users\vedan\Desktop\omr_evaluation_system"

REM Activate virtual environment
call .venv\Scripts\activate

REM Start Flask backend in background
echo Starting Flask backend...
start "Flask Backend" cmd /k "python app.py"

REM Wait a moment for Flask to start
timeout /t 3 /nobreak >nul

REM Start Streamlit frontend
echo Starting Streamlit frontend...
streamlit run streamlit_app.py

pause