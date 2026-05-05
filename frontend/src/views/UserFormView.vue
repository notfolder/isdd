<!--
  利用者登録・編集フォームコンポーネント。
  要件ID: RQ-FT-MANAGE-BORROWER
  設計ID: DS-VC-USER-FORM-FT-MANAGE-BORROWER
  要件概要: 管理者が利用者のログインID・表示名・パスワード・ロールを入力して登録または編集できる。ログインIDは編集時に変更不可。
  設計概要: route.params.id の有無で登録・編集モードを切り替え、createUser または updateUser を呼ぶ。
  呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">{{ isEdit ? '利用者編集' : '利用者登録' }}</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500">
      <v-card-text>
        <v-text-field
          v-model="form.login_id"
          label="ログインID"
          :disabled="isEdit"
          data-testid="login-id-input"
        />
        <v-text-field
          v-model="form.display_name"
          label="利用者名"
          data-testid="display-name-input"
        />
        <v-text-field
          v-model="form.password"
          :label="isEdit ? 'パスワード（変更する場合のみ）' : 'パスワード'"
          type="password"
          data-testid="password-input"
        />
        <v-select
          v-model="form.role"
          :items="[{ title: '管理者', value: 'admin' }, { title: '一般利用者', value: 'general' }]"
          label="権限"
          data-testid="role-select"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" :loading="loading" data-testid="submit-button" @click="handleSubmit">
          {{ isEdit ? '更新' : '登録' }}
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.push('/admin/users')">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 利用者登録・編集フォームのロジック。
 * 要件ID: RQ-FT-MANAGE-BORROWER, RQ-NF-PASSWORD-HASH
 * 設計ID: DS-VC-USER-FORM-FT-MANAGE-BORROWER
 * 呼び出し先: DS-IF-USER-API-FT-MANAGE-BORROWER
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listUsers, createUser, updateUser } from '../api/users.js'

const router = useRouter()
const route = useRoute()
const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const errorMessage = ref('')
const form = ref({ login_id: '', display_name: '', password: '', role: 'general' })

onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await listUsers()
      const user = res.data.find((u) => u.login_id === route.params.id)
      if (user) {
        form.value.login_id = user.login_id
        form.value.display_name = user.display_name
        form.value.role = user.role
      }
    } catch {
      errorMessage.value = '利用者情報の取得に失敗しました'
    }
  }
})

/**
 * 登録・更新ボタン押下時の処理。バリデーション後にAPIを呼び出し、成功時に利用者一覧へ遷移する。
 * 要件ID: RQ-FT-MANAGE-BORROWER
 * 設計ID: DS-VC-USER-FORM-FT-MANAGE-BORROWER
 */
async function handleSubmit() {
  errorMessage.value = ''
  if (!isEdit.value && (!form.value.login_id || !form.value.password)) {
    errorMessage.value = '全ての必須項目を入力してください'
    return
  }
  loading.value = true
  try {
    if (isEdit.value) {
      const updateData = { display_name: form.value.display_name, role: form.value.role }
      if (form.value.password) updateData.password = form.value.password
      await updateUser(route.params.id, updateData)
    } else {
      await createUser({
        login_id: form.value.login_id,
        display_name: form.value.display_name,
        password: form.value.password,
        role: form.value.role,
      })
    }
    router.push('/admin/users')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '操作に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
