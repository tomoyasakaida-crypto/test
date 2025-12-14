# 初心者向け セットアップガイド

このガイドでは、APSのMCPサーバーを最初から最後まで設定する方法を説明します。

## 前提条件

- Pythonがインストールされていること（Python 3.10以上）
- ターミナル（コマンドプロンプトまたはターミナルアプリ）が使えること

## ステップ1: Pythonのバージョン確認

ターミナルを開いて、以下のコマンドを実行してください：

```bash
python --version
```

または

```bash
python3 --version
```

`Python 3.10.x` や `Python 3.11.x` などと表示されればOKです。

## ステップ2: プロジェクトディレクトリに移動

ターミナルで、このプロジェクトのディレクトリに移動します：

```bash
cd /home/user/test
```

Windowsの場合は、プロジェクトをダウンロードした場所に移動してください。例：

```bash
cd C:\Users\YourName\Downloads\test
```

## ステップ3: 環境変数ファイルの作成

認証情報を設定するために、`.env`ファイルを作成します。

### Linuxまたはmacの場合：

```bash
cat > .env << 'EOF'
APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54
APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3
EOF
```

### Windowsの場合：

メモ帳などのテキストエディタで、プロジェクトフォルダに `.env` という名前のファイルを作成し、以下の内容を貼り付けて保存してください：

```
APS_CLIENT_ID=RNn7W7xutSNQsYcgGcCM4BMVmwcXlGXZF4BEyN6N1HfugA54
APS_CLIENT_SECRET=FVEIh3wfvw7mLwwyBDU9FCHW4whCDMFV4QVJ5tiHw172azdAsurv9ZRKl7T7cnx3
```

**重要**: ファイル名は `.env` で、拡張子は不要です。

## ステップ4: 必要なライブラリのインストール

ターミナルで以下のコマンドを実行してください：

```bash
pip install -r requirements.txt
```

または

```bash
pip3 install -r requirements.txt
```

以下のようなメッセージが表示されます：

```
Collecting mcp>=0.1.0
Collecting httpx>=0.27.0
Collecting python-dotenv>=1.0.0
Installing collected packages: ...
Successfully installed ...
```

## ステップ5: MCPサーバーの起動

### テスト実行（動作確認）

ターミナルで以下のコマンドを実行してください：

```bash
python -m aps_mcp_server.server
```

または

```bash
python3 -m aps_mcp_server.server
```

サーバーが起動すると、何も表示されずに待機状態になります。これは正常です！

Ctrl+C を押してサーバーを停止できます。

## ステップ6: Claude Desktopでの設定

### Windowsの場合

1. 以下のパスにある設定ファイルを開きます：
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. エクスプローラーのアドレスバーに `%APPDATA%\Claude` と入力してEnterを押すと、フォルダが開きます。

3. `claude_desktop_config.json` ファイルをメモ帳で開きます。

### macの場合

1. 以下のパスにある設定ファイルを開きます：
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. Finderで「移動」→「フォルダへ移動...」を選択し、上記のパスを入力します。

### 設定内容の追加

`claude_desktop_config.json` ファイルに以下の内容を追加します：

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

**重要**:
- `cwd` の部分を、実際にプロジェクトをダウンロードした場所に変更してください
- Windowsの場合は、バックスラッシュを2つ重ねるか、スラッシュを使います：
  ```json
  "cwd": "C:/Users/YourName/Downloads/test"
  ```

### Claude Desktopの再起動

1. Claude Desktopを完全に終了します
2. もう一度Claude Desktopを起動します

## ステップ7: 動作確認

Claude Desktopで以下のように質問してみてください：

```
APSのハブ一覧を取得してください
```

または

```
list_hubsツールを使ってください
```

## 使用例：BIM360/ACCプロジェクトのデータを取得する手順

### 1. ハブ一覧を取得

Claude Desktopで：
```
APSのハブ一覧を表示してください
```

以下のような情報が表示されます：
```
Found 2 hubs:

- My Company BIM360
  ID: b.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Type: hubs:autodesk.bim360:Account
  Region: US
```

### 2. プロジェクト一覧を取得

ハブIDをコピーして：
```
ハブID「b.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx」のプロジェクト一覧を表示してください
```

以下のような情報が表示されます：
```
Found 5 projects in hub:

- Office Building Project
  ID: b.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
  Type: projects
```

### 3. プロジェクトのトップフォルダを取得

```
ハブID「b.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx」、
プロジェクトID「b.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy」の
トップフォルダを表示してください
```

以下のような情報が表示されます：
```
Found 3 top-level folders:

- Project Files
  ID: urn:adsk.wipprod:fs.folder:co.zzzzzzzz
  Type: folders

- Plans
  ID: urn:adsk.wipprod:fs.folder:co.aaaaaaaa
  Type: folders
```

### 4. フォルダの中身を取得

```
プロジェクトID「b.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy」、
フォルダID「urn:adsk.wipprod:fs.folder:co.zzzzzzzz」の
中身を表示してください
```

以下のような情報が表示されます：
```
Found 10 items in folder:

Folders:
- Architecture
  ID: urn:adsk.wipprod:fs.folder:co.bbbbbbbb

Files:
- Building_Model.rvt
  ID: urn:adsk.wipprod:dm.lineage:cccccccc
  Extension: items:autodesk.bim360:File
  Version: 5
```

### 5. ファイルの最新バージョンを取得

```
プロジェクトID「b.yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy」、
アイテムID「urn:adsk.wipprod:dm.lineage:cccccccc」の
最新バージョンを表示してください
```

以下のような情報が表示されます：
```
Latest Version:
- Version Number: 5
- ID: urn:adsk.wipprod:dm.version:dddddddd
- Display Name: Building_Model.rvt
- Created: 2024-01-15T10:30:00.000Z
- Created By: john.doe@company.com
- File Type: rvt
- Storage Size: 52428800 bytes
- Derivative URN: urn:adsk.viewing:fs.file:dXJuOmFkc2sud2...
```

**Derivative URN**が、3Dビューアーやモデル解析に使用できるURNです！

## トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'mcp'`

**解決方法**:
```bash
pip install mcp httpx python-dotenv
```

### エラー: `APS_CLIENT_ID and APS_CLIENT_SECRET must be set`

**解決方法**:
`.env`ファイルが正しく作成されているか確認してください。

### Claude Desktopでツールが表示されない

**解決方法**:
1. Claude Desktopを完全に終了
2. `claude_desktop_config.json`の内容が正しいか確認
3. `cwd`パスが正しいか確認
4. Claude Desktopを再起動

### エラー: `401 Unauthorized`

**解決方法**:
認証情報（Client IDとClient Secret）が正しいか確認してください。

## 次のステップ

- Model Derivative APIを使用してモデルデータを取得（今後実装予定）
- プロパティ抽出機能の追加
- 3Dビューアーとの統合

## サポート

問題が解決しない場合は、以下の情報を共有してください：
- エラーメッセージの全文
- 使用しているPythonのバージョン
- 使用しているOSとバージョン
