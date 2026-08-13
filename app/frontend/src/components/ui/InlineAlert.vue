<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  tone?: 'success' | 'warning' | 'error' | 'info'
  message: string
}>(), {
  tone: 'info',
})

const semantics = computed(() => props.tone === 'error'
  ? { role: 'alert' as const, live: 'assertive' as const }
  : { role: 'status' as const, live: 'polite' as const })

const toneClass = computed(() => ({
  success: 'border-emerald-500/15 bg-emerald-500/8 text-emerald-700 dark:text-emerald-300',
  warning: 'border-amber-500/15 bg-amber-500/8 text-amber-700 dark:text-amber-300',
  error: 'border-rose-500/15 bg-rose-500/8 text-rose-700 dark:text-rose-300',
  info: 'border-sky-500/15 bg-sky-500/8 text-sky-700 dark:text-sky-300',
}[props.tone]))
</script>

<template>
  <div
    :role="semantics.role"
    :aria-live="semantics.live"
    :class="['flex items-start gap-2.5 rounded-2xl border px-3.5 py-3 text-xs font-semibold leading-5', toneClass]"
  >
    <span aria-hidden="true">{{ tone === 'success' ? '✓' : tone === 'warning' ? '!' : tone === 'error' ? '×' : 'i' }}</span>
    <span class="min-w-0 flex-1">{{ message }}</span>
    <slot name="action" />
  </div>
</template>
