"""備品の貸出の登録と返却を行う。担当者だけができる。"""

from datetime import date
from typing import Optional

from data.database import Database
from data.repositories import DuplicateError, EquipmentRepository, LendingRepository, UserRepository
from service.accounts import User
from service.errors import NotFoundError, ServiceError
from service.permissions import require_manager
from service.validation import validate_lending_fields

ALREADY_LENT_MESSAGE = "この備品は既に貸し出されています"
NOT_LENT_MESSAGE = "この備品は貸し出されていません"
UNKNOWN_BORROWER_MESSAGE = "借りる社員が登録されていません"


class LendingService:
    """貸出の登録と返却を行う。"""

    def __init__(self, db: Database, equipment: EquipmentRepository,
                 lendings: LendingRepository, users: UserRepository) -> None:
        """引数 db: データベース。引数 equipment・lendings・users: 各表の操作。"""
        self._db = db
        self._equipment = equipment
        self._lendings = lendings
        self._users = users

    def lend(self, actor: Optional[User], equipment_id: int, borrower_raw: str, lent_on_raw: str,
             today: date) -> None:
        """空きの備品に、借りる社員と貸出日を記録する。担当者だけができる。

        入力の不備は入力欄ごとの ServiceError。貸出中なら ServiceError で記録は変えない。
        同時に来た貸出は、書き込みの排他と貸出記録の主キーで 1 件だけ成功する。
        引数 today: 日本時間の今日（未来の貸出日を拒否するため）。
        """
        require_manager(actor)
        errors, borrower_id, lent_on = validate_lending_fields(borrower_raw, lent_on_raw, today)
        if errors or borrower_id is None or lent_on is None:
            raise ServiceError(field_errors=errors)
        try:
            with self._db.transaction() as conn:
                if self._equipment.find_by_id(conn, equipment_id) is None:
                    raise NotFoundError(f"備品 {equipment_id} は登録されていません")
                if self._users.find_by_id(conn, borrower_id) is None:
                    raise ServiceError(field_errors={"borrower": UNKNOWN_BORROWER_MESSAGE})
                if self._lendings.find_by_equipment(conn, equipment_id) is not None:
                    raise ServiceError(message=ALREADY_LENT_MESSAGE)
                self._lendings.insert(conn, equipment_id, borrower_id, lent_on.isoformat())
        except DuplicateError:
            raise ServiceError(message=ALREADY_LENT_MESSAGE)

    def return_equipment(self, actor: Optional[User], equipment_id: int) -> None:
        """貸出中の備品の返却を記録し、貸出記録を消す。担当者だけができる。"""
        require_manager(actor)
        with self._db.transaction() as conn:
            if self._equipment.find_by_id(conn, equipment_id) is None:
                raise NotFoundError(f"備品 {equipment_id} は登録されていません")
            if self._lendings.find_by_equipment(conn, equipment_id) is None:
                raise ServiceError(message=NOT_LENT_MESSAGE)
            self._lendings.delete(conn, equipment_id)
