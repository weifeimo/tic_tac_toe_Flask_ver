import json
import os
import uuid

RESULT_FILE = "game_results.json"              # ゲーム結果の保存ファイル


class TicTacToe:


    def start(self):

        # 0 = X
        # 1 = O

        self.player = 0

        self.cells = [None] * 9

        self.game_running = True

        self.game_id = str(uuid.uuid4())       #ユニークID

        self.saved = False                     #重複保存を避ける

        self.winning_pattern = None            # 勝った3マス（勝者なし/対局中は None）

    def play_turn(self, position):


        if not self.game_running:

            return


        # Cell already occupied
        if self.cells[position] is not None:

            return


        # Put player into cell
        self.cells[position] = self.player


        # Check game over
        if not self.is_game_over():

            self.next_player()

        else:

            self.save_result()


    def next_player(self):


        # 0 -> 1
        # 1 -> 0

        self.player = (self.player + 1) % 2


    def is_game_over(self):


        # -------------------------
        # WINNER
        # -------------------------

        winning_pattern = self.is_winner()

        if winning_pattern is not None:

            # 勝ったマスをゲーム本体に状態として保存
            self.winning_pattern = list(winning_pattern)

            self.game_running = False

            return True


        # -------------------------
        # DRAW
        # -------------------------

        if self.is_draw():

            self.game_running = False

            return True


        # -------------------------
        # CONTINUE
        # -------------------------

        return False


    # ------------------------------------------------
    # WINNER CHECKER
    # ------------------------------------------------

    def is_winner(self):


        win_patterns = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]


        for a, b, c in win_patterns:


            if (
                self.cells[a]
                == self.cells[b]
                == self.cells[c]
                == self.player
            ):

                return (a, b, c)


        return None


    # ------------------------------------------------
    # DRAW
    # ------------------------------------------------

    def is_draw(self):


        return all(

            value is not None

            for value in self.cells

        )


    # ------------------------------------------------
    # SAVE RESULT
    # ------------------------------------------------

    def save_result(self):

        # 重複保存を避ける
        if self.saved:

            return

        #辞書形式でゲームの結果を記録
        record = {

            "game_id": self.game_id,

            "player": self.player,

            "cells": self.cells

        }


        #空リストのファイル作成
        results = []

        if os.path.exists(RESULT_FILE):

            with open(RESULT_FILE, "r", encoding="utf-8") as f:

                results = json.load(f)


        # 既存ファイルに新しい結果を追加する
        results.append(record)

        with open(RESULT_FILE, "w", encoding="utf-8") as f:

            json.dump(results, f, ensure_ascii=False, indent=2)


        self.saved = True


    # ------------------------------------------------
    # SESSION (save / load)
    # ------------------------------------------------

    def to_dict(self):

        return {

            "player": self.player,

            "cells": self.cells,

            "game_running": self.game_running,

            "game_id": self.game_id,

            "saved": self.saved,

            "winning_pattern": self.winning_pattern

        }


    @classmethod
    def from_dict(cls, data):

        game = cls()

        game.player = data["player"]

        game.cells = data["cells"]

        game.game_running = data["game_running"]

        game.game_id = data["game_id"]

        game.saved = data["saved"]

        game.winning_pattern = data.get("winning_pattern")

        return game