#!/bin/bash

# APS MCP Server 起動スクリプト

echo "==========================================="
echo "  APS MCP Server を起動します"
echo "==========================================="
echo ""

# .envファイルの存在確認
if [ ! -f ".env" ]; then
    echo "❌ エラー: .env ファイルが見つかりません"
    echo ""
    echo "以下のコマンドで .env ファイルを作成してください:"
    echo ""
    echo "cat > .env << 'EOF'"
    echo "APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54"
    echo "APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3"
    echo "EOF"
    echo ""
    exit 1
fi

# 依存関係のチェック
echo "📦 依存関係をチェックしています..."
if ! python3 -c "import mcp" 2>/dev/null; then
    echo "❌ 必要なライブラリがインストールされていません"
    echo "📥 インストールを開始します..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ インストールに失敗しました"
        exit 1
    fi
    echo "✅ インストール完了"
fi

echo "✅ 依存関係OK"
echo ""

# サーバー起動
echo "🚀 MCP Server を起動しています..."
echo "   停止するには Ctrl+C を押してください"
echo ""
echo "==========================================="
echo ""

python3 -m aps_mcp_server.server
