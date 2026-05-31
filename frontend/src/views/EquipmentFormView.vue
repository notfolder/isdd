<!--
  備品登録・編集画面コンポーネント。
  要件ID: RQ-UI-EQUIPMENT-FORM-SCREEN / 設計ID: DS-CL-EQUIPMENT-FORM-VIEW-UI-EQUIPMENT-FORM-SCREEN
  要件概要: 管理者が備品の管理番号と備品名を登録または編集する。
  設計概要: EquipmentFormView。管理番号重複時は409エラーメッセージを表示する。
-->
<template>
  <v-container>
    <v-card max-width="500" class="mx-auto">
      <v-card-title>{{ isEdit ? '備品編集' : '備品登録' }}</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="handleSubmit">
          <v-text-field
            v-model="form.management_number"
            label="管理番号（必須）"
            :disabled="isEdit"
            required variant="outlined" class="mb-3"
            :error-messages="errors.management_number"
          />
          <v-text-field
            v-model="form.name"
            label="備品名（必須）"
            required variant="outlined" class="mb-3"
            :error-messages="errors.name"
          />
          <v-alert v-if="globalError" type="error" class="mb-3">{{ globalError }}</v-alert>
          <v-row>
            <v-col><v-btn type="submit" color="primary" block :loading="loading">保存</v-btn></v-col>
            <v-col><v-btn variant="outlined" block @click="$router.push('/equipment')">キャンセル</v-btn></v-col>
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
import { listEquipment, createEquipment, updateEquipment } from '../api/equipment.js'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const form = ref({ management_number: '', name: '' })
const errors = ref({})
const globalError = ref('')
const loading = ref(false)

onMounted(async () => {
  if (isEdit) {
    const list = await listEquipment(auth.token)
    const found = list.find(e => e.management_number === route.params.id)
    if (found) { form.value.management_number = found.management_number; form.value.name = found.name }
  }
})

async function handleSubmit() {
  errors.value = {}
  globalError.value = ''
  if (!form.value.management_number) { errors.value.management_number = ['入力してください']; return }
  if (!form.value.name) { errors.value.name = ['入力してください']; return }
  loading.value = true
  try {
    if (isEdit) {
      await updateEquipment(auth.token, route.params.id, { name: form.value.name })
    } else {
      await createEquipment(auth.token, form.value)
    }
    router.push('/equipment')
  } catch (err) {
    globalError.value = err.response?.data?.detail || '保存に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
