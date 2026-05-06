/**
 * APIクライアント - バックエンドAPIとの通信を管理
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-AT-FRONTEND-BACKEND-SEPARATION, RQ-FT-LOGIN, RQ-FT-REGISTER-ITEM, RQ-FT-REGISTER-USER
 *   設計ID: DS-CL-API-CLIENT-FT-LOGIN
 *   要件概要: バックエンドAPIと通信し、データの取得・登録・更新・削除を行う
 *   設計概要: Axiosを使用してHTTPリクエストを送信し、JWT認証ヘッダーを自動付与する
 *   呼び出し先: DS-MD-BACKEND-APP-AT-WEB-GUI (FastAPI)
 *   呼び出し元: LoginView.vue, ItemListView.vue, ItemManagementView.vue, UserManagementView.vue
 */

import axios from 'axios'

// Axiosインスタンスの作成
// 要件ID: RQ-AT-FRONTEND-BACKEND-SEPARATION
// 設計ID: DS-CL-API-CLIENT-FT-LOGIN
// 要件概要: バックエンドAPIのベースURLを設定する
// 設計概要: Nginxリバースプロキシ経由でアクセスするため相対パス /api を使用
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * リクエストインターセプター - JWT認証ヘッダーの自動付与
 * 
 * 要件ID: RQ-FT-LOGIN, RQ-NF-ACCESS-CONTROL
 * 設計ID: DS-CL-API-CLIENT-FT-LOGIN
 * 要件概要: APIリクエスト時にJWTトークンを自動的に付与する
 * 設計概要: localStorageからトークンを取得し、Authorizationヘッダーに設定する
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * レスポンスインターセプター - 401エラー時の処理
 * 
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-API-CLIENT-FT-LOGIN
 * 要件概要: 認証エラー時にログアウト処理を行う
 * 設計概要: 401エラーの場合、localStorageをクリアしてログイン画面にリダイレクトする
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // 認証エラーの場合、ログアウト処理
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_role')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 認証API
 * 
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-CL-API-CLIENT-FT-LOGIN
 */
export const authApi = {
  /**
   * ログイン
   * 
   * 要件ID: RQ-FT-LOGIN
   * 設計ID: DS-IF-LOGIN-API-FT-LOGIN
   * 要件概要: ユーザーIDとパスワードでログインし、JWTトークンを取得する
   * 設計概要: POST /api/auth/login にリクエストを送信する
   */
  login(userId, password) {
    return apiClient.post('/auth/login', {
      user_id: userId,
      password: password
    })
  }
}

/**
 * 備品API
 * 
 * 要件ID: RQ-FT-REGISTER-ITEM, RQ-FT-EDIT-ITEM, RQ-FT-DELETE-ITEM, RQ-FT-LEND-ITEM, RQ-FT-RETURN-ITEM, RQ-FT-VIEW-ITEM-LIST
 * 設計ID: DS-CL-API-CLIENT-FT-LOGIN
 */
export const itemApi = {
  /**
   * 備品一覧を取得
   * 
   * 要件ID: RQ-FT-VIEW-ITEM-LIST
   * 設計ID: DS-IF-GET-ITEMS-API-FT-VIEW-ITEM-LIST
   */
  getAll() {
    return apiClient.get('/items')
  },
  
  /**
   * 備品を1件取得
   * 
   * 要件ID: RQ-FT-VIEW-ITEM-LIST
   * 設計ID: DS-IF-GET-ITEM-API-FT-VIEW-ITEM-LIST
   */
  getOne(assetNumber) {
    return apiClient.get(`/items/${assetNumber}`)
  },
  
  /**
   * 備品を登録
   * 
   * 要件ID: RQ-FT-REGISTER-ITEM
   * 設計ID: DS-IF-CREATE-ITEM-API-FT-REGISTER-ITEM
   */
  create(assetNumber, name) {
    return apiClient.post('/items', {
      asset_number: assetNumber,
      name: name
    })
  },
  
  /**
   * 備品を更新
   * 
   * 要件ID: RQ-FT-EDIT-ITEM
   * 設計ID: DS-IF-UPDATE-ITEM-API-FT-EDIT-ITEM
   */
  update(assetNumber, name) {
    return apiClient.put(`/items/${assetNumber}`, {
      name: name
    })
  },
  
  /**
   * 備品を削除
   * 
   * 要件ID: RQ-FT-DELETE-ITEM
   * 設計ID: DS-IF-DELETE-ITEM-API-FT-DELETE-ITEM
   */
  delete(assetNumber) {
    return apiClient.delete(`/items/${assetNumber}`)
  },
  
  /**
   * 備品を貸出
   * 
   * 要件ID: RQ-FT-LEND-ITEM
   * 設計ID: DS-IF-LEND-ITEM-API-FT-LEND-ITEM
   */
  lend(assetNumber, borrower) {
    return apiClient.post(`/items/${assetNumber}/lend`, {
      borrower: borrower
    })
  },
  
  /**
   * 備品を返却
   * 
   * 要件ID: RQ-FT-RETURN-ITEM
   * 設計ID: DS-IF-RETURN-ITEM-API-FT-RETURN-ITEM
   */
  return(assetNumber) {
    return apiClient.post(`/items/${assetNumber}/return`)
  }
}

/**
 * 利用者API
 * 
 * 要件ID: RQ-FT-REGISTER-USER, RQ-FT-EDIT-USER, RQ-FT-DELETE-USER, RQ-FT-VIEW-USER-LIST
 * 設計ID: DS-CL-API-CLIENT-FT-LOGIN
 */
export const userApi = {
  /**
   * 利用者一覧を取得
   * 
   * 要件ID: RQ-FT-VIEW-USER-LIST
   * 設計ID: DS-IF-GET-USERS-API-FT-VIEW-USER-LIST
   */
  getAll() {
    return apiClient.get('/users')
  },
  
  /**
   * 利用者を1件取得
   * 
   * 要件ID: RQ-FT-VIEW-USER-LIST
   * 設計ID: DS-IF-GET-USER-API-FT-VIEW-USER-LIST
   */
  getOne(userId) {
    return apiClient.get(`/users/${userId}`)
  },
  
  /**
   * 利用者を登録
   * 
   * 要件ID: RQ-FT-REGISTER-USER
   * 設計ID: DS-IF-CREATE-USER-API-FT-REGISTER-USER
   */
  create(userId, name, password, role) {
    return apiClient.post('/users', {
      user_id: userId,
      name: name,
      password: password,
      role: role
    })
  },
  
  /**
   * 利用者を更新
   * 
   * 要件ID: RQ-FT-EDIT-USER
   * 設計ID: DS-IF-UPDATE-USER-API-FT-EDIT-USER
   */
  update(userId, name, password, role) {
    return apiClient.put(`/users/${userId}`, {
      name: name,
      password: password || undefined,
      role: role
    })
  },
  
  /**
   * 利用者を削除
   * 
   * 要件ID: RQ-FT-DELETE-USER
   * 設計ID: DS-IF-DELETE-USER-API-FT-DELETE-USER
   */
  delete(userId) {
    return apiClient.delete(`/users/${userId}`)
  }
}
