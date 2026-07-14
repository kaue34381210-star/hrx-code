@echo off
setlocal
title Desinstalar JARVIS
chcp 65001 >nul

set "DEST=%LOCALAPPDATA%\jarvis"
set "CFG=%APPDATA%\jarvis"

echo Removendo JARVIS...
if exist "%DEST%" rmdir /s /q "%DEST%"
powershell -NoProfile -Command "$p=[Environment]::GetEnvironmentVariable('Path','User'); $p=(($p -split ';') ^| Where-Object {$_ -and ($_ -notlike '*\jarvis')}) -join ';'; [Environment]::SetEnvironmentVariable('Path',$p,'User')"

echo   codigo e comando removidos.
echo   chaves preservadas em %CFG% (apague manualmente se quiser).
echo(
pause
