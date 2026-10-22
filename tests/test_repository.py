import pytest

from db_check import get_connection
from game import TicTacToe
from repository import get_game, insert_game, update_game


@pytest.fixture
def new_game(monkeypatch, tmp_path):
    # 対局終了時に game_results.json を書き換えないよう、保存先を一時フォルダにする
    monkeypatch.setattr("game.RESULT_FILE", str(tmp_path / "game_results.json"))

    game = TicTacToe()
    game.start()
    yield game

    # テストで作った行だけ削除する
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM games WHERE game_id = %s", (game.game_id,))
    finally:
        conn.close()


def winning_pattern_is_sql_null(game_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT winning_pattern IS NULL FROM games WHERE game_id = %s",
                (game_id,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def test_insert_and_get(new_game):
    insert_game(new_game)

    loaded = get_game(new_game.game_id)

    assert loaded.game_id == new_game.game_id
    assert loaded.player == 0
    assert loaded.cells == [None] * 9
    assert loaded.game_running is True
    assert loaded.winning_pattern is None


def test_get_missing_returns_none():
    assert get_game("00000000-0000-0000-0000-000000000000") is None


def test_update_saves_win(new_game):
    insert_game(new_game)

    for pos in [0, 3, 1, 4, 2]:  # X が 0,1,2 で勝つ
        new_game.play_turn(pos)
    assert update_game(new_game) is True

    loaded = get_game(new_game.game_id)
    assert loaded.game_running is False
    assert loaded.winning_pattern == [0, 1, 2]
    assert loaded.cells[:5] == [0, 0, 0, 1, 1]


def test_update_saves_draw_as_sql_null(new_game):
    insert_game(new_game)

    for pos in [0, 1, 2, 4, 3, 5, 7, 6, 8]:  # 引き分けになる手順
        new_game.play_turn(pos)
    update_game(new_game)

    loaded = get_game(new_game.game_id)
    assert loaded.game_running is False
    assert loaded.winning_pattern is None
    # JSON の null ではなく、SQL の NULL として保存されていること
    assert winning_pattern_is_sql_null(new_game.game_id) is True


def test_update_missing_returns_false(new_game):
    # insert していないので、更新対象の行がない
    assert update_game(new_game) is False