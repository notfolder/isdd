<!--
  貸出登録フォームコンポーネント。
  要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
  設計ID: DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN
  要件概要: 管理者が貸出先利用者と貸出日を選択して備品を貸出できる。選択肢に「利用者名（部署名）」を表示する。
  設計概要: getUsersForLoan で利用者を取得し、DeptStore で部署名を非同期取得して「利用者名（部署名）」形式で v-select に表示する。
  呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT, DS-IF-USER-API-FT-MANAGE-BORROWER, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">貸出登録</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500">
      <v-card-text>
        <p class="mb-2"><strong>備品ID:</strong> {{ route.params.id }}</p>
        <v-select
          v-model="form.user_login_id"
          :items="userItems"
          item-title="label"
          item-value="login_id"
          label="貸出先利用者"
          data-testid="user-select"
        />
        <v-text-field
          v-model="form.loan_date"
          label="貸出日"
          type="date"
          data-testid="loan-date-input"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" :loading="loading" data-testid="submit-loan-button" @click="handleSubmit">
          貸出登録
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/equipment')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 貸出登録フォームのロジック。
 * 要件ID: RQ-FT-LOAN-EQUIPMENT, RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN
 * 呼び出し先: DS-IF-EQUIPMENT-API-FT-MANAGE-EQUIPMENT, DS-IF-USER-API-FT-MANAGE-BORROWER, DS-CL-DEPT-STORE-FT-FETCH-DEPT-BY-LOGIN-ID
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { loanEquipment } from '../api/equipment.js'
import { getUsersForLoan } from '../api/users.js'
import { useDeptStore } from '../stores/dept.js'

const router = useRouter()
const route = useRoute()
const deptStore = useDeptStore()
const users = ref([])
const loading = ref(false)
const errorMessage = ref('')
const today = new Date().toISOString().split('T')[0]
const form = ref({ user_login_id: '', loan_date: today })

/**
 * 利用者一覧を「利用者名（部署名）」形式に変換した選択肢リスト。
 * 部署名未取得の場合は「利用者名（取得中...）」を表示する。
 * 要件ID: RQ-FT-FETCH-DEPT-BY-LOGIN-ID
 * 設計ID: DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN
 */
const userItems = computed(() =>
  users.value.map((u) => ({
    login_id: u.login_id,
    label: `${u.display_name}（${deptStore.deptNames[u.login_id] || '取得中...'}）`,
  }))
)

onMounted(async () => {
  try {
    const res = await getUsersForLoan()
    users.value = res.data
    await deptStore.fetchDeptNames(users.value.map((u) => u.login_id))
  } catch {
    errorMessage.value = '利用者の取得に失敗しました'
  }
})

/**
 * 貸出登録実行処理。バリデーション後にAPIを呼び出し、成功時に備品一覧へ遷移する。
 * 要件ID: RQ-FT-LOAN-EQUIPMENT
 * 設計ID: DS-CL-LOAN-FORM-VIEW-UI-LOAN-FORM-SCREEN
 */
async function handleSubmit() {
  errorMessage.value = ''
  if (!form.value.user_login_id || !form.value.loan_date) {
    errorMessage.value = '全ての項目を入力してください'
    return
  }
  loading.value = true
  try {
    await loanEquipment(route.params.id, {
      user_login_id: form.value.user_login_id,
      loan_date: form.value.loan_date,
    })
    router.push('/admin/equipment')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '貸出登録に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
