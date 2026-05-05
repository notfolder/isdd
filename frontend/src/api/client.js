/**
 * axios HTTPクライアント設定モジュール。
 * 全APIリクエストの基底クライアントを提供する。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-IF-API-CLIENT-FT-LOGIN
 * 要件概要: バックエンドAPIとの通信でCookieを自動送信し、401時にログインページへリダイレクトする。
 * 設計概要: axios.create で baseURL='/api'・withCredentials=true を設定し、401 レスポンスで /login へ遷移するインターセプターを追加する。
 * 呼び出し先: DS-CL-AUTH-ROUTER-FT-LOGIN, DS-CL-EQUIPMENT-ROUTER-FT-MANAGE-EQUIPMENT, DS-CL-USER-ROUTER-FT-MANAGE-BORROWER
 * 呼び出し元: DS-IF-AUTH-API-FT-LOGIN, DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT, DS-IF-USER-API-FT-MANAGE-BORROWER
 */
import axios from 'axios'
import router from '../router/index.js'

const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default client
