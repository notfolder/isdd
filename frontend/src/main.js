/**
 * Vueアプリケーション起動モジュール。
 * 要件ID: RQ-FT-LOGIN
 * 設計ID: DS-MD-FRONTEND-FT-LOGIN
 * 要件概要: 全画面のUI表示・操作を提供するフロントエンドアプリケーション。
 * 設計概要: Vue3 + Vuetify3 + Pinia + Vue Routerを起動し、#appにマウントする。
 * 呼び出し先設計ID: DS-CL-LOGIN-VIEW-UI-LOGIN-SCREEN
 * 呼び出し元設計ID: なし
 */
import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import { createPinia } from 'pinia'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import App from './App.vue'
import router from './router/index.js'

const vuetify = createVuetify({ components, directives })
const pinia = createPinia()

createApp(App).use(vuetify).use(pinia).use(router).mount('#app')
