import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DB_URL', 'sqlite:///./data/test.db')
os.environ.setdefault('VECTOR_BACKEND', 'local')
os.environ.setdefault('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
os.environ.setdefault('LLM_CHAIN', 'mock')
os.environ.setdefault('DATA_DIR', 'data')

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base, get_db
from app.main import app
from app.llm.factory import reset_llm
from app.llm.mock import MockLLM

TEST_DB = 'sqlite:///./data/test.db'

@pytest.fixture(scope='session', autouse=True)
def setup_test_db():
    import app.models
    engine = create_engine(TEST_DB, connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_test_db):
    engine = create_engine(TEST_DB, connect_args={'check_same_thread': False})
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def mock_llm():
    m = MockLLM()
    reset_llm(m)
    yield m
    reset_llm(None)

@pytest.fixture
def client(setup_test_db):
    engine = create_engine(TEST_DB, connect_args={'check_same_thread': False})
    TestSession = sessionmaker(bind=engine)
    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
