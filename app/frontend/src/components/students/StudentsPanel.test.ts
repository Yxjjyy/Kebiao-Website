import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { Student } from '@/api/types'
import StudentsPanel from './StudentsPanel.vue'

const students = [
  {
    id: 1, name: '林沐', color: '#7c3aed', hourly_rate: 300, phone: '13800138000',
    note: null, archived: 0, created_at: '', updated_at: '',
  },
  {
    id: 2, name: '周宁', color: '#ec4899', hourly_rate: 260, phone: '13900139000',
    note: null, archived: 0, created_at: '', updated_at: '',
  },
] satisfies Student[]

function mountPanel() {
  return mount(StudentsPanel, {
    props: { students, currencySymbol: '¥', selectedStudentId: 1 },
  })
}

describe('StudentsPanel', () => {
  it('filters by name and phone', async () => {
    const wrapper = mountPanel()
    const search = wrapper.get('[data-testid="student-search"]')

    await search.setValue('周')
    expect(wrapper.text()).toContain('周宁')
    expect(wrapper.text()).not.toContain('林沐')

    await search.setValue('138')
    expect(wrapper.text()).toContain('林沐')
    expect(wrapper.text()).not.toContain('周宁')
  })

  it('selects from the card without opening edit', async () => {
    const wrapper = mountPanel()
    const cards = wrapper.findAll('[data-testid="student-card"]')
    await cards[1].trigger('click')

    expect(wrapper.emitted('select-student')).toEqual([[2]])
    expect(wrapper.emitted('edit-student')).toBeUndefined()
  })

  it('emits edit only from the dedicated edit action', async () => {
    const wrapper = mountPanel()
    const editButtons = wrapper.findAll('[data-testid="edit-student"]')
    await editButtons[1].trigger('click')

    expect(wrapper.emitted('edit-student')).toEqual([[2]])
    expect(wrapper.emitted('select-student')).toBeUndefined()
  })

  it('shows a specific empty search result', async () => {
    const wrapper = mountPanel()
    await wrapper.get('[data-testid="student-search"]').setValue('不存在')
    expect(wrapper.text()).toContain('没有找到匹配的学生')
  })
})
