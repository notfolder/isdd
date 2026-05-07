"""
DepartmentService 単体テスト。

要件トレーサビリティ:
  要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-EX-FETCH-DEPARTMENT-MASTER
  設計ID: DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  要件概要: DepartmentService.get_department_name が None・例外時に "不明" を返すことを検証する。
  設計概要: モックオブジェクトを使い、正常・None・例外の3パターンを検証する。
  呼び出し先: DS-CL-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID
  呼び出し元: pytest
"""
import pytest
from app.services.department_service import DepartmentService


class FakeClientReturnsName:
    def fetch_department_name_by_login_id(self, login_id):
        return "営業部"


class FakeClientReturnsNone:
    def fetch_department_name_by_login_id(self, login_id):
        return None


class FakeClientRaisesError:
    def fetch_department_name_by_login_id(self, login_id):
        raise ConnectionError("接続失敗")


class TestDepartmentServiceGetDepartmentName:
    """
    DS-FN-TEST-DEPT-SERVICE-FT-FETCH-DEPT-BY-LOGIN-ID のテストクラス。
    """

    def test_returns_department_name_when_client_succeeds(self):
        service = DepartmentService(FakeClientReturnsName())
        assert service.get_department_name("U001") == "営業部"

    def test_returns_unknown_when_client_returns_none(self):
        service = DepartmentService(FakeClientReturnsNone())
        assert service.get_department_name("unknown") == "不明"

    def test_returns_unknown_when_client_raises_exception(self):
        service = DepartmentService(FakeClientRaisesError())
        assert service.get_department_name("U001") == "不明"
