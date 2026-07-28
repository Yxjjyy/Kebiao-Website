<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useToast } from '@/composables/useToast'
import MobileTabBar from './MobileTabBar.vue'

const props = defineProps<{ activeTab: string }>()
const emit = defineEmits<{ (e: 'change-tab', tab: string): void }>()

const settings = useSettingsStore()
const toast = useToast()
const router = useRouter()

const tabRoutes: Record<string, string> = {
  schedule: '/', students: '/students', stats: '/stats', settings: '/settings',
}

const navItems = [
  { id: 'schedule', label: '课表',   icon: 'M8 2v4m0 4v4m0 4v4M4 6h16M4 14h16' },
  { id: 'students', label: '学生',   icon: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8zM22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75' },
  { id: 'stats',    label: '统计',   icon: 'M18 20V10M12 20V4M6 20v-6' },
  { id: 'settings', label: '设置',   icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z' },
]

const displayName = computed(() => settings.profile.display_name || '教师')
const avatarColor = computed(() => settings.profile.avatar_color || '#4C7DFF')
const avatarInitial = computed(() => displayName.value.charAt(0))

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
      class="glass-sidebar hidden w-60 flex-col lg:flex"
      style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom)"
    >
      <div class="flex items-center gap-3 px-5 pt-7 pb-5">
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-base font-bold text-white shadow-lg"
          :style="{ background: avatarColor }"
        >
          {{ avatarInitial }}
        </div>
        <div class="min-w-0">
          <p class="truncate text-base font-semibold leading-tight">{{ displayName }}</p>
          <p class="text-[11px] text-[var(--text-dim)]">授课管理</p>
        </div>
      </div>

      <nav class="flex-1 space-y-1 px-3 py-2">
        <button
          v-for="item in navItems"
          :key="item.id"
          :class="[
            'flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-200',
            activeTab === item.id
              ? 'bg-white/70 text-[var(--accent)] shadow-sm dark:bg-white/14'
              : 'text-[var(--text-dim)] hover:bg-white/40 hover:text-[var(--text)] dark:hover:bg-white/6',
          ]"
          @click="selectTab(item.id)"
        >
          <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path :d="item.icon" />
          </svg>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="px-5 pb-6 pt-2">
        <p class="text-[11px] text-[var(--text-dim)]">课表 v0.1</p>
      </div>
    </aside>

    <main
      class="flex-1 overflow-y-auto"
      style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom)"
      :class="{ 'pb-16': true }"
    >
      <div class="mx-auto w-full max-w-6xl px-3 py-4 sm:px-4 sm:py-5 md:px-6 md:py-7 lg:pb-14">
        <slot />
      </div>
    </main>

    <MobileTabBar :active-tab="activeTab" @select="handleTabChange" />

    <div
      v-if="toast.visible.value"
      class="glass-strong fixed bottom-20 left-1/2 z-[60] -translate-x-1/2 rounded-2xl px-5 py-2.5 text-sm font-medium shadow-lg transition-all duration-300 lg:bottom-6"
      style="padding-bottom: calc(0.625rem + env(safe-area-inset-bottom))"
    >
      <span class="text-[var(--text)]">{{ toast.message.value }}</span>
    </div>
  </div>
</template>
