@echo off
title DEEBOT Controller
powershell.exe -ExecutionPolicy Bypass -File "%~dp0deebot_service.ps1"
pause
