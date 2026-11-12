"""ログイン状態の検証（auth.py と login_required）のテスト。

ゲーム API はログイン必須。次の場合はすべて 401 になる。
  - cookie が無い / JWT が不正 / 署名鍵が違う / JWT の期限切れ
  - DB の sessions に行が無い（ログアウト済み）/ DB の期限切れ
"""
from datetime import timedelta

import pytest

from helpers import COOKIE_NAME, create_session, delete_session, make_token

PROTECTED_ENDPOINTS = [
    ("get", "/api/state"),
    ("post", "/api/start"),
    ("post", "/api/play/0"),
]


def client_with_token(flask_app, token):
    client = flask_app.test_client()
    client.set_cookie(COOKIE_NAME, token)
    return client


def assert_unauthorized(response):
    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}


@pytest.mark.parametrize("method, url", PROTECTED_ENDPOINTS)
def test_api_requires_login(anonymous_client, method, url):
    assert_unauthorized(getattr(anonymous_client, method)(url))


def test_start_without_login_creates_nothing(anonymous_client, monkeypatch):
    inserted = []
    monkeypatch.setattr("app.insert_game", lambda game, user_id: inserted.append(game))

    response = anonymous_client.post("/api/start")

    assert response.status_code == 401
    assert inserted == []


def test_garbage_token_is_rejected(flask_app):
    client = client_with_token(flask_app, "not-a-jwt")

    assert_unauthorized(client.get("/api/state"))


def test_token_signed_with_another_secret_is_rejected(flask_app, make_user):
    session_id = create_session(make_user())
    token = make_token(session_id, secret="another-secret-0123456789abcdefghij")

    assert_unauthorized(client_with_token(flask_app, token).get("/api/state"))


def test_token_with_invalid_session_id_is_rejected(flask_app):
    token = make_token("not-a-uuid")

    assert_unauthorized(client_with_token(flask_app, token).get("/api/state"))


def test_expired_token_is_rejected(flask_app, make_user):
    session_id = create_session(make_user())
    token = make_token(session_id, expires_in=timedelta(seconds=-10))

    assert_unauthorized(client_with_token(flask_app, token).get("/api/state"))


def test_session_missing_in_db_is_rejected(flask_app, make_user):
    # JWT は正しいが、DB に sessions の行が無い
    session_id = create_session(make_user())
    delete_session(session_id)

    client = client_with_token(flask_app, make_token(session_id))

    assert_unauthorized(client.get("/api/state"))


def test_session_expired_in_db_is_rejected(flask_app, make_user):
    # JWT は有効期限内だが、DB の sessions.expires_at が過去
    session_id = create_session(make_user(), valid_for_seconds=-60)

    client = client_with_token(flask_app, make_token(session_id))

    assert_unauthorized(client.get("/api/state"))


def test_logout_takes_effect_immediately(client):
    assert client.post("/api/start").status_code == 200

    # ログアウト（Next.js の logout アクション）は DB のセッション行を削除する
    delete_session(client.session_id)

    assert_unauthorized(client.get("/api/state"))
    assert_unauthorized(client.post("/api/start"))


def test_missing_session_secret_rejects_everyone(client, monkeypatch):
    monkeypatch.delenv("SESSION_SECRET")

    assert_unauthorized(client.get("/api/state"))