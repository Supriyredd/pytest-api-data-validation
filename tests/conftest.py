import os
import sqlite3
import threading

import pytest
from werkzeug.serving import make_server

from app.api import API_TOKEN, create_app
from app.seed import seed
from qa_tools.client import PharmacyClient


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "pharmacy.db"
    with sqlite3.connect(path) as conn:
        seed(conn)
    return str(path)


@pytest.fixture(scope="session")
def base_url(db_path):
    """Starts the demo API on a free port for the whole session, unless BASE_URL points elsewhere."""
    if os.environ.get("BASE_URL"):
        yield os.environ["BASE_URL"]
        return
    server = make_server("127.0.0.1", 0, create_app(db_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def api(base_url):
    return PharmacyClient(base_url, os.environ.get("API_TOKEN", API_TOKEN))


@pytest.fixture
def anon(base_url):
    return PharmacyClient(base_url, token=None)


@pytest.fixture
def db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def query(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
