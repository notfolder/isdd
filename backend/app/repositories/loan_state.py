"""
貸出状態リポジトリモジュール。

要件トレーサビリティ:
  要件ID: RQ-DT-LOAN-STATE-ENTITY, RQ-FT-LOAN-EQUIPMENT
  設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
  要件概要: 貸出状態エンティティの永続化操作（検索・作成・削除）を提供する。
  設計概要: SQLAlchemy Session を受け取り、LoanState モデルに対するCRUD操作をカプセル化する。
  呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
  呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT, DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.loan_state import LoanState


class LoanStateRepository:
    """
    貸出状態エンティティのDB操作クラス。

    Args:
        db (Session): SQLAlchemy セッション。

    要件トレーサビリティ:
      要件ID: RQ-DT-LOAN-STATE-ENTITY
      設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
      要件概要: 貸出状態のCRUD操作をDBレイヤーとして提供する。
      設計概要: Service 層から受け取った db セッションで LoanState テーブルを操作する。
      呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
      呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
    """

    def __init__(self, db: Session):
        self.db = db

    def find_by_equipment_id(self, equipment_id: str) -> Optional[LoanState]:
        """
        備品IDで貸出状態を取得する。

        Args:
            equipment_id (str): 検索する備品ID。

        Returns:
            Optional[LoanState]: 見つかった貸出状態、または None。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOAN-EQUIPMENT
          設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          要件概要: 備品の現在の貸出先情報を取得するために使用する。
          設計概要: equipment_id で1件検索する。
          呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        return self.db.query(LoanState).filter(LoanState.equipment_id == equipment_id).first()

    def create(self, loan_state: LoanState) -> LoanState:
        """
        貸出状態を新規作成する。

        Args:
            loan_state (LoanState): 作成する貸出状態モデル。

        Returns:
            LoanState: 作成された貸出状態モデル。

        要件トレーサビリティ:
          要件ID: RQ-FT-LOAN-EQUIPMENT
          設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          要件概要: 備品の貸出開始時に貸出状態レコードを作成する。
          設計概要: db.add + flush でセッションに追加する。
          呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.add(loan_state)
        self.db.flush()
        return loan_state

    def delete_by_equipment_id(self, equipment_id: str) -> None:
        """
        備品IDで貸出状態を削除する。

        Args:
            equipment_id (str): 削除対象の備品ID。

        要件トレーサビリティ:
          要件ID: RQ-FT-RETURN-EQUIPMENT
          設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          要件概要: 備品の返却時に貸出状態レコードを削除する。
          設計概要: equipment_id でフィルタして delete クエリを実行し、flush する。
          呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT
        """
        self.db.query(LoanState).filter(LoanState.equipment_id == equipment_id).delete()
        self.db.flush()

    def exists_by_user_login_id(self, user_login_id: str) -> bool:
        """
        指定利用者が貸出中の備品を持つか確認する。

        Args:
            user_login_id (str): 確認する利用者のログインID。

        Returns:
            bool: 貸出中の備品が存在する場合 True。

        要件トレーサビリティ:
          要件ID: RQ-FT-MANAGE-BORROWER
          設計ID: DS-CL-LOAN-STATE-REPO-DT-LOAN-STATE-ENTITY
          要件概要: 貸出中の備品がある利用者の削除を防ぐために使用する。
          設計概要: user_login_id でフィルタし、1件でも存在すれば True を返す。
          呼び出し先: DS-MD-LOAN-STATE-DT-LOAN-STATE-ENTITY
          呼び出し元: DS-CL-USER-SERVICE-FT-MANAGE-BORROWER
        """
        return self.db.query(LoanState).filter(LoanState.user_login_id == user_login_id).first() is not None
