import json

from game import TicTacToe


def new_game():
    game = TicTacToe()
    game.start()
    return game


# ------------------------------------------------
# 基本動作
# ------------------------------------------------

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
# ------------------------------------------------
# 勝敗・引き分け
# ------------------------------------------------

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

    assert game.cells[8] is None   # 終了後は置けない


def test_draw_ends_the_game():
    game = new_game()

    # 最終盤面：
    # X O X
    # X O O
    # O X X
    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        game.play_turn(position)

    assert game.is_winner() is None
    assert game.is_draw() is True
    assert game.game_running is False


# ------------------------------------------------
# セッション（保存 / 復元）
# ------------------------------------------------

def test_to_dict_and_from_dict_restore_the_game():
    game = new_game()
    game.play_turn(0)
    game.play_turn(4)

    data = game.to_dict()
    restored = TicTacToe.from_dict(data)

    assert restored.cells == game.cells
    assert restored.player == game.player
    assert restored.game_running == game.game_running
    assert restored.game_id == game.game_id
    assert restored.saved == game.saved


# ------------------------------------------------
# game id
# ------------------------------------------------

def test_new_game_has_unique_game_id():
    game_a = new_game()
    game_b = new_game()

    assert game_a.game_id != game_b.game_id   # 毎回違うID
    assert game_a.saved is False              # 開始時は未保存


# ------------------------------------------------
# 結果の保存
# result_file は conftest.py の一時ファイル
# ------------------------------------------------

def test_nothing_is_saved_while_playing(result_file):
    game = new_game()

    game.play_turn(0)
    game.play_turn(4)

    assert not result_file.exists()   # 対局中は保存しない


def test_result_is_saved_when_game_is_won(result_file):
    game = new_game()

    for position in [0, 3, 1, 4, 2]:    # Xが0,1,2で勝利
        game.play_turn(position)

    records = json.loads(result_file.read_text(encoding="utf-8"))

    assert len(records) == 1
    assert records[0]["game_id"] == game.game_id
    assert records[0]["player"] == 0
    assert records[0]["cells"] == [0, 0, 0, 1, 1, None, None, None, None]
    assert game.saved is True


def test_result_is_saved_when_game_is_draw(result_file):
    game = new_game()

    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        game.play_turn(position)

    records = json.loads(result_file.read_text(encoding="utf-8"))

    assert len(records) == 1
    assert records[0]["game_id"] == game.game_id
    assert None not in records[0]["cells"]   # 全マス埋まっている


def test_same_game_is_saved_only_once(result_file):
    game = new_game()
    for position in [0, 3, 1, 4, 2]:
        game.play_turn(position)

    game.save_result()      # もう一度呼んでも保存されない
    game.play_turn(8)       # 終了後なので無視される

    records = json.loads(result_file.read_text(encoding="utf-8"))
    assert len(records) == 1


def test_restored_finished_game_is_not_saved_again(result_file):
    game = new_game()
    for position in [0, 3, 1, 4, 2]:
        game.play_turn(position)

    restored = TicTacToe.from_dict(game.to_dict())   # sessionから復元
    restored.save_result()

    records = json.loads(result_file.read_text(encoding="utf-8"))
    assert len(records) == 1   # 復元しても二重保存されない


def test_multiple_games_are_appended(result_file):
    for _ in range(2):
        game = new_game()
        for position in [0, 3, 1, 4, 2]:
            game.play_turn(position)

    records = json.loads(result_file.read_text(encoding="utf-8"))

    assert len(records) == 2                                  # 追記される
    assert records[0]["game_id"] != records[1]["game_id"]