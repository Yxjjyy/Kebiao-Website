<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', mode: '1' | '2' | '3'): void
}>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="emit('close')"
    >
      <div class="fixed inset-0 bg-black/30 modal-backdrop" />
      <div class="modal-panel glass-strong relative z-10 w-full max-w-xs p-6 text-center">
        <h2 class="text-base font-semibold">选择调课范围</h2>
        <p class="mt-1 text-xs text-[var(--text-dim)]">确定将课程移动到新时间的方式</p>
        <div class="mt-5 flex flex-col gap-2">
          <button class="btn-primary btn-sm w-full justify-center" @click="emit('select', '1')">
            仅移动本次
          </button>
          <button class="btn-ghost btn-sm w-full justify-center" @click="emit('select', '2')">
            本次及以后全部移动
          </button>
          <button class="btn-ghost btn-sm w-full justify-center" @click="emit('select', '3')">
            修改周课表模板
          </button>
        </div>
        <button class="mt-4 text-xs text-[var(--text-dim)] hover:text-[var(--text)]" @click="emit('close')">取消</button>
      </div>
    </div>
  </Teleport>
</template>
