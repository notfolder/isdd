"""
備品リポジトリモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-EQUIPMENT-ENTITY, RQ-FT-MANAGE-EQUIPMENT
  設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
  要件概要: 備品エンティティの永続化操作（検索・作成・更新・削除）を提供する。
  設計概要: SQLAlchemy Session を受け取り、Equipment モデルに対するCRUD操作をカプセル化する。
  呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
  呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.equipment import Equipment


class EquipmentRepository:
    """
    備品エンティティのDB操作クラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-DT-EQUIPMENT-ENTITY
      設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
      要件概要: 備品エンティティのCRUD操作をDBレイヤーとして提供する。
      設計概要: Service 層から受け取った db セッションで Equipment テーブルを操作する。
      呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
      呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
    """

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> List[Equipment]:
        """
        全備品を取得する。

        Returns:
            List[Equipment]: 全備品のリスト。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          要件概要: 管理者が全備品の一覧を確認できる。
          設計概要: equipment テーブルの全レコードを返す。
          呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        return self.db.query(Equipment).all()

    def find_by_id(self, equipment_id: str) -> Optional[Equipment]:
        """
        備品IDで備品を取得する。

        Args:
            equipment_id (str): 検索する備品ID。

        Returns:
            Optional[Equipment]: 見つかった備品、または None。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          要件概要: 特定の備品の詳細情報を取得する。
          設計概要: equipment_id を主キーとして1件検索する。
          呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        return self.db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()

    def create(self, equipment: Equipment) -> Equipment:
        """
        備品を新規作成する。

        Args:
            equipment (Equipment): 作成する備品モデル。

        Returns:
            Equipment: 作成された備品モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          要件概要: 管理者が新しい備品を登録できる。
          設計概要: db.add + flush でセッションに追加する（commit は Service 層が行う）。
          呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.add(equipment)
        self.db.flush()
        return equipment

    def update(self, equipment: Equipment) -> Equipment:
        """
        備品情報を更新する。

        Args:
            equipment (Equipment): 更新済み備品モデル。

        Returns:
            Equipment: 更新された備品モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          要件概要: 管理者が備品名称や貸出状態を更新できる。
          設計概要: セッション追跡済みオブジェクトを flush する（変更はセッションが検出済み）。
          呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.flush()
        return equipment

    def delete(self, equipment: Equipment) -> None:
        """
        備品を削除する。

        Args:
            equipment (Equipment): 削除する備品モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-EQUIPMENT
          設計ID: DS-CL-EQUIPMENT-REPO-DT-EQUIPMENT-ENTITY
          要件概要: 管理者が不要な備品を削除できる。
          設計概要: db.delete + flush で削除をセッションに反映する。
          呼び出し先: DS-MD-EQUIPMENT-DT-EQUIPMENT-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.delete(equipment)
        self.db.flush()
