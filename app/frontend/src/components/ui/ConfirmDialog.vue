<script setup lang="ts">
import AppDialog from './AppDialog.vue'
import AsyncButton from './AsyncButton.vue'

withDefaults(defineProps<{
  open: boolean
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  pending?: boolean
  pendingLabel?: string
  tone?: 'primary' | 'danger'
}>(), {
  description: '',
  confirmLabel: '确认',
  cancelLabel: '取消',
  pending: false,
  pendingLabel: '处理中…',
  tone: 'danger',
})

const emit = defineEmits<{
  'update:open': [open: boolean]
  confirm: []
  cancel: []
}>()

function close() {
  emit('update:open', false)
  emit('cancel')
}
</script>

<template>
  <AppDialog
    :open="open"
    :title="title"
    :description="description"
    size="sm"
    :close-disabled="pending"
    @update:open="emit('update:open', $event)"
    @close="emit('cancel')"
  >
    <slot />
    <template #footer>
      <button type="button" class="btn-ghost" :disabled="pending" @click="close">
        {{ cancelLabel }}
      </button>
      <AsyncButton
        type="button"
        data-action="confirm"
        :tone="tone"
        :pending="pending"
        :pending-label="pendingLabel"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </AsyncButton>
    </template>
  </AppDialog>
</template>
