<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  pending?: boolean
  pendingLabel?: string
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  tone?: 'primary' | 'ghost' | 'danger'
  size?: 'default' | 'sm'
}>(), {
  pending: false,
  pendingLabel: '提交中…',
  disabled: false,
  type: 'submit',
  tone: 'primary',
  size: 'default',
})

const buttonClass = computed(() => [
  props.tone === 'primary' ? 'btn-primary' : props.tone === 'danger' ? 'btn-danger' : 'btn-ghost',
  props.size === 'sm' ? 'btn-sm' : '',
])
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || pending"
    :aria-busy="pending ? 'true' : undefined"
    :class="buttonClass"
  >
    <span v-if="pending" class="inline-flex items-center gap-2">
      <i class="h-3 w-3 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden="true" />
      {{ pendingLabel }}
    </span>
    <slot v-else />
  </button>
</template>
