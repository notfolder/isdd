/**
 * 予約ストアモジュール。
 * 予約一覧の取得・登録・削除と状態管理を提供する。
 * 要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-FT-MAKE-RESERVATION, RQ-FT-CANCEL-RESERVATION
 * 設計ID: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
 * 要件概要: 予約一覧をメモリ内で管理し、CRUD 操作後に UI を自動更新する。
 * 設計概要: Pinia defineStore で reservations を ref で保持し、API 呼び出し後に状態を更新する。
 * 呼び出し先: DS-CL-RESERVATION-ROUTER-FT-MAKE-RESERVATION
 * 呼び出し元: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN, DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listReservations, createReservation, cancelReservation } from '../api/reservations.js'

export const useReservationStore = defineStore('reservation', () => {
  /** @type {import('vue').Ref<Array>} 現在表示中の備品の予約一覧 */
  const reservations = ref([])
  const loading = ref(false)
  const errorMessage = ref('')

  /**
   * 備品IDに紐づく予約一覧を取得してストアに保存する。
   * @param {string} equipmentId - 備品ID
   * @returns {Promise<void>}
   * 要件ID: RQ-FT-VIEW-RESERVATION-CALENDAR
   * 設計ID: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
   * 要件概要: カレンダー画面で備品の全予約一覧を表示する。
   * 設計概要: listReservations を呼び出し reservations を更新する。エラー時は errorMessage にセットする。
   * 呼び出し先: DS-IF-RESERVATION-LIST-FT-VIEW-RESERVATION-CALENDAR
   * 呼び出し元: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
   */
  async function fetchReservations(equipmentId) {
    loading.value = true
    errorMessage.value = ''
    try {
      const res = await listReservations(equipmentId)
      reservations.value = res.data
    } catch (err) {
      errorMessage.value = err.response?.data?.detail || '予約の取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  /**
   * 予約を新規作成してストアを更新する。
   * @param {string} equipmentId - 備品ID
   * @param {{ start_date: string, end_date: string, user_login_id?: string }} data - 予約データ
   * @returns {Promise<object>} 作成された予約レスポンス
   * @throws {Error} 重複（409）や権限（403）エラーを呼び出し元に伝播する
   * 要件ID: RQ-FT-MAKE-RESERVATION
   * 設計ID: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
   * 要件概要: 利用者が備品を期間指定で予約する。重複期間は拒否する。
   * 設計概要: createReservation を呼び出し成功時に reservations を再取得して更新する。
   * 呼び出し先: DS-IF-RESERVATION-CREATE-FT-MAKE-RESERVATION
   * 呼び出し元: DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN
   */
  async function addReservation(equipmentId, data) {
    const res = await createReservation(equipmentId, data)
    await fetchReservations(equipmentId)
    return res.data
  }

  /**
   * 予約をキャンセルしてストアを更新する。
   * @param {string} reservationId - 予約ID
   * @param {string} equipmentId - 備品ID（一覧再取得に使用）
   * @returns {Promise<void>}
   * @throws {Error} 権限（403）や存在なし（404）エラーを呼び出し元に伝播する
   * 要件ID: RQ-FT-CANCEL-RESERVATION
   * 設計ID: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR
   * 要件概要: 予約者本人または管理者が予約をキャンセルできる。
   * 設計概要: cancelReservation を呼び出し成功時に reservations を再取得して更新する。
   * 呼び出し先: DS-IF-RESERVATION-DELETE-FT-CANCEL-RESERVATION
   * 呼び出し元: DS-CL-RESERVATION-CALENDAR-VIEW-UI-RESERVATION-CALENDAR-SCREEN
   */
  async function removeReservation(reservationId, equipmentId) {
    await cancelReservation(reservationId)
    await fetchReservations(equipmentId)
  }

  return { reservations, loading, errorMessage, fetchReservations, addReservation, removeReservation }
})
