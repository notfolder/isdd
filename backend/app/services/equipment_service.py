"""
備品サービスモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
  要件概要: 備品のCRUD操作・貸出・返却を提供する。貸出中備品の削除および二重貸出を防ぐ。
  設計概要: EquipmentRepository・LoanStateRepository・UserRepository を組み合わせて備品管理のビジネスロジックを実装する。
  呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY, DS-CL-USER-REPO-DT-BORROWER-ENTITY
  呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
"""
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.equipment import Equipment
from app.models.loan_state import LoanState
from app.models.user import User
from app.repositories.equipment import EquipmentRepository
from app.repositories.loan_state import LoanStateRepository
from app.repositories.user import UserRepository
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse, LoanInfo
from app.schemas.loan import LoanCreate


class EquipmentService:
    """
    備品管理のビジネスロジックを担うサービスクラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
      設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
      要件概要: 備品のCRUD・貸出・返却と各種制約チェックを提供する。
      設計概要: 3つのリポジトリをコンポーズして備品管理のビジネスルールを適用する。
      呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
      呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
    """

    def __init__(self, db: Session):
        self.db = db
        self.equipment_repo = EquipmentRepository(db)
        self.loan_repo = LoanStateRepository(db)
        self.user_repo = UserRepository(db)

    def _to_response(self, equipment: Equipment) -> EquipmentResponse:
        """
        備品モデルをレスポンスに変換する。貸出情報を付加する。

        Args:
            equipment (Equipment): 変換する備品モデル。

        Returns:
            EquipmentResponse: 貸出情報付き備品レスポンス。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 備品一覧・詳細に貸出先利用者名と貸出日を表示する。
          設計概要: LoanState と User を結合して LoanInfo を構築し、EquipmentResponse に組み込む。
          呼び出し先: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY, DS-CL-USER-REPO-DT-BORROWER-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        loan_state = self.loan_repo.find_by_equipment_id(equipment.equipment_id)
        loan_info = None
        if loan_state:
            user = self.user_repo.find_by_login_id(loan_state.user_login_id)
            loan_info = LoanInfo(
                user_login_id=loan_state.user_login_id,
                user_display_name=user.display_name if user else loan_state.user_login_id,
                loan_date=loan_state.loan_date,
            )
        return EquipmentResponse(
            equipment_id=equipment.equipment_id,
            name=equipment.name,
            status=equipment.status,
            loan_info=loan_info,
        )

    def list_equipment(self) -> List[EquipmentResponse]:
        """
        全備品一覧を取得する。

        Returns:
            List[EquipmentResponse]: 貸出情報付き全備品のリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者・一般利用者が全備品と貸出状態を一覧で確認できる。
          設計概要: EquipmentRepository.find_all() の結果を _to_response で変換して返す。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        equipments = self.equipment_repo.find_all()
        return [self._to_response(e) for e in equipments]

    def create_equipment(self, data: EquipmentCreate) -> EquipmentResponse:
        """
        備品を新規作成する。

        Args:
            data (EquipmentCreate): 作成する備品データ（equipment_id・name）。

        Returns:
            EquipmentResponse: 作成された備品のレスポンス。

        Raises:
            HTTPException: 400 - 備品IDが既に使用されている場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者が新しい備品を登録できる。備品IDの重複は許可しない。
          設計概要: equipment_id の重複チェック後、status='available' で備品を作成する。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        if self.equipment_repo.find_by_id(data.equipment_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この備品IDは既に使用されています",
            )
        equipment = Equipment(
            equipment_id=data.equipment_id,
            name=data.name,
            status="available",
        )
        self.equipment_repo.create(equipment)
        self.db.commit()
        return self._to_response(equipment)

    def update_equipment(self, equipment_id: str, data: EquipmentUpdate) -> EquipmentResponse:
        """
        備品情報を更新する。

        Args:
            equipment_id (str): 更新対象の備品ID。
            data (EquipmentUpdate): 更新データ（name のみ）。

        Returns:
            EquipmentResponse: 更新後の備品レスポンス。

        Raises:
            HTTPException: 404 - 備品が見つからない場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者が備品名称を更新できる。
          設計概要: equipment_id で備品を検索し、name を更新してコミットする。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="備品が見つかりません")
        equipment.name = data.name
        self.equipment_repo.update(equipment)
        self.db.commit()
        return self._to_response(equipment)

    def delete_equipment(self, equipment_id: str) -> None:
        """
        備品を削除する。

        Args:
            equipment_id (str): 削除対象の備品ID。

        Raises:
            HTTPException: 404 - 備品が見つからない場合。
            HTTPException: 400 - 貸出中の備品を削除しようとした場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者が備品を削除できる。貸出中の備品は削除禁止とする。
          設計概要: status == 'loaned' の場合は 400 を返し、それ以外は削除する。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="備品が見つかりません")
        if equipment.status == "loaned":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="貸出中の備品は削除できません",
            )
        self.equipment_repo.delete(equipment)
        self.db.commit()

    def loan_equipment(self, equipment_id: str, data: LoanCreate) -> EquipmentResponse:
        """
        備品を貸出する。

        Args:
            equipment_id (str): 貸出対象の備品ID。
            data (LoanCreate): 貸出データ（user_login_id・loan_date）。

        Returns:
            EquipmentResponse: 貸出後の備品レスポンス（status='loaned'）。

        Raises:
            HTTPException: 404 - 備品または利用者が見つからない場合。
            HTTPException: 400 - 既に貸出中の備品を貸出しようとした場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOAN-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者が備品を指定利用者に貸出できる。貸出中備品の二重貸出は禁止する。
          設計概要: 備品と利用者の存在確認・貸出状態確認後、Equipment.status='loaned' と LoanState を同時更新する。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="備品が見つかりません")
        if equipment.status == "loaned":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="この備品は既に貸出中です",
            )
        user = self.user_repo.find_by_login_id(data.user_login_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="利用者が見つかりません")
        loan_state = LoanState(
            equipment_id=equipment_id,
            user_login_id=data.user_login_id,
            loan_date=data.loan_date,
        )
        equipment.status = "loaned"
        self.equipment_repo.update(equipment)
        self.loan_repo.create(loan_state)
        self.db.commit()
        return self._to_response(equipment)

    def return_equipment(self, equipment_id: str) -> EquipmentResponse:
        """
        備品を返却する。

        Args:
            equipment_id (str): 返却対象の備品ID。

        Returns:
            EquipmentResponse: 返却後の備品レスポンス（status='available'）。

        Raises:
            HTTPException: 404 - 備品が見つからない場合。
            HTTPException: 400 - 貸出中でない備品を返却しようとした場合。

        要件トレーサビリティ:
          要件ID: RQ-FT-RETURN-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
          要件概要: 管理者が貸出中の備品を返却処理できる。貸出中でない備品の返却は禁止する。
          設計概要: status == 'loaned' の確認後、Equipment.status='available' に戻し LoanState を削除する。
          呼び出し先: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY, DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
        """
        equipment = self.equipment_repo.find_by_id(equipment_id)
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="備品が見つかりません")
        if equipment.status != "loaned":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="この備品は貸出中ではありません",
            )
        equipment.status = "available"
        self.equipment_repo.update(equipment)
        self.loan_repo.delete_by_equipment_id(equipment_id)
        self.db.commit()
        return self._to_response(equipment)
