"""
EquipmentService単体テスト。

要件トレーサビリティ:
  要件ID: RQ-FT-LIST-EQUIPMENT, RQ-FT-CREATE-EQUIPMENT, RQ-FT-EDIT-EQUIPMENT, RQ-FT-DELETE-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  要件概要: 備品CRUDのビジネスロジックを検証する
  設計概要: test_list_all, test_create_success, test_create_duplicate_asset_number, test_update_success, test_update_not_found, test_delete_available, test_delete_lentを実装する
  呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
  呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
"""

import pytest
from fastapi import HTTPException

from app.models.equipment import Equipment
from app.services.equipment_service import EquipmentService
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


def create_test_equipment(db, asset_number="EQ-001", name="テスト備品", status="available"):
    """テスト用備品を作成するヘルパー関数。"""
    eq = Equipment(asset_number=asset_number, name=name, status=status)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


class TestEquipmentService:
    """
    EquipmentService単体テストクラス。

    要件トレーサビリティ:
      要件ID: RQ-FT-LIST-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      要件概要: 備品CRUDの正常系・異常系を検証する
      設計概要: list_all, create, update, deleteメソッドのテストケースを実装する
      呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
      呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
    """

    def test_list_all(self, db):
        """
        全備品が返ることを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-LIST-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 備品2件登録済みで全件返ること
          設計概要: list_all()がEquipmentResponseのリストを返すことを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        create_test_equipment(db, "EQ-001", "備品1")
        create_test_equipment(db, "EQ-002", "備品2")
        service = EquipmentService()
        result = service.list_all(db)
        assert len(result) == 2

    def test_create_success(self, db):
        """
        一意のasset_numberで備品が作成されることを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-CREATE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 備品が作成されること
          設計概要: create()がEquipmentを返しstatus='available'であることを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        service = EquipmentService()
        data = EquipmentCreate(asset_number="EQ-001", name="テスト備品")
        result = service.create(db, data)
        assert result.asset_number == "EQ-001"
        assert result.status == "available"

    def test_create_duplicate_asset_number(self, db):
        """
        重複資産管理番号で409例外が発生することを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-CREATE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 重複asset_numberで409例外が発生すること
          設計概要: 既存と同じasset_numberでHTTPException(409)が発生することを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        create_test_equipment(db, "EQ-001")
        service = EquipmentService()
        data = EquipmentCreate(asset_number="EQ-001", name="別の備品")
        with pytest.raises(HTTPException) as exc_info:
            service.create(db, data)
        assert exc_info.value.status_code == 409

    def test_update_success(self, db):
        """
        存在する備品IDで更新後の備品が返ることを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-EDIT-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 更新後の備品が返ること
          設計概要: update()が更新されたEquipmentを返すことを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        eq = create_test_equipment(db)
        service = EquipmentService()
        data = EquipmentUpdate(name="更新後備品")
        result = service.update(db, eq.id, data)
        assert result.name == "更新後備品"

    def test_update_not_found(self, db):
        """
        存在しないIDで404例外が発生することを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-EDIT-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 存在しないIDで404例外が発生すること
          設計概要: 存在しないIDでHTTPException(404)が発生することを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        service = EquipmentService()
        data = EquipmentUpdate(name="更新後備品")
        with pytest.raises(HTTPException) as exc_info:
            service.update(db, 9999, data)
        assert exc_info.value.status_code == 404

    def test_delete_available(self, db):
        """
        貸出可能な備品が削除されることを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          要件概要: 貸出可能な備品が削除されること
          設計概要: delete()後にDBから備品が消えることを確認する
          呼び出し先設計ID: DS-CL-EQUIPMENT-SERVICE-FT-LIST-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        eq = create_test_equipment(db, status="available")
        service = EquipmentService()
        service.delete(db, eq.id)
        deleted = db.query(Equipment).filter(Equipment.id == eq.id).first()
        assert deleted is None

    def test_delete_lent(self, db):
        """
        貸出中の備品削除で409例外が発生することを検証する。

        要件トレーサビリティ:
          要件ID: RQ-FT-DELETE-EQUIPMENT
          設計ID: DS-FN-CHECK-EQUIPMENT-DELETABLE-FT-DELETE-EQUIPMENT
          要件概要: 貸出中の備品は削除不可
          設計概要: status='lent'の備品でHTTPException(409)が発生することを確認する
          呼び出し先設計ID: DS-FN-CHECK-EQUIPMENT-DELETABLE-FT-DELETE-EQUIPMENT
          呼び出し元設計ID: DS-SC-DB-INIT-DT-DB-REQUIRED
        """
        eq = create_test_equipment(db, status="lent")
        service = EquipmentService()
        with pytest.raises(HTTPException) as exc_info:
            service.delete(db, eq.id)
        assert exc_info.value.status_code == 409
