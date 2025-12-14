@echo off
chcp 65001 >nul
cls

echo ===========================================
echo   APS MCP Server を起動します
echo ===========================================
echo.

REM .envファイルの存在確認
if not exist ".env" (
    echo ❌ エラー: .env ファイルが見つかりません
    echo.
    echo プロジェクトフォルダに .env ファイルを作成してください。
    echo メモ帳で以下の内容を貼り付けて、.env という名前で保存してください:
    echo.
    echo APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54
    echo APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3
    echo.
    pause
    exit /b 1
)

REM 依存関係のチェック
echo 📦 依存関係をチェックしています...
python -c "import mcp" 2>nul
if errorlevel 1 (
    echo ❌ 必要なライブラリがインストールされていません
    echo 📥 インストールを開始します...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ インストールに失敗しました
        pause
        exit /b 1
    )
    echo ✅ インストール完了
)

echo ✅ 依存関係OK
echo.

REM サーバー起動
echo 🚀 MCP Server を起動しています...
echo    停止するには Ctrl+C を押してください
echo.
echo ===========================================
echo.

python -m aps_mcp_server.server
