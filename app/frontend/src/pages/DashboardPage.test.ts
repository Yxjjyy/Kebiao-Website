import { flushPromises, shallowMount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import StudentOverview from '@/components/students/StudentOverview.vue'
import StudentsPanel from '@/components/students/StudentsPanel.vue'
import TemplateManager from '@/components/students/TemplateManager.vue'
import StatsPanel from '@/components/stats/StatsPanel.vue'
import DashboardPage from './DashboardPage.vue'

const apiMocks = vi.hoisted(() => ({
  lessonsList: vi.fn(),
  studentsList: vi.fn(),
  studentGet: vi.fn(),
  statsToday: vi.fn(),
  statsRange: vi.fn(),
  statsComparison: vi.fn(),
  statsStudents: vi.fn(),
  statsLeave: vi.fn(),
  templatesList: vi.fn(),
}))

vi.mock('@/api/lessons', () => ({
  lessonsApi: { list: apiMocks.lessonsList },
}))

vi.mock('@/api/students', () => ({
  studentsApi: {
    list: apiMocks.studentsList,
    get: apiMocks.studentGet,
  },
}))

vi.mock('@/api/stats', () => ({
  statsApi: {
    today: apiMocks.statsToday,
    range: apiMocks.statsRange,
    comparison: apiMocks.statsComparison,
    students: apiMocks.statsStudents,
    leave: apiMocks.statsLeave,
  },
}))

vi.mock('@/api/templates', () => ({
  templatesApi: { list: apiMocks.templatesList },
}))

vi.mock('@/api/settings', () => ({
  settingsApi: {
    getSettings: vi.fn().mockRejectedValue(new Error('settings unavailable')),
    getProfile: vi.fn().mockRejectedValue(new Error('profile unavailable')),
  },
}))

const students = [
  {
    id: 1,
    name: '林晓',
    color: '#8b39b5',
    hourly_rate: 260,
    phone: '13800000001',
    note: null,
    archived: 0,
    created_at: '2026-07-01T00:00:00',
    updated_at: '2026-07-01T00:00:00',
  },
  {
    id: 2,
    name: '周然',
    color: '#ec4899',
    hourly_rate: 300,
    phone: '13800000002',
    note: '准备考试',
    archived: 0,
    created_at: '2026-07-02T00:00:00',
    updated_at: '2026-07-02T00:00:00',
  },
]

function studentDetail(id: number) {
  return {
    ...students.find((student) => student.id === id)!,
    stats: {
      month_income: id * 1000,
      month_hours: id * 4,
      month_lesson_count: id * 4,
      month_leave_count: 0,
    },
    template_count: id,
  }
}

async function mountDashboard(path = '/') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: DashboardPage },
      { path: '/students', component: DashboardPage },
      { path: '/stats', component: DashboardPage },
    ],
  })
  await router.push(path)
  await router.isReady()

  const wrapper = shallowMount(DashboardPage, {
    global: {
      plugins: [createPinia(), router],
      stubs: {
        AppShell: { template: '<div><slot /></div>' },
      },
    },
  })
  await flushPromises()
  return { wrapper, router }
}

beforeEach(() => {
  vi.clearAllMocks()
  apiMocks.lessonsList.mockResolvedValue([])
  apiMocks.studentsList.mockResolvedValue(students)
  apiMocks.studentGet.mockImplementation((id: number) => Promise.resolve(studentDetail(id)))
  apiMocks.statsToday.mockResolvedValue(null)
  apiMocks.statsRange.mockResolvedValue(null)
  apiMocks.statsComparison.mockResolvedValue(null)
  apiMocks.statsStudents.mockResolvedValue([])
  apiMocks.statsLeave.mockResolvedValue([])
  apiMocks.templatesList.mockResolvedValue([])
})

describe('DashboardPage loading failures', () => {
  it('keeps the dashboard mounted and shows a recoverable message', async () => {
    apiMocks.lessonsList.mockRejectedValueOnce(new Error('network unavailable'))

    const { wrapper } = await mountDashboard()

    expect(wrapper.text()).toContain('数据加载失败，请检查网络后重试')
  })
})

describe('DashboardPage student workspace', () => {
  it('loads the selected student workspace without opening the edit form', async () => {
    const { wrapper } = await mountDashboard('/students')

    expect(apiMocks.studentGet).toHaveBeenCalledWith(1)
    expect(apiMocks.templatesList).toHaveBeenCalledWith(1)

    await wrapper.getComponent(StudentsPanel).vm.$emit('select-student', 2)
    await flushPromises()

    expect(apiMocks.studentGet).toHaveBeenLastCalledWith(2)
    expect(apiMocks.templatesList).toHaveBeenLastCalledWith(2)
    expect(wrapper.findComponent({ name: 'StudentFormModal' }).exists()).toBe(false)
  })

  it('keeps student-detail and template errors local to their panels', async () => {
    apiMocks.studentGet.mockRejectedValue(new Error('detail unavailable'))
    apiMocks.templatesList.mockRejectedValue(new Error('templates unavailable'))

    const { wrapper } = await mountDashboard('/students')

    expect(wrapper.getComponent(StudentOverview).props('error')).toBe('学生详情加载失败')
    expect(wrapper.getComponent(TemplateManager).props('error')).toBe('模板加载失败')
  })
})

describe('DashboardPage statistics workspace', () => {
  it('loads the selected explicit period through every statistics endpoint', async () => {
    const { wrapper } = await mountDashboard('/stats')

    const [from, to, granularity] = apiMocks.statsRange.mock.calls.at(-1)!
    expect(granularity).toBe('week')
    expect(apiMocks.statsComparison).toHaveBeenLastCalledWith(from, to, 'month')
    expect(apiMocks.statsStudents).toHaveBeenLastCalledWith(from, to)
    expect(apiMocks.statsLeave).toHaveBeenLastCalledWith(from, to)
    expect(wrapper.getComponent(StatsPanel).props('loading')).toBe(false)
  })

  it('keeps statistics failures local and retries the workspace', async () => {
    apiMocks.statsRange.mockRejectedValueOnce(new Error('stats unavailable'))
    const { wrapper } = await mountDashboard('/stats')

    expect(wrapper.getComponent(StatsPanel).props('error')).toBe('统计数据加载失败，请稍后重试')

    wrapper.getComponent(StatsPanel).vm.$emit('retry')
    await flushPromises()

    expect(apiMocks.statsRange).toHaveBeenCalledTimes(2)
    expect(wrapper.getComponent(StatsPanel).props('error')).toBe('')
  })

  it('opens a contribution student in the student workspace and preserves the route selection', async () => {
    const { wrapper, router } = await mountDashboard('/stats')

    wrapper.getComponent(StatsPanel).vm.$emit('select-student', 2)
    await flushPromises()

    expect(router.currentRoute.value.fullPath).toBe('/students?student=2')
    expect(apiMocks.studentGet).toHaveBeenLastCalledWith(2)
    expect(apiMocks.templatesList).toHaveBeenLastCalledWith(2)
  })

  it('restores the selected student from the route query', async () => {
    const { wrapper } = await mountDashboard('/students?student=2')

    expect(apiMocks.studentGet).toHaveBeenLastCalledWith(2)
    expect(wrapper.getComponent(StudentsPanel).props('selectedStudentId')).toBe(2)
  })

  it('ignores a stale response after the selected period changes', async () => {
    let resolveFirst!: (value: unknown) => void
    let resolveSecond!: (value: unknown) => void
    apiMocks.statsRange
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve }))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSecond = resolve }))

    const { wrapper } = await mountDashboard('/stats')
    wrapper.getComponent(StatsPanel).vm.$emit('change-range', 'week')
    await flushPromises()

    resolveSecond({ total_income: 222, buckets: [] })
    await flushPromises()
    expect(wrapper.getComponent(StatsPanel).props('range')).toMatchObject({ total_income: 222 })

    resolveFirst({ total_income: 111, buckets: [] })
    await flushPromises()
    expect(wrapper.getComponent(StatsPanel).props('range')).toMatchObject({ total_income: 222 })
  })
})
