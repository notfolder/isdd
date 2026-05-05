/**
 * 認証APIクライアントモジュール。
 * ログイン・ログアウトAPIの呼び出し関数を提供する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-IF-AUTH-API-FT-LOGIN
 * 要件概要: ログインIDとパスワードでログインし、JWTをCookieで受け取る。ログアウト時にCookieを削除する。
 * 設計概要: POST /api/auth/login と POST /api/auth/logout を axios クライアント経由で呼び出す。
 * 呼び出し先: DS-CL-AUTH-ROUTER-FT-LOGIN
 * 呼び出し元: DS-SC-AUTH-STORE-FT-LOGIN
 */
import client from './client.js'

/**
 * ログインAPIを呼び出す。
 * @param {string} loginId - ログインID
 * @param {string} password - パスワード
 * @returns {Promise} ログインIDと表示名とロールを含むレスポンス
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-IF-AUTH-API-FT-LOGIN
 * 呼び出し先: DS-CL-AUTH-ROUTER-FT-LOGIN
 * 呼び出し元: DS-SC-AUTH-STORE-FT-LOGIN
 */
export const login = (loginId, password) =>
  client.post('/auth/login', { login_id: loginId, password })

/**
 * ログアウトAPIを呼び出す。
 * @returns {Promise} ログアウト完了メッセージを含むレスポンス
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-IF-AUTH-API-FT-LOGIN
 * 呼び出し先: DS-CL-AUTH-ROUTER-FT-LOGIN
 * 呼び出し元: DS-SC-AUTH-STORE-FT-LOGIN
 */
export const logout = () => client.post('/auth/logout')
