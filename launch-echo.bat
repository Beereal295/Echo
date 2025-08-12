@echo off
echo Starting Echo Journal Application...
echo.

REM Get the current directory (root of the project)
set ROOT_DIR=%~dp0

REM Start frontend in a new window
echo Starting Frontend (React)...
start "Echo Frontend" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

REM Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

REM Start backend in a new window
echo Starting Backend (Python FastAPI)...
start "Echo Backend" cmd /k "cd /d "%ROOT_DIR%backend" && call venv\Scripts\activate && python run.py"

echo.
echo Echo Journal is starting up!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
echo Press any key to exit this launcher...
pause >nul