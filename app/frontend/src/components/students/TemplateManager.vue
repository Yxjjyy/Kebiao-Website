<script setup lang="ts">
import { computed } from 'vue'
import type { Student, Template } from '@/api/types'
import { formatHours } from '@/lib/format'
import { formatRepeatInterval, sortTemplates } from '@/lib/studentWorkspace'

const props = withDefaults(defineProps<{
  students: Student[]
  selectedStudentId: number | null
  templates: Template[]
  loading?: boolean
  error?: string
}>(), {
  loading: false,
  error: '',
})

const emit = defineEmits<{
  (e: 'edit-template', template: Template): void
  (e: 'add-template'): void
  (e: 'retry'): void
}>()

const weekdayOptions = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const selectedStudent = computed(
  () => props.students.find((student) => student.id === props.selectedStudentId) ?? null
)
const sortedTemplates = computed(() => sortTemplates(props.templates))
</script>

<template>
  <section class="glass-strong p-4 md:p-5">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-dim)]">Weekly rhythm</p>
        <h2 class="mt-1 text-lg font-extrabold tracking-[-0.03em]">固定课表</h2>
        <p class="mt-1 text-xs text-[var(--text-dim)]">
          {{ selectedStudent ? `${selectedStudent.name} · 自动生成未来课时` : '选择学生后管理固定课程' }}
        </p>
      </div>
      <button class="btn-primary min-h-11 !rounded-2xl text-xs" :disabled="!selectedStudent" @click="emit('add-template')">
        ＋ 新增模板
      </button>
    </header>

    <div v-if="loading" class="mt-4 grid animate-pulse gap-2.5 md:grid-cols-2 xl:grid-cols-3">
      <span v-for="index in 3" :key="index" class="h-28 rounded-[20px] bg-white/45 dark:bg-white/5" />
    </div>

    <div v-else-if="error" class="mt-4 rounded-[20px] border border-red-500/15 bg-red-500/5 px-4 py-6 text-center">
      <p class="text-sm font-semibold">{{ error }}</p>
      <p class="mt-1 text-xs text-[var(--text-dim)]">学生详情不受影响，可以单独重试。</p>
      <button data-action="retry-templates" class="btn-ghost btn-sm mt-3" @click="emit('retry')">重新加载</button>
    </div>

    <div v-else-if="!selectedStudent" class="mt-4 rounded-[20px] border border-dashed border-[var(--line)] px-4 py-8 text-center">
      <p class="text-sm font-semibold">先从左侧选择学生</p>
      <p class="mt-1 text-xs text-[var(--text-dim)]">选中后会显示对应的固定课程。</p>
    </div>

    <div v-else-if="sortedTemplates.length" class="mt-4 grid gap-2.5 md:grid-cols-2 xl:grid-cols-3">
      <button
        v-for="template in sortedTemplates"
        :key="template.id"
        data-testid="template-card"
        class="group relative min-h-28 overflow-hidden rounded-[20px] border border-white/75 bg-white/55 p-4 text-left transition-all hover:-translate-y-0.5 hover:bg-white/80 hover:shadow-[0_12px_28px_rgba(72,47,91,.09)] dark:border-white/8 dark:bg-white/5"
        @click="emit('edit-template', template)"
      >
        <span class="absolute right-3 top-3 rounded-full bg-[var(--accent-soft)] px-2 py-1 text-[10px] font-bold text-[var(--accent)]">
          {{ formatRepeatInterval(template.repeat_interval) }}
        </span>
        <span class="text-[11px] font-bold text-[var(--text-dim)]">{{ weekdayOptions[template.day_of_week] }}</span>
        <strong class="mt-1 block text-2xl tracking-[-0.05em]">{{ template.start_time.slice(0, 5) }}</strong>
        <span class="mt-2 block text-[11px] text-[var(--text-dim)]">{{ formatHours(template.duration_hours) }} · 点击编辑</span>
        <span class="mt-1 block text-[10px] text-[var(--text-dim)]">
          {{ template.effective_from }} — {{ template.effective_to || '长期有效' }}
        </span>
      </button>
    </div>

    <div v-else class="mt-4 flex min-h-40 flex-col items-center justify-center rounded-[20px] border border-dashed border-[var(--line)] px-4 text-center">
      <span class="grid h-11 w-11 place-items-center rounded-2xl bg-[var(--accent-soft)] text-lg text-[var(--accent)]">＋</span>
      <p class="mt-3 text-sm font-semibold">还没有固定课表</p>
      <p class="mt-1 text-xs text-[var(--text-dim)]">创建模板后，系统会自动生成未来课程。</p>
      <button data-action="add-empty-template" class="mt-3 text-xs font-bold text-[var(--accent)]" @click="emit('add-template')">创建第一个模板</button>
    </div>
  </section>
</template>
