/**
 * 備品API呼び出しモジュール。
 * 要件ID: RQ-FT-LIST-EQUIPMENT
 * 設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
 * 要件概要: 全備品の取得・登録・更新・削除・貸出・返却API呼び出しを提供する。
 * 設計概要: /api/equipment エンドポイント群を呼び出す。Authorizationヘッダーにトークンを付与する。
 * 呼び出し先設計ID: DS-IF-LIST-EQUIPMENT-FT-LIST-EQUIPMENT
 * 呼び出し元設計ID: DS-CL-EQUIPMENT-LIST-VIEW-UI-EQUIPMENT-LIST-SCREEN
 */
import axios from 'axios'

function authHeader(token) {
  return { Authorization: `Bearer ${token}` }
}

export async function listEquipment(token) {
  const res = await axios.get('/api/equipment', { headers: authHeader(token) })
  return res.data
}

export async function createEquipment(token, data) {
  const res = await axios.post('/api/equipment', data, { headers: authHeader(token) })
  return res.data
}

export async function updateEquipment(token, managementNumber, data) {
  const res = await axios.put(`/api/equipment/${managementNumber}`, data, { headers: authHeader(token) })
  return res.data
}

export async function deleteEquipment(token, managementNumber) {
  await axios.delete(`/api/equipment/${managementNumber}`, { headers: authHeader(token) })
}

export async function lendEquipment(token, managementNumber, data) {
  const res = await axios.post(`/api/equipment/${managementNumber}/lend`, data, { headers: authHeader(token) })
  return res.data
}

export async function returnEquipment(token, managementNumber) {
  await axios.post(`/api/equipment/${managementNumber}/return`, {}, { headers: authHeader(token) })
}
