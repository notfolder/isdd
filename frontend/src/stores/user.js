/**
 * 利用者状態管理ストア。
 * 利用者一覧のフェッチと状態保持を提供する。
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-SC-USER-STORE-FT-MANAGE-BORROWER
 * 要件概要: 利用者一覧を取得してメモリ内で管理し、各画面コンポーネントに提供する。
 * 設計概要: Pinia defineStore で userList を ref で保持し、fetchUsers() でAPIから取得する。
 * 呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
 * 呼び出し元: DS-VC-USER-LIST-FT-MANAGE-BORROWER
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listUsers } from '../api/users.js'

export const useUserStore = defineStore('user', () => {
  const userList = ref([])
  const loading = ref(false)
  const errorMessage = ref('')

  /**
   * バックエンドから全利用者一覧を取得してストアに保存する。
   * @returns {Promise<void>}
   * 要件ID: RQ-FT-MANAGE-BORROWER
   * 設計ID: DS-SC-USER-STORE-FT-MANAGE-BORROWER
   * 呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
   * 呼び出し元: DS-VC-USER-LIST-FT-MANAGE-BORROWER
   */
  async function fetchUsers() {
    loading.value = true
    errorMessage.value = ''
    try {
      const res = await listUsers()
      userList.value = res.data
    } catch (err) {
      errorMessage.value = err.response?.data?.detail || '利用者の取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  return { userList, loading, errorMessage, fetchUsers }
})
