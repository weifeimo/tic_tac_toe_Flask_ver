import os
import psycopg2
from flask import Blueprint

bp = Blueprint("db_check", __name__)

@bp.route("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        conn.close()
        return {"status": "ok", "result": result[0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500