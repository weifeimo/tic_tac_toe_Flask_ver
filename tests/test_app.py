import os


os.environ["SECRET_KEY"] = "test-secret-key"

from app import app


def make_client():
    app.config["TESTING"] = True
    return app.test_client()


def test_start_returns_new_game():
    client = make_client()

    response = client.post("/api/start")

    assert response.status_code == 200
    assert response.json["cells"] == [None] * 9
    assert response.json["player"] == 0
    assert response.json["game_running"] is True


def test_play_is_kept_in_session():
    client = make_client()
    client.post("/api/start")

    client.post("/api/play/0")
    response = client.get("/api/state")

    assert response.json["cells"][0] == 0   # X's mark is still there
    assert response.json["player"] == 1     # turn to O


def test_moves_accumulate_across_requests():
    client = make_client()
    client.post("/api/start")

    client.post("/api/play/0")   # X
    client.post("/api/play/4")   # O
    response = client.get("/api/state")

    assert response.json["cells"][0] == 0
    assert response.json["cells"][4] == 1


def test_invalid_position_is_ignored():
    client = make_client()
    client.post("/api/start")

    response = client.post("/api/play/9")

    assert response.json["cells"] == [None] * 9
    assert response.json["player"] == 0


def test_start_resets_the_game():
    client = make_client()
    client.post("/api/start")
    client.post("/api/play/0")

    response = client.post("/api/start")

    assert response.json["cells"] == [None] * 9


def test_different_clients_have_separate_games():
    client_a = make_client()
    client_b = make_client()
    client_a.post("/api/start")
    client_b.post("/api/start")

    client_a.post("/api/play/0")
    response = client_b.get("/api/state")

    assert response.json["cells"][0] is None   # B is not affected by A's move