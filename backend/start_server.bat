@echo off
echo Starting Echo Journal Backend Server...
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create a virtual environment first: python -m venv venv
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if run.py exists
if not exist "run.py" (
    echo ERROR: run.py not found!
    echo Make sure you're in the correct backend directory.
    pause
    exit /b 1
)

:: Start the server
echo Starting server...
echo.
python run.py

:: Keep the window open if there's an error
if %ERRORLEVEL% neq 0 (
    echo.
    echo Server stopped with error code: %ERRORLEVEL%
    pause
)