import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { Student, Template } from '@/api/types'
import TemplateManager from './TemplateManager.vue'

const student = {
  id: 1, name: '林沐', color: '#7c3aed', hourly_rate: 300, phone: null,
  note: null, archived: 0, created_at: '', updated_at: '',
} satisfies Student

const templates = [
  {
    id: 2, student_id: 1, day_of_week: 2, start_time: '16:00', duration_hours: 1,
    effective_from: '2026-07-01', effective_to: null, repeat_interval: 2,
  },
  {
    id: 1, student_id: 1, day_of_week: 0, start_time: '09:00', duration_hours: 1.5,
    effective_from: '2026-06-01', effective_to: '2026-12-31', repeat_interval: 1,
  },
] satisfies Template[]

describe('TemplateManager', () => {
  it('sorts templates and shows repeat and effective-range details', () => {
    const wrapper = mount(TemplateManager, {
      props: {
        students: [student],
        selectedStudentId: 1,
        templates,
        loading: false,
        error: '',
      },
    })

    const cards = wrapper.findAll('[data-testid="template-card"]')
    expect(cards[0].text()).toContain('周一')
    expect(cards[0].text()).toContain('每周')
    expect(cards[0].text()).toContain('2026-06-01 — 2026-12-31')
    expect(cards[1].text()).toContain('周三')
    expect(cards[1].text()).toContain('隔周')
  })

  it('emits retry from the local error state', async () => {
    const wrapper = mount(TemplateManager, {
      props: {
        students: [student],
        selectedStudentId: 1,
        templates: [],
        loading: false,
        error: '课表模板加载失败',
      },
    })

    await wrapper.get('[data-action="retry-templates"]').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('offers template creation from the empty state', async () => {
    const wrapper = mount(TemplateManager, {
      props: {
        students: [student],
        selectedStudentId: 1,
        templates: [],
        loading: false,
        error: '',
      },
    })

    expect(wrapper.text()).toContain('还没有固定课表')
    await wrapper.get('[data-action="add-empty-template"]').trigger('click')
    expect(wrapper.emitted('add-template')).toHaveLength(1)
  })
})
