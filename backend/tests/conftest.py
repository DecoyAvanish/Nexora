import pytest

from backend.app import create_app
from backend.config import Settings


class FakePrediction:
    artifacts_available = True


@pytest.fixture()
def settings():
    return Settings("test", "127.0.0.1", 5001, ("http://localhost:3000",), None, 1)


@pytest.fixture()
def app(settings):
    app = create_app(settings, prediction=FakePrediction())
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
