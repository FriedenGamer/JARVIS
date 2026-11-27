import pytest
import db


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    temp_db_path = tmp_path / "test_jarvis.db"
    monkeypatch.setattr(db, "DB_PATH", temp_db_path)