<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Student } from '@/api/types'
import { formatCurrency } from '@/lib/format'
import { filterStudents } from '@/lib/studentWorkspace'

const props = defineProps<{
  students: Student[]
  currencySymbol: string
  selectedStudentId: number | null
}>()

const emit = defineEmits<{
  (e: 'select-student', value: number): void
  (e: 'edit-student', value: number): void
  (e: 'add-student'): void
}>()

const query = ref('')
const filteredStudents = computed(() => filterStudents(props.students, query.value))
</script>

<template>
  <section class="glass-strong overflow-hidden p-4 lg:sticky lg:top-2">
    <header class="flex items-start justify-between gap-3">
      <div>
        <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-dim)]">Student directory</p>
        <h1 class="mt-1 text-xl font-extrabold tracking-[-0.04em]">学生管理</h1>
        <p class="mt-1 text-xs text-[var(--text-dim)]">{{ students.length }} 位活跃学生</p>
      </div>
      <button class="btn-primary min-h-11 !rounded-2xl !px-3 text-xs" @click="emit('add-student')">
        <span class="text-lg leading-none">＋</span> 新增
      </button>
    </header>

    <label class="relative mt-4 block">
      <span class="sr-only">搜索学生</span>
      <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-dim)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <circle cx="11" cy="11" r="7" />
        <path d="m16.5 16.5 4 4" stroke-linecap="round" />
      </svg>
      <input
        v-model="query"
        data-testid="student-search"
        class="input min-h-11 !rounded-2xl !pl-10 !text-sm"
        placeholder="搜索姓名或电话号码"
        type="search"
      />
    </label>

    <div class="mt-3 max-h-[calc(100vh-245px)] space-y-2 overflow-y-auto pr-1 lg:min-h-64">
      <article
        v-for="student in filteredStudents"
        :key="student.id"
        :class="[
          'group relative overflow-hidden rounded-[18px] border transition-all duration-200',
          student.id === selectedStudentId
            ? 'border-[var(--accent)]/20 bg-[var(--accent-soft)] shadow-[0_9px_24px_rgba(80,47,105,.08)]'
            : 'border-white/70 bg-white/55 hover:bg-white/80 dark:border-white/8 dark:bg-white/5',
        ]"
      >
        <button
          data-testid="student-card"
          class="flex min-h-[74px] w-full items-center gap-3 px-3 py-2.5 pr-12 text-left"
          :aria-current="student.id === selectedStudentId ? 'true' : undefined"
          @click="emit('select-student', student.id)"
        >
          <span
            class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl text-sm font-extrabold text-white shadow-sm"
            :style="{ background: `linear-gradient(145deg, ${student.color}, ${student.color}bb)` }"
          >
            {{ student.name.charAt(0) }}
          </span>
          <span class="min-w-0 flex-1">
            <span class="flex items-center gap-2">
              <b class="truncate text-sm">{{ student.name }}</b>
              <i class="h-1.5 w-1.5 shrink-0 rounded-full" :class="student.archived ? 'bg-slate-400' : 'bg-emerald-500'" />
            </span>
            <span class="mt-1 block truncate text-[11px] text-[var(--text-dim)]">
              {{ formatCurrency(student.hourly_rate, currencySymbol) }}/小时
              <template v-if="student.phone"> · {{ student.phone }}</template>
            </span>
          </span>
        </button>
        <button
          data-testid="edit-student"
          class="absolute right-2.5 top-1/2 grid h-10 w-9 -translate-y-1/2 place-items-center rounded-xl text-[var(--text-dim)] transition-colors hover:bg-white/70 hover:text-[var(--accent)] dark:hover:bg-white/10"
          :aria-label="`编辑 ${student.name}`"
          @click.stop="emit('edit-student', student.id)"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z" stroke-linejoin="round" />
            <path d="m14 7 3 3" />
          </svg>
        </button>
      </article>

      <div v-if="!filteredStudents.length" class="rounded-[20px] border border-dashed border-[var(--line)] px-4 py-8 text-center">
        <p class="text-sm font-semibold">{{ query ? '没有找到匹配的学生' : '还没有学生' }}</p>
        <p class="mt-1 text-xs text-[var(--text-dim)]">{{ query ? '试试其他姓名或电话号码' : '新增第一位学生开始排课' }}</p>
        <button v-if="query" class="mt-3 text-xs font-semibold text-[var(--accent)]" @click="query = ''">清除搜索</button>
      </div>
    </div>
  </section>
</template>
