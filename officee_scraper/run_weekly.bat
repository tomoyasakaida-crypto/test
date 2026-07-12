@echo off
REM ============================================================
REM  officee スクレイパー 週次実行用（タスクスケジューラから呼ぶ）
REM  Excel(output\officee_osaka_offices.xlsx) を更新します。
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo 仮想環境がありません。先に setup_windows.bat を実行してください。
    pause & exit /b 1
)

echo [%date% %time%] officee スクレイピング開始
".venv\Scripts\python.exe" scraper.py
echo [%date% %time%] 終了 (exit=%errorlevel%)

REM タスクスケジューラから無人実行する場合、下の pause は削除してください。
REM （手動確認用に残しています）
pause
