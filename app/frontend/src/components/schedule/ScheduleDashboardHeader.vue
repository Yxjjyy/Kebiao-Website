<script setup lang="ts">
import { computed } from 'vue'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { Lesson } from '@/api/types'
import { getCompletionRate, getGreeting } from '@/lib/scheduleDashboard'

const props = withDefaults(defineProps<{
  displayName: string
  avatarColor: string
  todayLessons: Lesson[]
  now?: Date
}>(), {
  now: () => new Date(),
})

const emit = defineEmits<{ (e: 'create'): void }>()

const greeting = computed(() => getGreeting(props.now.getHours()))
const dateLabel = computed(() => format(props.now, 'M月d日 · EEEE', { locale: zhCN }))
const seasonLabel = computed(() => `${props.now.getFullYear()} 年 · 我的授课工作台`)
const completionRate = computed(() => getCompletionRate(props.todayLessons))
const avatarInitial = computed(() => props.displayName.charAt(0) || '师')
const progressStyle = computed(() => ({
  background: `conic-gradient(#fff 0 ${completionRate.value}%, rgba(255,255,255,.22) ${completionRate.value}% 100%)`,
}))
</script>

<template>
  <header>
    <div class="hidden items-end justify-between gap-6 lg:flex">
      <div>
        <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--text-dim)]">{{ seasonLabel }}</p>
        <h1 class="mt-2 text-[30px] font-extrabold leading-none tracking-[-0.04em]">
          {{ greeting }}，<span class="lumina-gradient-text">{{ displayName }}</span>
          <span class="ml-1 inline-block origin-bottom animate-[wave_1.8s_ease-in-out_1]">👋</span>
        </h1>
        <p class="mt-2 text-sm text-[var(--text-dim)]">
          今天安排了 {{ todayLessons.length }} 节课程，按自己的节奏从容开始。
        </p>
      </div>
      <button data-action="create-lesson" class="btn-primary min-h-11 !rounded-2xl !px-5" @click="emit('create')">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" stroke-linecap="round" />
        </svg>
        新建课程
      </button>
    </div>

    <div class="lg:hidden">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="lumina-mark h-9 w-9 text-sm">L</span>
          <div>
            <p class="text-sm font-extrabold tracking-tight">Lumina</p>
            <p class="text-[10px] text-[var(--text-dim)]">轻盈安排每一课</p>
          </div>
        </div>
        <span
          class="grid h-10 w-10 place-items-center rounded-2xl border border-white/80 text-sm font-bold text-white shadow-[0_8px_20px_rgba(85,57,112,0.12)]"
          :style="{ background: avatarColor }"
        >
          {{ avatarInitial }}
        </span>
      </div>

      <div class="mt-6">
        <p class="text-xs font-medium text-[var(--text-dim)]">{{ dateLabel }}</p>
        <h1 class="mt-1 text-[26px] font-extrabold tracking-[-0.04em]">
          {{ greeting }}，<span class="lumina-gradient-text">{{ displayName }}</span>
        </h1>
      </div>

      <div class="relative mt-5 overflow-hidden rounded-[24px] px-5 py-4 text-white shadow-[0_18px_35px_rgba(139,57,181,0.22)]" style="background: var(--accent-gradient)">
        <span class="absolute -right-8 -top-12 h-32 w-32 rounded-full border border-white/15" />
        <span class="absolute -right-2 -top-5 h-20 w-20 rounded-full bg-white/10 blur-sm" />
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-[11px] font-semibold tracking-wide text-white/70">今日课程</p>
            <strong class="mt-1 block text-2xl tracking-tight">{{ todayLessons.length }} 节</strong>
            <span class="mt-1 block text-[11px] text-white/65">完成度 {{ completionRate }}%</span>
          </div>
          <div class="relative grid h-14 w-14 place-items-center rounded-full" :style="progressStyle">
            <span class="absolute inset-[5px] rounded-full bg-[#a24ac5]" />
            <b class="relative text-xs">{{ completionRate }}%</b>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
