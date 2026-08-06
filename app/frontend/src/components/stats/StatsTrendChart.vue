<script setup lang="ts">
import { computed, ref } from 'vue'
import type { RangeStats } from '@/api/types'
import { formatCurrency, formatHours } from '@/lib/format'
import { fillTrendPoints } from '@/lib/statsWorkspace'

const props = defineProps<{
  range: RangeStats | null
  currencySymbol: string
}>()

const mobileMetric = ref<'income' | 'hours'>('income')
const activeIndex = ref<number | null>(null)
const hasSourceData = computed(() => Boolean(props.range?.buckets.length))
const points = computed(() => props.range ? fillTrendPoints(props.range) : [])

const chart = computed(() => {
  const width = 640
  const height = 220
  const padX = 34
  const padTop = 24
  const padBottom = 34
  const plotHeight = height - padTop - padBottom
  const incomeMax = Math.max(...points.value.map((point) => point.income), 1)
  const hoursMax = Math.max(...points.value.map((point) => point.hours), 1)
  const x = (index: number) =>
    padX + index * ((width - padX * 2) / Math.max(points.value.length - 1, 1))
  const y = (value: number, maximum: number) =>
    padTop + plotHeight - (value / maximum) * plotHeight
  const path = (metric: 'income' | 'hours') => points.value
    .map((point, index) => {
      const value = metric === 'income' ? point.income : point.hours
      const maximum = metric === 'income' ? incomeMax : hoursMax
      return `${index ? 'L' : 'M'} ${x(index)} ${y(value, maximum)}`
    })
    .join(' ')
  const incomePath = path('income')
  const areaPath = points.value.length
    ? `${incomePath} L ${x(points.value.length - 1)} ${height - padBottom} L ${x(0)} ${height - padBottom} Z`
    : ''
  return { width, height, padX, padTop, padBottom, plotHeight, incomeMax, hoursMax, x, y, path, areaPath }
})

const selectedPoint = computed(() => activeIndex.value === null ? null : points.value[activeIndex.value])

function pointLabel(index: number): string {
  const point = points.value[index]
  return `${point.bucket}，收入 ${formatCurrency(point.income, props.currencySymbol)}，课时 ${formatHours(point.hours)}，${point.lesson_count} 节课`
}

function shortDate(bucket: string): string {
  return bucket.length === 10 ? bucket.slice(5).replace('-', '/') : bucket
}

function showPoint(index: number) {
  activeIndex.value = index
}
</script>

<template>
  <section class="glass-strong overflow-hidden p-4 md:p-5">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-[10px] font-extrabold uppercase tracking-[0.16em] text-[var(--text-dim)]">Performance curve</p>
        <h3 class="mt-1 text-lg font-extrabold tracking-[-0.03em]">收入与课时趋势</h3>
        <p class="mt-1 text-xs text-[var(--text-dim)]">同一时间轴观察经营结果与教学投入</p>
      </div>
      <div class="flex rounded-xl bg-white/45 p-1 dark:bg-white/5 lg:hidden">
        <button
          data-testid="metric-income-toggle"
          :aria-pressed="mobileMetric === 'income'"
          :class="['min-h-11 rounded-lg px-3 text-xs font-bold transition-colors', mobileMetric === 'income' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-dim)]']"
          @click="mobileMetric = 'income'"
        >收入</button>
        <button
          data-testid="metric-hours-toggle"
          :aria-pressed="mobileMetric === 'hours'"
          :class="['min-h-11 rounded-lg px-3 text-xs font-bold transition-colors', mobileMetric === 'hours' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-dim)]']"
          @click="mobileMetric = 'hours'"
        >课时</button>
      </div>
      <div class="hidden items-center gap-4 text-[11px] font-semibold text-[var(--text-dim)] lg:flex">
        <span class="flex items-center gap-1.5"><i class="h-2 w-5 rounded-full bg-[var(--accent)]" />收入</span>
        <span class="flex items-center gap-1.5"><i class="h-0 w-5 border-t-2 border-dashed border-pink-400" />课时</span>
      </div>
    </header>

    <div v-if="!hasSourceData" class="mt-4 grid min-h-52 place-items-center rounded-[20px] border border-dashed border-[var(--line)] text-center">
      <div>
        <span class="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)]">↗</span>
        <p class="mt-3 text-sm font-semibold">当前周期暂无趋势数据</p>
        <p class="mt-1 text-xs text-[var(--text-dim)]">有已完成或待上课程后，这里会出现变化曲线。</p>
      </div>
    </div>

    <div v-else class="relative mt-3">
      <div v-if="selectedPoint" class="absolute right-1 top-1 z-10 rounded-2xl border border-white/70 bg-white/88 px-3 py-2 text-right shadow-lg backdrop-blur dark:border-white/10 dark:bg-slate-950/85">
        <p class="text-[10px] font-bold text-[var(--text-dim)]">{{ selectedPoint.bucket }}</p>
        <p class="mt-0.5 text-sm font-extrabold text-[var(--accent)]">{{ formatCurrency(selectedPoint.income, currencySymbol) }}</p>
        <p class="text-[10px] text-[var(--text-dim)]">{{ formatHours(selectedPoint.hours) }} · {{ selectedPoint.lesson_count }} 节</p>
      </div>
      <svg :viewBox="`0 0 ${chart.width} ${chart.height}`" class="w-full overflow-visible" role="img" aria-label="收入与课时趋势图">
        <defs>
          <linearGradient id="income-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.28" />
            <stop offset="100%" stop-color="var(--accent)" stop-opacity="0" />
          </linearGradient>
          <linearGradient id="income-stroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#7c3aed" />
            <stop offset="100%" stop-color="#ec4899" />
          </linearGradient>
        </defs>
        <g aria-hidden="true">
          <line
            v-for="tick in 4"
            :key="tick"
            :x1="chart.padX"
            :x2="chart.width - chart.padX"
            :y1="chart.padTop + (chart.plotHeight / 3) * (tick - 1)"
            :y2="chart.padTop + (chart.plotHeight / 3) * (tick - 1)"
            stroke="currentColor"
            class="text-[var(--line)]"
            stroke-dasharray="3 7"
          />
          <path
            :d="chart.areaPath"
            fill="url(#income-area)"
            :class="[mobileMetric === 'income' ? 'opacity-100' : 'opacity-15', 'transition-opacity lg:opacity-100']"
          />
        </g>
        <path
          data-testid="income-line"
          :data-active="mobileMetric === 'income'"
          :d="chart.path('income')"
          fill="none"
          stroke="url(#income-stroke)"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
          :class="[mobileMetric === 'income' ? 'opacity-100' : 'opacity-15', 'transition-opacity lg:opacity-100']"
        />
        <path
          data-testid="hours-line"
          :data-active="mobileMetric === 'hours'"
          :d="chart.path('hours')"
          fill="none"
          stroke="#f472b6"
          stroke-width="2.5"
          stroke-dasharray="7 7"
          stroke-linecap="round"
          :class="[mobileMetric === 'hours' ? 'opacity-100' : 'opacity-15', 'transition-opacity lg:opacity-100']"
        />
        <g v-for="(point, index) in points" :key="point.bucket">
          <circle
            data-testid="trend-point"
            :aria-label="pointLabel(index)"
            :cx="chart.x(index)"
            :cy="chart.y(mobileMetric === 'income' ? point.income : point.hours, mobileMetric === 'income' ? chart.incomeMax : chart.hoursMax)"
            :r="activeIndex === index ? 6 : 4"
            fill="white"
            stroke="var(--accent)"
            stroke-width="3"
            role="button"
            tabindex="0"
            class="cursor-pointer outline-none transition-all focus:stroke-[5px]"
            @click="showPoint(index)"
            @focus="showPoint(index)"
            @mouseenter="showPoint(index)"
          />
          <text
            v-if="points.length <= 8 || index % Math.ceil(points.length / 7) === 0"
            :x="chart.x(index)"
            :y="chart.height - 9"
            text-anchor="middle"
            font-size="10"
            fill="currentColor"
            class="text-[var(--text-dim)]"
          >{{ shortDate(point.bucket) }}</text>
        </g>
      </svg>
    </div>
  </section>
</template>
