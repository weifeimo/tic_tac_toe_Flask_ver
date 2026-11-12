# client / make_client は conftest.py のフィクスチャ（ログイン済みのクライアント）


def test_start_returns_new_game(client):
    response = client.post("/api/start")

    assert response.status_code == 200
    assert response.json["cells"] == [None] * 9
    assert response.json["player"] == 0
    assert response.json["game_running"] is True


def test_play_is_kept_in_session(client):
    client.post("/api/start")

    client.post("/api/play/0")
    response = client.get("/api/state")

    assert response.json["cells"][0] == 0   # X's mark is still there
    assert response.json["player"] == 1     # turn to O


def test_moves_accumulate_across_requests(client):
    client.post("/api/start")

    client.post("/api/play/0")   # X
    client.post("/api/play/4")   # O
    response = client.get("/api/state")

    assert response.json["cells"][0] == 0
    assert response.json["cells"][4] == 1


def test_invalid_position_is_ignored(client):
    client.post("/api/start")

    response = client.post("/api/play/9")

    assert response.json["cells"] == [None] * 9
    assert response.json["player"] == 0


def test_start_resets_the_game(client):
    client.post("/api/start")
    client.post("/api/play/0")

    response = client.post("/api/start")

    assert response.json["cells"] == [None] * 9


def test_different_clients_have_separate_games(make_client):
    client_a = make_client()   # 別のユーザー・別のブラウザ
    client_b = make_client()
    client_a.post("/api/start")
    client_b.post("/api/start")

    client_a.post("/api/play/0")
    response = client_b.get("/api/state")

    assert response.json["cells"][0] is None   # B is not affected by A's move


# test of JSON file

def test_state_includes_game_id_and_status(client):
    response = client.post("/api/start")

    assert response.json["status"] == "playing"
    assert response.json["winner"] is None
    assert response.json["winning_pattern"] is None
    assert response.json["game_id"]


def test_game_id_stays_the_same_during_a_game(client):
    started = client.post("/api/start")

    client.post("/api/play/0")
    response = client.get("/api/state")

    assert response.json["game_id"] == started.json["game_id"]


def test_start_creates_a_new_game_id(client):
    first = client.post("/api/start")

    second = client.post("/api/start")

    assert first.json["game_id"] != second.json["game_id"]


def test_win_state_is_returned(client):
    client.post("/api/start")

    for position in [0, 3, 1, 4, 2]:    # X wins with 0, 1, 2
        response = client.post(f"/api/play/{position}")

    assert response.json["status"] == "win"
    assert response.json["winner"] == 0
    assert response.json["winning_pattern"] == [0, 1, 2]
    assert response.json["game_running"] is False


def test_draw_state_is_returned(client):
    client.post("/api/start")

    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        response = client.post(f"/api/play/{position}")

    assert response.json["status"] == "draw"
    assert response.json["winner"] is None
    assert response.json["winning_pattern"] is None


def test_win_state_is_kept_in_session(client):
    client.post("/api/start")
    for position in [0, 3, 1, 4, 2]:
        client.post(f"/api/play/{position}")

    response = client.get("/api/state")     # reload the page

    assert response.json["status"] == "win"
    assert response.json["winning_pattern"] == [0, 1, 2]


def test_cannot_play_after_game_over_via_api(client):
    client.post("/api/start")
    for position in [0, 3, 1, 4, 2]:
        client.post(f"/api/play/{position}")

    response = client.post("/api/play/8")

    assert response.json["cells"][8] is None