<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useToast } from '@/composables/useToast'
import { useServiceWorkerUpdate } from '@/composables/useServiceWorkerUpdate'
import MobileTabBar from './MobileTabBar.vue'

const props = withDefaults(defineProps<{
  activeTab: string
  completedCount?: number
}>(), {
  completedCount: 0,
})

const emit = defineEmits<{ (e: 'change-tab', tab: string): void }>()

const settings = useSettingsStore()
const toast = useToast()
const router = useRouter()
const serviceWorkerUpdate = useServiceWorkerUpdate()

const tabRoutes: Record<string, string> = {
  schedule: '/', students: '/students', stats: '/stats', settings: '/settings',
}

const navItems = [
  { id: 'schedule', label: '我的课表', icon: 'M8 2v4m0 4v4m0 4v4M4 6h16M4 14h16' },
  { id: 'students', label: '学生管理', icon: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8zM22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75' },
  { id: 'stats', label: '数据统计', icon: 'M18 20V10M12 20V4M6 20v-6' },
  { id: 'settings', label: '系统设置', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z' },
]

const displayName = computed(() => settings.profile.display_name || '教师')

function selectTab(tab: string) {
  emit('change-tab', tab)
  router.push(tabRoutes[tab] || '/')
}

function handleTabChange(tab: string) {
  props.activeTab !== tab && selectTab(tab)
}
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <aside
      class="glass-sidebar hidden w-56 flex-col lg:flex"
      style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom)"
    >
      <div class="flex items-center gap-3 px-5 pb-6 pt-7">
        <span class="lumina-mark h-10 w-10">L</span>
        <div>
          <p class="text-[17px] font-extrabold leading-none tracking-[-0.04em]">Lumina</p>
          <p class="mt-1 text-[10px] text-[var(--text-dim)]">授课节奏管理</p>
        </div>
      </div>

      <nav class="flex-1 space-y-1 px-3 py-2">
        <button
          v-for="item in navItems"
          :key="item.id"
          :class="[
            'group flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-all duration-200',
            activeTab === item.id
              ? 'bg-[linear-gradient(90deg,rgba(124,58,237,.12),rgba(236,72,153,.09))] text-[var(--accent)] shadow-[inset_0_0_0_1px_rgba(124,58,237,.06)]'
              : 'text-[var(--text-dim)] hover:bg-white/50 hover:text-[var(--text)] dark:hover:bg-white/6',
          ]"
          @click="selectTab(item.id)"
        >
          <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path :d="item.icon" />
          </svg>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="px-4 pb-5 pt-2">
        <div class="relative overflow-hidden rounded-[20px] p-4 text-white shadow-[0_14px_28px_rgba(139,57,181,.22)]" style="background: var(--accent-gradient)">
          <span class="absolute -right-5 -top-7 h-20 w-20 rounded-full border border-white/15" />
          <p class="relative text-[10px] font-semibold text-white/65">本月已完成</p>
          <strong class="relative mt-1 block text-2xl tracking-tight">{{ completedCount }} 节</strong>
          <p class="relative mt-1 text-[10px] text-white/60">{{ displayName }} · 保持好节奏</p>
        </div>
      </div>
    </aside>

    <main
      class="flex-1 overflow-y-auto pb-24 lg:pb-0"
      style="padding-top: env(safe-area-inset-top)"
    >
      <div class="mx-auto w-full max-w-[1380px] px-4 py-5 sm:px-5 md:px-7 lg:px-8 lg:py-7 lg:pb-14">
        <slot />
      </div>
    </main>

    <MobileTabBar :active-tab="activeTab" @select="handleTabChange" />

    <aside
      v-if="serviceWorkerUpdate.updateAvailable.value"
      role="status"
      class="glass-strong fixed bottom-24 left-1/2 z-[85] flex w-[min(92vw,420px)] -translate-x-1/2 items-center justify-between gap-3 rounded-2xl px-4 py-3 shadow-lg lg:bottom-6"
    >
      <div class="min-w-0">
        <p class="text-xs font-extrabold">新版本已就绪</p>
        <p class="mt-0.5 text-[10px] text-[var(--text-dim)]">更新后将刷新页面，请先保存正在编辑的内容。</p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <button type="button" class="btn-ghost btn-sm" @click="serviceWorkerUpdate.dismissUpdate">稍后</button>
        <button type="button" class="btn-primary btn-sm" @click="serviceWorkerUpdate.applyUpdate">立即更新</button>
      </div>
    </aside>

    <div
      v-if="toast.visible.value"
      class="glass-strong fixed bottom-24 left-1/2 z-[90] -translate-x-1/2 rounded-2xl px-5 py-2.5 text-sm font-medium shadow-lg transition-all duration-300 lg:bottom-6"
      style="padding-bottom: calc(0.625rem + env(safe-area-inset-bottom))"
    >
      <span class="text-[var(--text)]">{{ toast.message.value }}</span>
    </div>
  </div>
</template>
