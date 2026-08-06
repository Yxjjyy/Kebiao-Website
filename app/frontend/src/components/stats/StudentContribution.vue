<script setup lang="ts">
import { computed } from 'vue'
import type { StudentStatsRow } from '@/api/types'
import { formatCurrency, formatHours } from '@/lib/format'
import { contributionPercent } from '@/lib/statsWorkspace'

const props = defineProps<{
  ranking: StudentStatsRow[]
  currencySymbol: string
}>()

const emit = defineEmits<{
  (event: 'select-student', studentId: number): void
}>()

const rankedStudents = computed(() =>
  [...props.ranking].sort((left, right) => right.total_income - left.total_income),
)
const maximumIncome = computed(() => rankedStudents.value[0]?.total_income ?? 0)
</script>

<template>
  <section class="glass-strong flex min-h-[272px] flex-col overflow-hidden p-4 md:p-5">
    <header class="flex items-start justify-between gap-4">
      <div>
        <p class="text-[9px] font-extrabold tracking-[0.16em] text-[var(--text-dim)]">CONTRIBUTION</p>
        <h3 class="mt-1 text-base font-extrabold tracking-[-0.025em]">学生贡献</h3>
      </div>
      <span class="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-[10px] font-bold text-[var(--accent)]">
        按收入排序
      </span>
    </header>

    <div v-if="rankedStudents.length" class="mt-4 space-y-2">
      <button
        v-for="(student, index) in rankedStudents"
        :key="student.student_id"
        type="button"
        data-testid="student-contribution"
        :aria-label="`查看${student.name}学生详情`"
        class="contribution-row group w-full rounded-2xl border border-transparent px-2.5 py-2 text-left transition hover:border-[var(--border)] hover:bg-[var(--surface-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
        @click="emit('select-student', student.student_id)"
      >
        <div class="flex items-center gap-2.5">
          <span class="w-4 shrink-0 text-center text-[10px] font-extrabold text-[var(--text-dim)]">{{ index + 1 }}</span>
          <span
            class="grid h-7 w-7 shrink-0 place-items-center rounded-xl text-[11px] font-extrabold text-white shadow-sm"
            :style="{ backgroundColor: student.color }"
            aria-hidden="true"
          >{{ student.name.slice(0, 1) }}</span>
          <div class="min-w-0 flex-1">
            <div class="flex items-baseline justify-between gap-2">
              <span class="truncate text-xs font-bold">{{ student.name }}</span>
              <span class="shrink-0 text-xs font-extrabold">{{ formatCurrency(student.total_income, currencySymbol) }}</span>
            </div>
            <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[var(--surface-soft)]">
              <span
                class="block h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-400 transition-[width] duration-500"
                :style="{ width: `${contributionPercent(student.total_income, maximumIncome)}%` }"
              />
            </div>
            <p class="mt-1 text-[10px] font-semibold text-[var(--text-dim)]">
              {{ student.lesson_count }} 节 · {{ formatHours(student.total_hours) }}
            </p>
          </div>
          <span class="translate-x-0 text-xs text-[var(--text-dim)] transition group-hover:translate-x-0.5 group-hover:text-[var(--accent)]" aria-hidden="true">→</span>
        </div>
      </button>
    </div>

    <div v-else class="grid flex-1 place-items-center py-10 text-center">
      <div>
        <span class="mx-auto grid h-10 w-10 place-items-center rounded-2xl bg-[var(--surface-soft)] text-sm text-[var(--text-dim)]">人</span>
        <p class="mt-3 text-xs font-semibold text-[var(--text-dim)]">当前周期暂无学生贡献数据</p>
      </div>
    </div>
  </section>
</template>
