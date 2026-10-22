from psycopg2.extras import Json #cellsのlistをJSONB型に変換するため
from db_check import get_connection
from game import TicTacToe


def _json_or_none(value):
    # None は JSON の null ではなく SQL の NULL として保存する
    if value is not None:
        return Json(value)
    else:
        return None


def insert_game(game):
    """新しいゲームを games テーブルに1行追加する。"""
    conn = get_connection()
    try:
        with conn:  # 成功すれば commit、例外なら rollback
            with conn.cursor() as cur:
                cur.execute(
                    #SQL
                    """
                    INSERT INTO games
                        (game_id, player, cells, game_running, winning_pattern)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        game.game_id,
                        game.player,
                        Json(game.cells),
                        game.game_running,
                        _json_or_none(game.winning_pattern),
                    ),
                )
    finally:
        conn.close()


def get_game(game_id):
    """game_id で1局を取得して TicTacToe（Python list）にして返す。なければ None。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                #SQL
                """
                SELECT game_id, player, cells, game_running, winning_pattern
                FROM games
                WHERE game_id = %s
                """,
                (game_id,), #tuple要素、SQLパラメータに渡す。文字列ではない。
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return TicTacToe.from_dict(
        {
            "game_id": str(row[0]),
            "player": row[1],
            "cells": row[2],
            "game_running": row[3],
            "winning_pattern": row[4],
        }
    )


def update_game(game):
    """既存の1局を上書き保存する。更新できたら True、行がなければ False。"""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    #SQL
                    """
                    UPDATE games
                    SET player = %s,
                        cells = %s,
                        game_running = %s,
                        winning_pattern = %s
                    WHERE game_id = %s
                    """,
                    (
                        game.player,
                        Json(game.cells),
                        game.game_running,
                        _json_or_none(game.winning_pattern),
                        game.game_id,
                    ),
                )
                return cur.rowcount == 1
    finally:
        conn.close()