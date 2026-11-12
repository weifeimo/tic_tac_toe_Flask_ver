import os

import pytest
from dotenv import load_dotenv

# app.py を import する前に環境変数をそろえる。
# load_dotenv() は既に設定済みの値を上書きしないので、CI の値や手元の .env が優先される。
load_dotenv()
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-0123456789abcdef")

import game as game_module  # noqa: E402
from helpers import (  # noqa: E402
    COOKIE_NAME,
    create_session,
    create_user,
    delete_users,
    make_token,
)


@pytest.fixture(autouse=True)
def result_file(tmp_path, monkeypatch):
    path = tmp_path / "game_results.json"
    monkeypatch.setattr(game_module, "RESULT_FILE", str(path))
    return path


@pytest.fixture
def make_user():
    """テスト用のユーザーを作る関数を返す。テスト終了後に、作った全員（と games / sessions）を削除する。"""
    user_ids = []

    def _make():
        user_id = create_user()
        user_ids.append(user_id)
        return user_id

    yield _make

    delete_users(user_ids)


@pytest.fixture
def flask_app():
    import app as app_module

    app_module.app.config["TESTING"] = True
    return app_module.app


@pytest.fixture
def make_client(flask_app, make_user):
    """ログイン済みのテストクライアントを作る関数を返す。

    引数なしなら新しいユーザーとして、user_id を渡せばそのユーザーとしてログインする。
    クライアントは別々の cookie を持つので、別のブラウザに相当する。
    """

    def _make(user_id=None):
        if user_id is None:
            user_id = make_user()
        session_id = create_session(user_id)

        client = flask_app.test_client()
        client.set_cookie(COOKIE_NAME, make_token(session_id))
        client.user_id = user_id
        client.session_id = session_id
        return client

    return _make


@pytest.fixture
def client(make_client):
    """新しいユーザーとしてログイン済みのクライアント。"""
    return make_client()


@pytest.fixture
def anonymous_client(flask_app):
    """ログインしていない（cookie が無い）クライアント。"""
    return flask_app.test_client()