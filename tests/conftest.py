import pytest
from src import create_app

@pytest.fixture
def app_db():
    app, db = create_app()

