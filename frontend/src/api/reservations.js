/**
 * 予約APIクライアントモジュール。
 * 予約CRUD APIの呼び出し関数を提供する。
 * 要件ID: RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION, RQ-FT-VIEW-RESERVATION-CALENDAR
 * 設計ID: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 要件概要: 予約の一覧取得・登録・キャンセルをバックエンドAPIに委譲する。
 * 設計概要: /api/equipment/{id}/reservations および /api/reservations/{id} の各エンドポイントを axios 経由で呼び出す。
 * 呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 呼び出し元: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
 */
import client from './client.js'

/**
 * 備品IDに紐づく予約一覧を取得する。
 * @param {string} equipmentId - 備品ID
 * @returns {Promise} 予約レスポンスのリスト
 * 要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
 * 設計ID: DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR
 * 要件概要: 指定備品の全予約を開始日昇順で返す。
 * 設計概要: GET /api/equipment/{id}/reservations を呼び出す。
 * 呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 呼び出し元: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
 */
export const listReservations = (equipmentId) =>
  client.get(`/equipment/${equipmentId}/reservations`)

/**
 * 備品に予約を新規作成する。
 * @param {string} equipmentId - 備品ID
 * @param {{ start_date: string, end_date: string, user_login_id?: string }} data - 予約データ
 * @returns {Promise} 作成された予約レスポンス
 * 要件ID: RQ-FT-MAKE-RESERVATION
 * 設計ID: DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION
 * 要件概要: 利用者が備品を期間指定で予約する。重複期間は 409 で拒否する。
 * 設計概要: POST /api/equipment/{id}/reservations を呼び出し 201 レスポンスを返す。
 * 呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 呼び出し元: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
 */
export const createReservation = (equipmentId, data) =>
  client.post(`/equipment/${equipmentId}/reservations`, data)

/**
 * 予約をキャンセルする。
 * @param {string} reservationId - 予約ID
 * @returns {Promise} 204 No Content
 * 要件ID: RQ-FT-CANCEL-RESERVATION
 * 設計ID: DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION
 * 要件概要: 予約者本人または管理者が予約をキャンセルできる。
 * 設計概要: DELETE /api/reservations/{reservation_id} を呼び出し 204 を返す。
 * 呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 呼び出し元: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
 */
export const cancelReservation = (reservationId) =>
  client.delete(`/reservations/${reservationId}`)
