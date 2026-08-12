<script setup lang="ts">
import AppDialog from '@/components/ui/AppDialog.vue'

defineProps<{ visible: boolean }>()

const emit = defineEmits<{
  close: []
  select: [mode: '1' | '2' | '3']
}>()
</script>

<template>
  <AppDialog
    :open="visible"
    title="选择调课范围"
    description="确定将课程移动到新时间的方式"
    size="sm"
    @close="emit('close')"
  >
    <div class="flex flex-col gap-2">
      <button class="btn-primary min-h-11 w-full justify-center" @click="emit('select', '1')">仅移动本次</button>
      <button class="btn-ghost min-h-11 w-full justify-center" @click="emit('select', '2')">本次及以后全部移动</button>
      <button class="btn-ghost min-h-11 w-full justify-center" @click="emit('select', '3')">修改周课表模板</button>
    </div>
  </AppDialog>
</template>
