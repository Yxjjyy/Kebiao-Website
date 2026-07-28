<script setup lang="ts">
defineProps<{ label: string; value: string; hint?: string; accent?: string }>()
</script>

<template>
  <section class="glass relative overflow-hidden p-5 transition-shadow hover:shadow-md">
    <div
      v-if="accent"
      class="absolute top-0 left-0 right-0 h-[3px] rounded-b-full opacity-70"
      :style="{ background: accent }"
    />
    <p class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)]">
      {{ label }}
    </p>
    <p class="mt-2 text-[22px] font-bold tracking-tight text-[var(--text)] sm:text-[26px] md:text-[28px]">
      {{ value }}
    </p>
    <p v-if="hint" class="mt-1.5 text-xs text-[var(--text-dim)]">
      {{ hint }}
    </p>
  </section>
</template>
