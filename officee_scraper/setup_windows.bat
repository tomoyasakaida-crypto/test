@echo off
REM ============================================================
REM  officee スクレイパー 初回セットアップ（Windows）
REM  この bat をダブルクリックするだけで環境構築が完了します。
REM  事前に Python 3.10+ をインストールしておいてください。
REM   https://www.python.org/downloads/  （Add python to PATH にチェック）
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo [1/4] 仮想環境を作成します...
python -m venv .venv
if errorlevel 1 (
    echo Python が見つかりません。python.org からインストールしてください。
    pause & exit /b 1
)

echo [2/4] ライブラリをインストールします...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [3/4] ブラウザ(Chromium)をインストールします...
python -m playwright install chromium

echo [4/4] ロジック自己テストを実行します...
python scraper.py --selftest

echo.
echo ============================================================
echo  セットアップ完了。
echo  次のステップ:
echo   1) run_weekly.bat をダブルクリックして動作確認
echo   2) うまく取れない場合:
echo        .venv\Scripts\python scraper.py --inspect "https://officee.jp/area/p_osaka/30_50/"
echo      を実行し、debug\page.html / page.png を確認して
echo      config.py の SELECTORS を調整
echo   3) タスクスケジューラで run_weekly.bat を週1登録（README参照）
echo ============================================================
pause
