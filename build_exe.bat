@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Vocabulary Killer - Build EXE
echo ============================================
echo.
echo [1/3] Installing PyInstaller (Tsinghua mirror)...
python -m pip install --upgrade pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
echo.
echo [2/3] Building single-file exe (this takes a few minutes)...
python -m PyInstaller --noconsole --onefile --name "Vocabulary Killer" --clean --noconfirm app.py
echo.
echo [3/3] Moving exe next to stardict.db (this folder)...
if exist "dist\Vocabulary Killer.exe" (
    move /Y "dist\Vocabulary Killer.exe" "Vocabulary Killer.exe" >nul
    rmdir /S /Q dist 2>nul
    rmdir /S /Q build 2>nul
    echo.
    echo ============================================
    echo   DONE!  Double-click:  Vocabulary Killer.exe
    echo   (keep stardict.db in this same folder)
    echo ============================================
) else (
    echo.
    echo BUILD FAILED - see messages above.
)
echo.
pause
