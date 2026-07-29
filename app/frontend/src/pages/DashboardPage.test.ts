import { flushPromises, shallowMount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'
import DashboardPage from './DashboardPage.vue'

vi.mock('@/api/lessons', () => ({
  lessonsApi: {
    list: vi.fn().mockRejectedValue(new Error('network unavailable')),
  },
}))

vi.mock('@/api/students', () => ({
  studentsApi: { list: vi.fn().mockResolvedValue([]) },
}))

vi.mock('@/api/stats', () => ({
  statsApi: {
    today: vi.fn().mockResolvedValue(null),
    range: vi.fn().mockResolvedValue(null),
    comparison: vi.fn().mockResolvedValue(null),
    students: vi.fn().mockResolvedValue([]),
    leave: vi.fn().mockResolvedValue([]),
  },
}))

vi.mock('@/api/templates', () => ({
  templatesApi: { list: vi.fn().mockResolvedValue([]) },
}))

vi.mock('@/api/settings', () => ({
  settingsApi: {
    getSettings: vi.fn().mockRejectedValue(new Error('network unavailable')),
    getProfile: vi.fn().mockRejectedValue(new Error('network unavailable')),
  },
}))

describe('DashboardPage loading failures', () => {
  it('keeps the dashboard mounted and shows a recoverable message', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: DashboardPage }],
    })
    await router.push('/')
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

    expect(wrapper.text()).toContain('数据加载失败，请检查网络后重试')
  })
})
