# クイックスタートガイド（5分で始める）

## 1. 環境変数ファイルを作成

### Linuxまたはmacの場合:

ターミナルでプロジェクトフォルダに移動して、以下を実行：

```bash
cd /home/user/test

cat > .env << 'EOF'
APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54
APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3
EOF
```

### Windowsの場合:

1. プロジェクトフォルダを開く
2. 新しいテキストファイルを作成
3. 以下をコピー＆ペースト：
```
APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54
APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3
```
4. 「名前を付けて保存」で `.env` という名前で保存（拡張子なし）

## 2. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

または

```bash
pip3 install -r requirements.txt
```

## 3. サーバーを起動

### 簡単な方法（スクリプトを使用）:

**Linuxまたはmac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
start.bat
```
（または start.bat をダブルクリック）

### 手動で起動:

```bash
python -m aps_mcp_server.server
```

## 4. Claude Desktopで使用

### 設定ファイルを編集

**Windows:**
- パス: `%APPDATA%\Claude\claude_desktop_config.json`
- エクスプローラーで `%APPDATA%\Claude` を開く

**mac:**
- パス: `~/Library/Application Support/Claude/claude_desktop_config.json`

### 設定内容を追加

```json
{
  "mcpServers": {
    "aps": {
      "command": "python",
      "args": ["-m", "aps_mcp_server.server"],
      "cwd": "/home/user/test",
      "env": {
        "APS_CLIENT_ID": "RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54",
        "APS_CLIENT_SECRET": "FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3"
      }
    }
  }
}
```

**重要**: `cwd` をあなたのプロジェクトフォルダのパスに変更してください！

### Claude Desktopを再起動

1. Claude Desktopを完全に終了
2. もう一度起動

## 5. 動作確認

Claude Desktopで質問してみましょう：

```
APSのハブ一覧を取得してください
```

## よく使うコマンド例

### ハブ一覧を見る
```
list_hubsツールを使ってハブ一覧を表示してください
```

### プロジェクト一覧を見る
```
ハブID「b.xxxxxxxx」のプロジェクト一覧を表示してください
```

### フォルダの中身を見る
```
プロジェクトID「b.yyyyyyyy」のフォルダID「urn:adsk.wipprod:fs.folder:co.zzz」の中身を表示してください
```

### ファイルの最新バージョンを取得
```
プロジェクトID「b.yyyyyyyy」のアイテムID「urn:adsk.wipprod:dm.lineage:xxx」の最新バージョンを取得してください
```

## トラブルシューティング

### エラー: `ModuleNotFoundError`
```bash
pip install mcp httpx python-dotenv
```

### エラー: `.env file not found`
`.env`ファイルをプロジェクトフォルダに作成してください

### Claude Desktopでツールが見えない
1. Claude Desktop完全終了
2. 設定ファイルの`cwd`パスを確認
3. Claude Desktop再起動

## 詳しいガイド

詳細な説明は `SETUP_GUIDE.md` を参照してください。
