<!--
  貸出処理モーダルコンポーネント。
  要件ID: RQ-UI-LENDING-MODAL / 設計ID: DS-CL-LENDING-MODAL-UI-LENDING-MODAL
  要件概要: 在庫中の備品を選択した社員に貸し出す。貸出先・貸出日・返却予定日を入力する。
  設計概要: LendingModal。返却予定日<貸出日のバリデーションを行う。
-->
<template>
  <v-dialog model-value persistent max-width="480">
    <v-card>
      <v-card-title>貸出処理: {{ equipment.management_number }} / {{ equipment.name }}</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="handleSubmit">
          <v-select
            v-model="form.user_id"
            label="貸出先"
            :items="users"
            item-title="name"
            item-value="id"
            required variant="outlined" class="mb-3"
            :error-messages="errors.user_id"
          />
          <v-text-field v-model="form.lend_date" label="貸出日" type="date" required variant="outlined" class="mb-3" :error-messages="errors.lend_date" />
          <v-text-field v-model="form.expected_return_date" label="返却予定日" type="date" required variant="outlined" class="mb-3" :error-messages="errors.expected_return_date" />
          <v-alert v-if="globalError" type="error" class="mb-3">{{ globalError }}</v-alert>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="$emit('close')">キャンセル</v-btn>
        <v-btn color="primary" :loading="loading" @click="handleSubmit">実行</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { lendEquipment } from '../api/equipment.js'

const props = defineProps({ equipment: Object, users: Array })
const emit = defineEmits(['close', 'submitted'])
const auth = useAuthStore()
const form = ref({ user_id: null, lend_date: '', expected_return_date: '' })
const errors = ref({})
const globalError = ref('')
const loading = ref(false)

async function handleSubmit() {
  errors.value = {}; globalError.value = ''
  if (!form.value.user_id) { errors.value.user_id = ['入力してください']; return }
  if (!form.value.lend_date) { errors.value.lend_date = ['入力してください']; return }
  if (!form.value.expected_return_date) { errors.value.expected_return_date = ['入力してください']; return }
  if (form.value.expected_return_date < form.value.lend_date) {
    errors.value.expected_return_date = ['返却予定日は貸出日以降に設定してください']; return
  }
  loading.value = true
  try {
    await lendEquipment(auth.token, props.equipment.management_number, form.value)
    emit('submitted')
  } catch (err) {
    globalError.value = err.response?.data?.detail || '貸出処理に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
