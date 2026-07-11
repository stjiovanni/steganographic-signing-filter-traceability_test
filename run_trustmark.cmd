@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
python trustmark_robustness.py --image-count 1000 --resume > output\logs\trustmark_run_log.txt 2>&1
exit /b %ERRORLEVEL%
