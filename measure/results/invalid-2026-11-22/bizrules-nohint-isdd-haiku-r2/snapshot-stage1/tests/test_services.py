"""業務層の業務ルールと権限を確かめる（結合: 業務層とデータ層を一時の SQLite で結ぶ）。"""

from datetime import date

import pytest

from data.database import Database
from service.accounts import MANAGER_ROLE, MEMBER_ROLE, hash_password, verify_password
from service.errors import NotFoundError, ServiceError
from service.permissions import PermissionDenied

TODAY = date(2026, 11, 22)


def _register(services, number, name="山田 太郎", password="password1"):
    services["accounts"].register(number, name, password)
    return services["accounts"].authenticate(number, password)


def test_first_account_is_manager_and_next_are_members(services):
    first = _register(services, "100001")
    second = _register(services, "100002")
    assert first.role == MANAGER_ROLE
    assert second.role == MEMBER_ROLE


def test_duplicate_employee_number_is_rejected(services):
    _register(services, "100001")
    with pytest.raises(ServiceError) as info:
        services["accounts"].register("100001", "別人", "password1")
    assert "employee_number" in info.value.field_errors


def test_password_is_not_stored_in_plain_text(db: Database, services):
    _register(services, "100001", password="secret-pass-word")
    with db.connection() as conn:
        stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "secret-pass-word" not in stored
    assert verify_password("secret-pass-word", stored)
    assert not verify_password("wrong-password", stored)


def test_hash_is_salted():
    assert hash_password("password1") != hash_password("password1")


def test_authenticate_failure_has_one_message(services):
    _register(services, "100001")
    for number, password in [("100001", "wrong-pass"), ("999999", "password1")]:
        with pytest.raises(ServiceError) as info:
            services["accounts"].authenticate(number, password)
        assert info.value.message == "社員番号またはパスワードが違います"


def test_equipment_register_list_and_sort(services):
    manager = _register(services, "100001")
    services["equipment"].register(manager, "EQ-0002", "マウス")
    services["equipment"].register(manager, "EQ-0001", "ノート PC")
    rows = services["equipment"].list_status()
    assert [row.equipment_number for row in rows] == ["EQ-0001", "EQ-0002"]
    assert all(row.status == "空き" and row.borrower_name is None for row in rows)


def test_member_cannot_manage_equipment(services):
    _register(services, "100001")
    member = _register(services, "100002")
    with pytest.raises(PermissionDenied):
        services["equipment"].register(member, "EQ-0001", "ノート PC")
    with pytest.raises(PermissionDenied):
        services["equipment"].register(None, "EQ-0001", "ノート PC")


def test_equipment_number_duplicate_on_update(services):
    manager = _register(services, "100001")
    services["equipment"].register(manager, "EQ-0001", "A")
    eq2 = services["equipment"].register(manager, "EQ-0002", "B")
    with pytest.raises(ServiceError) as info:
        services["equipment"].update(manager, eq2, "EQ-0001", "B")
    assert "equipment_number" in info.value.field_errors


def test_lend_return_and_status(services):
    manager = _register(services, "100001")
    member = _register(services, "100002")
    eq = services["equipment"].register(manager, "EQ-0001", "ノート PC")
    services["lending"].lend(manager, eq, str(member.id), TODAY.isoformat(), TODAY)
    row = services["equipment"].list_status()[0]
    assert row.status == "貸出中"
    assert row.borrower_name == "山田 太郎"
    assert row.lent_on == "2026-11-22"
    services["lending"].return_equipment(manager, eq)
    assert services["equipment"].list_status()[0].status == "空き"


def test_one_lending_per_equipment(services):
    manager = _register(services, "100001")
    eq = services["equipment"].register(manager, "EQ-0001", "ノート PC")
    services["lending"].lend(manager, eq, str(manager.id), "2026-11-20", TODAY)
    with pytest.raises(ServiceError) as info:
        services["lending"].lend(manager, eq, str(manager.id), "2026-11-21", TODAY)
    assert info.value.message == "この備品は既に貸し出されています"
    assert services["equipment"].list_status()[0].lent_on == "2026-11-20"


def test_cannot_delete_lent_equipment(services):
    manager = _register(services, "100001")
    eq = services["equipment"].register(manager, "EQ-0001", "ノート PC")
    services["lending"].lend(manager, eq, str(manager.id), "2026-11-20", TODAY)
    with pytest.raises(ServiceError) as info:
        services["equipment"].delete(manager, eq)
    assert info.value.message == "貸出中の備品は削除できません"
    assert len(services["equipment"].list_status()) == 1


def test_return_of_available_equipment_is_rejected(services):
    manager = _register(services, "100001")
    eq = services["equipment"].register(manager, "EQ-0001", "ノート PC")
    with pytest.raises(ServiceError):
        services["lending"].return_equipment(manager, eq)


def test_lending_of_unknown_equipment_is_not_found(services):
    manager = _register(services, "100001")
    with pytest.raises(NotFoundError):
        services["lending"].lend(manager, 999, str(manager.id), "2026-11-20", TODAY)


def test_lending_rejects_future_date_and_unknown_borrower(services):
    manager = _register(services, "100001")
    eq = services["equipment"].register(manager, "EQ-0001", "ノート PC")
    with pytest.raises(ServiceError) as info:
        services["lending"].lend(manager, eq, str(manager.id), "2026-11-23", TODAY)
    assert "lent_on" in info.value.field_errors
    with pytest.raises(ServiceError) as info:
        services["lending"].lend(manager, eq, "999", "2026-11-20", TODAY)
    assert "borrower" in info.value.field_errors
    assert services["equipment"].list_status()[0].status == "空き"
