"""テスト用の補助関数。

DB にユーザー・セッションの行を作り、Flask が受け付けるログイン用 cookie（JWT）を発行する。
フロントエンド（Next.js）が行っていることを、テストの中で再現するためのもの。
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT

COOKIE_NAME = "session"  # auth.py / frontend/lib/session.ts の COOKIE_NAME と同じ
SEVEN_DAYS = 7 * 24 * 60 * 60  # 秒


def connect():
    # DB を使わないテスト（test_game.py）でも conftest.py を読み込めるよう、ここで import する
    from db_check import get_connection

    return get_connection()


def fetch_one(sql, params=()):
    """SELECT を1回実行し、先頭の1行を返す（なければ None）。"""
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


def create_user(prefix="test_user"):
    """users に1行追加して、その id を返す。パスワードはログインに使わないのでダミー。"""
    username = f"{prefix}_{uuid.uuid4().hex[:12]}"  # username は UNIQUE
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                    (username, "not-a-real-hash"),
                )
                return cur.fetchone()[0]
    finally:
        conn.close()


def create_session(user_id, valid_for_seconds=SEVEN_DAYS):
    """sessions に1行追加して、その id（UUID の文字列）を返す。

    expires_at は auth.py と同じ UTC 基準（timestamp without time zone）で保存する。
    valid_for_seconds が負の値なら、期限切れのセッションになる。
    """
    session_id = str(uuid.uuid4())
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sessions (id, user_id, expires_at)
                    VALUES (%s, %s, (NOW() AT TIME ZONE 'UTC') + make_interval(secs => %s))
                    """,
                    (session_id, user_id, valid_for_seconds),
                )
    finally:
        conn.close()
    return session_id


def delete_session(session_id):
    """ログアウトと同じ：DB のセッションの行を削除する。"""
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
    finally:
        conn.close()


def make_token(session_id, secret=None, expires_in=timedelta(days=7)):
    """Next.js と同じ形式（HS256、payload に sessionId）のログイン用 JWT を作る。"""
    if secret is None:
        secret = os.environ["SESSION_SECRET"]
    payload = {
        "sessionId": str(session_id),
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def delete_users(user_ids):
    """テストで作ったユーザーと、そのユーザーの games / sessions を削除する。"""
    if not user_ids:
        return
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM games WHERE user_id = ANY(%s)", (user_ids,))
                cur.execute("DELETE FROM sessions WHERE user_id = ANY(%s)", (user_ids,))
                cur.execute("DELETE FROM users WHERE id = ANY(%s)", (user_ids,))
    finally:
        conn.close()