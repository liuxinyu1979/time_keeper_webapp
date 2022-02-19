import pytest
from src import create_app
from src.config import TestingConfig

@pytest.fixture
def app_db(mocker):
    app, db = create_app({'TESTING':True})
    return app, db, mocker

