import os
import sys
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-bytes-min"
os.environ["DATABASE_URL"] = "sqlite:///./test_academiccheck.db"
os.environ["STORAGE_LOCAL_PATH"] = "./test_storage"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

get_settings.cache_clear()

from app.db.session import Base, engine, get_db, SessionLocal
from app.main import app
from app.seed import seed_if_needed


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_if_needed()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
