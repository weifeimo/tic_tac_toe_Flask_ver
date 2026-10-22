import os
from dotenv import load_dotenv

from flask import Flask, jsonify, render_template, session
from game import TicTacToe
from repository import get_game, insert_game, update_game
from db_check import bp as db_check_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # DEVELOPMENT only

app.register_blueprint(db_check_bp)

def load_game():
    """session の game_id から DB のゲームを取得する。なければ新規作成して保存する。"""
    game_id = session.get("game_id")
    if game_id is not None:
        game = get_game(game_id)
        if game is not None:
            return game

    # session に game_id がない、または DB に該当行がない場合は新しく始める
    game = TicTacToe()
    game.start()
    insert_game(game)
    session["game_id"] = game.game_id
    return game


def save_game(game):
    update_game(game)


def get_state(data):
    winning_pattern = data.winning_pattern
    winner = None
    status = "playing"

    if not data.game_running:
        if winning_pattern is not None:
            status = "win"
            winner = data.cells[winning_pattern[0]]
            # 勝ったマスの持ち主 (0 = X, 1 = O)
        else:
            status = "draw"

    return {
        "cells": data.cells,
        "player": data.player,
        "game_running": data.game_running,
        "game_id": data.game_id,
        "status": status,                 # "playing" / "win" / "draw"
        "winner": winner,                 # 0 / 1 / None
        "winning_pattern": winning_pattern,   # list（例: [0, 1, 2]）または None
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    game = load_game()
    return jsonify(get_state(game))


@app.route("/api/start", methods=["POST"])
def api_start():
    game = TicTacToe()
    game.start()
    insert_game(game)
    return jsonify(get_state(game))


@app.route("/api/play/<int:position>", methods=["POST"])
def api_play(position):
    game = load_game()
    if 0 <= position < 9:
        game.play_turn(position)
    save_game(game)
    return jsonify(get_state(game))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)