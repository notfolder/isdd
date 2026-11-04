"""単体・結合テストの共通設定。DB は一時ディレクトリに作る。"""

import pytest

from app import create_app


@pytest.fixture
def make_app(tmp_path):
    """設定を指定して Flask アプリを作る。テストごとに別の DATA_DIR を使う。"""

    def _make(idle_timeout=1800):
        return create_app(
            {
                "PORT": 0,
                "DATA_DIR": str(tmp_path / "data"),
                "SESSION_IDLE_TIMEOUT_SECONDS": idle_timeout,
            }
        )

    return _make


@pytest.fixture
def app(make_app):
    return make_app()


@pytest.fixture
def client(app):
    return app.test_client()
