<script setup lang="ts">
import { computed } from 'vue'
import type { Lesson } from '@/api/types'
import { formatHourMinute } from '@/lib/date'
import { findNextLesson, getCompletionRate } from '@/lib/scheduleDashboard'

const props = withDefaults(defineProps<{
  todayLessons: Lesson[]
  activeStudentCount: number
  now?: Date
}>(), {
  now: () => new Date(),
})

const completionRate = computed(() => getCompletionRate(props.todayLessons))
const completedCount = computed(() => props.todayLessons.filter((lesson) => lesson.status === '已完成').length)
const nextLesson = computed(() => findNextLesson(props.todayLessons, props.now))
</script>

<template>
  <aside class="hidden min-w-0 space-y-3 xl:block">
    <section class="glass-strong overflow-hidden p-4">
      <div class="flex items-center justify-between">
        <p class="text-sm font-bold">今日概览</p>
        <span class="rounded-full bg-[var(--accent-soft)] px-2 py-1 text-[10px] font-bold text-[var(--accent)]">实时</span>
      </div>
      <div class="mt-5 flex items-end gap-2">
        <strong class="text-4xl font-extrabold tracking-[-0.06em]">{{ todayLessons.length }}</strong>
        <span class="pb-1 text-xs text-[var(--text-dim)]">节课程</span>
      </div>
      <div class="mt-4 h-2 overflow-hidden rounded-full bg-[#eee7f3] dark:bg-white/10">
        <div class="h-full rounded-full transition-[width] duration-500" :style="{ width: `${completionRate}%`, background: 'var(--accent-gradient)' }" />
      </div>
      <p class="mt-2 text-[11px] text-[var(--text-dim)]">{{ completedCount }} 节已完成 · {{ completionRate }}%</p>
    </section>

    <section class="glass-strong p-4">
      <p class="text-sm font-bold">接下来</p>
      <div v-if="nextLesson" class="mt-4 flex items-start gap-3">
        <span class="rounded-xl bg-[var(--accent-soft)] px-2.5 py-2 text-xs font-extrabold text-[var(--accent)]">
          {{ formatHourMinute(nextLesson.start_time) }}
        </span>
        <div class="min-w-0">
          <p class="truncate text-sm font-bold">{{ nextLesson.student?.name ?? `学生 #${nextLesson.student_id}` }}</p>
          <p class="mt-1 truncate text-[11px] text-[var(--text-dim)]">{{ nextLesson.note || '待上课程' }}</p>
        </div>
      </div>
      <div v-else class="mt-4 rounded-2xl border border-dashed border-[var(--line)] px-3 py-4 text-center">
        <p class="text-xs font-semibold">今日课程已结束</p>
        <p class="mt-1 text-[10px] text-[var(--text-dim)]">辛苦了，记得休息。</p>
      </div>
    </section>

    <section class="glass-strong relative overflow-hidden p-4">
      <span class="absolute -right-5 -top-7 h-20 w-20 rounded-full bg-[var(--accent-soft)] blur-xl" />
      <p class="relative text-sm font-bold">活跃学生</p>
      <div class="relative mt-4 flex items-end gap-2">
        <strong class="text-3xl font-extrabold tracking-[-0.05em]">{{ activeStudentCount }}</strong>
        <span class="pb-1 text-[11px] text-[var(--text-dim)]">人正在授课</span>
      </div>
    </section>
  </aside>
</template>
