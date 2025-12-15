@echo off
echo ===================================
echo APS MCP Server Setup (Windows)
echo ===================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo .env file created!
    echo Please edit .env and add your APS credentials.
    echo.
    pause
    notepad .env
) else (
    echo .env file already exists.
)

echo.
echo Installing dependencies...
pip install -e .

echo.
echo ===================================
echo Setup complete!
echo ===================================
echo.
echo Next steps:
echo 1. Make sure your .env file has correct credentials
echo 2. Add http://localhost:8080/callback to your APS app
echo 3. Run: python auth.py
echo 4. Restart Claude Desktop
echo.
pause
