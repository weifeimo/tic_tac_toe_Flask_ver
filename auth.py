"""Next.js が発行したログイン用 Cookie（JWT）を検証し、user_id を取り出す。"""
import os
import uuid
import jwt  # PyJWT
from flask import request
from db_check import get_connection

COOKIE_NAME = "session"  # frontend/lib/session.ts の COOKIE_NAME と同じ


def get_current_user_id():
    """ログイン中なら user_id（int）、未ログイン・期限切れ・不正なら None を返す。"""
    token = request.cookies.get(COOKIE_NAME)
    secret = os.environ.get("SESSION_SECRET")
    if not token or not secret:
        return None

    # 1. JWT の署名と有効期限（exp）を検証する
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        session_id = str(uuid.UUID(str(payload.get("sessionId"))))
    except (jwt.PyJWTError, ValueError):
        return None

    # 2. DB 上のセッションが存在し、期限内か確認する（ログアウト済みなら行が無い）
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id
                FROM sessions
                WHERE id = %s
                    AND expires_at > (NOW() AT TIME ZONE 'UTC')
                """,
                (session_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    return row[0] if row else None