<script setup lang="ts">
import type { StudentDetail } from '@/api/types'
import type { AppError } from '@/api/error'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import { formatCurrency, formatHours } from '@/lib/format'

defineProps<{
  student: StudentDetail | null
  loading: boolean
  error: AppError | null
  currencySymbol: string
}>()

const emit = defineEmits<{
  (e: 'edit-student', value: number): void
  (e: 'retry'): void
}>()
</script>

<template>
  <section class="glass-strong overflow-hidden p-4 md:p-5">
    <ErrorNotice v-if="error" class="mb-4" :error="error" @retry="emit('retry')" />

    <div v-if="loading && !student" class="animate-pulse">
      <div class="flex items-center gap-3">
        <span class="h-14 w-14 rounded-[20px] bg-[var(--accent-soft)]" />
        <div class="space-y-2">
          <span class="block h-4 w-28 rounded bg-[var(--line)]" />
          <span class="block h-3 w-40 rounded bg-[var(--line)]" />
        </div>
      </div>
      <div class="mt-5 grid grid-cols-2 gap-2.5 md:grid-cols-5">
        <span v-for="index in 5" :key="index" class="h-20 rounded-[18px] bg-white/45 dark:bg-white/5" />
      </div>
    </div>

    <div v-else-if="!student" class="flex min-h-48 flex-col items-center justify-center text-center">
      <span class="grid h-12 w-12 place-items-center rounded-[18px] bg-[var(--accent-soft)] text-xl text-[var(--accent)]">人</span>
      <p class="mt-3 text-sm font-semibold">选择一位学生</p>
      <p class="mt-1 text-xs text-[var(--text-dim)]">查看月度数据、联系方式和固定课表。</p>
    </div>

    <template v-else>
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div class="flex min-w-0 items-center gap-3.5">
          <span
            class="grid h-14 w-14 shrink-0 place-items-center rounded-[20px] text-xl font-extrabold text-white shadow-[0_10px_24px_rgba(73,48,92,.14)]"
            :style="{ background: `linear-gradient(145deg, ${student.color}, ${student.color}b8)` }"
          >
            {{ student.name.charAt(0) }}
          </span>
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h2 class="truncate text-xl font-extrabold tracking-[-0.04em]">{{ student.name }}</h2>
              <span :class="student.archived ? 'badge-muted' : 'badge-success'" class="badge text-[10px]">
                {{ student.archived ? '已归档' : '活跃' }}
              </span>
            </div>
            <p class="mt-1 text-xs text-[var(--text-dim)]">
              {{ formatCurrency(student.hourly_rate, currencySymbol) }}/小时 · {{ student.phone || '未填写电话' }}
            </p>
          </div>
        </div>
        <button data-action="edit-student" class="btn-ghost min-h-11 !rounded-2xl text-xs" @click="emit('edit-student', student.id)">
          编辑资料
        </button>
      </header>

      <div class="mt-5 grid grid-cols-2 gap-2.5 md:grid-cols-5">
        <article class="student-metric col-span-2 md:col-span-1">
          <span>本月收入</span>
          <strong>{{ formatCurrency(student.stats.month_income, currencySymbol) }}</strong>
        </article>
        <article class="student-metric">
          <span>本月课时</span>
          <strong>{{ formatHours(student.stats.month_hours) }}</strong>
        </article>
        <article class="student-metric">
          <span>课程数量</span>
          <strong>{{ student.stats.month_lesson_count }} <small>节</small></strong>
        </article>
        <article class="student-metric">
          <span>请假次数</span>
          <strong>{{ student.stats.month_leave_count }} <small>次</small></strong>
        </article>
        <article class="student-metric">
          <span>固定模板</span>
          <strong>{{ student.template_count }} <small>个</small></strong>
        </article>
      </div>

      <div class="mt-3 grid gap-2.5 md:grid-cols-[minmax(0,1fr)_1.4fr]">
        <div class="rounded-[18px] border border-white/75 bg-white/48 px-4 py-3 dark:border-white/8 dark:bg-white/5">
          <p class="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-dim)]">联系电话</p>
          <p class="mt-1.5 text-sm font-semibold">{{ student.phone || '未填写电话' }}</p>
        </div>
        <div class="rounded-[18px] border border-white/75 bg-white/48 px-4 py-3 dark:border-white/8 dark:bg-white/5">
          <p class="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-dim)]">学生备注</p>
          <p class="mt-1.5 text-sm leading-relaxed" :class="student.note ? '' : 'text-[var(--text-dim)]'">{{ student.note || '暂无备注' }}</p>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.student-metric {
  min-height: 82px;
  border: 1px solid rgba(255,255,255,.74);
  border-radius: 18px;
  background: rgba(255,255,255,.5);
  padding: .8rem;
}
.student-metric span { display: block; color: var(--text-dim); font-size: .65rem; font-weight: 600; }
.student-metric strong { display: block; margin-top: .42rem; font-size: 1.15rem; letter-spacing: -.04em; }
.student-metric small { color: var(--text-dim); font-size: .65rem; font-weight: 500; }
:global(.dark) .student-metric { border-color: rgba(255,255,255,.08); background: rgba(255,255,255,.045); }
</style>
