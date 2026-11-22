"""備品の登録、修正、削除と、貸出状況の一覧を行う。"""

from dataclasses import dataclass
from typing import Optional

from data.database import Database
from data.repositories import DuplicateError, EquipmentRepository, LendingRepository
from service.accounts import User
from service.errors import NotFoundError, ServiceError
from service.permissions import require_manager
from service.validation import validate_equipment_fields

STATUS_AVAILABLE = "空き"
STATUS_LENT = "貸出中"
DUPLICATE_EQUIPMENT_NUMBER_MESSAGE = "この管理番号は登録されています"
DELETE_LENT_MESSAGE = "貸出中の備品は削除できません"


@dataclass(frozen=True)
class EquipmentStatus:
    """貸出状況の一覧の 1 行。貸出中でなければ借りている社員の名前と貸出日は None。"""

    id: int
    equipment_number: str
    name: str
    status: str
    borrower_name: Optional[str]
    lent_on: Optional[str]


@dataclass(frozen=True)
class EquipmentItem:
    """備品 1 件の値（修正画面の初期値などに使う）。"""

    id: int
    equipment_number: str
    name: str


class EquipmentService:
    """備品の管理と、貸出状況の一覧を行う。"""

    def __init__(self, db: Database, equipment: EquipmentRepository,
                 lendings: LendingRepository) -> None:
        """引数 db: データベース。引数 equipment・lendings: 備品と貸出記録の表の操作。"""
        self._db = db
        self._equipment = equipment
        self._lendings = lendings

    def list_status(self) -> list[EquipmentStatus]:
        """全備品を管理番号の昇順で、状態つきで返す。"""
        with self._db.connection() as conn:
            rows = self._equipment.list_with_lending(conn)
        result: list[EquipmentStatus] = []
        for row in rows:
            lent = row["lent_on"] is not None
            result.append(EquipmentStatus(
                id=int(row["id"]),
                equipment_number=row["equipment_number"],
                name=row["name"],
                status=STATUS_LENT if lent else STATUS_AVAILABLE,
                borrower_name=row["borrower_name"] if lent else None,
                lent_on=row["lent_on"] if lent else None,
            ))
        return result

    def get(self, equipment_id: int) -> EquipmentItem:
        """備品 1 件を返す。無ければ NotFoundError。"""
        with self._db.connection() as conn:
            row = self._equipment.find_by_id(conn, equipment_id)
        if row is None:
            raise NotFoundError(f"備品 {equipment_id} は登録されていません")
        return EquipmentItem(id=int(row["id"]), equipment_number=row["equipment_number"],
                             name=row["name"])

    def register(self, actor: Optional[User], equipment_number: str, name: str) -> int:
        """備品を登録し、その id を返す。担当者だけができる。"""
        require_manager(actor)
        errors = validate_equipment_fields(equipment_number, name)
        if errors:
            raise ServiceError(field_errors=errors)
        try:
            with self._db.transaction() as conn:
                return self._equipment.insert(conn, equipment_number, name.strip())
        except DuplicateError:
            raise ServiceError(field_errors={"equipment_number": DUPLICATE_EQUIPMENT_NUMBER_MESSAGE})

    def update(self, actor: Optional[User], equipment_id: int, equipment_number: str,
               name: str) -> None:
        """備品の管理番号と備品名を修正する。担当者だけができる。貸出中でも修正できる。"""
        require_manager(actor)
        errors = validate_equipment_fields(equipment_number, name)
        if errors:
            raise ServiceError(field_errors=errors)
        try:
            with self._db.transaction() as conn:
                if self._equipment.find_by_id(conn, equipment_id) is None:
                    raise NotFoundError(f"備品 {equipment_id} は登録されていません")
                self._equipment.update(conn, equipment_id, equipment_number, name.strip())
        except DuplicateError:
            raise ServiceError(field_errors={"equipment_number": DUPLICATE_EQUIPMENT_NUMBER_MESSAGE})

    def delete(self, actor: Optional[User], equipment_id: int) -> None:
        """備品を削除する。担当者だけができる。貸出中の備品は削除せず ServiceError を投げる。"""
        require_manager(actor)
        with self._db.transaction() as conn:
            if self._equipment.find_by_id(conn, equipment_id) is None:
                raise NotFoundError(f"備品 {equipment_id} は登録されていません")
            if self._lendings.find_by_equipment(conn, equipment_id) is not None:
                raise ServiceError(message=DELETE_LENT_MESSAGE)
            self._equipment.delete(conn, equipment_id)
