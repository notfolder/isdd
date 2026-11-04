"""備品の検査・登録・修正・削除・一覧の単体・結合テスト。"""

import pytest

from app import equipment


def test_validate_equipment_rules():
    assert equipment.validate_equipment("EQ-0001", "ノートパソコン") == {}
    errors = equipment.validate_equipment("EQ_0001", "")
    assert errors == {
        "equipment_number": "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください",
        "name": "備品名を入力してください",
    }
    assert equipment.validate_equipment("A" * 20, "x")  == {}
    assert "equipment_number" in equipment.validate_equipment("A" * 21, "x")
    assert equipment.validate_equipment("EQ-1", "x" * 50) == {}
    assert equipment.validate_equipment("EQ-1", "x" * 51)["name"] == "備品名は 50 文字以内で入力してください"


def test_create_and_duplicate(app):
    with app.app_context():
        assert equipment.create_equipment("EQ-1", "A") == {}
        assert equipment.create_equipment("EQ-1", "B") == {
            "equipment_number": "この管理番号は既に使われています"
        }


def test_update_changes_number_and_name(app):
    with app.app_context():
        equipment.create_equipment("EQ-1", "旧名")
        assert equipment.update_equipment("EQ-1", "EQ-2", "新名") == {}
        assert equipment.get_equipment("EQ-1") is None
        assert equipment.get_equipment("EQ-2") == {"equipment_number": "EQ-2", "name": "新名"}


def test_update_missing_raises_lookup_error(app):
    with app.app_context():
        with pytest.raises(LookupError):
            equipment.update_equipment("NONE", "EQ-9", "x")


def test_update_to_existing_number_is_rejected(app):
    with app.app_context():
        equipment.create_equipment("EQ-1", "a")
        equipment.create_equipment("EQ-2", "b")
        assert equipment.update_equipment("EQ-2", "EQ-1", "b") == {
            "equipment_number": "この管理番号は既に使われています"
        }


def test_delete_returns_whether_deleted(app):
    with app.app_context():
        equipment.create_equipment("EQ-1", "a")
        assert equipment.delete_equipment("EQ-1") is True
        assert equipment.delete_equipment("EQ-1") is False


def test_list_is_sorted_by_number_and_all_available(app):
    with app.app_context():
        equipment.create_equipment("EQ-2", "b")
        equipment.create_equipment("EQ-1", "a")
        rows = equipment.list_loan_status()
        assert [r["equipment_number"] for r in rows] == ["EQ-1", "EQ-2"]
        assert all(r["status"] == "空き" and r["borrower_name"] == "" and r["loan_date"] == "" for r in rows)
