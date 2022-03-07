import pytest
from src import create_app
from src.config import TestingConfig

# https://pytest-cov.readthedocs.io/en/latest/readme.html#installation


@pytest.fixture
def app_db(mocker):
    app, db = create_app({'TESTING':True, 'MONGO_URI' : f"mongodb://localhost:27017/unittest"})
    return app, db, mocker

