/**
 * 部署ストアモジュール。
 * 部署名のキャッシュ付き取得と状態管理を提供する。
 * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 * 要件概要: ログインIDから部署名を取得してキャッシュする。外部DB接続失敗時は "不明" を返す。
 * 設計概要: reactive({}) でキャッシュを保持し、未キャッシュ時のみ API を呼び出す。Vue 3 の reactive オブジェクトはプロパティ追加を検知してテンプレートを再描画する。
 * 呼び出し先: DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API
 * 呼び出し元: DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN, DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN, DS-CL-ADMIN-EQUIPMENT-LIST-VIEW-UI-ADMIN-EQUIPMENT-LIST-SCREEN
 */
import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { fetchDeptName } from '../api/department.js'

export const useDeptStore = defineStore('dept', () => {
  /**
   * 部署名キャッシュ。{ loginId: deptName } 形式の reactive オブジェクト。
   * reactive() を使うことでプロパティ追加時にテンプレートが自動再描画される。
   */
  const deptNames = reactive({})

  /**
   * ログインIDから部署名を取得する。キャッシュがあればAPIを呼ばない。
   * @param {string} loginId - 検索対象のログインID
   * @returns {Promise<string>} 部署名（取得失敗時は "不明"）
   * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
   * 設計ID: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
   * 要件概要: キャッシュ済みの場合はキャッシュから返し、未取得の場合のみ API を呼び出す。
   * 設計概要: deptNames オブジェクトに loginId が存在する場合はキャッシュ値を返す。なければ fetchDeptName を呼び出して deptNames に追加する。
   * 呼び出し先: DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API
   * 呼び出し元: DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN, DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN
   */
  async function getDeptName(loginId) {
    if (loginId in deptNames) {
      return deptNames[loginId]
    }
    const name = await fetchDeptName(loginId)
    deptNames[loginId] = name
    return name
  }

  /**
   * 複数ログインIDの部署名を並行取得する。
   * @param {string[]} loginIds - 取得対象のログインIDリスト
   * @returns {Promise<void>}
   * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
   * 設計ID: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
   * 要件概要: 利用者一覧の全部署名を並行取得して表示する。
   * 設計概要: Promise.all で loginIds を並行処理し、全部署名を deptNames に格納する。
   * 呼び出し先: DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API
   * 呼び出し元: DS-CL-USER-LIST-VIEW-UI-BORROWER-LIST-SCREEN
   */
  async function fetchDeptNames(loginIds) {
    await Promise.all(loginIds.map((id) => getDeptName(id)))
  }

  return { deptNames, getDeptName, fetchDeptNames }
})
