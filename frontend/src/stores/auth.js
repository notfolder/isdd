/**
 * 認証状態管理ストア。
 * ログイン状態・ユーザー情報・セッション期限管理を提供する。
 * 要件ID: RQ-FT-LOGIN, RQ-NF-SESSION-AUTO-LOGOUT-60MIN
 * 設計ID: DS-SC-AUTH-STORE-FT-LOGIN
 * 要件概要: ログイン状態とユーザー情報をメモリ内で管理し、60分経過時の自動ログアウト判定を行う。
 * 設計概要: Pinia defineStore でログイン情報を ref で保持し、loginTime を基準に isSessionExpired() を提供する。
 * 呼び出し先: DS-IF-AUTH-API-FT-LOGIN
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS, DS-VC-APP-NF-SESSION-AUTO-LOGOUT
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout } from '../api/auth.js'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const loginId = ref('')
  const displayName = ref('')
  const role = ref('')
  const errorMessage = ref('')

  const loginTime = ref(0)

  /**
   * ログイン処理を実行し、成功時にユーザー情報をストアに保存する。
   * @param {string} id - ログインID
   * @param {string} password - パスワード
   * @returns {Promise<string|null>} 成功時はロール文字列、失敗時は null
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-SC-AUTH-STORE-FT-LOGIN
   * 呼び出し先: DS-IF-AUTH-API-FT-LOGIN
   * 呼び出し元: DS-VC-LOGIN-FT-LOGIN
   */
  async function login(id, password) {
    errorMessage.value = ''
    try {
      const res = await apiLogin(id, password)
      isLoggedIn.value = true
      loginId.value = res.data.login_id
      displayName.value = res.data.display_name
      role.value = res.data.role
      loginTime.value = Date.now()
      return res.data.role
    } catch (err) {
      errorMessage.value = err.response?.data?.detail || 'ログインに失敗しました'
      return null
    }
  }

  /**
   * ログアウト処理を実行し、ストアのユーザー情報をクリアする。
   * @returns {Promise<void>}
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-SC-AUTH-STORE-FT-LOGIN
   * 呼び出し先: DS-IF-AUTH-API-FT-LOGIN
   * 呼び出し元: DS-VC-APP-NF-SESSION-AUTO-LOGOUT, 各管理画面コンポーネント
   */
  async function logout() {
    try {
      await apiLogout()
    } finally {
      isLoggedIn.value = false
      loginId.value = ''
      displayName.value = ''
      role.value = ''
      loginTime.value = 0
    }
  }

  /**
   * ユーザー情報を直接ストアにセットする。
   * @param {{ login_id: string, display_name: string, role: string }} data
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-SC-AUTH-STORE-FT-LOGIN
   * 呼び出し先: なし
   * 呼び出し元: DS-VC-LOGIN-FT-LOGIN
   */
  function setUser(data) {
    isLoggedIn.value = true
    loginId.value = data.login_id
    displayName.value = data.display_name
    role.value = data.role
    loginTime.value = Date.now()
  }

  /**
   * セッションが60分経過して期限切れかどうかを判定する。
   * @returns {boolean} 期限切れの場合 true
   * 要件ID: RQ-NF-SESSION-AUTO-LOGOUT-60MIN
   * 設計ID: DS-SC-AUTH-STORE-FT-LOGIN
   * 呼び出し先: なし
   * 呼び出し元: DS-VC-APP-NF-SESSION-AUTO-LOGOUT
   */
  function isSessionExpired() {
    if (!isLoggedIn.value || loginTime.value === 0) return false
    return Date.now() - loginTime.value >= 60 * 60 * 1000
  }

  return { isLoggedIn, loginId, displayName, role, errorMessage, loginTime, login, logout, setUser, isSessionExpired }
})
