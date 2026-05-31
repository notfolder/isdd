/**
 * 認証状態管理ストア（Pinia）。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-AUTH-SERVICE-FT-LOGIN
 * 要件概要: ログイン・ログアウト状態とJWTトークン・ロールを管理する。
 * 設計概要: PiniaストアでtokenとroleをlocalStorageに永続化する。
 * 呼び出し先設計ID: DS-IF-AUTH-LOGIN-FT-LOGIN
 * 呼び出し元設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
 */
import { defineStore } from 'pinia'
import { login as apiLogin } from '../api/auth.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    async login(email, password) {
      const data = await apiLogin(email, password)
      this.token = data.access_token
      this.role = data.role
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('role', data.role)
    },
    logout() {
      this.token = null
      this.role = null
      localStorage.removeItem('token')
      localStorage.removeItem('role')
    },
  },
})
