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



## How to Play
run `app.py`


## Project Structure
```text
tic_tac_toe/
├── app.py
├── db_check.py
├── docker-compose.yml
├── .env.example
├── game.py
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
