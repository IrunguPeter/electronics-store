@echo off
REM ============================================================
REM  Build ElectronStore.exe (Windows)
REM  Double-click this file, or run it from a command prompt.
REM  Requires: Python 3.8+ installed and on PATH.
REM ============================================================
setlocal

echo.
echo [1/3] Installing dependencies including PyInstaller...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/3] Building the executable...
py -m PyInstaller electronstore.spec --noconfirm
if errorlevel 1 goto :error

echo.
echo [3/3] Done!
echo.
echo   Your program is ready at:
echo     %cd%\dist\ElectronStore.exe
echo.
echo   Copy the whole "dist\ElectronStore.exe" file to the shop PC.
echo   Double-click ElectronStore.exe to run the shop.
echo.
pause
exit /b 0

:error
echo.
echo  BUILD FAILED. Look at the messages above.
pause
exit /b 1
