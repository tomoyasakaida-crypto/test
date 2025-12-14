# APS MCP Server

MCP (Model Context Protocol) Server for Autodesk Platform Services (APS).

## 機能

このMCPサーバーは、Autodesk Platform Services (旧 Forge) のData Management APIとAEC Data Model APIへのアクセスを提供します。

### 提供するツール

#### Data Management API
- `list_buckets` - バケット一覧の取得
- `create_bucket` - 新しいバケットの作成
- `get_bucket_details` - バケット詳細情報の取得
- `list_objects` - バケット内のオブジェクト一覧
- `get_object_details` - オブジェクト詳細情報の取得

#### AEC Data Model API
- `list_hubs` - アクセス可能なハブ（アカウント）一覧の取得
- `list_projects` - ハブ内のプロジェクト一覧の取得
- `get_project_top_folders` - プロジェクトのトップレベルフォルダの取得
- `get_folder_contents` - フォルダ内のコンテンツ（サブフォルダとファイル）の取得
- `get_item_versions` - アイテムの全バージョン履歴の取得
- `get_item_tip` - アイテムの最新バージョン情報の取得

#### Model Derivative API
- `get_manifest` - モデルのマニフェスト取得
- `get_metadata_views` - モデル内のビュー（視点）一覧取得
- `get_object_tree` - オブジェクトツリー（階層構造）の取得
- `get_all_properties` - すべてのオブジェクトのプロパティ取得

## セットアップ

### 1. APS認証情報の取得

1. [APS Developer Portal](https://aps.autodesk.com/myapps) にアクセス
2. 新しいアプリケーションを作成、または既存のアプリを使用
3. Client IDとClient Secretを取得

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して、認証情報を設定：

```
APS_CLIENT_ID=your_actual_client_id
APS_CLIENT_SECRET=your_actual_client_secret
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

または

```bash
pip install -e .
```

## 使用方法

### MCPサーバーとして起動

```bash
python -m aps_mcp_server.server
```

または

```bash
aps-mcp-server
```

### Claude Desktopでの設定

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に以下を追加：

```json
{
  "mcpServers": {
    "aps": {
      "command": "python",
      "args": ["-m", "aps_mcp_server.server"],
      "env": {
        "APS_CLIENT_ID": "your_client_id",
        "APS_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

または、絶対パスで指定：

```json
{
  "mcpServers": {
    "aps": {
      "command": "/path/to/python",
      "args": ["/path/to/aps-mcp-server/src/aps_mcp_server/server.py"]
    }
  }
}
```

## ツールの使用例

### Data Management API

#### バケット一覧の取得

```
list_buckets
```

パラメータ：
- `region`: リージョン（"US" または "EMEA"）
- `limit`: 取得する最大件数

#### バケットの作成

```
create_bucket
```

パラメータ：
- `bucket_key`: バケット名（小文字、スペース不可）
- `policy_key`: データ保持ポリシー（"transient", "temporary", "persistent"）

#### オブジェクト一覧の取得

```
list_objects
```

パラメータ：
- `bucket_key`: バケット名
- `limit`: 取得する最大件数

### AEC Data Model API

#### ハブ一覧の取得

```
list_hubs
```

アクセス可能なすべてのハブ（BIM360、ACC等）を取得します。

#### プロジェクト一覧の取得

```
list_projects
```

パラメータ：
- `hub_id`: ハブID（例：`b.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

特定のハブ内のすべてのプロジェクトを取得します。

#### プロジェクトのトップフォルダ取得

```
get_project_top_folders
```

パラメータ：
- `hub_id`: ハブID
- `project_id`: プロジェクトID（例：`b.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

プロジェクトのルートレベルにあるフォルダ（Plans、Project Files等）を取得します。

#### フォルダコンテンツの取得

```
get_folder_contents
```

パラメータ：
- `project_id`: プロジェクトID
- `folder_id`: フォルダID（例：`urn:adsk.wipprod:fs.folder:co.xxxxxx`）

指定したフォルダ内のサブフォルダとファイル一覧を取得します。

#### アイテムバージョン履歴の取得

```
get_item_versions
```

パラメータ：
- `project_id`: プロジェクトID
- `item_id`: アイテムID（例：`urn:adsk.wipprod:dm.lineage:xxxxxx`）

ファイルのすべてのバージョン履歴を取得します。

#### アイテムの最新バージョン取得

```
get_item_tip
```

パラメータ：
- `project_id`: プロジェクトID
- `item_id`: アイテムID

ファイルの最新バージョン情報を取得します。Derivative URN（Model Derivative APIで使用）も含まれます。

### Model Derivative API

#### マニフェストの取得

```
get_manifest
```

パラメータ：
- `urn`: モデルのURN（`get_item_tip`で取得したDerivative URN）

モデルの変換状態と派生ファイルの情報を取得します。

#### メタデータビュー一覧の取得

```
get_metadata_views
```

パラメータ：
- `urn`: モデルのURN

モデル内のビュー（3Dビュー、2D図面等）の一覧を取得します。

#### オブジェクトツリーの取得

```
get_object_tree
```

パラメータ：
- `urn`: モデルのURN
- `guid`: ビューGUID（`get_metadata_views`で取得）

モデルの階層構造（壁、柱、ドア等の親子関係）を取得します。

#### 全プロパティの取得

```
get_all_properties
```

パラメータ：
- `urn`: モデルのURN
- `guid`: ビューGUID

すべてのオブジェクトのプロパティ（寸法、材質、位置等）を取得します。

## ワークフロー例

### BIM360/ACCプロジェクトからモデルの要素データを取得

完全なワークフロー：

1. `list_hubs` でハブ一覧を取得
2. `list_projects` で特定ハブのプロジェクト一覧を取得
3. `get_project_top_folders` でプロジェクトのトップフォルダを取得
4. `get_folder_contents` でフォルダ内のファイルを探索
5. `get_item_tip` で目的のファイルの最新バージョンとDerivative URNを取得
6. `get_manifest` でモデルの変換状態を確認
7. `get_metadata_views` でモデル内のビュー一覧を取得
8. `get_object_tree` でオブジェクトの階層構造を取得
9. `get_all_properties` ですべてのオブジェクトのプロパティ（寸法、材質等）を取得

このワークフローで、BIM360/ACCプロジェクト内のRevitモデル等から、壁、柱、ドア等の要素データと詳細プロパティを取得できます。

## 開発

### テストの実行

```bash
pip install -e ".[dev]"
pytest
```

## 注意事項

- このサーバーは2-legged OAuth（クライアント認証）を使用します
- アクセストークンは自動的に取得・更新されます
- バケット名は、Client IDをプレフィックスとして含める必要がある場合があります（例：`{client_id}_mybucket`）

## ライセンス

MIT

## 参考リンク

- [APS Documentation](https://aps.autodesk.com/en/docs)
- [MCP Documentation](https://modelcontextprotocol.io)
- [Data Management API](https://aps.autodesk.com/en/docs/data/v2)
- [AEC Data Model API](https://aps.autodesk.com/en/docs/bim360/v1/overview/)
- [Model Derivative API](https://aps.autodesk.com/en/docs/model-derivative/v2)
