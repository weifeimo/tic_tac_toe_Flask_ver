from flask import Flask, jsonify, render_template
from game import game

app = Flask(__name__)


def get_state():
    return {
        "cells": game.cells,
        "player": game.player,
        "game_running": game.game_running,

        "winning_pattern": None if game.game_running else game.is_winner(),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def api_start():
    game.start()
    return jsonify(get_state())


@app.route("/api/play/<int:position>", methods=["POST"])
def api_play(position):
    if 0 <= position < 9:
        game.play_turn(position)
    return jsonify(get_state())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)