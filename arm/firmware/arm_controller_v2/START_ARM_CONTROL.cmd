@echo off
cd /d "%~dp0"
python arm_control_panel.py
if errorlevel 1 pause
