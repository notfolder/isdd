/**
 * Vue Routerルーティング定義・ナビゲーションガードモジュール。
 * 要件ID: RQ-NF-ROLE-CONTROL
 * 設計ID: DS-FN-CHECK-ROLE-NF-ROLE-CONTROL
 * 要件概要: 管理者/一般の権限制御をページ単位で行う。管理者専用ページへの一般ユーザーアクセスを禁止する。
 * 設計概要: Vue Routerのナビゲーションガードでroleをチェックし、管理者専用ルートへの一般ユーザーのアクセスをリダイレクトする。
 * 呼び出し先設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
 * 呼び出し元設計ID: DS-MD-FRONTEND-FT-LOGIN
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import LoginView from '../views/LoginView.vue'
import EquipmentListView from '../views/EquipmentListView.vue'
import EquipmentFormView from '../views/EquipmentFormView.vue'
import UserListView from '../views/UserListView.vue'
import UserFormView from '../views/UserFormView.vue'

const routes = [
  { path: '/', redirect: '/equipment' },
  { path: '/login', component: LoginView },
  { path: '/equipment', component: EquipmentListView, meta: { requiresAuth: true } },
  { path: '/equipment/new', component: EquipmentFormView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/equipment/:id/edit', component: EquipmentFormView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/users', component: UserListView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/users/new', component: UserFormView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/users/:id/edit', component: UserFormView, meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return '/equipment'
  }
})

export default router
