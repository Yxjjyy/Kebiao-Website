<script setup lang="ts">
import {
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  open: boolean
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  closeDisabled?: boolean
}>(), {
  description: '',
  size: 'md',
  closeDisabled: false,
})

const emit = defineEmits<{
  'update:open': [open: boolean]
  close: []
}>()

const panelSize = computed(() => ({
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
})[props.size])

function requestClose() {
  if (props.closeDisabled) return
  emit('update:open', false)
  emit('close')
}

function handleOpenChange(open: boolean) {
  if (!open) requestClose()
}

function preventClose(event: Event) {
  if (props.closeDisabled) event.preventDefault()
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <DialogOverlay class="modal-backdrop fixed inset-0 z-[100] bg-slate-950/45 backdrop-blur-sm" />
      <DialogContent
        :class="[
          'modal-panel glass-strong fixed inset-x-0 bottom-0 z-[101] max-h-[85vh] w-full overflow-y-auto p-6 shadow-2xl focus:outline-none',
          'sm:inset-auto sm:left-1/2 sm:top-1/2 sm:max-h-[85vh] sm:w-[calc(100%-2rem)] sm:-translate-x-1/2 sm:-translate-y-1/2',
          panelSize,
        ]"
        @escape-key-down="preventClose"
        @pointer-down-outside="preventClose"
      >
        <header class="mb-5 flex items-start justify-between gap-4">
          <div class="min-w-0">
            <DialogTitle class="text-lg font-semibold text-[var(--text)]">
              {{ title }}
            </DialogTitle>
            <DialogDescription v-if="description" class="mt-1 text-sm text-[var(--text-muted)]">
              {{ description }}
            </DialogDescription>
          </div>
          <button
            type="button"
            data-action="close-dialog"
            class="btn-ghost -mr-2 -mt-2 h-11 w-11 shrink-0 !p-0 text-xl leading-none"
            :disabled="closeDisabled"
            aria-label="关闭对话框"
            @click="requestClose"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div>
          <slot />
        </div>

        <footer v-if="$slots.footer" class="mt-6 flex flex-wrap justify-end gap-2">
          <slot name="footer" />
        </footer>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
