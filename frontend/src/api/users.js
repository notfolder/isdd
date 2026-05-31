/**
 * ユーザー管理API呼び出しモジュール。
 * 要件ID: RQ-FT-MANAGE-USERS
 * 設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
 * 要件概要: 管理者がユーザーの一覧取得・登録・更新・削除を行うAPI呼び出しを提供する。
 * 設計概要: /api/users エンドポイント群を呼び出す。管理者トークンをAuthorizationヘッダーに付与する。
 * 呼び出し先設計ID: DS-IF-LIST-USERS-FT-MANAGE-USERS
 * 呼び出し元設計ID: DS-CL-USER-LIST-VIEW-UI-USER-LIST-SCREEN
 */
import axios from 'axios'

function authHeader(token) {
  return { Authorization: `Bearer ${token}` }
}

export async function listUsers(token) {
  const res = await axios.get('/api/users', { headers: authHeader(token) })
  return res.data
}

export async function createUser(token, data) {
  const res = await axios.post('/api/users', data, { headers: authHeader(token) })
  return res.data
}

export async function updateUser(token, userId, data) {
  const res = await axios.put(`/api/users/${userId}`, data, { headers: authHeader(token) })
  return res.data
}

export async function deleteUser(token, userId) {
  await axios.delete(`/api/users/${userId}`, { headers: authHeader(token) })
}
