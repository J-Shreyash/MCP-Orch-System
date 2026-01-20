@echo off
echo ============================================
echo   AI Agent System - Auto Starter
echo   Sepia ML - Production Ready
echo ============================================
echo.

cd /d "%~dp0"

echo Starting MCP Servers...
echo.

echo [1/5] Starting Search MCP (Port 8001)...
start "Search MCP" cmd /k "cd mcp_google_search && uvicorn server:app --host 0.0.0.0 --port 8001"
timeout /t 3 /nobreak >nul

echo [2/5] Starting Drive MCP (Port 8002)...
start "Drive MCP" cmd /k "cd mcp_google_drive && uvicorn server:app --host 0.0.0.0 --port 8002"
timeout /t 3 /nobreak >nul

echo [3/5] Starting Database MCP (Port 8003)...
start "Database MCP" cmd /k "cd mcp_database && uvicorn server:app --host 0.0.0.0 --port 8003"
echo    Waiting for Database MCP to initialize (this may take 30-60 seconds)...
timeout /t 60 /nobreak >nul

echo [4/5] Starting RAG PDF MCP (Port 8004)...
start "RAG PDF MCP" cmd /k "cd mcp_rag_pdf && uvicorn server:app --host 0.0.0.0 --port 8004"
echo    Waiting for RAG PDF MCP to initialize (this may take 30-60 seconds)...
timeout /t 60 /nobreak >nul

echo [5/5] Starting AI Agent System (Port 8501)...
echo.
echo ============================================
echo   All servers started!
echo   Opening AI Agent in browser...
echo ============================================
echo.

cd ai_agent_system
streamlit run app.py

pause