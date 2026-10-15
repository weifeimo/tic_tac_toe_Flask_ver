import os

import psycopg2
from flask import Blueprint

bp = Blueprint("db_check", __name__)


def get_connection():
    """環境変数からPostgreSQLの接続情報を読み取って接続する。"""
    return psycopg2.connect(
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        connect_timeout=5,
    )



@bp.route("/db-check")
def db_check():
    """DBに接続して SELECT 1 を実行し、結果を返す（開発用の接続確認）。"""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
        finally:
            conn.close()
        return {"status": "ok", "result": result[0]}
    except KeyError as e:
        # 環境変数の設定漏れ
        return {"status": "error", "message": f"環境変数が未設定です: {e}"}, 500
    except Exception as e:
        # 接続失敗の原因をそのまま返す（開発用。本番では詳細を返さないこと）
        return {"status": "error", "message": str(e)}, 500