<!--
  返却確認ダイアログコンポーネント。
  要件ID: RQ-UI-RETURN-DIALOG / 設計ID: DS-CL-RETURN-DIALOG-UI-RETURN-DIALOG
  要件概要: 貸出中の備品の返却を確認して記録する。
  設計概要: ReturnDialog。備品名・貸出先・返却予定日を表示し確認後に返却処理を行う。
-->
<template>
  <v-dialog model-value persistent max-width="420">
    <v-card>
      <v-card-title>返却確認</v-card-title>
      <v-card-text>
        <p>以下の備品の返却を記録しますか？</p>
        <p><strong>備品名:</strong> {{ equipment.name }}</p>
        <p><strong>貸出先:</strong> {{ equipment.lending_info?.user_name }}</p>
        <p><strong>返却予定:</strong> {{ equipment.lending_info?.expected_return_date }}</p>
        <v-alert v-if="errorMsg" type="error" class="mt-2">{{ errorMsg }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="$emit('close')">キャンセル</v-btn>
        <v-btn color="warning" :loading="loading" @click="handleReturn">返却する</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { returnEquipment } from '../api/equipment.js'

const props = defineProps({ equipment: Object })
const emit = defineEmits(['close', 'submitted'])
const auth = useAuthStore()
const errorMsg = ref('')
const loading = ref(false)

async function handleReturn() {
  loading.value = true
  try {
    await returnEquipment(auth.token, props.equipment.management_number)
    emit('submitted')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '返却処理に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
