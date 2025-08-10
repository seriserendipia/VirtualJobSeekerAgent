@echo off
echo Building manifest.json...
python build_manifest.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build completed! You can now load the Chrome extension
    echo.
    echo 📁 Extension directory: %~dp0frontend
    echo.
    echo 🔧 To modify configuration, edit the .env file
) else (
    echo.
    echo ❌ Build failed, please check configuration
)

pause
