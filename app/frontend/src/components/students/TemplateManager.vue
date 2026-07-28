<script setup lang="ts">
import { computed } from 'vue'
import type { Student, Template } from '@/api/types'

const props = defineProps<{
  students: Student[]
  selectedStudentId: number | null
  templates: Template[]
}>()

const emit = defineEmits<{
  (e: 'select-student', value: number): void
  (e: 'edit-template', template: Template): void
  (e: 'add-template'): void
}>()

const weekdayOptions = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const selectedStudent = computed(
  () => props.students.find((student) => student.id === props.selectedStudentId) ?? null
)
</script>

<template>
  <section class="glass p-4 md:p-5">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold">周课表模板</h2>
        <p class="text-xs text-[var(--text-dim)]">固定重复课程，自动生成课时</p>
      </div>
      <button class="btn-primary btn-sm" @click="emit('add-template')">+ 新增模板</button>
    </div>

    <div v-if="selectedStudent" class="space-y-2.5">
      <article
        v-for="template in templates"
        :key="template.id"
        class="rounded-2xl border border-white/35 bg-white/45 p-3.5 dark:border-white/8 dark:bg-white/5"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-semibold">
              {{ weekdayOptions[template.day_of_week] }} {{ template.start_time }}
            </p>
            <p class="mt-0.5 text-xs text-[var(--text-dim)]">
              {{ template.duration_hours }}h · {{ template.effective_from }}
              <span v-if="template.effective_to"> ~ {{ template.effective_to }}</span>
            </p>
          </div>
          <div class="flex gap-1.5">
            <button class="btn-ghost btn-sm" @click="emit('edit-template', template)">编辑</button>
          </div>
        </div>
      </article>
      <div
        v-if="!templates.length"
        class="rounded-xl border border-dashed border-white/30 px-3 py-6 text-center text-xs text-[var(--text-dim)] dark:border-white/8"
      >
        暂无模板
      </div>
    </div>
  </section>
</template>
