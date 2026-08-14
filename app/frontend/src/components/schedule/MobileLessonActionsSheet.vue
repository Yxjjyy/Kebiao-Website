<script setup lang="ts">
import type { Lesson } from '@/api/types'
import { downloadICS } from '@/composables/useCalendar'
import { formatHourMinute, formatShortDate, formatWeekday } from '@/lib/date'
import { formatCurrency, formatHours } from '@/lib/format'

const props = defineProps<{
  lesson: Lesson | null
  currencySymbol: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'complete', lesson: Lesson): void
  (e: 'restore', lesson: Lesson): void
  (e: 'cancel', lesson: Lesson): void
  (e: 'reschedule', lesson: Lesson): void
  (e: 'edit', lesson: Lesson): void
  (e: 'delete', lesson: Lesson): void
}>()

function addToCalendar() {
  if (!props.lesson) return
  downloadICS(props.lesson, props.lesson.student?.name ?? '课程')
}
</script>

<template>
  <div v-if="lesson" class="fixed inset-0 z-[80] lg:hidden" role="dialog" aria-modal="true" aria-label="课程操作">
    <button
      data-testid="action-sheet-backdrop"
      class="absolute inset-0 h-full w-full bg-[#21192c]/35 backdrop-blur-[2px]"
      aria-label="关闭课程操作"
      @click="emit('close')"
    />

    <section class="action-sheet absolute inset-x-0 bottom-0 max-h-[85dvh] overflow-y-auto rounded-t-[28px] border border-white/70 bg-[#fbf9fd]/95 px-4 pb-5 pt-2 shadow-[0_-20px_60px_rgba(64,42,82,0.18)] backdrop-blur-2xl dark:border-white/10 dark:bg-[#211a2a]/95">
      <div class="mx-auto mb-3 h-1 w-11 rounded-full bg-[#d8cfdf] dark:bg-white/20" />

      <header class="flex items-start justify-between gap-4 px-1">
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--text-dim)]">课程操作</p>
          <h2 class="mt-1 truncate text-lg font-bold tracking-tight">
            {{ lesson.student?.name ?? `学生 #${lesson.student_id}` }}
          </h2>
          <p class="mt-1 text-xs text-[var(--text-dim)]">
            {{ formatWeekday(lesson.date) }} {{ formatShortDate(lesson.date) }}
            · {{ formatHourMinute(lesson.start_time) }}
            · {{ formatHours(lesson.duration_hours) }}
          </p>
        </div>
        <button
          data-action="close"
          class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-white/80 text-[var(--text-dim)] shadow-sm dark:bg-white/10"
          aria-label="关闭"
          @click="emit('close')"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="m6 6 12 12M18 6 6 18" stroke-linecap="round" />
          </svg>
        </button>
      </header>

      <div class="mt-4 flex items-center justify-between rounded-2xl border border-white/80 bg-white/65 px-4 py-3 text-xs dark:border-white/10 dark:bg-white/5">
        <span class="text-[var(--text-dim)]">{{ lesson.note || '暂无课程备注' }}</span>
        <strong class="ml-3 shrink-0">{{ formatCurrency(lesson.price, currencySymbol) }}</strong>
      </div>

      <div class="mt-3 grid grid-cols-2 gap-2">
        <button
          v-if="lesson.status === '待上'"
          data-action="complete"
          class="sheet-action sheet-action-primary"
          @click="emit('complete', lesson)"
        >
          <span class="sheet-action-icon">✓</span>
          <span><b>完成课程</b><small>计入课时与收入</small></span>
        </button>
        <button
          v-else
          data-action="restore"
          class="sheet-action sheet-action-primary"
          @click="emit('restore', lesson)"
        >
          <span class="sheet-action-icon">↺</span>
          <span><b>恢复待上</b><small>撤销当前状态</small></span>
        </button>
        <button
          v-if="lesson.status === '待上'"
          data-action="cancel"
          class="sheet-action"
          @click="emit('cancel', lesson)"
        >
          <span class="sheet-action-icon sheet-action-icon-warm">○</span>
          <span><b>标记请假</b><small>保留课程记录</small></span>
        </button>
        <button
          v-if="lesson.status === '待上'"
          data-action="reschedule"
          class="sheet-action"
          @click="emit('reschedule', lesson)"
        >
          <span class="sheet-action-icon sheet-action-icon-violet">↗</span>
          <span><b>调整时间</b><small>移动到其他时段</small></span>
        </button>
        <button data-action="edit" class="sheet-action" @click="emit('edit', lesson)">
          <span class="sheet-action-icon sheet-action-icon-pink">✎</span>
          <span><b>编辑详情</b><small>时间、课时与备注</small></span>
        </button>
        <button data-action="calendar" class="sheet-action" @click="addToCalendar">
          <span class="sheet-action-icon sheet-action-icon-blue">＋</span>
          <span><b>加入日历</b><small>下载日历事件</small></span>
        </button>
      </div>

      <button
        data-action="delete"
        class="mt-2 flex min-h-11 w-full items-center justify-center rounded-2xl text-sm font-semibold text-red-500 transition-colors active:bg-red-500/10"
        @click="emit('delete', lesson)"
      >
        删除课程
      </button>
    </section>
  </div>
</template>
