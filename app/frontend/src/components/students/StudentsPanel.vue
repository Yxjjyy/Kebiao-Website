<script setup lang="ts">
import type { Student } from '@/api/types'
import { formatCurrency } from '@/lib/format'

defineProps<{
  students: Student[]
  currencySymbol: string
  selectedStudentId: number | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'select-student', value: number): void
  (e: 'add-student'): void
}>()
</script>

<template>
  <section class="glass p-4 md:p-5">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold">学生列表</h2>
        <p class="text-xs text-[var(--text-dim)]">管理学生资料与单价</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="badge-info">{{ students.length }} 位</span>
        <button class="btn-primary btn-sm" @click="emit('add-student')">+ 新增学生</button>
      </div>
    </div>

    <div class="grid gap-2.5 md:grid-cols-2">
      <article
        v-for="student in students"
        :key="student.id"
        :class="[
          'cursor-pointer rounded-2xl border bg-white/45 p-3.5 transition-all duration-150 dark:border-white/8 dark:bg-white/5',
          student.id === selectedStudentId
            ? 'border-[var(--accent)] shadow-[0_0_0_3px_rgba(76,125,255,0.12)]'
            : 'border-white/35 hover:border-white/60 dark:hover:border-white/12',
        ]"
        @click="emit('select-student', student.id)"
      >
        <div class="flex items-start gap-3">
          <span class="mt-1 h-3 w-3 shrink-0 rounded-full" :style="{ background: student.color }" />
          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-2">
              <p class="text-sm font-semibold truncate">{{ student.name }}</p>
              <span :class="student.archived ? 'badge-muted' : 'badge-success'" class="text-[10px]">
                {{ student.archived ? '归档' : '活跃' }}
              </span>
            </div>
            <p class="mt-1 text-xs text-[var(--text-dim)]">
              {{ formatCurrency(student.hourly_rate, currencySymbol) }}/h
              <span v-if="student.phone" class="ml-2 opacity-60">{{ student.phone }}</span>
            </p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
