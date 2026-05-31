/**
 * 認証API呼び出しモジュール。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
 * 要件概要: メール/パスワードでログインしJWTトークンを取得する。
 * 設計概要: POST /api/auth/login を呼び出しTokenResponseを返す。
 * 呼び出し先設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
 * 呼び出し元設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
 */
import axios from 'axios'

export async function login(email, password) {
  const res = await axios.post('/api/auth/login', { email, password })
  return res.data
}
