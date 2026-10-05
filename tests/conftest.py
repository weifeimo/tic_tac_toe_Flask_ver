import pytest
import game as game_module


@pytest.fixture(autouse=True)
def result_file(tmp_path, monkeypatch):
    path = tmp_path / "game_results.json"
    monkeypatch.setattr(game_module, "RESULT_FILE", str(path))
    return path