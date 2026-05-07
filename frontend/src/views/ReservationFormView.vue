<!--
  予約登録フォームコンポーネント。
  要件ID: RQ-FT-MAKE-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION
  設計ID: DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN
  要件概要: 利用者が備品を期間指定で予約できる。重複期間は拒否される。管理者は予約者を変更できる。
  設計概要: 開始日・終了日入力フォームと予約者選択（管理者のみ）を提供し、ReservationStore.addReservation で登録する。
  呼び出し先: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR, DS-SC-AUTH-STORE-FT-LOGIN
  呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
-->
<template>
  <v-container>
    <h1 class="text-h5 mb-4">予約登録</h1>

    <v-alert v-if="errorMessage" type="error" class="mb-4" data-testid="error-message">{{ errorMessage }}</v-alert>

    <v-card max-width="500">
      <v-card-text>
        <p class="mb-2"><strong>備品ID:</strong> {{ equipmentId }}</p>
        <v-select
          v-if="authStore.role === 'admin'"
          v-model="form.user_login_id"
          :items="userItems"
          item-title="display_name"
          item-value="login_id"
          label="予約者（管理者のみ変更可能）"
          data-testid="user-select"
        />
        <v-text-field
          v-model="form.start_date"
          label="開始日"
          type="date"
          :rules="[v => !!v || '開始日は必須です']"
          data-testid="start-date-input"
        />
        <v-text-field
          v-model="form.end_date"
          label="終了日"
          type="date"
          :rules="[v => !!v || '終了日は必須です']"
          data-testid="end-date-input"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" :loading="loading" data-testid="submit-reservation-button" @click="handleSubmit">
          予約登録
        </v-btn>
        <v-btn data-testid="cancel-button" @click="router.go(-1)">キャンセル</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * 予約登録フォームのロジック。
 * 要件ID: RQ-FT-MAKE-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION
 * 設計ID: DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN
 * 呼び出し先: DS-CL-RESERVATION-STORE-FT-VIEW-RESERVATION-CALENDAR, DS-SC-AUTH-STORE-FT-LOGIN
 * 呼び出し元: DS-SC-ROUTER-NF-ROLE-ACCESS
 */
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useReservationStore } from '../stores/reservation.js'
import { getUsersForLoan } from '../api/users.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const reservationStore = useReservationStore()

const equipmentId = route.params.id
const loading = ref(false)
const errorMessage = ref('')
const userItems = ref([])
const form = ref({
  start_date: '',
  end_date: '',
  user_login_id: authStore.loginId,
})

onMounted(async () => {
  if (authStore.role === 'admin') {
    try {
      const res = await getUsersForLoan()
      userItems.value = res.data
    } catch {
      // ユーザー一覧取得失敗時は管理者自身のみ選択可能
    }
  }
})

/**
 * 予約登録実行処理。バリデーション後にストア経由でAPIを呼び出し、成功時にカレンダー画面へ遷移する。
 * 要件ID: RQ-FT-MAKE-RESERVATION, RQ-NF-RESERVATION-CONFLICT-PREVENTION
 * 設計ID: DS-CL-RESERVATION-FORM-VIEW-UI-RESERVATION-FORM-SCREEN
 */
async function handleSubmit() {
  errorMessage.value = ''
  if (!form.value.start_date || !form.value.end_date) {
    errorMessage.value = '開始日と終了日は必須です'
    return
  }
  if (form.value.start_date >= form.value.end_date) {
    errorMessage.value = '終了日は開始日より後の日付を指定してください'
    return
  }
  loading.value = true
  try {
    const data = { start_date: form.value.start_date, end_date: form.value.end_date }
    if (authStore.role === 'admin' && form.value.user_login_id !== authStore.loginId) {
      data.user_login_id = form.value.user_login_id
    }
    await reservationStore.addReservation(equipmentId, data)
    router.push(`/equipment/${equipmentId}/reservations`)
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '予約登録に失敗しました'
  } finally {
    loading.value = false
  }
}
</script>
