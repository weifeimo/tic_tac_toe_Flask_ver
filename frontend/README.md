# Tic Tac Toe — Frontend (Next.js + TypeScript)

Flask + JavaScript で実装していた画面を、Next.js + TypeScript に置き換えたフロントエンドです。
ゲームのロジックと状態管理は、これまでどおり Flask と PostgreSQL が担当します。フロントエンドは API の結果を表示し、操作を送るだけです。

## Requirements
- Node.js 24 以上（npm が使えることと、セキュリティーサポート継続中のバージョン）
- バックエンド（Flask + PostgreSQL）が起動できること → 手順はプロジェクトルートの [README](../README.md) を参照

## Setup

```bash
cd frontend
npm install
```

### 環境変数（任意）

| 変数名 | 内容 | 既定値 |
|---|---|---|
| `FLASK_URL` | 転送先の Flask の URL | `http://127.0.0.1:5001` |

既定値以外を使う場合は、`frontend/.env.local` に書きます。

```
FLASK_URL=http://127.0.0.1:5001
```

> `next.config.ts` の変更や `.env.local` の変更は、`npm run dev` を再起動しないと反映されません。

## 起動方法

ターミナルを2つ使います。

**1. バックエンド（プロジェクトのルートで実行）**

```bash
docker compose up -d      # PostgreSQL を起動（healthy になるまで待つ）
python app.py             # Flask を起動（http://127.0.0.1:5001）
```

**2. フロントエンド（`frontend/` で実行）**

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

## 仕組み

ブラウザは常に `localhost:3000`（Next.js）だけと通信します。
`/api/*` へのリクエストは、`next.config.ts` の `rewrites` で Flask に転送されます。
ブラウザから見ると同一オリジンになるため、Flask のセッション cookie がそのまま使え、CORS の設定は不要です。

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/api/state` | 現在のゲーム状態を取得（読み取り専用。ページ再読み込み時の復元にも使用。ゲームがなければ `404`） |
| POST | `/api/start` | 新しいゲームを開始（ゲームの作成はここだけ） |
| POST | `/api/play/<position>` | マス（0〜8）を選択 |

初回表示では、`page.tsx` の `useEffect` が `GET /api/state` を呼び、`404`（ゲームなし）のときだけ `POST /api/start` を呼びます。
`useEffect` のクリーンアップで「古い実行」を無視するため、開発時の React Strict Mode で Effect が2回走っても、ゲームの作成は1回だけです。

## ディレクトリ構成

```
frontend/
├── app/
│   ├── layout.tsx            # 共通レイアウト
│   ├── globals.css
│   └── page.tsx              # ゲーム画面（状態管理・API 呼び出し）
├── components/
│   ├── Board.tsx             # 盤面
│   ├── Cell.tsx              # 1マス
│   ├── StatusMessage.tsx     # メッセージ表示
│   ├── RestartButton.tsx     # RESTART ボタン
│   └── game.module.css       # スタイル
├── lib/
│   └── api.ts                # Flask API 呼び出しとエラー処理
├── types/
│   └── game.ts               # API レスポンスの型（GameState）
└── next.config.ts            # /api/* を Flask へ転送する設定
```

## 動作確認

1. マスを選ぶと X と O が交互に表示される。
2. 縦・横・斜めを揃えると勝者が表示され、勝ったマスが強調される。盤面は操作できなくなる。
3. 9マス埋まって勝者がいない場合、`Draw!` が表示される。
4. ゲーム終了後に `RESTART` を押すと、盤面が空になる。
5. 対局の途中でページを再読み込みしても、盤面が保持されている。
6. Flask を停止した状態でマスを選ぶと、エラーメッセージが表示される。

## Troubleshooting

| 症状 | 原因と対処 |
|---|---|
| `Missing script: "dev"` | `frontend/` ではない場所で実行している。`cd frontend` してから `npm run dev` |
| `/api/state` が 403 | macOS の AirPlay レシーバーが 5000 番ポートを使っている。Flask は 5001 番で起動する（既定） |
| `/api/state` が 500 | Flask または PostgreSQL に問題がある。Flask 側のターミナルのエラーを確認し、`docker compose ps` で DB が healthy か確認する |
| 画面が「サーバーに接続できませんでした」になる | Flask が起動していない、または `FLASK_URL` のポートが違う。設定を直したら `npm run dev` を再起動する |