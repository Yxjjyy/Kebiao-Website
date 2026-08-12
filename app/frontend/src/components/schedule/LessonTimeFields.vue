<script setup lang="ts">
import FormField from '@/components/ui/FormField.vue'

withDefaults(defineProps<{
  date: string
  startTime: string
  durationHours: number
  dateLabel?: string
  timeLabel?: string
  durationLabel?: string
  idPrefix?: string
}>(), {
  dateLabel: '日期',
  timeLabel: '开始时间',
  durationLabel: '课时',
  idPrefix: 'lesson',
})

const emit = defineEmits<{
  'update:date': [value: string]
  'update:startTime': [value: string]
  'update:durationHours': [value: number]
}>()
</script>

<template>
  <div class="grid gap-3.5 md:grid-cols-2">
    <FormField :for-id="`${idPrefix}-date`" :label="dateLabel" required>
      <template #default="{ describedby }">
        <input
          :id="`${idPrefix}-date`"
          data-field="lesson-date"
          class="input"
          type="date"
          required
          :value="date"
          :aria-describedby="describedby || undefined"
          @input="emit('update:date', ($event.target as HTMLInputElement).value)"
        />
      </template>
    </FormField>
    <FormField :for-id="`${idPrefix}-start-time`" :label="timeLabel" required>
      <template #default="{ describedby }">
        <input
          :id="`${idPrefix}-start-time`"
          data-field="lesson-start-time"
          class="input"
          type="time"
          required
          :value="startTime"
          :aria-describedby="describedby || undefined"
          @input="emit('update:startTime', ($event.target as HTMLInputElement).value)"
        />
      </template>
    </FormField>
    <FormField :for-id="`${idPrefix}-duration`" :label="durationLabel" class="md:col-span-2">
      <template #default="{ describedby }">
        <select
          :id="`${idPrefix}-duration`"
          data-field="lesson-duration"
          class="input"
          :value="durationHours"
          :aria-describedby="describedby || undefined"
          @change="emit('update:durationHours', Number(($event.target as HTMLSelectElement).value))"
        >
          <option :value="0.5">0.5 小时</option>
          <option :value="1">1 小时</option>
          <option :value="1.5">1.5 小时</option>
        </select>
      </template>
    </FormField>
  </div>
</template>
