@echo off
chcp 65001 >nul 2>&1
echo.
echo   ========================================
echo    GitHub Login
echo   ========================================
echo.
echo   Press ENTER to open browser for login...
echo   After authorizing in browser, return here.
echo.
where gh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    gh auth login -p https -h github.com -w
) else if exist "C:\Program Files\GitHub CLI\gh.exe" (
    "C:\Program Files\GitHub CLI\gh.exe" auth login -p https -h github.com -w
) else (
    echo   [ERROR] gh CLI not found.
)
echo.
echo   This window will close in 3 seconds...
timeout /t 3 >nul
