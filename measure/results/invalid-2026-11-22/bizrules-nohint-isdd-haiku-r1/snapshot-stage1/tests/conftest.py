"""単体・結合テストの共通の準備: アカウントと備品を作る補助関数。"""
import pytest

from accounts.models import Account, Role
from equipment.models import Equipment, Lending


@pytest.fixture
def make_account(db):
    """社員番号・名前・役割を指定してアカウントを作る。"""

    def _make(employee_number, name="テスト 太郎", role=Role.EMPLOYEE, password="password123"):
        account = Account(employee_number=employee_number, name=name, role=role)
        account.set_password(password)
        account.save()
        return account

    return _make


@pytest.fixture
def make_equipment(db):
    """管理番号と備品名を指定して備品を作る。"""

    def _make(equipment_number, name="ノート PC"):
        return Equipment.objects.create(equipment_number=equipment_number, name=name)

    return _make


@pytest.fixture
def lend(db):
    """備品に貸出の記録を作る（テストの前提を作るためだけに使う）。"""

    def _lend(equipment, borrower, lent_on):
        return Lending.objects.create(equipment=equipment, borrower=borrower, lent_on=lent_on)

    return _lend
