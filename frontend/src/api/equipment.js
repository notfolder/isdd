/**
 * 備品APIクライアントモジュール。
 * 備品のCRUD・貸出・返却APIの呼び出し関数を提供する。
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT, RQ-FT-LOAN-EQUIPMENT, RQ-FT-RETURN-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 * 要件概要: 備品の一覧取得・登録・編集・削除・貸出・返却をバックエンドAPIに委譲する。
 * 設計概要: /api/equipment の各エンドポイントを axios クライアント経由で呼び出す関数を提供する。
 * 呼び出し先: DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT
 * 呼び出し元: DS-SC-EQUIPMENT-STORE-FT-MANAGE-EQUIPMENT, 各 Vue ビューコンポーネント
 */
import client from './client.js'

/**
 * 全備品一覧を取得する。
 * @returns {Promise} 貸出情報付き備品リスト
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const listEquipment = () => client.get('/equipment')

/**
 * 備品を新規作成する。
 * @param {{ equipment_id: string, name: string }} data
 * @returns {Promise} 作成された備品
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const createEquipment = (data) => client.post('/equipment', data)

/**
 * 備品情報を更新する。
 * @param {string} id - 備品ID
 * @param {{ name: string }} data
 * @returns {Promise} 更新後の備品
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const updateEquipment = (id, data) => client.put(`/equipment/${id}`, data)

/**
 * 備品を削除する。
 * @param {string} id - 備品ID
 * @returns {Promise} 削除完了メッセージ
 * 要件ID: RQ-FT-MANAGE-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const deleteEquipment = (id) => client.delete(`/equipment/${id}`)

/**
 * 備品を貸出する。
 * @param {string} id - 備品ID
 * @param {{ user_login_id: string, loan_date: string }} data
 * @returns {Promise} 貸出後の備品
 * 要件ID: RQ-FT-LOAN-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const loanEquipment = (id, data) => client.post(`/equipment/${id}/loan`, data)

/**
 * 備品を返却する。
 * @param {string} id - 備品ID
 * @returns {Promise} 返却後の備品
 * 要件ID: RQ-FT-RETURN-EQUIPMENT
 * 設計ID: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT
 */
export const returnEquipment = (id) => client.post(`/equipment/${id}/return`)
