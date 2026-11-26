import psycopg2
import pytest

from game import TicTacToe
from helpers import connect, fetch_one
from repository import get_game, insert_game, update_game


@pytest.fixture
def user_id(make_user):
    # games.user_id は users.id への外部キーなので、先にユーザーを作る。
    # テスト終了後、conftest.py の make_user がユーザーと games の行を削除する。
    return make_user()


@pytest.fixture
def new_game(monkeypatch, tmp_path):
    # 対局終了時に game_results.json を書き換えないよう、保存先を一時フォルダにする
    monkeypatch.setattr("game.RESULT_FILE", str(tmp_path / "game_results.json"))

    game = TicTacToe()
    game.start()
    return game


def winning_pattern_is_sql_null(game_id):
    row = fetch_one(
        "SELECT winning_pattern IS NULL FROM games WHERE game_id = %s", (game_id,)
    )
    return row[0]


def test_insert_and_get(new_game, user_id):
    insert_game(new_game, user_id)

    loaded = get_game(new_game.game_id, user_id)

    assert loaded.game_id == new_game.game_id
    assert loaded.player == 0
    assert loaded.cells == [None] * 9
    assert loaded.game_running is True
    assert loaded.winning_pattern is None


def test_insert_saves_user_id(new_game, user_id):
    insert_game(new_game, user_id)

    row = fetch_one("SELECT user_id FROM games WHERE game_id = %s", (new_game.game_id,))

    assert row[0] == user_id


def test_get_missing_returns_none(user_id):
    assert get_game("00000000-0000-0000-0000-000000000000", user_id) is None


def test_get_returns_none_for_another_users_game(new_game, user_id, make_user):
    insert_game(new_game, user_id)
    other_user_id = make_user()

    # game_id が合っていても、持ち主でなければ取得できない
    assert get_game(new_game.game_id, other_user_id) is None


def test_insert_fails_for_unknown_user(new_game):
    # 存在しない user_id は外部キー制約で拒否される
    with pytest.raises(psycopg2.IntegrityError):
        insert_game(new_game, 2_147_483_647)


def test_deleting_user_deletes_their_games(new_game, user_id):
    insert_game(new_game, user_id)

    # ON DELETE CASCADE：ユーザーを消すと、そのユーザーの games も消える
    # （sessions も同様。user_id の行は make_user の後片付けが再度削除しても問題ない）
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    finally:
        conn.close()

    assert fetch_one("SELECT 1 FROM games WHERE game_id = %s", (new_game.game_id,)) is None


def test_update_saves_win(new_game, user_id):
    insert_game(new_game, user_id)

    for pos in [0, 3, 1, 4, 2]:  # X が 0,1,2 で勝つ
        new_game.play_turn(pos)
    assert update_game(new_game) is True

    loaded = get_game(new_game.game_id, user_id)
    assert loaded.game_running is False
    assert loaded.winning_pattern == [0, 1, 2]
    assert loaded.cells[:5] == [0, 0, 0, 1, 1]


def test_update_saves_draw_as_sql_null(new_game, user_id):
    insert_game(new_game, user_id)

    for pos in [0, 1, 2, 4, 3, 5, 7, 6, 8]:  # 引き分けになる手順
        new_game.play_turn(pos)
    update_game(new_game)

    loaded = get_game(new_game.game_id, user_id)
    assert loaded.game_running is False
    assert loaded.winning_pattern is None
    # JSON の null ではなく、SQL の NULL として保存されていること
    assert winning_pattern_is_sql_null(new_game.game_id) is True


def test_update_missing_returns_false(new_game):
    # insert していないので、更新対象の行がない
    assert update_game(new_game) is False