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
    first = call(client, "get", "/api/state")
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