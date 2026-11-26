@echo off
chcp 65001 >nul
title MoliBox - Cloudflare One-Click Deploy
cd /d "%~dp0"
echo.
echo  ============================================
echo   MoliBox - Cloudflare One-Click Deploy
echo  ============================================
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Please install Python 3.8+ first.
  pause
  exit /b 1
)
python deploy_cloudflare.py %*
echo.
pause
