<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { templatesApi } from '@/api/templates'
import type { Student, Template } from '@/api/types'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  mode: 'create' | 'edit'
  students: Student[]
  selectedStudentId: number | null
  template: Template | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh-templates'): void
}>()

const weekdayOptions = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const studentId = ref(0)
const dayOfWeek = ref(0)
const startTime = ref('16:00')
const durationHours = ref(1)
const effectiveFrom = ref(new Date().toISOString().slice(0, 10))
const effectiveTo = ref('')
const repeatInterval = ref(1)
const applyMode = ref<'future_only' | 'from_date' | 'template_only' | 'update_all'>('future_only')
const applyFromDate = ref('')

const saving = ref(false)
const message = ref('')
const error = ref('')
const toast = useToast()

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

watch(
  () => props.selectedStudentId,
  (value) => {
    if (value && props.mode === 'create') studentId.value = value
  },
  { immediate: true }
)

watch(
  () => props.template,
  (t) => {
    if (!t || props.mode !== 'edit') return
    dayOfWeek.value = t.day_of_week
    startTime.value = t.start_time
    durationHours.value = t.duration_hours
    effectiveFrom.value = t.effective_from
    effectiveTo.value = t.effective_to ?? ''
    repeatInterval.value = (t as any).repeat_interval || 1
    applyMode.value = 'future_only'
    applyFromDate.value = t.effective_from
    message.value = ''
    error.value = ''
  },
  { immediate: true }
)

async function createTemplate() {
  if (!studentId.value) return
  saving.value = true
  error.value = ''
  try {
    await templatesApi.create({
      student_id: studentId.value,
      day_of_week: dayOfWeek.value,
      start_time: startTime.value,
      duration_hours: durationHours.value,
      effective_from: effectiveFrom.value,
      effective_to: effectiveTo.value || null,
      repeat_interval: repeatInterval.value,
    })
    toast.show('模板已创建')
    emit('refresh-templates')
    emit('close')
  } catch {
    error.value = '保存失败'
  } finally {
    saving.value = false
  }
}

async function updateTemplate() {
  if (!props.template) return
  saving.value = true
  error.value = ''
  try {
    await templatesApi.update(props.template.id, {
      day_of_week: dayOfWeek.value,
      start_time: startTime.value,
      duration_hours: durationHours.value,
      effective_from: effectiveFrom.value,
      effective_to: effectiveTo.value || null,
      repeat_interval: repeatInterval.value,
      apply_mode: applyMode.value,
      apply_from_date: applyMode.value === 'from_date' ? applyFromDate.value : undefined,
    })
    message.value = '模板已更新'
    toast.show('模板已更新')
    emit('refresh-templates')
  } catch {
    error.value = '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeTemplate() {
  if (!props.template) return
  if (!window.confirm('删除模板后将取消所有未来待上课时，确定继续？')) return
  try {
    await templatesApi.remove(props.template.id, true)
    toast.show('模板已删除')
    emit('refresh-templates')
    emit('close')
  } catch {
    error.value = '删除失败'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="emit('close')">
      <div class="fixed inset-0 bg-black/30 modal-backdrop" />
      <div class="modal-panel glass-strong relative z-10 max-h-[85vh] w-full max-w-md overflow-y-auto p-6">
        <button class="absolute right-4 top-4 text-[var(--text-dim)] hover:text-[var(--text)]" @click="emit('close')">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>

        <h2 class="text-base font-semibold">{{ mode === 'create' ? '新增模板' : '编辑模板' }}</h2>
        <p class="text-xs text-[var(--text-dim)]">{{ mode === 'create' ? '添加固定重复课程模板' : '修改后从今天起重建未来课时' }}</p>

        <form
          class="mt-4 grid gap-3.5 md:grid-cols-2"
          @submit.prevent="mode === 'create' ? createTemplate() : updateTemplate()"
        >
          <label class="block">
            <span class="label">学生</span>
            <select v-model.number="studentId" class="input" :disabled="mode === 'edit'" required>
              <option v-for="s in students" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </label>
          <label class="block">
            <span class="label">星期</span>
            <select v-model.number="dayOfWeek" class="input">
              <option v-for="(label, index) in weekdayOptions" :key="label" :value="index">{{ label }}</option>
            </select>
          </label>
          <label class="block">
            <span class="label">开始时间</span>
            <input v-model="startTime" class="input" type="time" required />
          </label>
          <label class="block">
            <span class="label">课时</span>
            <select v-model.number="durationHours" class="input">
              <option :value="0.5">0.5 小时</option>
              <option :value="1">1 小时</option>
              <option :value="1.5">1.5 小时</option>
            </select>
          </label>
          <label class="block">
            <span class="label">重复间隔</span>
            <select v-model.number="repeatInterval" class="input">
              <option :value="1">每周</option>
              <option :value="2">隔周 (单双周)</option>
              <option :value="3">每3周</option>
              <option :value="4">每4周</option>
            </select>
          </label>
          <label class="block">
            <span class="label">生效日期</span>
            <input v-model="effectiveFrom" class="input" type="date" required />
          </label>
          <label class="block">
            <span class="label">结束日期</span>
            <input v-model="effectiveTo" class="input" type="date" />
          </label>

          <template v-if="mode === 'edit'">
            <label class="block">
              <span class="label">应用方式</span>
              <select v-model="applyMode" class="input">
                <option value="future_only">从今天起重建未来课时</option>
                <option value="from_date">指定日期重建</option>
                <option value="template_only">仅更新模板</option>
                <option value="update_all">更新所有未来课时</option>
              </select>
            </label>
            <label v-if="applyMode === 'from_date'" class="block">
              <span class="label">起始日期</span>
              <input v-model="applyFromDate" class="input" type="date" required />
            </label>
          </template>

          <div class="md:col-span-2 flex flex-wrap gap-2">
            <button class="btn-primary btn-sm" :disabled="saving">{{ saving ? '保存中...' : mode === 'create' ? '保存模板' : '保存修改' }}</button>
            <button v-if="mode === 'edit'" class="btn-danger btn-sm" type="button" @click="removeTemplate">删除模板</button>
          </div>
        </form>

        <p v-if="message" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ message }}</p>
        <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>
