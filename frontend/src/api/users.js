/**
 * 利用者APIクライアントモジュール。
 * 利用者のCRUD・貸出先一覧取得APIの呼び出し関数を提供する。
 * 要件ID: RQ-FT-MANAGE-BORROWER, RQ-FT-LOAN-EQUIPMENT
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 * 要件概要: 利用者の一覧取得・登録・編集・削除・貸出先選択用一覧をバックエンドAPIに委譲する。
 * 設計概要: /api/users の各エンドポイントを axios クライアント経由で呼び出す関数を提供する。
 * 呼び出し先: DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
 * 呼び出し元: DS-SC-USER-STORE-FT-MANAGE-BORROWER, 各 Vue ビューコンポーネント
 */
import client from './client.js'

/**
 * 全利用者一覧を取得する。
 * @returns {Promise} 利用者リスト
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 */
export const listUsers = () => client.get('/users')

/**
 * 利用者を新規作成する。
 * @param {{ login_id: string, display_name: string, password: string, role: string }} data
 * @returns {Promise} 作成された利用者
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 */
export const createUser = (data) => client.post('/users', data)

/**
 * 利用者情報を更新する。
 * @param {string} loginId - ログインID
 * @param {{ display_name?: string, password?: string, role?: string }} data
 * @returns {Promise} 更新後の利用者
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 */
export const updateUser = (loginId, data) => client.put(`/users/${loginId}`, data)

/**
 * 利用者を削除する。
 * @param {string} loginId - ログインID
 * @returns {Promise} 削除完了メッセージ
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 */
export const deleteUser = (loginId) => client.delete(`/users/${loginId}`)

/**
 * 貸出先選択用の利用者一覧を取得する。
 * @returns {Promise} ログインIDと表示名のみの利用者リスト
 * 要件ID: RQ-FT-LOAN-EQUIPMENT
 * 設計ID: DS-IF-USER-API-FT-MANAGE-BORROWER
 */
export const getUsersForLoan = () => client.get('/users/for-loan')
