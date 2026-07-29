import { flushPromises, shallowMount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import StudentOverview from '@/components/students/StudentOverview.vue'
import StudentsPanel from '@/components/students/StudentsPanel.vue'
import TemplateManager from '@/components/students/TemplateManager.vue'
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
  return wrapper
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

    const wrapper = await mountDashboard()

    expect(wrapper.text()).toContain('数据加载失败，请检查网络后重试')
  })
})

describe('DashboardPage student workspace', () => {
  it('loads the selected student workspace without opening the edit form', async () => {
    const wrapper = await mountDashboard('/students')

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

    const wrapper = await mountDashboard('/students')

    expect(wrapper.getComponent(StudentOverview).props('error')).toBe('学生详情加载失败')
    expect(wrapper.getComponent(TemplateManager).props('error')).toBe('模板加载失败')
  })
})
