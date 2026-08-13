<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { Student } from '@/api/types'
import { studentsApi } from '@/api/students'
import AppDialog from '@/components/ui/AppDialog.vue'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { useToast } from '@/composables/useToast'
import { parseFormError } from '@/lib/formError'

const props = defineProps<{ mode: 'create' | 'edit'; student: Student | null; currencySymbol: string }>()
const emit = defineEmits<{ close: []; refresh: [] }>()
const colors = ['#4C7DFF','#FF6B9D','#10B981','#F59E0B','#8B5CF6','#EF4444','#06B6D4','#F97316']
const form = reactive({ name: '', color: '#4C7DFF', hourly_rate: 300, phone: '', note: '' })
const saving = ref(false)
const archiving = ref(false)
const message = ref('')
const error = ref('')
const recalcMode = ref('today')
const originalRate = ref(0)
const toast = useToast()
const busy = computed(() => saving.value || archiving.value)
const rateChanged = computed(() => props.mode === 'edit' && form.hourly_rate !== originalRate.value)

watch(() => [props.student, props.mode] as const, ([student, mode]) => {
  if (mode === 'create') {
    Object.assign(form, { name: '', color: '#4C7DFF', hourly_rate: 300, phone: '', note: '' })
    return
  }
  if (!student) return
  Object.assign(form, { name: student.name, color: student.color, hourly_rate: student.hourly_rate, phone: student.phone ?? '', note: student.note ?? '' })
  originalRate.value = student.hourly_rate
  recalcMode.value = 'today'; message.value = ''; error.value = ''
}, { immediate: true })

async function save() {
  if (busy.value) return
  saving.value = true; message.value = ''; error.value = ''
  const data = { name: form.name, color: form.color, hourly_rate: form.hourly_rate, phone: form.phone || null, note: form.note || null }
  try {
    if (props.mode === 'create') {
      await studentsApi.create(data); toast.show('学生已创建'); emit('refresh'); emit('close')
    } else if (props.student) {
      const result = await studentsApi.update(props.student.id, data, rateChanged.value ? recalcMode.value : 'none')
      message.value = result.affected_future_lessons > 0 ? `已保存，未来 ${result.affected_future_lessons} 节待上课价格已重算` : '已保存'
      originalRate.value = form.hourly_rate; toast.show('学生信息已保存'); emit('refresh')
    }
  } catch (err) { error.value = parseFormError(err, '保存失败，请稍后再试') }
  finally { saving.value = false }
}

async function toggleArchive() {
  if (!props.student || busy.value) return
  archiving.value = true; message.value = ''; error.value = ''
  try {
    if (props.student.archived) await studentsApi.unarchive(props.student.id)
    else await studentsApi.archive(props.student.id)
    message.value = props.student.archived ? '已取消归档' : '已归档'
    toast.show(message.value); emit('refresh')
  } catch (err) { error.value = parseFormError(err) }
  finally { archiving.value = false }
}
</script>

<template>
  <AppDialog :open="true" :title="mode === 'create' ? '新增学生' : '编辑学生'" :description="mode === 'create' ? '添加新学生' : '修改学生资料与单价'" :close-disabled="busy" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="save">
      <FormField for-id="student-name" label="姓名" required><template #default="{ describedby }"><input id="student-name" v-model="form.name" class="input" maxlength="64" required :aria-describedby="describedby || undefined" /></template></FormField>
      <div class="grid gap-3.5 md:grid-cols-2">
        <FormField for-id="student-rate" :label="`小时单价（${currencySymbol}）`" required><template #default="{ describedby }"><input id="student-rate" v-model.number="form.hourly_rate" class="input" min="0" type="number" required :aria-describedby="describedby || undefined" /></template></FormField>
        <FormField for-id="student-color" label="颜色"><template #default="{ describedby }"><div class="mb-2 flex flex-wrap gap-2"><button v-for="color in colors" :key="color" type="button" class="h-11 w-11 rounded-full border-2" :class="form.color === color ? 'border-[var(--text)] shadow-md' : 'border-transparent'" :style="{ background: color }" :aria-label="`选择颜色 ${color}`" @click="form.color = color" /></div><input id="student-color" v-model="form.color" class="h-11 w-full rounded-2xl border border-white/40 bg-transparent px-2 dark:border-white/10" type="color" :aria-describedby="describedby || undefined" /></template></FormField>
      </div>
      <InlineAlert v-if="rateChanged" tone="warning" message="单价已变更，请选择未来课程价格的处理方式。" />
      <FormField v-if="rateChanged" for-id="student-recalc" label="价格变动处理方式"><template #default="{ describedby }"><select id="student-recalc" v-model="recalcMode" class="input" :aria-describedby="describedby || undefined"><option value="today">从当前课时重算</option><option value="tomorrow">从下一节开始</option><option value="none">仅修改单价</option></select></template></FormField>
      <FormField for-id="student-phone" label="电话"><template #default="{ describedby }"><input id="student-phone" v-model="form.phone" class="input" type="tel" :aria-describedby="describedby || undefined" /></template></FormField>
      <FormField for-id="student-note" label="备注"><template #default="{ describedby }"><textarea id="student-note" v-model="form.note" class="input min-h-24 resize-y" :aria-describedby="describedby || undefined" /></template></FormField>
      <InlineAlert v-if="message" tone="success" :message="message" /><InlineAlert v-if="error" tone="error" :message="error" />
      <div class="flex flex-wrap gap-2">
        <AsyncButton data-action="save-student" :pending="saving" :disabled="busy" pending-label="保存中…">{{ mode === 'create' ? '保存学生' : '保存修改' }}</AsyncButton>
        <AsyncButton v-if="mode === 'edit'" type="button" data-action="toggle-archive" tone="ghost" :pending="archiving" :disabled="busy" pending-label="处理中…" @click="toggleArchive">{{ student?.archived ? '取消归档' : '归档' }}</AsyncButton>
      </div>
    </form>
  </AppDialog>
</template>
