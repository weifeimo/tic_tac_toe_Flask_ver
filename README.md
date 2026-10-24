## Tic Tac Toe (Web-APP)
### Flask and JavaScript version

Instead of the previous one-page version which I wrote with PyScript,
this version is updated with Flask and JavaScript.

### Previous version
https://github.com/weifeimo/tic_tac_toe_PyScript_ver


## Requirements
- Python 3.10+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（PostgreSQLをDockerで起動するために使用。事前に起動しておく）
- Pythonライブラリ（`requirements.txt` に記載）: Flask / python-dotenv / psycopg2-binary / pytest

```bash
pip install -r requirements.txt
```


## Setup
### 1. 環境変数を設定する
`.env.example` をコピーして `.env` を作成し、値（特にパスワード）を書き換えます。

```bash
cp .env.example .env        # Windows (PowerShell): Copy-Item .env.example .env
```

| 変数名 | 内容 |
|---|---|
| `SECRET_KEY` | Flaskのセッション用の秘密鍵 |
| `POSTGRES_DB` | データベース名 |
| `POSTGRES_USER` | ユーザー名 |
| `POSTGRES_PASSWORD` | パスワード |
| `POSTGRES_HOST` | 接続先ホスト（ローカルは `localhost`） |
| `POSTGRES_PORT` | ポート番号（通常 `5432`） |


### 2. PostgreSQLを起動・停止する
```bash
docker compose up -d      # 起動（バックグラウンド）
docker compose ps         # 状態確認（healthy になれば準備完了）
docker compose logs db    # ログ確認（接続できない時の原因調査用）
docker compose down       # 停止（データは保持される）
docker compose down -v    # 停止＋データも削除（DBを初期化したい時）
```

### 3. Flaskを起動して接続確認する
```bash
python app.py
```

ブラウザで http://127.0.0.1:5000/db-check を開きます。

- 成功: `{"result": 1, "status": "ok"}`
- 失敗: `{"message": "（原因）", "status": "error"}`

## Troubleshooting
| 症状 | 原因と対処 |
|---|---|
| `password authentication failed` | ① ローカルにインストール済みのPostgreSQLが5432番ポートを使っている → そのサービスを停止するか、`.env` の `POSTGRES_PORT` を `5433` などに変更して `docker compose up -d` をやり直す。② `.env` のユーザー名・パスワードを変更した → データボリュームに旧設定が残っているため `docker compose down -v` で初期化してから再起動 |
| `Connection refused` | コンテナが起動していない。`docker compose ps` で確認し、`docker compose up -d` を実行 |
| `環境変数が未設定です` | `.env` が存在しない、または項目が足りない。`.env.example` と見比べる |
| `ModuleNotFoundError: psycopg2` | `pip install -r requirements.txt` を実行 |


## データベース構成

ゲームの状態は PostgreSQL の `games` テーブルに保存されます（1ゲーム = 1行のレコード作成）。Flask のセッションには `game_id` だけを保存し、盤面などの状態は DB から取得します。

### テーブル構成

テーブル定義は [`schema.sql`](schema.sql) にあります。

```sql
CREATE TABLE IF NOT EXISTS games (
    game_id         UUID PRIMARY KEY,
    player          INTEGER NOT NULL CHECK (player IN (0, 1)),
    cells           JSONB NOT NULL CHECK (jsonb_array_length(cells) = 9),
    game_running    BOOLEAN NOT NULL,
    winning_pattern JSONB CHECK (winning_pattern IS NULL OR jsonb_array_length(winning_pattern) = 3)
);
```

| カラム | 型 | NULL | 内容 |
|---|---|---|---|
| `game_id` | UUID | 不可 | ゲームの一意なID（主キー） |
| `player` | INTEGER | 不可 | 現在の手番。`0` = X、`1` = O（勝敗が決まった後は最後に打ったプレイヤー） |
| `cells` | JSONB | 不可 | 盤面。長さ9の配列で、左上から右下の順。`null` = 空き、`0` = X、`1` = O（例: `[0, 1, null, 0, 1, null, 0, null, null]`） |
| `game_running` | BOOLEAN | 不可 | 対局中は `true`、勝敗または引き分けで終了すると `false` |
| `winning_pattern` | JSONB | 可 | 勝った3マスの位置（例: `[0, 1, 2]`）。対局中と引き分けのときは SQL の `NULL` |

### 関連ファイル

| ファイル | 役割 |
|---|---|
| `schema.sql` | テーブル作成用の SQL |
| `repository.py` | `games` テーブルの保存・取得・更新（`insert_game` / `get_game` / `update_game`） |
| `app.py` | セッションの `game_id` をもとに DB からゲームを読み書きする |

### テーブルの作成

PostgreSQL のコンテナを起動した状態で、プロジェクトのルートで実行します。

macOS / Linux:

```
set -a; source .env; set +a
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < schema.sql
```

`CREATE TABLE IF NOT EXISTS` を使っているため、繰り返し実行してもエラーになりません。ただし、すでに旧い定義のテーブルがある場合は変更が反映されません。作り直す場合は `DROP TABLE games;` を実行してから再度作成してください。

テーブルの構造は次のコマンドで確認できます。

```
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\d games'
```

> `source .env` は実行したターミナルでのみ有効です。新しいターミナルを開いた場合は、もう一度実行してください。

## 動作確認手順

### 1. 起動する

```
docker compose up -d      # PostgreSQL を起動
docker compose ps         # healthy になるまで待つ
python app.py
```

ブラウザで [http://127.0.0.1:5000/](http://127.0.0.1:5000/) を開きます。

### 2. 保存・再読み込みを確認する（DB に保存される）

1. いくつかマスを選択する。
2. 別のターミナルで DB の内容を確認する。`cells` が操作に合わせて更新されていれば OK。

```
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT game_id, player, cells, game_running, winning_pattern FROM games;'
```

3. ブラウザを再読み込みする。盤面が保持されていれば OK。

### 3. 勝敗判定を確認する

1. 縦・横・斜めのいずれかを揃えて勝敗を決める。
2. 画面で勝ったマスが表示されることを確認する。
3. DB を確認する。`game_running` が `f`、`winning_pattern` に3マスの位置（例: `[0, 1, 2]`）が入っていれば OK。

### 4. 引き分けを確認する

マスを次の順に選択すると引き分けになります（X が先手）。

```
0 → 1 → 2 → 4 → 3 → 5 → 7 → 6 → 8
```

画面に引き分けが表示され、DB では `game_running` が `f`、`winning_pattern` が `NULL` であれば OK。次のコマンドで `NULL` と JSON の `null` を区別して確認できます。

```
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT game_id, winning_pattern IS NULL AS is_sql_null FROM games WHERE game_running = false;'
```

### 5. リスタートを確認する

1. リスタートボタンを押す。盤面が空になることを確認する。
2. DB を確認する。新しい `game_id` の行が追加され、以前の対局の行も残っていれば OK。
3. 再読み込みしても、新しい対局の状態が表示されることを確認する。

### 6. 自動テストを実行する（任意）

```
pytest -v
```

`tests/` の内容は、保存・取得・更新（`repository.py`）と、API を通したゲームの進行・勝敗・引き分け・リスタートの確認です。PostgreSQL が起動している必要があります。

### テストデータの削除

動作確認で作成した行をすべて削除する場合:

```
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'DELETE FROM games;'
```

## Project Structure
```
tic_tac_toe/
├── app.py                # Flask アプリ本体（API とセッション管理）
├── game.py               # ゲームのロジック（TicTacToe クラス）
├── repository.py         # games テーブルの保存・取得・更新（CRUD）
├── db_check.py           # DB 接続と接続確認（/db-check）
├── schema.sql            # games テーブルの作成用 SQL
├── docker-compose.yml    # PostgreSQL の起動設定
├── requirements.txt
├── pytest.ini            # pytest の設定（プロジェクトルートを import パスに追加）
├── conftest.py           # テスト時に .env を読み込む
├── .env.example          # 環境変数のサンプル
├── .github/
│   └── workflows/        # GitHub Actions の設定
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
└── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_app.py
    ├── test_game.py
    └── test_repository.py
```

## How to Play
run `app.py`