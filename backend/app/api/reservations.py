"""
予約APIルーターモジュール。

要件トレーサビリティ:
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR
  設計ID: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
  要件概要: 予約CRUD API エンドポイント（一覧取得・登録・キャンセル）を提供する。
  設計概要: FastAPI Router で /api/equipment/{id}/reservations と /api/reservations/{id} を定義する。
  呼び出し先: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
  呼び出し元: DS-MD-BACKEND-FT-MANAGE-EQUIPMENT
"""
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.reservation_service import ReservationService
from app.schemas.reservation import ReservationCreate, ReservationResponse

router = APIRouter(tags=["reservations"])


@router.get("/api/equipment/{equipment_id}/reservations", response_model=List[ReservationResponse])
def list_reservations(
    equipment_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    備品の予約一覧を取得する。

    Args:
        equipment_id (str): 対象備品ID。
        db (Session): DBセッション。
        _current_user (User): ログイン確認用（未認証は 401）。

    Returns:
        List[ReservationResponse]: 予約レスポンスのリスト（開始日昇順）。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
      設計ID: DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR
      要件概要: カレンダー画面で備品の全予約一覧を取得する。全ログイン済みユーザーがアクセス可。
      設計概要: GET /api/equipment/{id}/reservations。ReservationService.list_by_equipment に委譲する。
      呼び出し先: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
      呼び出し元: フロントエンド DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
    """
    return ReservationService(db).list_by_equipment(equipment_id)


@router.post(
    "/api/equipment/{equipment_id}/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    equipment_id: str,
    data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    予約を登録する。

    Args:
        equipment_id (str): 予約対象備品ID。
        data (ReservationCreate): 予約データ（start_date・end_date・user_login_id）。
        db (Session): DBセッション。
        current_user (User): ログインユーザー（一般利用者は自分のIDのみ予約可）。

    Returns:
        ReservationResponse: 作成された予約（201 Created）。

    Raises:
        HTTPException: 401 - 未認証。
        HTTPException: 403 - 一般利用者が他人のIDで予約しようとした場合。
        HTTPException: 404 - 備品が存在しない場合。
        HTTPException: 409 - 重複する予約期間がある場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-MAKE-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION
      設計ID: DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION
      要件概要: 全ログイン済みユーザーが予約可。一般利用者は自分の ID のみ、管理者は任意の利用者で登録可。
      設計概要: POST /api/equipment/{id}/reservations。一般利用者が user_login_id を指定すると 403。
      呼び出し先: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
      呼び出し元: フロントエンド DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
    """
    from fastapi import HTTPException

    if current_user.role != "admin" and data.user_login_id and data.user_login_id != current_user.login_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user_login_id = data.user_login_id if (current_user.role == "admin" and data.user_login_id) else current_user.login_id

    return ReservationService(db).create(
        equipment_id=equipment_id,
        user_login_id=user_login_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )


@router.delete("/api/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    予約をキャンセルする。

    Args:
        reservation_id (str): キャンセルする予約ID。
        db (Session): DBセッション。
        current_user (User): 操作者（本人または管理者のみ）。

    Returns:
        204 No Content。

    Raises:
        HTTPException: 401 - 未認証。
        HTTPException: 403 - 本人でも管理者でもない場合。
        HTTPException: 404 - 予約が存在しない場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-CANCEL-RESERVATION
      設計ID: DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION
      要件概要: 予約者本人または管理者が予約をキャンセルできる。一般利用者は自分の予約のみ。
      設計概要: DELETE /api/reservations/{reservation_id}。ReservationService.cancel に委譲する。
      呼び出し先: DS-CL-RESERVATION-SERVICE-FT-MAKE-RESERVATION
      呼び出し元: フロントエンド DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
    """
    ReservationService(db).cancel(
        reservation_id=reservation_id,
        requesting_login_id=current_user.login_id,
        requesting_role=current_user.role,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
