<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(defineProps<{
  forId: string
  label: string
  hint?: string
  error?: string
  required?: boolean
}>(), {
  hint: '',
  error: '',
  required: false,
})

const instanceId = useId()
const hintId = computed(() => `${props.forId}-${instanceId}-hint`)
const errorId = computed(() => `${props.forId}-${instanceId}-error`)
</script>

<template>
  <div class="form-field min-w-0">
    <label :for="forId" class="label flex items-center gap-1.5">
      <span>{{ label }}</span>
      <span v-if="required" class="text-[9px] font-bold text-[var(--accent)]">必填</span>
    </label>
    <slot :describedby="[hint && !error ? hintId : '', error ? errorId : ''].filter(Boolean).join(' ')" />
    <p v-if="hint && !error" :id="hintId" class="mt-1.5 text-[10px] leading-4 text-[var(--text-dim)]">
      {{ hint }}
    </p>
    <p v-if="error" :id="errorId" role="alert" class="mt-1.5 text-[10px] font-semibold leading-4 text-rose-600 dark:text-rose-300">
      {{ error }}
    </p>
  </div>
</template>
