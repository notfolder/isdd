/**
 * Vue Router設定モジュール。
 * 全ルート定義とロールベース認可ガードを提供する。
 * 要件ID: RQ-NF-ROLE-ACCESS, RQ-FT-LOGIN, RQ-FT-VIEW-RESERVATION-CALENDAR, RQ-FT-MAKE-RESERVATION
 * 設計ID: DS-SC-ROUTER-NF-ROLE-ACCESS
 * 要件概要: 管理者と一般利用者で異なる画面へのアクセスを制御する。未認証アクセスはログインページへリダイレクトする。予約カレンダー・予約登録画面は全ロールがアクセス可能。
 * 設計概要: createWebHistory で SPA ルーティングを構成し、beforeEach ガードで isLoggedIn と role を確認して遷移先を制御する。/equipment/:id/reservations はロール制限なし・要ログイン。
 * 呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN
 * 呼び出し元: DS-MD-FRONTEND-FT-MANAGE-EQUIPMENT
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  {
    path: '/admin/equipment',
    component: () => import('../views/AdminEquipmentListView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/equipment/new',
    component: () => import('../views/EquipmentFormView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/equipment/:id/edit',
    component: () => import('../views/EquipmentFormView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/equipment/:id/delete',
    component: () => import('../views/EquipmentDeleteConfirmView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/equipment/:id/loan',
    component: () => import('../views/LoanFormView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/equipment/:id/return',
    component: () => import('../views/ReturnConfirmView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/users',
    component: () => import('../views/UserListView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/users/new',
    component: () => import('../views/UserFormView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/users/:id/edit',
    component: () => import('../views/UserFormView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin/users/:id/delete',
    component: () => import('../views/UserDeleteConfirmView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/general/equipment',
    component: () => import('../views/GeneralEquipmentListView.vue'),
    meta: { requiresAuth: true, role: 'general' },
  },
  {
    path: '/equipment/:id/reservations',
    component: () => import('../views/ReservationCalendarView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/equipment/:id/reservations/new',
    component: () => import('../views/ReservationFormView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * ルートガード。ログイン状態とロールを確認して遷移を制御する。
 * 要件ID: RQ-NF-ROLE-ACCESS, RQ-FT-LOGIN
 * 設計ID: DS-SC-ROUTER-NF-ROLE-ACCESS
 * 要件概要: 未認証ユーザーはログインページへ、ロール不一致ユーザーは適切な画面へリダイレクトする。
 * 設計概要: to.meta.requiresAuth で認証確認、to.meta.role でロール確認を行い、不一致時はリダイレクトする。
 * 呼び出し先: DS-SC-AUTH-STORE-FT-LOGIN
 * 呼び出し元: Vue Router（自動呼び出し）
 */
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return '/login'
  }
  if (to.meta.role && authStore.isLoggedIn && authStore.role !== to.meta.role) {
    if (authStore.role === 'admin') return '/admin/equipment'
    return '/general/equipment'
  }
  if (to.path === '/login' && authStore.isLoggedIn) {
    if (authStore.role === 'admin') return '/admin/equipment'
    return '/general/equipment'
  }
})

export default router
