# Tic Tac Toe

Flask API + PostgreSQL + Next.js (TypeScript) で動く三目並べです。

- バックエンド：Flask（ゲームのロジックと API）、PostgreSQL（ゲーム状態の保存）
- フロントエンド：Next.js + TypeScript（`frontend/`）。画面表示と操作の送信だけを担当し、ゲームのロジックは持ちません。
- Flask のセッションには `game_id` だけを保存し、盤面などの状態は DB から取得します。

## Requirements
- Python 3.10+
- Node.js 24+（npm）
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（PostgreSQL を起動するために使用。事前に起動しておく）

## Setup

### 1. Python ライブラリをインストールする
```bash
pip install -r requirements.txt
```

### 2. 環境変数を設定する
`.env.example` をコピーして `.env` を作成し、値（特にパスワード）を書き換えます。

```bash
cp .env.example .env        # Windows (PowerShell): Copy-Item .env.example .env
```

| 変数名 | 内容 |
|---|---|
| `SECRET_KEY` | Flask のセッション用の秘密鍵（未設定の場合は開発用の値になる） |
| `POSTGRES_DB` | データベース名 |
| `POSTGRES_USER` | ユーザー名 |
| `POSTGRES_PASSWORD` | パスワード |
| `POSTGRES_HOST` | 接続先ホスト（ローカルは `localhost`） |
| `POSTGRES_PORT` | ポート番号（通常 `5432`） |

### 3. PostgreSQL を起動し、テーブルを作成する
```bash
docker compose up -d      # 起動（healthy になれば準備完了。確認: docker compose ps）

set -a; source .env; set +a
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < schema.sql
```

`CREATE TABLE IF NOT EXISTS` なので、繰り返し実行してもエラーになりません。
旧い定義のテーブルがある場合は、`DROP TABLE games;` を実行してから作り直してください。

その他のコマンド:
```bash
docker compose logs db    # ログ確認（接続できない時の原因調査用）
docker compose down       # 停止（データは保持される）
docker compose down -v    # 停止＋データも削除（DB を初期化したい時）
```

### 4. フロントエンドの依存パッケージをインストールする
```bash
cd frontend
npm install
```

## 起動方法

ターミナルを2つ使います。

**1. Flask（プロジェクトのルートで実行）**
```bash
python app.py             # http://127.0.0.1:5001
```
接続確認: http://127.0.0.1:5001/db-check を開き、`{"result": 1, "status": "ok"}` が表示されれば OK です。

> macOS では AirPlay レシーバーが 5000 番ポートを使うため、Flask は 5001 番で起動します。

**2. Next.js（`frontend/` で実行）**
```bash
npm run dev               # http://localhost:3000
```

ブラウザで http://localhost:3000 を開きます。

`/api/*` へのリクエストは、`frontend/next.config.ts` の `rewrites` で Flask に転送されます。
ブラウザからは同一オリジンに見えるため、セッション cookie がそのまま使え、CORS の設定は不要です。
転送先を変える場合は、`frontend/.env.local` に `FLASK_URL=http://127.0.0.1:5001` の形式で指定します（変更後は `npm run dev` を再起動）。

## API

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/api/state` | 現在のゲーム状態を取得（読み取り専用。ゲームがなければ `404`） |
| POST | `/api/start` | 新しいゲームを開始（ゲームの作成はここだけ） |
| POST | `/api/play/<position>` | マス（0〜8）を選択（ゲームがなければ `404`） |

`GET /api/state` と `POST /api/play/<position>` はゲームを新規作成しません。セッションに `game_id` がない、または DB に該当する行がない場合は、`404`（`{"error": "game_not_found"}`）を返します。
初回表示では、フロントエンドが先に `GET /api/state` で復元を試み、`404` のときだけ `POST /api/start` を呼びます。
これにより、初回表示のリクエストが重複しても（開発時の React Strict Mode など）、不要なゲームの行は作られません。

成功したときのレスポンスは、すべて同じ形式の JSON です。

```json
{
  "game_id": "…",
  "cells": [0, 1, null, null, null, null, null, null, null],
  "player": 0,
  "game_running": true,
  "status": "playing",
  "winner": null,
  "winning_pattern": null
}
```

| フィールド | 内容 |
|---|---|
| `cells` | 盤面。長さ9で、左上から右下の順。`null` = 空き、`0` = X、`1` = O |
| `player` | 現在の手番（`0` = X、`1` = O）。終了後は切り替わらず、最後に打ったプレイヤーのまま |
| `game_running` | 対局中は `true`、勝敗または引き分けで `false` |
| `status` | `"playing"` / `"win"` / `"draw"` |
| `winner` | 勝者（`0` / `1`）。勝敗が決まっていないとき・引き分けのときは `null` |
| `winning_pattern` | 勝った3マスの位置（例: `[0, 1, 2]`）。なければ `null` |

## データベース構成

ゲームの状態は `games` テーブルに保存されます（1ゲーム = 1行）。定義は [`schema.sql`](schema.sql) にあります。

| カラム | 型 | NULL | 内容 |
|---|---|---|---|
| `game_id` | UUID | 不可 | ゲームの一意な ID（主キー） |
| `player` | INTEGER | 不可 | 現在の手番（`0` = X、`1` = O） |
| `cells` | JSONB | 不可 | 盤面（長さ9の配列） |
| `game_running` | BOOLEAN | 不可 | 対局中は `true` |
| `winning_pattern` | JSONB | 可 | 勝った3マスの位置。対局中と引き分けのときは SQL の `NULL` |

テーブルの内容を確認するコマンド:
```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT * FROM games;'
```

## 動作確認

Flask と Next.js を起動した状態で、http://localhost:3000 を開いて確認します。

1. マスを選ぶと、X と O が交互に表示される。
2. 縦・横・斜めを揃えると勝者が表示され、勝ったマスが強調される。盤面は操作できなくなる。
3. 引き分けを確認する。次の順にマスを選ぶ（X が先手）: `0 → 1 → 2 → 4 → 3 → 5 → 7 → 6 → 8`。`Draw!` が表示される。
4. ゲーム終了後に `RESTART` を押すと、盤面が空になる。DB には新しい `game_id` の行が追加され、以前の対局の行も残る。
5. 対局の途中でページを再読み込みしても、盤面が保持されている。
6. Flask を停止した状態でマスを選ぶと、エラーメッセージが表示される。

動作確認で作成した行をすべて削除する場合:
```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'DELETE FROM games;'
```

### 自動テスト
PostgreSQL を起動した状態で、プロジェクトのルートで実行します。
```bash
pytest -v
```

## Troubleshooting

| 症状 | 原因と対処 |
|---|---|
| `password authentication failed` | ① ローカルにインストール済みの PostgreSQL が 5432 番ポートを使っている → そのサービスを停止するか、`.env` の `POSTGRES_PORT` を `5433` などに変更して `docker compose up -d` をやり直す。② `.env` のユーザー名・パスワードを変更した → 旧設定がデータボリュームに残っているため、`docker compose down -v` で初期化してから再起動 |
| `Connection refused` | コンテナが起動していない。`docker compose ps` で確認し、`docker compose up -d` を実行 |
| `環境変数が未設定です` | `.env` が存在しない、または項目が足りない。`.env.example` と見比べる |
| `relation "games" does not exist` | テーブルが未作成。「Setup の 3」の `schema.sql` を実行する |
| `ModuleNotFoundError: psycopg2` | `pip install -r requirements.txt` を実行 |
| `/api/state` が 403 | macOS の AirPlay レシーバーが 5000 番ポートを使っている。Flask は 5001 番で起動する |
| `/api/state` が 500 | Flask 側のターミナルのエラーを確認する（DB 未起動・テーブル未作成が多い） |
| 画面に「サーバーに接続できませんでした」と出る | Flask が起動していない、または転送先のポートが違う。設定を直したら `npm run dev` を再起動する |
| `Missing script: "dev"` | `frontend/` ではない場所で実行している。`cd frontend` してから実行 |

## Project Structure
```
tic_tac_toe/
├── app.py                # Flask アプリ本体（API とセッション管理）
├── game.py               # ゲームのロジック（TicTacToe クラス）
├── repository.py         # games テーブルの保存・取得・更新
├── db_check.py           # DB 接続と接続確認（/db-check）
├── schema.sql            # games テーブルの作成用 SQL
├── docker-compose.yml    # PostgreSQL の起動設定
├── requirements.txt
├── pytest.ini
├── .env.example          # 環境変数のサンプル
├── .github/workflows/    # GitHub Actions の設定
├── templates/            # 旧フロントエンド（Flask + JavaScript）
├── static/               # 旧フロントエンド（Flask + JavaScript）
├── tests/                # pytest
└── frontend/             # Next.js + TypeScript のフロントエンド
    ├── app/              # ページとレイアウト
    ├── components/       # Board / Cell / StatusMessage / RestartButton
    ├── lib/api.ts        # Flask API の呼び出しとエラー処理
    ├── types/game.ts     # API レスポンスの型
    └── next.config.ts    # /api/* を Flask へ転送する設定
```