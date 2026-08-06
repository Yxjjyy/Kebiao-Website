<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { LeaveItem } from '@/api/types'
import { visibleAttentionItems } from '@/lib/statsWorkspace'

const props = defineProps<{
  items: LeaveItem[]
}>()

const expanded = ref(false)
const visibleItems = computed(() => visibleAttentionItems(props.items, expanded.value))

watch(() => props.items, () => {
  expanded.value = false
})

function statusTone(status: string) {
  return status === '已调课'
    ? 'bg-sky-500/10 text-sky-600 dark:text-sky-300'
    : 'bg-amber-500/10 text-amber-700 dark:text-amber-300'
}
</script>

<template>
  <section class="glass-strong flex min-h-[272px] flex-col overflow-hidden p-4 md:p-5">
    <header class="flex items-start justify-between gap-4">
      <div>
        <p class="text-[9px] font-extrabold tracking-[0.16em] text-[var(--text-dim)]">ATTENTION</p>
        <h3 class="mt-1 text-base font-extrabold tracking-[-0.025em]">待关注事项</h3>
      </div>
      <span v-if="items.length" class="grid h-7 min-w-7 place-items-center rounded-full bg-amber-500/10 px-2 text-[10px] font-extrabold text-amber-700 dark:text-amber-300">
        {{ items.length }}
      </span>
    </header>

    <div v-if="items.length" class="mt-4 space-y-2">
      <article
        v-for="item in visibleItems"
        :key="item.id"
        data-testid="attention-item"
        class="flex items-center gap-3 rounded-2xl bg-[var(--surface-soft)] px-3 py-2.5"
      >
        <div class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/55 text-xs font-extrabold text-[var(--accent)] shadow-sm dark:bg-white/5">
          {{ item.date.slice(8, 10) }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <p class="truncate text-xs font-bold">{{ item.student_name }}</p>
            <span :class="['shrink-0 rounded-full px-2 py-0.5 text-[9px] font-extrabold', statusTone(item.status)]">{{ item.status }}</span>
          </div>
          <p class="mt-1 truncate text-[10px] font-semibold text-[var(--text-dim)]">
            {{ item.date }} · {{ item.start_time }} · {{ item.duration_hours }}h<span v-if="item.note"> · {{ item.note }}</span>
          </p>
        </div>
      </article>

      <button
        v-if="items.length > 3"
        type="button"
        data-action="expand-attention"
        class="mt-1 w-full rounded-xl py-2 text-[11px] font-bold text-[var(--accent)] transition hover:bg-[var(--accent-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起' : `查看其余 ${items.length - 3} 项` }}
      </button>
    </div>

    <div v-else class="grid flex-1 place-items-center py-10 text-center">
      <div>
        <span class="mx-auto grid h-10 w-10 place-items-center rounded-2xl bg-emerald-500/10 text-sm text-emerald-600 dark:text-emerald-300">✓</span>
        <p class="mt-3 text-xs font-semibold text-[var(--text-dim)]">当前周期没有请假或调课记录</p>
      </div>
    </div>
  </section>
</template>
