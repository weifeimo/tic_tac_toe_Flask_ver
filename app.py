import os

from flask import Flask, jsonify, render_template, session
from game import TicTacToe

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]


def load_game():
    data = session.get("game")
    if data is None:
        game = TicTacToe()
        game.start()
        return game
    return TicTacToe.from_dict(data)


def save_game(game):
    session["game"] = game.to_dict()


def get_state(game):
    return {
        "cells": game.cells,
        "player": game.player,
        "game_running": game.game_running,
        "winning_pattern": None if game.game_running else game.is_winner(),
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
    return jsonify(get_state(game))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)