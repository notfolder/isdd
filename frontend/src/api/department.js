/**
 * 部署APIクライアントモジュール。
 * 部署名取得APIの呼び出し関数を提供する。
 * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID, RQ-FT-DEPT-NAME-API
 * 設計ID: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
 * 要件概要: ログインIDに対応する部署名を外部DB経由で取得する。
 * 設計概要: GET /api/department/by-login-id を呼び出し department_name を返す。
 * 呼び出し先: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
 * 呼び出し元: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 */
import client from './client.js'

/**
 * ログインIDから部署名を取得する。
 * @param {string} loginId - 検索対象のログインID
 * @returns {Promise<string>} 部署名（取得失敗時は "不明"）
 * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-IF-DEPT-NAME-BY-LOGIN-ID-FT-DEPT-NAME-API
 * 要件概要: ログインIDに対応する部署名を返す。存在しない場合は "不明" を返す。
 * 設計概要: GET /api/department/by-login-id?login_id={loginId} を呼び出し department_name フィールドを返す。
 * 呼び出し先: DS-CL-DEPT-ROUTER-FT-DEPT-NAME-API
 * 呼び出し元: DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 */
export const fetchDeptName = (loginId) =>
  client.get('/department/by-login-id', { params: { login_id: loginId } })
    .then((res) => res.data.department_name)
    .catch(() => '不明')
