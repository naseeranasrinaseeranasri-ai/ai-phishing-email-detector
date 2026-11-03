import pytest

from app import create_app
from app.database import init_db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own throwaway database, so your real history is never touched."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()