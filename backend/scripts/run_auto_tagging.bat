@echo off
echo ===============================================
echo    Echo Diary - Auto-Tagging Script
echo ===============================================
echo.

cd /d "%~dp0"
cd ..

echo Current directory: %cd%
echo.

REM Check if echo.db exists
if not exist "echo.db" (
    echo ❌ ERROR: echo.db not found in backend directory
    echo Please make sure you're running this from the correct location
    pause
    exit /b 1
)

echo ✅ Database found: echo.db
echo.

REM Ask user what they want to do
echo What would you like to do?
echo 1. Dry run (see what would be processed)
echo 2. Process first 10 entries (test)
echo 3. Process all entries
echo 4. Exit
echo.
set /p choice=Enter your choice (1-4): 

if "%choice%"=="1" (
    echo.
    echo 🔍 Running dry run...
    python scripts\auto_tag_existing_entries.py --dry-run
) else if "%choice%"=="2" (
    echo.
    echo 🧪 Processing first 10 entries as test...
    python scripts\auto_tag_existing_entries.py --max-entries 10
) else if "%choice%"=="3" (
    echo.
    echo ⚠️  This will process ALL entries. Are you sure? (y/N)
    set /p confirm=
    if /i "%confirm%"=="y" (
        echo.
        echo 🚀 Processing all entries...
        python scripts\auto_tag_existing_entries.py
    ) else (
        echo Cancelled.
    )
) else if "%choice%"=="4" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please try again.
)

echo.
echo ===============================================
echo Script completed. Press any key to exit...
pause > nul