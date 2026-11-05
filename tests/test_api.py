import pytest

import app as app_module
from db_check import get_connection


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("game.RESULT_FILE", str(tmp_path / "game_results.json"))
    app_module.app.config["TESTING"] = True

    created_ids = []
    with app_module.app.test_client() as client:
        client.created_ids = created_ids
        yield client

    # テストで作った行だけ削除する
    if created_ids:
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM games WHERE game_id = ANY(%s::uuid[])",
                        (created_ids,),
                    )
        finally:
            conn.close()


def call(client, method, url):
    """リクエストを送り、返ってきた game_id を後片付け用に記録する。"""
    response = getattr(client, method)(url)
    data = response.get_json()
    if data["game_id"] not in client.created_ids:
        client.created_ids.append(data["game_id"])
    return data


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


def test_state_without_game_returns_404_and_creates_nothing(client, monkeypatch):
    inserted = []
    monkeypatch.setattr(app_module, "insert_game", lambda game: inserted.append(game))

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
    monkeypatch.setattr(app_module, "insert_game", lambda game: inserted.append(game))

    response = client.post("/api/play/0")

    assert response.status_code == 404
    assert inserted == []


def test_state_returns_404_when_game_is_missing_in_db(client):
    # session には game_id があるが、DB に該当行がない場合
    with client.session_transaction() as sess:
        sess["game_id"] = "00000000-0000-0000-0000-000000000000"

    response = client.get("/api/state")

    assert response.status_code == 404