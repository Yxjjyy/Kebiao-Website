<script setup lang="ts">
import { ref } from 'vue'
import type { AppError } from '@/api/error'
import InlineAlert from './InlineAlert.vue'

defineProps<{ error: AppError }>()
defineEmits<{ (event: 'retry'): void }>()

const expanded = ref(false)

function detailText(detail: unknown): string {
  if (typeof detail === 'string') return detail
  try {
    return JSON.stringify(detail)
  } catch {
    return String(detail)
  }
}
</script>

<template>
  <InlineAlert tone="error" :message="error.message">
    <template #action>
      <div class="flex shrink-0 items-center gap-2">
        <button
          type="button"
          data-action="toggle-error-details"
          class="text-[11px] font-extrabold hover:underline"
          :aria-expanded="expanded"
          @click="expanded = !expanded"
        >{{ expanded ? '收起详情' : '查看详情' }}</button>
        <button
          v-if="error.retryable"
          type="button"
          data-action="retry-error"
          class="text-[11px] font-extrabold hover:underline"
          @click="$emit('retry')"
        >重新加载</button>
      </div>
    </template>
  </InlineAlert>
  <dl
    v-if="expanded"
    class="mt-2 grid gap-x-4 gap-y-1 rounded-xl border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-[10px] text-[var(--text-dim)] sm:grid-cols-[auto_1fr]"
  >
    <dt>错误类型</dt><dd>{{ error.kind }}</dd>
    <template v-if="error.status"><dt>状态码</dt><dd>{{ error.status }}</dd></template>
    <template v-if="error.requestId"><dt>请求编号</dt><dd class="break-all">{{ error.requestId }}</dd></template>
    <template v-if="error.detail !== undefined"><dt>服务端信息</dt><dd class="break-all">{{ detailText(error.detail) }}</dd></template>
  </dl>
</template>
