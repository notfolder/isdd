<!--
  ユーザー登録・編集画面コンポーネント。
  要件ID: RQ-UI-USER-FORM-SCREEN / 設計ID: DS-CL-USER-FORM-VIEW-UI-USER-FORM-SCREEN
  要件概要: 管理者が社員アカウントの登録または編集を行う。
  設計概要: UserFormView。メールアドレス重複時は409エラーを表示する。
-->
<template>
  <v-container>
    <v-card max-width="500" class="mx-auto">
      <v-card-title>{{ isEdit ? 'ユーザー編集' : 'ユーザー登録' }}</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="handleSubmit">
          <v-text-field v-model="form.name" label="氏名（必須）" required variant="outlined" class="mb-3" :error-messages="errors.name" />
          <v-text-field v-model="form.email" label="メールアドレス（必須）" type="email" required variant="outlined" class="mb-3" :error-messages="errors.email" />
          <v-text-field v-model="form.password" :label="isEdit ? 'パスワード（変更する場合のみ）' : 'パスワード（必須）'" type="password" :required="!isEdit" variant="outlined" class="mb-3" />
          <v-select v-model="form.role" label="権限（必須）" :items="[{title:'管理者',value:'admin'},{title:'一般',value:'general'}]" item-title="title" item-value="value" variant="outlined" class="mb-3" />
          <v-alert v-if="globalError" type="error" class="mb-3">{{ globalError }}</v-alert>
          <v-row>
            <v-col><v-btn type="submit" color="primary" block :loading="loading">保存</v-btn></v-col>
            <v-col><v-btn variant="outlined" block @click="$router.push('/users')">キャンセル</v-btn></v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { listUsers, createUser, updateUser } from '../api/users.js'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const form = ref({ name: '', email: '', password: '', role: 'general' })
const errors = ref({})
const globalError = ref('')
const loading = ref(false)

onMounted(async () => {
  if (isEdit) {
    const list = await listUsers(auth.token)
    const found = list.find(u => u.id === parseInt(route.params.id))
    if (found) { form.value.name = found.name; form.value.email = found.email; form.value.role = found.role }
  }
})

async function handleSubmit() {
  errors.value = {}; globalError.value = ''
  if (!form.value.name) { errors.value.name = ['入力してください']; return }
  if (!form.value.email) { errors.value.email = ['入力してください']; return }
  loading.value = true
  try {
    if (isEdit) {
      await updateUser(auth.token, parseInt(route.params.id), form.value)
    } else {
      await createUser(auth.token, form.value)
    }
    router.push('/users')
  } catch (err) {
    globalError.value = err.response?.data?.detail || '保存に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
