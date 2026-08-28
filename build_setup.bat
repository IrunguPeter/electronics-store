@echo off
REM ============================================================
REM  Build ElectronStoreSetup.exe — the online installer
REM  Double-click this file, or run it from a command prompt.
REM  Requires: Python 3.8+ installed and on PATH (Windows PC).
REM
REM  This builds both:
REM    dist\ElectronStore.exe          the app
REM    dist\ElectronStoreSetup.exe     the installer to give the shop
REM
REM  Publish the app exe as a GitHub Release asset named exactly
REM  "ElectronStore.exe", then send only ElectronStoreSetup.exe to
REM  the shop. It downloads the app, installs it, and adds a
REM  Start Menu shortcut.
REM ============================================================
setlocal

echo.
echo [1/3] Installing dependencies including PyInstaller...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/3] Building the app executable...
py -m PyInstaller electronstore.spec --noconfirm
if errorlevel 1 goto :error

echo.
echo [3/3] Building the online installer...
py -m PyInstaller electronstore-setup.spec --noconfirm
if errorlevel 1 goto :error

echo.
echo All done!
echo   App:       %cd%\dist\ElectronStore.exe
echo   Installer: %cd%\dist\ElectronStoreSetup.exe
echo.
echo Next: create a GitHub Release and attach dist\ElectronStore.exe
echo as an asset named exactly ElectronStore.exe, so the installer can
echo download it. Then give the shop dist\ElectronStoreSetup.exe.
echo.
pause
exit /b 0

:error
echo.
echo  BUILD FAILED. Look at the messages above.
pause
exit /b 1