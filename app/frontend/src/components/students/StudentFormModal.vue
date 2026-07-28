<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import type { Student } from '@/api/types'
import { studentsApi } from '@/api/students'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  mode: 'create' | 'edit'
  student: Student | null
  currencySymbol: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh'): void
}>()

const form = reactive({
  name: '',
  color: '#4C7DFF',
  hourly_rate: 300,
  phone: '',
  note: '',
})

const saving = ref(false)
const updating = ref(false)
const message = ref('')
const error = ref('')
const recalcMode = ref('today')
const showRecalcOptions = ref(false)
const originalRate = ref(0)
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
  () => props.student,
  (student) => {
    if (!student || props.mode !== 'edit') return
    form.name = student.name
    form.color = student.color
    form.hourly_rate = student.hourly_rate
    form.phone = student.phone ?? ''
    form.note = student.note ?? ''
    originalRate.value = student.hourly_rate
    message.value = ''
    error.value = ''
    showRecalcOptions.value = false
    recalcMode.value = 'today'
  },
  { immediate: true }
)

function onRateChange() {
  if (props.mode === 'edit' && form.hourly_rate !== originalRate.value) {
    showRecalcOptions.value = true
  } else {
    showRecalcOptions.value = false
  }
}

async function submit() {
  saving.value = true
  error.value = ''
  try {
    await studentsApi.create({
      name: form.name,
      color: form.color,
      hourly_rate: form.hourly_rate,
      phone: form.phone || null,
      note: form.note || null,
    })
    toast.show('学生已创建')
    emit('refresh')
    emit('close')
  } catch (err) {
    error.value = '保存失败，请稍后再试'
  } finally {
    saving.value = false
  }
}

async function updateStudent() {
  if (!props.student) return
  message.value = ''
  error.value = ''
  updating.value = true
  try {
    const mode = form.hourly_rate !== originalRate.value ? recalcMode.value : 'none'
    const result = await studentsApi.update(props.student.id, {
      name: form.name,
      color: form.color,
      hourly_rate: form.hourly_rate,
      phone: form.phone || null,
      note: form.note || null,
    }, mode)
    message.value =
      result.affected_future_lessons > 0
        ? `已保存，未来 ${result.affected_future_lessons} 节待上课价格已重算`
        : '已保存'
    toast.show('学生信息已保存')
    emit('refresh')
  } catch (err) {
    error.value = '保存失败，请稍后再试'
  } finally {
    updating.value = false
  }
}

async function toggleArchive() {
  if (!props.student) return
  updating.value = true
  try {
    if (props.student.archived) {
      await studentsApi.unarchive(props.student.id)
    } else {
      await studentsApi.archive(props.student.id)
    }
    message.value = props.student.archived ? '已取消归档' : '已归档'
    toast.show(props.student.archived ? '已取消归档' : '已归档')
    emit('refresh')
  } catch {
    error.value = '操作失败'
  } finally {
    updating.value = false
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

        <h2 class="text-base font-semibold">{{ mode === 'create' ? '新增学生' : '编辑学生' }}</h2>
        <p class="text-xs text-[var(--text-dim)]">{{ mode === 'create' ? '添加新学生' : '修改学生资料与单价' }}</p>

        <form class="mt-4 space-y-3.5" @submit.prevent="mode === 'create' ? submit() : updateStudent()">
          <label class="block">
            <span class="label">姓名</span>
            <input v-model="form.name" class="input" maxlength="64" required />
          </label>
          <div class="grid gap-3.5 md:grid-cols-2">
            <label class="block">
              <span class="label">小时单价</span>
              <input v-model.number="form.hourly_rate" class="input" min="0" type="number" required @input="onRateChange" />
            </label>
            <label class="block">
              <span class="label">颜色</span>
              <div class="mb-1.5 flex flex-wrap gap-1.5">
                <button v-for="c in ['#4C7DFF','#FF6B9D','#10B981','#F59E0B','#8B5CF6','#EF4444','#06B6D4','#F97316']" :key="c" type="button" class="h-7 w-7 rounded-full border-2 transition-transform hover:scale-110" :class="form.color === c ? 'border-white scale-110 shadow-md' : 'border-transparent'" :style="{ background: c }" @click="form.color = c" />
              </div>
              <input v-model="form.color" class="h-11 w-full rounded-2xl border border-white/40 bg-transparent px-2 dark:border-white/10" type="color" />
            </label>
          </div>

          <div v-if="showRecalcOptions" class="rounded-2xl border border-amber-400/30 bg-amber-400/5 p-3">
            <p class="text-xs font-semibold text-amber-700 dark:text-amber-300">价格变动处理方式</p>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <button type="button" :class="['rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors', recalcMode === 'today' ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300' : 'bg-white/30 text-[var(--text-dim)]']" @click="recalcMode = 'today'">从当前课时重算</button>
              <button type="button" :class="['rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors', recalcMode === 'tomorrow' ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300' : 'bg-white/30 text-[var(--text-dim)]']" @click="recalcMode = 'tomorrow'">从下一节开始</button>
              <button type="button" :class="['rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors', recalcMode === 'none' ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300' : 'bg-white/30 text-[var(--text-dim)]']" @click="recalcMode = 'none'">仅修改单价</button>
            </div>
          </div>

          <label class="block">
            <span class="label">电话</span>
            <input v-model="form.phone" class="input" />
          </label>
          <label class="block">
            <span class="label">备注</span>
            <textarea v-model="form.note" class="input min-h-24 resize-y" />
          </label>
          <div v-if="mode === 'edit'" class="flex flex-wrap gap-2">
            <button class="btn-primary btn-sm" :disabled="updating">{{ updating ? '保存中...' : '保存修改' }}</button>
            <button class="btn-ghost btn-sm" type="button" @click="toggleArchive">
              {{ student?.archived ? '取消归档' : '归档' }}
            </button>
          </div>
          <button v-else class="btn-primary w-full" :disabled="saving">{{ saving ? '保存中...' : '保存学生' }}</button>
        </form>

        <p v-if="message" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ message }}</p>
        <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>
