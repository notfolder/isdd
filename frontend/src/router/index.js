/**
 * Vue Router 設定ファイル
 * 
 * 要件トレーサビリティ:
 *   要件ID: RQ-FT-LOGIN, RQ-FT-VIEW-ITEM-LIST, RQ-FT-REGISTER-ITEM, RQ-FT-REGISTER-USER
 *   設計ID: DS-CL-ROUTER-FT-LOGIN
 *   要件概要: 画面遷移とルーティングを管理する
 *   設計概要: Vue Routerでルートを定義し、認証ガードを実装する
 *   呼び出し先: DS-CL-LOGIN-VIEW-FT-LOGIN, DS-CL-ITEM-LIST-VIEW-FT-VIEW-ITEM-LIST, DS-CL-ITEM-MANAGEMENT-VIEW-FT-REGISTER-ITEM, DS-CL-USER-MANAGEMENT-VIEW-FT-REGISTER-USER
 *   呼び出し元: main.js, NavigationBar.vue
 */

import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import ItemListView from '../views/ItemListView.vue'
import ItemManagementView from '../views/ItemManagementView.vue'
import UserManagementView from '../views/UserManagementView.vue'

// ルート定義
// 要件ID: RQ-FT-LOGIN, RQ-FT-VIEW-ITEM-LIST, RQ-FT-REGISTER-ITEM, RQ-FT-REGISTER-USER
// 設計ID: DS-CL-ROUTER-FT-LOGIN
// 要件概要: 各画面へのルートを定義する
// 設計概要: パス、コンポーネント、メタ情報（認証要否）を設定する
const routes = [
  {
    path: '/',
    redirect: '/items'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/items',
    name: 'ItemList',
    component: ItemListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/items/manage',
    name: 'ItemManagement',
    component: ItemManagementView,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: UserManagementView,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

// ルーターインスタンスの作成
const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * ナビゲーションガード - 認証チェック
 * 
 * 要件ID: RQ-FT-LOGIN, RQ-NF-ACCESS-CONTROL
 * 設計ID: DS-CL-ROUTER-FT-LOGIN
 * 要件概要: ログインが必要な画面へのアクセスを制御する
 * 設計概要: localStorageのトークンと権限をチェックし、未認証の場合はログイン画面にリダイレクトする
 */
router.beforeEach((to, from, next) => {
  const isLoggedIn = !!localStorage.getItem('access_token')
  const userRole = localStorage.getItem('user_role')
  
  // 認証が必要なルート
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
    return
  }
  
  // 管理者権限が必要なルート
  if (to.meta.requiresAdmin && userRole !== '管理者') {
    next('/items')
    return
  }
  
  // ログイン済みの場合、ログイン画面にアクセスしたら備品一覧にリダイレクト
  if (to.path === '/login' && isLoggedIn) {
    next('/items')
    return
  }
  
  next()
})

export default router
