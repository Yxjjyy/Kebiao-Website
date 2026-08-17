<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  if (loading.value) return
  if (!username.value.trim() || !password.value) {
    error.value = '请输入账号和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value.trim(), password.value)
    router.replace('/')
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 429) {
      error.value = '尝试次数过多，请 15 分钟后再试'
    } else {
      error.value = '账号或密码错误'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center px-4 py-8 p-safe-top p-safe-bottom">
    <div class="glass-strong w-full max-w-sm p-8">
      <div class="flex flex-col items-center pb-7">
        <span class="lumina-mark h-12 w-12 text-xl">L</span>
        <p class="mt-4 text-[22px] font-extrabold leading-none tracking-[-0.04em]">Lumina</p>
        <p class="mt-2 text-xs text-[var(--text-dim)]">授课节奏管理</p>
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-1.5 block text-sm font-semibold text-[var(--text-dim)]" for="login-username">
            账号
          </label>
          <input
            id="login-username"
            v-model="username"
            class="input"
            type="text"
            autocomplete="username"
            placeholder="请输入账号"
            :disabled="loading"
          />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-semibold text-[var(--text-dim)]" for="login-password">
            密码
          </label>
          <input
            id="login-password"
            v-model="password"
            class="input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="loading"
          />
        </div>

        <p v-if="error" class="flex items-center gap-1.5 pt-0.5 text-sm font-medium text-[var(--danger)]">
          <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
          {{ error }}
        </p>

        <button type="submit" class="btn-primary w-full py-3 text-[15px]" :disabled="loading">
          <svg v-if="loading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p class="mt-6 text-center text-xs text-[var(--text-dim)]">登录后此设备长期保持登录，无需重复输入</p>
    </div>
  </main>
</template>
