class TicTacToe:


    def start(self):

        # 0 = X
        # 1 = O

        self.player = 0

        self.cells = [None] * 9

        self.game_running = True


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


    def next_player(self):


        # 0 -> 1
        # 1 -> 0

        self.player = (self.player + 1) % 2


    def is_game_over(self):


        # -------------------------
        # WINNER
        # -------------------------

        winning_pattern = (
            self.is_winner()
        )


        if winning_pattern is not None:

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
    # SESSION (save / load)
    # ------------------------------------------------

    def to_dict(self):

        return {

            "player": self.player,

            "cells": self.cells,

            "game_running": self.game_running

        }


    @classmethod
    def from_dict(cls, data):

        game = cls()

        game.player = data["player"]

        game.cells = data["cells"]

        game.game_running = data["game_running"]

        return game