<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { AppSettings, UserProfile } from '@/api/types'
import { backupApi } from '@/api/backup'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { parseFormError } from '@/lib/formError'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const form = reactive({
  display_name: '', avatar_color: '#4C7DFF', currency_symbol: '¥', default_duration_hours: 1,
  generate_weeks_ahead: 12, week_start: 1, visible_time_start: '07:00', visible_time_end: '22:00',
  theme: 'auto' as 'auto' | 'light' | 'dark',
})
const saving = ref(false), downloading = ref(false), restoring = ref(false), restoreDialogOpen = ref(false)
const restoreFile = ref<File | null>(null), restoreConfirm = ref('')
const restoreFileInput = ref<HTMLInputElement | null>(null)
const settingsMessage = ref(''), settingsError = ref(''), backupMessage = ref(''), backupError = ref('')

watch(() => [settingsStore.profile, settingsStore.settings], () => {
  Object.assign(form, {
    display_name: settingsStore.profile.display_name, avatar_color: settingsStore.profile.avatar_color,
    currency_symbol: settingsStore.settings.currency_symbol, default_duration_hours: settingsStore.settings.default_duration_hours,
    generate_weeks_ahead: settingsStore.settings.generate_weeks_ahead, week_start: settingsStore.settings.week_start,
    visible_time_start: settingsStore.settings.visible_time_start, visible_time_end: settingsStore.settings.visible_time_end,
    theme: settingsStore.settings.theme,
  })
}, { immediate: true, deep: true })

function applyThemePreview(theme: AppSettings['theme']) {
  const dark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
}

watch(() => form.theme, applyThemePreview)

async function save() {
  if (saving.value) return
  saving.value = true; settingsMessage.value = ''; settingsError.value = ''
  const previousSettings: AppSettings = { ...settingsStore.settings }
  const previousProfile: UserProfile = { ...settingsStore.profile }
  try {
    await Promise.all([
      settingsStore.saveProfile({ display_name: form.display_name, avatar_color: form.avatar_color }),
      settingsStore.saveSettings({ currency_symbol: form.currency_symbol, default_duration_hours: form.default_duration_hours, generate_weeks_ahead: form.generate_weeks_ahead, week_start: form.week_start, visible_time_start: form.visible_time_start, visible_time_end: form.visible_time_end, theme: form.theme }),
    ])
    settingsMessage.value = '设置已保存'
  } catch (error) {
    settingsStore.settings = previousSettings
    settingsStore.profile = previousProfile
    Object.assign(form, { ...previousSettings, ...previousProfile })
    settingsStore.applyTheme()
    settingsError.value = parseFormError(error, '设置保存失败，界面已恢复到保存前状态；请重试以确认服务器设置')
  } finally { saving.value = false }
}

async function downloadBackup() {
  if (downloading.value) return
  downloading.value = true; backupMessage.value = ''; backupError.value = ''
  try {
    const blob = await backupApi.download(), url = URL.createObjectURL(blob), link = document.createElement('a')
    link.href = url; link.download = `kebiao-backup-${new Date().toISOString().slice(0, 10)}.db`
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url)
    backupMessage.value = '备份已开始下载'
  } catch (error) { backupError.value = parseFormError(error, '备份下载失败，请稍后重试') }
  finally { downloading.value = false }
}

function onFileChange(event: Event) { restoreFile.value = (event.target as HTMLInputElement).files?.[0] ?? null }
function prepareRestore() {
  backupMessage.value = ''; backupError.value = ''
  if (!restoreFile.value) { backupError.value = '请选择备份文件'; return }
  if (restoreConfirm.value !== '确认恢复') { backupError.value = '请输入“确认恢复”'; return }
  restoreDialogOpen.value = true
}
async function restoreBackup() {
  if (!restoreFile.value || restoring.value) return
  restoring.value = true; backupMessage.value = ''; backupError.value = ''
  try {
    await backupApi.restore(restoreFile.value)
    restoreDialogOpen.value = false; restoreConfirm.value = ''; restoreFile.value = null
    if (restoreFileInput.value) restoreFileInput.value.value = ''
    backupMessage.value = '恢复完成，请刷新页面重新加载数据'
  } catch (error) { backupError.value = parseFormError(error, '恢复失败，请检查备份文件') }
  finally { restoring.value = false }
}
</script>

<template>
  <div class="grid gap-4">
    <section class="glass p-4 md:p-5">
      <h2 class="text-lg font-semibold">系统设置</h2><p class="text-xs text-[var(--text-dim)]">主题、默认课时、显示与导出</p>
      <form data-form="settings" class="mt-4 grid gap-3.5 md:grid-cols-2" @submit.prevent="save">
        <FormField for-id="settings-name" label="显示名称"><template #default="{ describedby }"><input id="settings-name" v-model="form.display_name" class="input" maxlength="64" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="settings-avatar" label="头像颜色"><template #default="{ describedby }"><input id="settings-avatar" v-model="form.avatar_color" class="h-11 w-full rounded-2xl border border-white/40 bg-transparent px-2 dark:border-white/10" type="color" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="settings-currency" label="货币符号"><template #default="{ describedby }"><input id="settings-currency" v-model="form.currency_symbol" class="input" maxlength="4" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="settings-duration" label="默认课时"><template #default="{ describedby }"><select id="settings-duration" v-model.number="form.default_duration_hours" class="input" :disabled="saving" :aria-describedby="describedby || undefined"><option :value="0.5">0.5 小时</option><option :value="1">1 小时</option><option :value="1.5">1.5 小时</option></select></template></FormField>
        <FormField for-id="settings-weeks" label="预生成周数" hint="范围为 1–52 周"><template #default="{ describedby }"><input id="settings-weeks" v-model.number="form.generate_weeks_ahead" class="input" type="number" min="1" max="52" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="settings-week-start" label="周起始日"><template #default="{ describedby }"><select id="settings-week-start" v-model.number="form.week_start" class="input" :disabled="saving" :aria-describedby="describedby || undefined"><option :value="1">周一</option><option :value="0">周日</option></select></template></FormField>
        <FormField for-id="settings-theme" label="主题"><template #default="{ describedby }"><select id="settings-theme" v-model="form.theme" class="input" :disabled="saving" :aria-describedby="describedby || undefined"><option value="auto">跟随系统</option><option value="light">浅色</option><option value="dark">深色</option></select></template></FormField>
        <FormField for-id="settings-time-start" label="可视起始"><template #default="{ describedby }"><input id="settings-time-start" v-model="form.visible_time_start" class="input" type="time" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="settings-time-end" label="可视结束"><template #default="{ describedby }"><input id="settings-time-end" v-model="form.visible_time_end" class="input" type="time" :disabled="saving" :aria-describedby="describedby || undefined" /></template></FormField>
        <InlineAlert v-if="settingsMessage" class="md:col-span-2" tone="success" :message="settingsMessage" /><InlineAlert v-if="settingsError" class="md:col-span-2" tone="error" :message="settingsError" />
        <div class="md:col-span-2"><AsyncButton data-action="save-settings" class="!min-h-[44px]" :pending="saving" pending-label="保存中…">保存设置</AsyncButton></div>
      </form>
    </section>

    <section class="glass p-4 md:p-5">
      <h2 class="text-lg font-semibold">数据备份</h2><p class="text-xs text-[var(--text-dim)]">下载一致性快照或从备份恢复数据库</p>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <div class="rounded-2xl border border-white/35 bg-white/45 p-4 dark:border-white/10 dark:bg-white/5"><h3 class="text-sm font-semibold">下载备份</h3><p class="mt-1.5 text-xs text-[var(--text-dim)]">保存当前 SQLite 数据库快照</p><AsyncButton type="button" class="mt-3 !min-h-[44px]" :pending="downloading" pending-label="下载中…" @click="downloadBackup">下载备份</AsyncButton></div>
        <div class="rounded-2xl border border-rose-500/15 bg-rose-500/5 p-4"><h3 class="text-sm font-semibold">恢复备份</h3><p class="mt-1.5 text-xs text-[var(--text-dim)]">将覆盖当前数据，系统会自动保存旧副本</p><div class="mt-3 space-y-3"><FormField for-id="restore-file" label="备份文件"><template #default="{ describedby }"><input id="restore-file" ref="restoreFileInput" class="input text-xs" type="file" accept=".db,.sqlite,.sqlite3" :disabled="restoring" :aria-describedby="describedby || undefined" @change="onFileChange" /></template></FormField><FormField for-id="restore-confirm" label="确认文字" hint="输入“确认恢复”后才能继续"><template #default="{ describedby }"><input id="restore-confirm" v-model="restoreConfirm" class="input text-xs" placeholder="确认恢复" :disabled="restoring" :aria-describedby="describedby || undefined" /></template></FormField><button type="button" data-action="prepare-restore" class="btn-danger !min-h-[44px]" :disabled="restoring" @click="prepareRestore">恢复数据</button></div></div>
      </div>
      <InlineAlert v-if="backupMessage" class="mt-3" tone="success" :message="backupMessage" /><InlineAlert v-if="backupError" class="mt-3" tone="error" :message="backupError" />
    </section>
  </div>

  <ConfirmDialog v-model:open="restoreDialogOpen" title="覆盖当前数据？" description="恢复备份会覆盖当前数据。操作前系统会自动保存旧数据库副本，但仍建议先下载最新备份。" confirm-label="确认覆盖并恢复" :pending="restoring" :error="backupError" pending-label="恢复中…" @confirm="restoreBackup" />
</template>
