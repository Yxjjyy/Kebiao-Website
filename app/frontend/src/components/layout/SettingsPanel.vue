<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { backupApi } from '@/api/backup'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  display_name: '',
  avatar_color: '#4C7DFF',
  currency_symbol: '¥',
  default_duration_hours: 1,
  generate_weeks_ahead: 12,
  week_start: 1,
  visible_time_start: '07:00',
  visible_time_end: '22:00',
  theme: 'auto' as 'auto' | 'light' | 'dark',
})
const restoreFile = ref<File | null>(null)
const restoreConfirm = ref('')
const backupMessage = ref('')
const backupError = ref('')

watch(
  () => [settingsStore.profile, settingsStore.settings],
  () => {
    form.display_name = settingsStore.profile.display_name
    form.avatar_color = settingsStore.profile.avatar_color
    form.currency_symbol = settingsStore.settings.currency_symbol
    form.default_duration_hours = settingsStore.settings.default_duration_hours
    form.generate_weeks_ahead = settingsStore.settings.generate_weeks_ahead
    form.week_start = settingsStore.settings.week_start
    form.visible_time_start = settingsStore.settings.visible_time_start
    form.visible_time_end = settingsStore.settings.visible_time_end
    form.theme = settingsStore.settings.theme
  },
  { immediate: true, deep: true }
)

async function save() {
  await Promise.all([
    settingsStore.saveProfile({
      display_name: form.display_name,
      avatar_color: form.avatar_color,
    }),
    settingsStore.saveSettings({
      currency_symbol: form.currency_symbol,
      default_duration_hours: form.default_duration_hours,
      generate_weeks_ahead: form.generate_weeks_ahead,
      week_start: form.week_start,
      visible_time_start: form.visible_time_start,
      visible_time_end: form.visible_time_end,
      theme: form.theme,
    }),
  ])
}

async function downloadBackup() {
  backupMessage.value = ''
  backupError.value = ''
  try {
    const blob = await backupApi.download()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `kebiao-backup-${new Date().toISOString().slice(0, 10)}.db`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    backupMessage.value = '备份已开始下载'
  } catch {
    backupError.value = '备份下载失败'
  }
}

function onFileChange(event: Event) {
  restoreFile.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

async function restoreBackup() {
  backupMessage.value = ''
  backupError.value = ''
  if (!restoreFile.value) {
    backupError.value = '请选择备份文件'
    return
  }
  if (restoreConfirm.value !== '确认恢复') {
    backupError.value = '请输入"确认恢复"'
    return
  }
  try {
    await backupApi.restore(restoreFile.value)
    backupMessage.value = '恢复完成，请刷新页面重新加载数据'
  } catch {
    backupError.value = '恢复失败，请检查备份文件'
  }
}

function resetLocalToken() {
  auth.clear()
  router.push('/login')
}
</script>

<template>
  <div class="grid gap-4">
    <section class="glass p-4 md:p-5">
      <h2 class="text-lg font-semibold">系统设置</h2>
      <p class="text-xs text-[var(--text-dim)]">主题、默认课时、显示与导出</p>

      <form class="mt-4 grid gap-3.5 md:grid-cols-2" @submit.prevent="save">
        <label class="block">
          <span class="label">账号名</span>
          <input v-model="form.display_name" class="input" maxlength="64" />
        </label>
        <label class="block">
          <span class="label">头像颜色</span>
          <input v-model="form.avatar_color" class="h-11 w-full rounded-2xl border border-white/40 bg-transparent px-2 dark:border-white/10" type="color" />
        </label>
        <label class="block">
          <span class="label">货币符号</span>
          <input v-model="form.currency_symbol" class="input" maxlength="4" />
        </label>
        <label class="block">
          <span class="label">默认课时</span>
          <select v-model.number="form.default_duration_hours" class="input">
            <option :value="0.5">0.5h</option>
            <option :value="1">1h</option>
            <option :value="1.5">1.5h</option>
          </select>
        </label>
        <label class="block">
          <span class="label">预生成周数</span>
          <input v-model.number="form.generate_weeks_ahead" class="input" type="number" min="1" max="52" />
        </label>
        <label class="block">
          <span class="label">周起始日</span>
          <select v-model.number="form.week_start" class="input">
            <option :value="1">周一</option>
            <option :value="0">周日</option>
          </select>
        </label>
        <label class="block">
          <span class="label">主题</span>
          <select v-model="form.theme" class="input">
            <option value="auto">跟随系统</option>
            <option value="light">浅色</option>
            <option value="dark">深色</option>
          </select>
        </label>
        <label class="block">
          <span class="label">可视起始</span>
          <input v-model="form.visible_time_start" class="input" type="time" />
        </label>
        <label class="block">
          <span class="label">可视结束</span>
          <input v-model="form.visible_time_end" class="input" type="time" />
        </label>
        <div class="md:col-span-2">
          <button class="btn-primary btn-sm">保存设置</button>
        </div>
      </form>
    </section>

    <section class="glass p-4 md:p-5">
      <h2 class="text-lg font-semibold">数据备份</h2>
      <p class="text-xs text-[var(--text-dim)]">下载快照或恢复数据库</p>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <div class="rounded-2xl border border-white/35 bg-white/45 p-4 dark:border-white/8 dark:bg-white/5">
          <h3 class="text-sm font-semibold">下载备份</h3>
          <p class="mt-1.5 text-xs text-[var(--text-dim)]">SQLite 一致性快照下载</p>
          <button class="btn-primary btn-sm mt-3" @click="downloadBackup">下载备份</button>
        </div>
        <div class="rounded-2xl border border-white/35 bg-white/45 p-4 dark:border-white/8 dark:bg-white/5">
          <h3 class="text-sm font-semibold">恢复备份</h3>
          <p class="mt-1.5 text-xs text-[var(--text-dim)]">覆盖当前数据（自动保存旧副本）</p>
          <div class="mt-3 space-y-2.5">
            <input class="input text-xs" type="file" accept=".db,.sqlite,.sqlite3" @change="onFileChange" />
            <input v-model="restoreConfirm" class="input text-xs" placeholder="输入: 确认恢复" />
            <button class="btn-danger btn-sm" @click="restoreBackup">恢复数据</button>
          </div>
        </div>
      </div>
      <p v-if="backupMessage" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ backupMessage }}</p>
      <p v-if="backupError" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ backupError }}</p>
    </section>
  </div>
</template>
