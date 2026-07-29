<script setup lang="ts">
defineProps<{ activeTab: string }>()
const emit = defineEmits<{ (e: 'select', tab: string): void }>()

const tabs = [
  { id: 'schedule', label: '课表', icon: 'M8 2v4m0 4v4m0 4v4M4 6h16M4 14h16' },
  { id: 'students', label: '学生', icon: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8zM22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75' },
  { id: 'stats', label: '统计', icon: 'M18 20V10M12 20V4M6 20v-6' },
  { id: 'settings', label: '设置', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z' },
]

</script>

<template>
  <nav
    class="fixed bottom-2 left-3 right-3 z-50 rounded-[22px] border border-white/80 bg-white/80 shadow-[0_16px_40px_rgba(58,38,73,.16)] backdrop-blur-2xl dark:border-white/10 dark:bg-[#211a2a]/90 lg:hidden"
    style="padding-bottom: env(safe-area-inset-bottom)"
  >
    <div class="flex h-[62px] items-stretch px-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="[
          'flex flex-1 flex-col items-center justify-center gap-0.5 transition-colors duration-150',
          activeTab === tab.id ? 'text-[var(--accent)]' : 'text-[var(--text-dim)]',
        ]"
        @click="emit('select', tab.id)"
      >
        <span
          :class="['grid h-8 w-9 place-items-center rounded-xl transition-all', activeTab === tab.id ? 'text-white shadow-[0_6px_14px_rgba(139,57,181,.22)]' : '']"
          :style="activeTab === tab.id ? { background: 'var(--accent-gradient)' } : undefined"
        >
          <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" :stroke-width="activeTab === tab.id ? 2 : 1.6" stroke-linecap="round" stroke-linejoin="round">
            <path :d="tab.icon" />
          </svg>
        </span>
        <span class="text-[10px] font-medium">{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>
