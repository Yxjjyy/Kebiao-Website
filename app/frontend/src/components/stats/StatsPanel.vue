<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ComparisonStats, LeaveItem, RangeStats, StudentStatsRow, TodayStats } from '@/api/types'
import { formatCurrency, formatHours } from '@/lib/format'
import { getTodayIso } from '@/lib/date'

const props = defineProps<{
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
}>()

const emit = defineEmits<{
  (e: 'change-range', range: 'today' | 'week' | 'month'): void
  (e: 'export-range'): void
  (e: 'prev-period'): void
  (e: 'next-period'): void
  (e: 'go-current-period'): void
}>()

const rangeLabel = computed(() =>
  props.statRange === 'today' ? '今日' : props.statRange === 'week' ? '本周' : '本月'
)

const growthLabel = computed(() => {
  if (!props.comparison?.income_growth_pct) return null
  const pct = props.comparison.income_growth_pct
  return pct > 0 ? `↑${pct.toFixed(1)}%` : `↓${Math.abs(pct).toFixed(1)}%`
})

const growthColor = computed(() => {
  if (!props.comparison?.income_growth_pct) return ''
  return props.comparison.income_growth_pct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'
})

const maxIncome = computed(() => Math.max(...(props.range?.buckets?.map((b) => b.income) ?? [0]), 1))
const maxRankIncome = computed(() => Math.max(...props.ranking.map((r) => r.total_income), 1))

const todayIso = getTodayIso()

interface TrendBucket {
  bucket: string
  income: number
  hours: number
  lesson_count: number
  isToday: boolean
}

const filledBuckets = computed<TrendBucket[]>(() => {
  const raw = props.range?.buckets ?? []
  if (!raw.length) return []
  const map = new Map(raw.map((b) => [b.bucket, b]))
  if (props.range?.granularity === 'day' && props.statRange !== 'today') {
    const first = raw[0].bucket
    const last = raw[raw.length - 1].bucket
    const result: TrendBucket[] = []
    const cursor = new Date(first)
    const end = new Date(last)
    while (cursor <= end) {
      const iso = cursor.toISOString().slice(0, 10)
      const found = map.get(iso)
      result.push({
        bucket: iso,
        income: found?.income ?? 0,
        hours: found?.hours ?? 0,
        lesson_count: found?.lesson_count ?? 0,
        isToday: iso === todayIso,
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    return result
  }
  return raw.map((b) => ({ ...b, isToday: b.bucket === todayIso }))
})

const averageIncome = computed(() => {
  const buckets = filledBuckets.value
  if (!buckets.length) return 0
  const todayStr = getTodayIso()
  const pastBuckets = props.statRange === 'today'
    ? buckets
    : buckets.filter(b => b.bucket <= todayStr)
  if (!pastBuckets.length) return 0
  return pastBuckets.reduce((sum, b) => sum + b.income, 0) / pastBuckets.length
})

const hoveredIndex = ref<number | null>(null)
const hoveredBucket = computed(() => {
  if (hoveredIndex.value === null) return null
  return filledBuckets.value[hoveredIndex.value] ?? null
})

const trendChart = computed(() => {
  const buckets = filledBuckets.value
  const count = Math.max(buckets.length, 1)
  const barW = Math.max(6, Math.min(36, Math.floor(600 / count) - 4))
  const gap = Math.max(2, Math.min(4, Math.floor((600 - barW * count) / count)))
  const padL = 42
  const padB = 24
  const padT = 8
  const chartH = 160

  const labelEvery = count > 21 ? 7 : count > 14 ? 3 : count > 7 ? 2 : 1

  const max = maxIncome.value
  const avgVal = averageIncome.value

  const yTicks = 5
  const yTickStep = max > 0 ? max / (yTicks - 1) : 1

  return { buckets, count, barW, gap, padL, padB, padT, chartH, max, avgVal, labelEvery, yTicks, yTickStep }
})

const rankBars = computed(() => {
  const barH = 22, gap = 6, padL = 6, chartW = 200
  const h = props.ranking.length * (barH + gap) + 10
  return { barH, gap, padL, chartW, h, max: maxRankIncome.value }
})

function xLabel(bucket: string, idx: number): string {
  if (trendChart.value.labelEvery > 1 && idx % trendChart.value.labelEvery !== 0) return ''
  if (bucket.length === 10) {
    if (props.statRange === 'week') {
      const dayNames = ['日', '一', '二', '三', '四', '五', '六']
      return dayNames[new Date(bucket + 'T00:00:00').getDay()]
    }
    return bucket.slice(5)
  }
  if (bucket.length === 7) return bucket.slice(5) + '月'
  return bucket
}

function isTodayBar(b: TrendBucket): boolean {
  return b.isToday
}

function showTooltip(idx: number) { hoveredIndex.value = idx }
function hideTooltip() { hoveredIndex.value = null }
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-lg font-semibold">统计</h2>
      <div class="flex items-center gap-1 rounded-xl bg-white/40 p-0.5 dark:bg-white/8">
        <button
          v-for="r in (['today', 'week', 'month'] as const)"
          :key="r"
          :class="['rounded-lg px-2.5 py-1 text-xs font-medium transition-colors', statRange === r ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-dim)] hover:text-[var(--text)]']"
          @click="emit('change-range', r)"
        >
          {{ r === 'today' ? '今日' : r === 'week' ? '本周' : '本月' }}
        </button>
      </div>
    </div>

    <div v-if="statRange !== 'today'" class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-1">
        <button class="btn-ghost btn-sm !px-2" @click="emit('prev-period')">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <span class="text-xs font-semibold">{{ statsPeriodLabel }}</span>
        <button class="btn-ghost btn-sm !px-2" :disabled="isCurrentPeriod" :class="{ 'opacity-30 pointer-events-none': isCurrentPeriod }" @click="emit('next-period')">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>
      <button v-if="!isCurrentPeriod" class="btn-ghost btn-sm text-xs" @click="emit('go-current-period')">
        回到当期
      </button>
    </div>

    <div class="grid gap-3 md:grid-cols-3">
      <article class="glass rounded-2xl p-4">
        <p class="text-xs text-[var(--text-dim)]">{{ rangeLabel }}收入</p>
        <p class="mt-2 text-2xl font-bold">{{ formatCurrency(range?.total_income ?? 0, currencySymbol) }}</p>
        <p v-if="growthLabel" :class="['mt-1 text-xs', growthColor]">
          较上期 {{ growthLabel }}
        </p>
        <p v-else class="mt-1 text-xs text-[var(--text-dim)]">暂无同期对比</p>
      </article>
      <article class="glass rounded-2xl p-4">
        <p class="text-xs text-[var(--text-dim)]">{{ rangeLabel }}课时</p>
        <p class="mt-2 text-2xl font-bold">{{ formatHours(range?.total_hours ?? 0) }}</p>
        <p class="mt-1 text-xs text-[var(--text-dim)]">{{ range?.total_lessons ?? 0 }} 节课</p>
      </article>
      <article class="glass rounded-2xl p-4">
        <p class="text-xs text-[var(--text-dim)]">今日收入</p>
        <p class="mt-2 text-2xl font-bold">{{ formatCurrency(today?.earned_income ?? 0, currencySymbol) }}</p>
        <p class="mt-1 text-xs text-[var(--text-dim)]">{{ today?.total_lessons ?? 0 }} 节今日课程</p>
      </article>
    </div>

    <div class="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
      <section class="glass p-4 md:p-5">
        <h3 class="text-sm font-semibold">{{ rangeLabel }}趋势</h3>
        <p class="text-xs text-[var(--text-dim)]">
          日均 {{ formatCurrency(averageIncome, currencySymbol) }}
          <span class="ml-2 opacity-60">{{ trendChart.count }} 个时段</span>
        </p>

        <div class="relative mt-4">
          <svg
            :viewBox="`0 0 ${trendChart.padL + trendChart.count * (trendChart.barW + trendChart.gap)} ${trendChart.chartH + trendChart.padB + trendChart.padT}`"
            class="w-full"
            style="max-height:220px"
          >
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#4C7DFF" stop-opacity="0.95" />
              <stop offset="100%" stop-color="#9C6BFF" stop-opacity="0.7" />
            </linearGradient>
            <linearGradient id="barGradToday" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#FF6B4C" stop-opacity="0.95" />
              <stop offset="100%" stop-color="#FF9C6B" stop-opacity="0.7" />
            </linearGradient>

            <line
              v-for="i in trendChart.yTicks"
              :key="'yl'+i"
              :x1="trendChart.padL"
              :y1="trendChart.padT + (trendChart.chartH / (trendChart.yTicks - 1)) * (i - 1)"
              :x2="trendChart.padL + trendChart.count * (trendChart.barW + trendChart.gap)"
              :y2="trendChart.padT + (trendChart.chartH / (trendChart.yTicks - 1)) * (i - 1)"
              stroke-dasharray="3,3"
              :stroke="i === 1 ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)'"
            />
            <text
              v-for="i in trendChart.yTicks"
              :key="'yt'+i"
              :x="trendChart.padL - 6"
              :y="trendChart.padT + (trendChart.chartH / (trendChart.yTicks - 1)) * (i - 1) + 4"
              text-anchor="end"
              font-size="9"
              fill="#999"
            >{{ formatCurrency(trendChart.yTickStep * (trendChart.yTicks - i), currencySymbol) }}</text>

            <line
              v-if="trendChart.avgVal > 0"
              :x1="trendChart.padL"
              :y1="trendChart.padT + trendChart.chartH - (trendChart.avgVal / trendChart.max) * trendChart.chartH"
              :x2="trendChart.padL + trendChart.count * (trendChart.barW + trendChart.gap)"
              :y2="trendChart.padT + trendChart.chartH - (trendChart.avgVal / trendChart.max) * trendChart.chartH"
              stroke="#FF6B4C"
              stroke-dasharray="6,4"
              stroke-width="1"
              opacity="0.5"
            />

            <g v-for="(b, idx) in trendChart.buckets" :key="b.bucket">
              <rect
                :x="trendChart.padL + idx * (trendChart.barW + trendChart.gap)"
                :y="trendChart.padT + trendChart.chartH - (b.income / trendChart.max) * trendChart.chartH"
                :width="trendChart.barW"
                :height="Math.max(2, (b.income / trendChart.max) * trendChart.chartH)"
                rx="3"
                :fill="isTodayBar(b) ? 'url(#barGradToday)' : 'url(#barGrad)'"
                :opacity="hoveredIndex === idx ? 1 : hoveredIndex === null ? 0.85 : 0.4"
                class="cursor-pointer transition-opacity duration-150"
                @mouseenter="showTooltip(idx)"
                @mouseleave="hideTooltip"
              />
              <text
                :x="trendChart.padL + idx * (trendChart.barW + trendChart.gap) + trendChart.barW / 2"
                :y="trendChart.padT + trendChart.chartH + 16"
                text-anchor="middle"
                font-size="8"
                :fill="xLabel(b.bucket, idx) ? '#999' : 'transparent'"
              >{{ xLabel(b.bucket, idx) }}</text>
            </g>
          </svg>

          <div
            v-if="hoveredBucket"
            class="glass-strong pointer-events-none absolute z-10 -translate-x-1/2 rounded-xl px-3 py-2 text-center shadow-lg"
            :style="{
              left: `${((hoveredIndex ?? 0) + 0.5) / trendChart.count * 100}%`,
              top: '-4px',
            }"
          >
            <p class="text-xs font-semibold whitespace-nowrap">{{ hoveredBucket.bucket }}</p>
            <p class="text-sm font-bold text-[var(--accent)]">{{ formatCurrency(hoveredBucket.income, currencySymbol) }}</p>
            <p class="text-[10px] text-[var(--text-dim)]">{{ hoveredBucket.lesson_count }}节 · {{ hoveredBucket.hours.toFixed(1) }}h</p>
          </div>
        </div>
      </section>

      <div class="grid gap-4">
        <section class="glass p-4 md:p-5">
          <h3 class="text-sm font-semibold">学生排行</h3>
          <p class="text-xs text-[var(--text-dim)]">按区间收入降序</p>
          <div v-if="ranking.length" class="mt-3">
            <svg :viewBox="`0 0 ${rankBars.chartW + rankBars.padL + 80} ${rankBars.h}`" class="w-full" style="max-height:260px">
              <g v-for="(s, idx) in ranking" :key="s.student_id">
                <rect :x="rankBars.padL" :y="idx * (rankBars.barH + rankBars.gap)" :width="Math.max(4, (s.total_income / rankBars.max) * rankBars.chartW)" :height="rankBars.barH" rx="4" :fill="s.color" opacity="0.75">
                  <title>{{ s.name }} — {{ formatCurrency(s.total_income, currencySymbol) }}</title>
                </rect>
                <text :x="rankBars.padL + 6" :y="idx * (rankBars.barH + rankBars.gap) + rankBars.barH / 2 + 4" font-size="11" fill="#fff" font-weight="600">{{ s.name }}</text>
                <text :x="rankBars.padL + (s.total_income / rankBars.max) * rankBars.chartW + 6" :y="idx * (rankBars.barH + rankBars.gap) + rankBars.barH / 2 + 4" font-size="10" fill="#666">{{ formatCurrency(s.total_income, currencySymbol) }}</text>
              </g>
            </svg>
          </div>
          <div v-else class="mt-4 rounded-xl border border-dashed border-white/30 px-3 py-8 text-center text-xs text-[var(--text-dim)] dark:border-white/8">暂无数据</div>
        </section>
      </div>
    </div>

    <section v-if="leaveItems.length" class="glass p-4 md:p-5">
      <h3 class="text-sm font-semibold">请假与调课记录</h3>
      <p class="text-xs text-[var(--text-dim)]">{{ rangeLabel }}异常课时</p>
      <div class="mt-3 space-y-2">
        <article
          v-for="item in leaveItems"
          :key="item.id"
          class="flex items-center justify-between rounded-xl border border-white/35 bg-white/45 px-3 py-2.5 dark:border-white/8 dark:bg-white/5"
        >
          <div class="flex items-center gap-3 min-w-0">
            <span :class="['badge text-[10px] shrink-0', item.status === '请假' ? 'badge-warning' : 'badge-muted']">{{ item.status }}</span>
            <div class="min-w-0">
              <p class="text-sm font-medium truncate">{{ item.student_name }}</p>
              <p class="text-xs text-[var(--text-dim)]">{{ item.date }} {{ item.start_time.slice(0,5) }} · {{ item.duration_hours }}h</p>
            </div>
          </div>
          <span v-if="item.note" class="text-xs text-[var(--text-dim)] ml-2 shrink-0 truncate max-w-32">{{ item.note }}</span>
        </article>
      </div>
    </section>
  </div>
</template>
