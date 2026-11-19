"""DB に保存される動作、404、ユーザーごとのデータ分離のテスト。

client / make_client は conftest.py のフィクスチャ（ログイン済みのクライアント）。
テストで作ったユーザーと、そのユーザーの games は、テスト終了後に conftest.py が削除する。
"""
from helpers import COOKIE_NAME, create_session, fetch_one, make_token


def call(client, method, url):
    """リクエストを送り、レスポンスの JSON を返す。"""
    return getattr(client, method)(url).get_json()


# ------------------------------------------------
# 保存と復元
# ------------------------------------------------

def test_state_persists_across_requests(client):
    first = call(client, "post", "/api/start")
    call(client, "post", "/api/play/0")

    again = call(client, "get", "/api/state")  # 再読み込みに相当

    assert again["game_id"] == first["game_id"]
    assert again["cells"][0] == 0


def test_restart_creates_new_game(client):
    first = call(client, "post", "/api/start")
    second = call(client, "post", "/api/start")

    assert first["game_id"] != second["game_id"]
    # 再読み込みしても、新しい方の局が返る
    assert call(client, "get", "/api/state")["game_id"] == second["game_id"]


def test_win_flow(client):
    call(client, "post", "/api/start")

    for pos in [0, 3, 1, 4, 2]:
        state = call(client, "post", f"/api/play/{pos}")

    assert state["status"] == "win"
    assert state["winner"] == 0
    assert state["winning_pattern"] == [0, 1, 2]

    # 再読み込みしても勝敗が残っている
    again = call(client, "get", "/api/state")
    assert again["status"] == "win"


def test_draw_flow(client):
    call(client, "post", "/api/start")

    for pos in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        state = call(client, "post", f"/api/play/{pos}")

    assert state["status"] == "draw"
    assert state["winning_pattern"] is None


def test_game_is_kept_after_logging_in_again(client):
    # ログアウト → 再ログインで新しいセッション（cookie）になっても、同じユーザーなら自分の局が見える
    first = call(client, "post", "/api/start")
    call(client, "post", "/api/play/0")

    client.set_cookie(COOKIE_NAME, make_token(create_session(client.user_id)))

    again = call(client, "get", "/api/state")
    assert again["game_id"] == first["game_id"]
    assert again["cells"][0] == 0


# ------------------------------------------------
# ゲームが見つからない（404）
# ------------------------------------------------

def test_state_without_game_returns_404_and_creates_nothing(client, monkeypatch):
    inserted = []
    monkeypatch.setattr("app.insert_game", lambda game, user_id: inserted.append(game))

    # 初回表示でリクエストが重複しても（React Strict Mode）、ゲームは作られない
    first = client.get("/api/state")
    second = client.get("/api/state")

    assert first.status_code == 404
    assert second.status_code == 404
    assert first.get_json() == {"error": "game_not_found"}
    assert inserted == []
    with client.session_transaction() as sess:
        assert "game_id" not in sess


def test_play_without_game_returns_404_and_creates_nothing(client, monkeypatch):
    inserted = []
    monkeypatch.setattr("app.insert_game", lambda game, user_id: inserted.append(game))

    response = client.post("/api/play/0")

    assert response.status_code == 404
    assert inserted == []


def test_state_returns_404_when_game_is_missing_in_db(client):
    # session には game_id があるが、DB に該当行がない場合
    with client.session_transaction() as sess:
        sess["game_id"] = "00000000-0000-0000-0000-000000000000"

    response = client.get("/api/state")

    assert response.status_code == 404


# ------------------------------------------------
# ユーザーごとのデータ分離
# ------------------------------------------------

def test_started_game_is_saved_with_the_logged_in_user_id(client):
    state = call(client, "post", "/api/start")

    row = fetch_one("SELECT user_id FROM games WHERE game_id = %s", (state["game_id"],))

    assert row is not None
    assert row[0] == client.user_id


def test_other_user_cannot_read_the_game(make_client):
    owner = make_client()
    other = make_client()
    started = call(owner, "post", "/api/start")

    # other の session に owner の game_id が入っていても（推測・盗用されても）取得できない
    with other.session_transaction() as sess:
        sess["game_id"] = started["game_id"]
    response = other.get("/api/state")

    assert response.status_code == 404
    assert response.get_json() == {"error": "game_not_found"}


def test_other_user_cannot_play_in_the_game(make_client):
    owner = make_client()
    other = make_client()
    started = call(owner, "post", "/api/start")

    with other.session_transaction() as sess:
        sess["game_id"] = started["game_id"]
    response = other.post("/api/play/0")

    assert response.status_code == 404
    # owner の盤面は変わっていない
    assert call(owner, "get", "/api/state")["cells"] == [None] * 9