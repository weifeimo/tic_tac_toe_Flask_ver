from psycopg2.extras import Json #cellsのlistをJSONB型に変換するため
from db_check import get_connection
from game import TicTacToe


def _json_or_none(value):
    # None は JSON の null ではなく SQL の NULL として保存する
    return Json(value) if value is not None else None


# insert_game は前回のまま（winning_pattern の処理を _json_or_none に置き換えてもOK）


def get_game(game_id):
    """game_id で1局を取得して TicTacToe にして返す。なければ None。"""
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
                (game_id,),
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
                        game.game_id,
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