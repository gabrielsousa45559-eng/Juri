@echo off
setlocal
cd /d "%~dp0.."
title ᴍᴀɢɪsᴛʀᴀᴛᴜʀᴀ - SIA
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar as dependencias do SIA.
    pause
    exit /b 1
)
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
