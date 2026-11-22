"""単体テストの共通設定。src を import パスに入れ、一時フォルダの SQLite で業務層を組み立てる。"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data.database import Database  # noqa: E402
from data.repositories import EquipmentRepository, LendingRepository, UserRepository  # noqa: E402
from service.accounts import AccountService  # noqa: E402
from service.equipment import EquipmentService  # noqa: E402
from service.lending import LendingService  # noqa: E402


@pytest.fixture
def db(tmp_path):
    """空のデータベース（一時フォルダ）。"""
    return Database(tmp_path / "app.db")


@pytest.fixture
def services(db):
    """空のデータベースに対する業務層一式。"""
    users = UserRepository()
    equipment_repo = EquipmentRepository()
    lending_repo = LendingRepository()
    return {
        "accounts": AccountService(db, users),
        "equipment": EquipmentService(db, equipment_repo, lending_repo),
        "lending": LendingService(db, equipment_repo, lending_repo, users),
    }
