<script setup lang="ts">
import { computed } from 'vue'
import type { ComparisonStats, RangeStats } from '@/api/types'
import { formatCurrency, formatHours } from '@/lib/format'
import { calculateCompletionRate, formatGrowth } from '@/lib/statsWorkspace'

const props = defineProps<{
  range: RangeStats | null
  comparison: ComparisonStats | null
  currencySymbol: string
}>()

const metrics = computed(() => {
  const range = props.range
  const denominator = (range?.completed_lessons ?? 0)
    + (range?.pending_lessons ?? 0)
  const incomeGrowth = formatGrowth(props.comparison?.income_growth_pct ?? null)
  const hoursGrowth = formatGrowth(props.comparison?.hours_growth_pct ?? null)
  return [
    {
      id: 'income',
      label: '实际收入',
      value: formatCurrency(range?.total_income ?? 0, props.currencySymbol),
      detail: incomeGrowth.label,
      tone: incomeGrowth.tone,
      eyebrow: 'REVENUE',
      icon: '¥',
    },
    {
      id: 'hours',
      label: '有效课时',
      value: formatHours(range?.total_hours ?? 0),
      detail: hoursGrowth.label,
      tone: hoursGrowth.tone,
      eyebrow: 'TEACHING TIME',
      icon: '时',
    },
    {
      id: 'completion',
      label: '课程完成率',
      value: `${calculateCompletionRate(
        range?.completed_lessons ?? 0,
        range?.pending_lessons ?? 0,
      )}%`,
      detail: denominator
        ? `已完成 ${range?.completed_lessons ?? 0} / 共 ${denominator} 节`
        : '暂无课程',
      tone: 'neutral' as const,
      eyebrow: 'COMPLETION',
      icon: '✓',
    },
    {
      id: 'students',
      label: '活跃学生',
      value: String(range?.active_students ?? 0),
      detail: '本期覆盖学生',
      tone: 'neutral' as const,
      eyebrow: 'ACTIVE STUDENTS',
      icon: '人',
    },
  ]
})

const toneClass = {
  positive: 'text-emerald-600 dark:text-emerald-400',
  negative: 'text-rose-600 dark:text-rose-400',
  neutral: 'text-[var(--text-dim)]',
  muted: 'text-[var(--text-dim)]',
}
</script>

<template>
  <div class="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
    <article
      v-for="metric in metrics"
      :key="metric.id"
      :data-testid="`metric-${metric.id}`"
      class="metric-card glass-strong group relative min-w-0 overflow-hidden p-3.5 md:p-4"
    >
      <div class="pointer-events-none absolute -right-5 -top-7 h-20 w-20 rounded-full bg-[var(--accent)]/6 blur-xl transition-transform duration-500 group-hover:scale-125" />
      <div class="relative flex items-start justify-between gap-2">
        <div class="min-w-0">
          <p class="text-[9px] font-extrabold tracking-[0.15em] text-[var(--text-dim)]">{{ metric.eyebrow }}</p>
          <p class="mt-1 text-xs font-semibold text-[var(--text-dim)]">{{ metric.label }}</p>
        </div>
        <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[var(--accent-soft)] text-[11px] font-extrabold text-[var(--accent)]">
          {{ metric.icon }}
        </span>
      </div>
      <strong class="relative mt-3 block truncate text-xl font-extrabold tracking-[-0.045em] md:text-2xl">
        {{ metric.value }}
      </strong>
      <p :class="['relative mt-1.5 truncate text-[10px] font-semibold md:text-[11px]', toneClass[metric.tone]]">
        {{ metric.detail }}
      </p>
    </article>
  </div>
</template>

<style scoped>
.metric-card::after {
  position: absolute;
  right: 18%;
  bottom: 0;
  left: 18%;
  height: 1px;
  content: '';
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 35%, transparent), transparent);
}
</style>
