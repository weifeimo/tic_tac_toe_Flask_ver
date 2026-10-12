import os
from dotenv import load_dotenv

from flask import Flask, jsonify, render_template, session
from game import TicTacToe

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # DEVELOPMENT only


def load_game():
    data = session.get("game")
    if data is None:
        game = TicTacToe()
        game.start()
        return game
    return TicTacToe.from_dict(data)


def save_game(savedata):
    session["game"] = savedata.to_dict()


def get_state(savedata):
    winning_pattern = savedata.winning_pattern
    winner = None
    status = "playing"

    if not savedata.game_running:
        if winning_pattern is not None:
            status = "win"
            winner = savedata.cells[winning_pattern[0]]
            # 勝ったマスの持ち主 (0 = X, 1 = O)
        else:
            status = "draw"

    return {
        "cells": savedata.cells,
        "player": savedata.player,
        "game_running": savedata.game_running,
        "game_id": savedata.game_id,
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
    save_game(game)
    return jsonify(get_state(game))


@app.route("/api/start", methods=["POST"])
def api_start():
    game = TicTacToe()
    game.start()
    save_game(game)
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