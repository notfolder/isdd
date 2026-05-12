/**
 * フロントエンドのルーティング定義。
 * 要件ID: RQ-UI-WEB-GUI-USE
 * 設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 * 要件概要: ログイン、備品、ユーザー、パスワード変更画面へ遷移できること。
 * 設計概要: 固定された画面遷移に対応するルートを定義する。
 * 呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
 * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 */

import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import AssetListView from "../views/AssetListView.vue";
import AssetCreateView from "../views/AssetCreateView.vue";
import AssetEditView from "../views/AssetEditView.vue";
import UserListView from "../views/UserListView.vue";
import UserCreateView from "../views/UserCreateView.vue";
import UserEditView from "../views/UserEditView.vue";
import PasswordChangeView from "../views/PasswordChangeView.vue";
import AssetReservationCalendarView from "../views/AssetReservationCalendarView.vue";

const routes = [
  { path: "/", name: "login", component: LoginView },
  { path: "/assets", name: "assets", component: AssetListView },
  { path: "/assets/new", name: "asset-create", component: AssetCreateView },
  { path: "/assets/:assetNumber/edit", name: "asset-edit", component: AssetEditView, props: true },
  {
    path: "/assets/:assetNumber/reservations",
    name: "asset-reservations",
    component: AssetReservationCalendarView,
    props: true,
  },
  { path: "/users", name: "users", component: UserListView },
  { path: "/users/new", name: "user-create", component: UserCreateView },
  { path: "/users/:loginId/edit", name: "user-edit", component: UserEditView, props: true },
  { path: "/password/change", name: "password-change", component: PasswordChangeView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
