from game import TicTacToe


def new_game():
    game = TicTacToe()
    game.start()
    return game


def test_game_can_be_created():
    game = new_game()

    assert game.game_running is True
    assert game.player == 0
    assert game.cells == [None] * 9


def test_play_turn_places_mark_and_switches_player():
    game = new_game()

    game.play_turn(0)

    assert game.cells[0] == 0   # X put into 0 position
    assert game.player == 1     # turn to O


def test_cannot_play_on_occupied_cell():
    game = new_game()
    game.play_turn(0)

    game.play_turn(0)           # try to play on the same cell

    assert game.cells[0] == 0   # not overwritten
    assert game.player == 1     # player not switched

def test_winner_ends_the_game():
    game = new_game()

    # X: 0, 1, 2 / O: 3, 4
    for position in [0, 3, 1, 4, 2]:
        game.play_turn(position)

    assert game.is_winner() == (0, 1, 2)
    assert game.game_running is False


def test_cannot_play_after_game_over():
    game = new_game()
    for position in [0, 3, 1, 4, 2]:
        game.play_turn(position)

    game.play_turn(8)

    assert game.cells[8] is None


def test_draw_ends_the_game():
    game = new_game()

    # 最终棋盘：
    # X O X
    # X O O
    # O X X
    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        game.play_turn(position)

    assert game.is_winner() is None
    assert game.is_draw() is True
    assert game.game_running is False


def test_to_dict_and_from_dict_restore_the_game():
    game = new_game()
    game.play_turn(0)
    game.play_turn(4)

    data = game.to_dict()
    restored = TicTacToe.from_dict(data)

    assert restored.cells == game.cells
    assert restored.player == game.player
    assert restored.game_running == game.game_running