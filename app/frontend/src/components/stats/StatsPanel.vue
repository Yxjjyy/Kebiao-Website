<script setup lang="ts">
import type { ComparisonStats, LeaveItem, RangeStats, StudentStatsRow, TodayStats } from '@/api/types'
import type { AppError } from '@/api/error'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import AttentionList from './AttentionList.vue'
import StatsMetricGrid from './StatsMetricGrid.vue'
import StatsTrendChart from './StatsTrendChart.vue'
import StudentContribution from './StudentContribution.vue'

defineProps<{
  today: TodayStats | null
  range: RangeStats | null
  ranking: StudentStatsRow[]
  comparison: ComparisonStats | null
  leaveItems: LeaveItem[]
  statRange: string
  currencySymbol: string
  statsOffset: number
  statsPeriodLabel: string
  isCurrentPeriod: boolean
  loading?: boolean
  error?: AppError | null
}>()

const emit = defineEmits<{
  (event: 'change-range', range: 'today' | 'week' | 'month'): void
  (event: 'export-range'): void
  (event: 'prev-period'): void
  (event: 'next-period'): void
  (event: 'go-current-period'): void
  (event: 'retry'): void
  (event: 'select-student', studentId: number): void
}>()

const ranges = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
] as const
</script>

<template>
  <div class="stats-workspace space-y-3.5 md:space-y-4">
    <header class="glass-strong overflow-hidden p-3.5 md:p-4">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div class="min-w-0">
          <p class="text-[9px] font-extrabold tracking-[0.18em] text-[var(--accent)]">INSIGHTS WORKSPACE</p>
          <div class="mt-1 flex items-center gap-2">
            <h2 class="text-lg font-extrabold tracking-[-0.035em] md:text-xl">数据统计</h2>
            <span v-if="loading && range" class="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--accent)]" aria-label="正在刷新" />
          </div>
          <p class="mt-0.5 truncate text-[10px] font-semibold text-[var(--text-dim)] md:text-xs">
            {{ statsPeriodLabel }} · 收入、课时与学生动态
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <div class="flex items-center rounded-xl bg-[var(--surface-soft)] p-0.5" aria-label="统计周期">
            <button
              v-for="rangeOption in ranges"
              :key="rangeOption.value"
              type="button"
              :data-range="rangeOption.value"
              :aria-pressed="statRange === rangeOption.value"
              :class="[
                'min-h-11 rounded-[10px] px-3 py-1.5 text-[11px] font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]',
                statRange === rangeOption.value
                  ? 'bg-[var(--accent)] text-white shadow-sm'
                  : 'text-[var(--text-dim)] hover:text-[var(--text)]',
              ]"
              @click="emit('change-range', rangeOption.value)"
            >
              {{ rangeOption.label }}
            </button>
          </div>
          <button
            type="button"
            class="btn-ghost btn-sm min-h-11 text-[11px]"
            :disabled="loading"
            @click="emit('export-range')"
          >
            导出
          </button>
        </div>
      </div>

      <div v-if="statRange !== 'today'" class="mt-3 flex items-center justify-between border-t border-[var(--border)] pt-2.5">
        <div class="flex items-center gap-1.5">
          <button type="button" class="nav-button" aria-label="上一周期" @click="emit('prev-period')">←</button>
          <span class="max-w-[180px] truncate text-[11px] font-bold md:max-w-none">{{ statsPeriodLabel }}</span>
          <button
            type="button"
            class="nav-button"
            aria-label="下一周期"
            :disabled="isCurrentPeriod"
            @click="emit('next-period')"
          >→</button>
        </div>
        <button
          v-if="!isCurrentPeriod"
          type="button"
          class="text-[10px] font-bold text-[var(--accent)] hover:underline"
          @click="emit('go-current-period')"
        >回到当期</button>
      </div>
    </header>

    <ErrorNotice v-if="error" :error="error" @retry="emit('retry')" />

    <div v-if="loading && !range" data-testid="stats-skeleton" class="space-y-3" aria-label="正在加载统计数据">
      <div class="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
        <div v-for="index in 4" :key="index" class="glass-strong h-[122px] animate-pulse bg-[var(--surface-soft)]" />
      </div>
      <div class="grid gap-3 lg:grid-cols-[1.55fr_0.85fr]">
        <div class="glass-strong h-[304px] animate-pulse bg-[var(--surface-soft)]" />
        <div class="glass-strong h-[304px] animate-pulse bg-[var(--surface-soft)]" />
      </div>
    </div>

    <template v-else>
      <StatsMetricGrid :range="range" :comparison="comparison" :currency-symbol="currencySymbol" />
      <StatsTrendChart :range="range" :currency-symbol="currencySymbol" />
      <div class="grid gap-3 lg:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.85fr)]">
        <StudentContribution
          :ranking="ranking"
          :currency-symbol="currencySymbol"
          @select-student="emit('select-student', $event)"
        />
        <AttentionList :items="leaveItems" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.nav-button {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border-radius: 0.65rem;
  color: var(--text-dim);
  font-size: 0.75rem;
  font-weight: 800;
  transition: 160ms ease;
}

.nav-button:hover:not(:disabled) {
  color: var(--accent);
  background: var(--accent-soft);
}

.nav-button:disabled {
  cursor: not-allowed;
  opacity: 0.25;
}
</style>
