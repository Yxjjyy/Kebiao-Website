<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { templatesApi } from '@/api/templates'
import type { Student, Template } from '@/api/types'
import AppDialog from '@/components/ui/AppDialog.vue'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { useToast } from '@/composables/useToast'
import { parseFormError } from '@/lib/formError'

const props = defineProps<{ mode: 'create' | 'edit'; students: Student[]; selectedStudentId: number | null; template: Template | null }>()
const emit = defineEmits<{ close: []; 'refresh-templates': [] }>()
const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const studentId = ref(0), dayOfWeek = ref(0), startTime = ref('16:00'), durationHours = ref(1)
const effectiveFrom = ref(new Date().toISOString().slice(0, 10)), effectiveTo = ref(''), repeatInterval = ref(1)
const applyMode = ref<'future_only' | 'from_date' | 'template_only' | 'update_all'>('future_only'), applyFromDate = ref('')
const saving = ref(false), deleting = ref(false), confirmDeleteOpen = ref(false), message = ref(''), error = ref('')
const toast = useToast()
const busy = computed(() => saving.value || deleting.value)

watch(() => props.selectedStudentId, value => { if (value && props.mode === 'create') studentId.value = value }, { immediate: true })
watch(() => props.template, (template) => {
  if (!template || props.mode !== 'edit') return
  studentId.value = template.student_id; dayOfWeek.value = template.day_of_week; startTime.value = template.start_time.slice(0, 5)
  durationHours.value = template.duration_hours; effectiveFrom.value = template.effective_from; effectiveTo.value = template.effective_to ?? ''
  repeatInterval.value = template.repeat_interval || 1; applyMode.value = 'future_only'; applyFromDate.value = template.effective_from
  message.value = ''; error.value = ''; confirmDeleteOpen.value = false
}, { immediate: true })

async function save() {
  if (busy.value || !studentId.value) return
  saving.value = true; message.value = ''; error.value = ''
  try {
    if (props.mode === 'create') {
      await templatesApi.create({ student_id: studentId.value, day_of_week: dayOfWeek.value, start_time: startTime.value, duration_hours: durationHours.value, effective_from: effectiveFrom.value, effective_to: effectiveTo.value || null, repeat_interval: repeatInterval.value })
      toast.show('模板已创建'); emit('refresh-templates'); emit('close')
    } else if (props.template) {
      await templatesApi.update(props.template.id, { day_of_week: dayOfWeek.value, start_time: startTime.value, duration_hours: durationHours.value, effective_from: effectiveFrom.value, effective_to: effectiveTo.value || null, repeat_interval: repeatInterval.value, apply_mode: applyMode.value, apply_from_date: applyMode.value === 'from_date' ? applyFromDate.value : undefined })
      message.value = '模板已更新'; toast.show(message.value); emit('refresh-templates')
    }
  } catch (err) { error.value = parseFormError(err, '保存失败，请稍后再试') }
  finally { saving.value = false }
}

async function removeTemplate() {
  if (!props.template || busy.value) return
  deleting.value = true; message.value = ''; error.value = ''
  try { await templatesApi.remove(props.template.id, true); toast.show('模板已删除'); confirmDeleteOpen.value = false; emit('refresh-templates'); emit('close') }
  catch (err) { error.value = parseFormError(err, '删除失败，请稍后再试') }
  finally { deleting.value = false }
}
</script>

<template>
  <AppDialog :open="true" :title="mode === 'create' ? '新增模板' : '编辑模板'" :description="mode === 'create' ? '添加固定重复课程模板' : '设置模板及其未来课程的更新范围'" :close-disabled="busy" @close="emit('close')">
    <form class="grid gap-3.5 md:grid-cols-2" @submit.prevent="save">
      <FormField for-id="template-student" label="学生" required><template #default="{ describedby }"><select id="template-student" v-model.number="studentId" class="input" :disabled="mode === 'edit' || busy" required :aria-describedby="describedby || undefined"><option disabled value="0">请选择学生</option><option v-for="student in students" :key="student.id" :value="student.id">{{ student.name }}</option></select></template></FormField>
      <FormField for-id="template-weekday" label="星期"><template #default="{ describedby }"><select id="template-weekday" v-model.number="dayOfWeek" class="input" :disabled="busy" :aria-describedby="describedby || undefined"><option v-for="(label, index) in weekdays" :key="label" :value="index">{{ label }}</option></select></template></FormField>
      <FormField for-id="template-time" label="开始时间" required><template #default="{ describedby }"><input id="template-time" v-model="startTime" class="input" type="time" required :disabled="busy" :aria-describedby="describedby || undefined" /></template></FormField>
      <FormField for-id="template-duration" label="课时"><template #default="{ describedby }"><select id="template-duration" v-model.number="durationHours" class="input" :disabled="busy" :aria-describedby="describedby || undefined"><option :value="0.5">0.5 小时</option><option :value="1">1 小时</option><option :value="1.5">1.5 小时</option></select></template></FormField>
      <FormField for-id="template-interval" label="重复间隔"><template #default="{ describedby }"><select id="template-interval" v-model.number="repeatInterval" class="input" :disabled="busy" :aria-describedby="describedby || undefined"><option :value="1">每周</option><option :value="2">隔周（单双周）</option><option :value="3">每 3 周</option><option :value="4">每 4 周</option></select></template></FormField>
      <FormField for-id="template-from" label="生效日期" required><template #default="{ describedby }"><input id="template-from" v-model="effectiveFrom" class="input" type="date" required :disabled="busy" :aria-describedby="describedby || undefined" /></template></FormField>
      <FormField for-id="template-to" label="结束日期" hint="留空表示长期有效"><template #default="{ describedby }"><input id="template-to" v-model="effectiveTo" class="input" type="date" :disabled="busy" :aria-describedby="describedby || undefined" /></template></FormField>
      <template v-if="mode === 'edit'">
        <FormField for-id="template-apply" label="应用方式" class="md:col-span-2"><template #default="{ describedby }"><select id="template-apply" v-model="applyMode" class="input" :disabled="busy" :aria-describedby="describedby || undefined"><option value="future_only">从今天起重建未来课时</option><option value="from_date">指定日期重建</option><option value="template_only">仅更新模板</option><option value="update_all">更新所有未来课时</option></select></template></FormField>
        <FormField v-if="applyMode === 'from_date'" for-id="template-apply-from" label="起始日期" required class="md:col-span-2"><template #default="{ describedby }"><input id="template-apply-from" v-model="applyFromDate" class="input" type="date" required :disabled="busy" :aria-describedby="describedby || undefined" /></template></FormField>
      </template>
      <InlineAlert v-if="message" class="md:col-span-2" tone="success" :message="message" /><InlineAlert v-if="error" class="md:col-span-2" tone="error" :message="error" />
      <div class="md:col-span-2 flex flex-wrap gap-2"><AsyncButton :pending="saving" :disabled="busy" pending-label="保存中…">{{ mode === 'create' ? '保存模板' : '保存修改' }}</AsyncButton><button v-if="mode === 'edit'" type="button" data-action="delete-template" class="btn-danger" :disabled="busy" @click="confirmDeleteOpen = true">删除模板</button></div>
    </form>
  </AppDialog>
  <ConfirmDialog v-model:open="confirmDeleteOpen" title="删除这个课程模板？" description="删除模板后将取消所有未来待上课时，此操作不可撤销。" confirm-label="删除模板" :pending="deleting" pending-label="删除中…" @confirm="removeTemplate" />
</template>
