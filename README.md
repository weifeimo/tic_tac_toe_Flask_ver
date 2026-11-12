# Tic Tac Toe

Flask API + PostgreSQL + Next.js (TypeScript) で動く三目並べです。ユーザー登録・ログインができ、ゲームデータはユーザーごとに分離して保存されます。

- バックエンド：Flask（ゲームのロジックと API、ログイン状態の検証）、PostgreSQL（ユーザー・セッション・ゲーム状態の保存）
- フロントエンド：Next.js + TypeScript（`frontend/`）。画面表示、ユーザー登録・ログイン・ログアウト（Server Actions）を担当します。ゲームのロジックは持ちません。
- Flask のセッション cookie（`flask_session`）には `game_id` だけを保存し、盤面などの状態は DB から取得します。

## 認証の仕組み

認証（誰か）は Next.js、認可（そのデータにアクセスしてよいか）は Flask が担当します。

| 項目 | 内容 |
|---|---|
| ユーザー登録・ログイン・ログアウト | Next.js の Server Action（`frontend/app/actions/auth.ts`） |
| パスワードの保存 | Node 標準の `scrypt` + ユーザーごとのランダムなソルト（16 byte）。`<salt hex>:<hash hex>` の形式で `users.password` に保存。平文は保存しない |
| パスワードの照合 | `timingSafeEqual` で比較。ユーザーが存在しない場合も同程度の時間をかけ、エラーメッセージも常に同じにする |
| ログイン状態 | DB の `sessions` テーブルに行を作り、その `id` を入れた JWT（HS256、有効期限 7 日）を cookie `session` に保存 |
| cookie の属性 | `HttpOnly` / `SameSite=Lax` / `Path=/` / `Secure`（本番環境のみ） |
| ログアウト | cookie の削除に加えて、DB の `sessions` の行も削除（その場で無効になる） |
| ページの保護 | `frontend/proxy.ts` が JWT の署名だけを検証し、未ログインなら `/login` へ。`frontend/lib/dal.ts` が DB のセッションの有効期限まで確認 |
| API の保護 | Flask の `login_required`（`app.py`）。`auth.py` が JWT と DB のセッションを検証し、`user_id` を取り出す。未ログインなら `401` |
| データの分離 | `games.user_id` が `users.id` を参照（外部キー）。ゲームの取得は `game_id` と `user_id` の両方が一致する行だけ。他人の `game_id` は `404` になる |

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

**プロジェクトのルート**：`.env.example` をコピーして `.env` を作成し、値を書き換えます。

```bash
cp .env.example .env        # Windows (PowerShell): Copy-Item .env.example .env
```

| 変数名 | 内容 |
|---|---|
| `SECRET_KEY` | Flask のセッション用の秘密鍵（未設定の場合は開発用の値になる） |
| `SESSION_SECRET` | ログイン用 JWT の署名鍵。**`frontend/.env.local` と同じ値にする** |
| `POSTGRES_DB` | データベース名 |
| `POSTGRES_USER` | ユーザー名 |
| `POSTGRES_PASSWORD` | パスワード |
| `POSTGRES_HOST` | 接続先ホスト（ローカルは `localhost`） |
| `POSTGRES_PORT` | ポート番号（通常 `5432`） |

**`frontend/`**：`frontend/.env.example` をコピーして `frontend/.env.local` を作成します。

```bash
cp frontend/.env.example frontend/.env.local
```

| 変数名 | 内容 |
|---|---|
| `SESSION_SECRET` | ルートの `.env` と同じ値（異なると Flask がログインを認識できず、API が `401` になる） |
| `DATABASE_URL` | Next.js が接続する PostgreSQL の URL。例: `postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:<POSTGRES_PORT>/<POSTGRES_DB>` |

> `SESSION_SECRET` は推測されにくいランダムな文字列にしてください。例: `openssl rand -base64 32`

### 3. PostgreSQL を起動し、テーブルを作成する
```bash
docker compose up -d      # 起動（healthy になれば準備完了。確認: docker compose ps）

set -a; source .env; set +a
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < schema.sql
```

`CREATE TABLE IF NOT EXISTS` なので、繰り返し実行してもエラーになりません。
`games` に `user_id` 列が無い旧い定義のテーブルがある場合は、`DROP TABLE games;` を実行してから作り直してください（既存の対局データは失われます）。

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

ブラウザで http://localhost:3000 を開きます。未ログインの場合は `/login` に移動します。`/signup` でユーザーを登録してください。

`/api/*` へのリクエストは、`frontend/next.config.ts` の `rewrites` で Flask に転送されます。
ブラウザからは同一オリジンに見えるため、ログイン用の `session` cookie と Flask の `flask_session` cookie がそのまま Flask に届き、CORS の設定は不要です。
転送先を変える場合は、`frontend/.env.local` に `FLASK_URL=http://127.0.0.1:5001` の形式で指定します（変更後は `npm run dev` を再起動）。

## 画面

| パス | 内容 | ログイン |
|---|---|---|
| `/` | ゲーム画面（ユーザー名とログアウトボタンを表示） | 必要 |
| `/login` | ログイン | 不要（ログイン済みなら `/` へ移動） |
| `/signup` | ユーザー登録 | 不要（ログイン済みなら `/` へ移動） |

ユーザー登録の入力ルール:
- ユーザー名: 2文字以上（重複不可）
- パスワード: 8文字以上で、英字・数字・記号をそれぞれ1文字以上含む

## API

すべての `/api/*` はログインが必要です。未ログイン・期限切れ・ログアウト済みの場合は `401`（`{"error": "unauthorized"}`）を返します。

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/api/state` | 現在のゲーム状態を取得（読み取り専用。ゲームがなければ `404`） |
| POST | `/api/start` | 新しいゲームを開始（ゲームの作成はここだけ。ログイン中のユーザーのゲームとして保存） |
| POST | `/api/play/<position>` | マス（0〜8）を選択（ゲームがなければ `404`） |

`GET /api/state` と `POST /api/play/<position>` はゲームを新規作成しません。セッションに `game_id` がない、DB に該当する行がない、またはその行が別のユーザーのものである場合は、`404`（`{"error": "game_not_found"}`）を返します。
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

定義は [`schema.sql`](schema.sql) にあります（Next.js 側の定義は `frontend/lib/db/schema.ts`。両者は同じ内容にしてください）。

```
users (1) ──< sessions (多)
users (1) ──< games    (多)
```

**users**

| カラム | 型 | NULL | 内容 |
|---|---|---|---|
| `id` | SERIAL | 不可 | 主キー |
| `username` | VARCHAR(50) | 不可 | ユーザー名（UNIQUE） |
| `password` | TEXT | 不可 | `<salt hex>:<scrypt hash hex>`（平文は保存しない） |
| `created_at` | TIMESTAMP | 不可 | 登録日時 |

**sessions**

| カラム | 型 | NULL | 内容 |
|---|---|---|---|
| `id` | UUID | 不可 | 主キー（JWT に入れる値） |
| `user_id` | INTEGER | 不可 | `users.id` への外部キー（`ON DELETE CASCADE`） |
| `expires_at` | TIMESTAMP | 不可 | 有効期限（UTC）。ログインから 7 日 |
| `created_at` | TIMESTAMP | 不可 | 作成日時 |

**games**（1ゲーム = 1行）

| カラム | 型 | NULL | 内容 |
|---|---|---|---|
| `game_id` | UUID | 不可 | ゲームの一意な ID（主キー） |
| `user_id` | INTEGER | 不可 | ゲームの持ち主。`users.id` への外部キー（`ON DELETE CASCADE`）。インデックスあり |
| `player` | INTEGER | 不可 | 現在の手番（`0` = X、`1` = O） |
| `cells` | JSONB | 不可 | 盤面（長さ9の配列） |
| `game_running` | BOOLEAN | 不可 | 対局中は `true` |
| `winning_pattern` | JSONB | 可 | 勝った3マスの位置。対局中と引き分けのときは SQL の `NULL` |

テーブルの内容を確認するコマンド:
```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT id, username, password FROM users;'
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT game_id, user_id, game_running FROM games;'
```

## 動作確認

Flask と Next.js を起動した状態で、http://localhost:3000 を開いて確認します。

**認証**
1. `/signup` でユーザーを登録する。登録後にゲーム画面へ移動し、ユーザー名が表示される。同じユーザー名で再登録するとエラーになる。
2. ログアウトボタンを押すと `/login` に移動する。登録したユーザーで再びログインできる。間違ったパスワードでは `Invalid username or password.` と表示される。
3. ログイン後にページを再読み込みしても、ログイン状態が維持される。
4. 上記の `SELECT … FROM users;` で、`password` が `<salt>:<hash>` の形式（平文でない）で保存されていることを確認する。
5. ログアウト後に `curl -i http://127.0.0.1:5001/api/state` を実行すると `401` が返る（ログインしていない状態でもゲーム API は使えない）。

**ユーザーごとのデータ分離**
6. 通常のウィンドウとシークレットウィンドウで、別のユーザーとしてログインする。それぞれ別の盤面で遊べ、`SELECT game_id, user_id FROM games;` で `user_id` が分かれている。
7. 一方のユーザーでログアウトし、別のユーザーでログインし直すと、前のユーザーの盤面は表示されず、新しいゲームが始まる（他のユーザーの `game_id` では `404` になる）。

**ゲーム**
8. マスを選ぶと、X と O が交互に表示される。
9. 縦・横・斜めを揃えると勝者が表示され、勝ったマスが強調される。盤面は操作できなくなる。
10. 引き分けを確認する。次の順にマスを選ぶ（X が先手）: `0 → 1 → 2 → 4 → 3 → 5 → 7 → 6 → 8`。`Draw!` が表示される。
11. ゲーム終了後に `RESTART` を押すと、盤面が空になる。DB には新しい `game_id` の行が追加され、以前の対局の行も残る。
12. 対局の途中でページを再読み込みしても、盤面が保持されている。
13. Flask を停止した状態でマスを選ぶと、エラーメッセージが表示される。

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
| `password authentication failed` | ① ローカルにインストール済みの PostgreSQL が 5432 番ポートを使っている → そのサービスを停止するか、`.env` の `POSTGRES_PORT` を `5433` などに変更して `docker compose up -d` をやり直す（`frontend/.env.local` の `DATABASE_URL` のポートも合わせる）。② `.env` のユーザー名・パスワードを変更した → 旧設定がデータボリュームに残っているため、`docker compose down -v` で初期化してから再起動 |
| `Connection refused` | コンテナが起動していない。`docker compose ps` で確認し、`docker compose up -d` を実行 |
| `環境変数が未設定です` | `.env` が存在しない、または項目が足りない。`.env.example` と見比べる |
| `SESSION_SECRET is not defined` / `DATABASE_URL is not defined` | `frontend/.env.local` が無い、または項目が足りない。設定後に `npm run dev` を再起動する |
| `relation "games" / "users" / "sessions" does not exist` | テーブルが未作成。「Setup の 3」の `schema.sql` を実行する |
| `column "user_id" of relation "games" does not exist` | `user_id` 列の無い旧い `games` テーブルが残っている。`DROP TABLE games;` してから `schema.sql` を再実行する |
| ログインしているのに `/api/*` が `401` | ルートの `.env` と `frontend/.env.local` の `SESSION_SECRET` が違う、または Flask を `.env` の変更後に再起動していない |
| ログインできたのに `/login` に戻される | `sessions` テーブルに行が無い、または期限切れ。再ログインする |
| `ModuleNotFoundError: psycopg2` / `jwt` | `pip install -r requirements.txt` を実行 |
| `/api/state` が 403 | macOS の AirPlay レシーバーが 5000 番ポートを使っている。Flask は 5001 番で起動する |
| `/api/state` が 500 | Flask 側のターミナルのエラーを確認する（DB 未起動・テーブル未作成が多い） |
| 画面に「サーバーに接続できませんでした」と出る | Flask が起動していない、または転送先のポートが違う。設定を直したら `npm run dev` を再起動する |
| `Missing script: "dev"` | `frontend/` ではない場所で実行している。`cd frontend` してから実行 |

## Project Structure
```
tic_tac_toe/
├── app.py                # Flask アプリ本体（API、login_required、セッション管理）
├── auth.py               # ログイン用 cookie（JWT）と DB のセッションを検証して user_id を返す
├── game.py               # ゲームのロジック（TicTacToe クラス）
├── repository.py         # games テーブルの保存・取得・更新（user_id で絞り込み）
├── db_check.py           # DB 接続と接続確認（/db-check）
├── schema.sql            # users / sessions / games テーブルの作成用 SQL
├── docker-compose.yml    # PostgreSQL の起動設定
├── requirements.txt
├── pytest.ini
├── .env.example          # 環境変数のサンプル
├── .github/workflows/    # GitHub Actions の設定
├── templates/            # 旧フロントエンド（Flask + JavaScript）
├── static/               # 旧フロントエンド（Flask + JavaScript）
├── tests/                # pytest
└── frontend/             # Next.js + TypeScript のフロントエンド
    ├── app/
    │   ├── page.tsx          # ゲーム画面（要ログイン）
    │   ├── login/, signup/   # ログイン・ユーザー登録ページ
    │   └── actions/auth.ts   # signup / login / logout（Server Actions、scrypt でハッシュ化）
    ├── components/       # Game / Board / Cell / StatusMessage / RestartButton / LogoutButton
    ├── ui/               # login-form / signup-form
    ├── lib/
    │   ├── session.ts    # JWT の作成・検証、セッション cookie の設定
    │   ├── dal.ts        # DB のセッションを確認する verifySession / getUser
    │   ├── definitions.ts# 入力チェック（zod）
    │   ├── db/           # Drizzle の接続とテーブル定義
    │   └── api.ts        # Flask API の呼び出しとエラー処理
    ├── proxy.ts          # 未ログインのページアクセスを /login へ移動
    ├── types/game.ts     # API レスポンスの型
    └── next.config.ts    # /api/* を Flask へ転送する設定