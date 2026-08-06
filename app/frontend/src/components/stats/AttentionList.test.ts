import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { LeaveItem } from '@/api/types'
import AttentionList from './AttentionList.vue'

const items: LeaveItem[] = [
  { id: 1, student_id: 1, student_name: '林晓', date: '2026-07-01', start_time: '09:00', duration_hours: 1, status: '请假', note: '身体不适' },
  { id: 2, student_id: 2, student_name: '周然', date: '2026-07-02', start_time: '10:00', duration_hours: 1.5, status: '已调课', note: null },
  { id: 3, student_id: 3, student_name: '陈禾', date: '2026-07-03', start_time: '14:00', duration_hours: 2, status: '请假', note: null },
  { id: 4, student_id: 4, student_name: '许安', date: '2026-07-04', start_time: '16:00', duration_hours: 1, status: '请假', note: null },
]

describe('AttentionList', () => {
  it('shows three items first and expands the remaining records', async () => {
    const wrapper = mount(AttentionList, { props: { items } })

    expect(wrapper.findAll('[data-testid="attention-item"]')).toHaveLength(3)
    expect(wrapper.text()).toContain('请假')
    expect(wrapper.text()).toContain('已调课')

    await wrapper.get('[data-action="expand-attention"]').trigger('click')
    expect(wrapper.findAll('[data-testid="attention-item"]')).toHaveLength(4)
    expect(wrapper.text()).toContain('收起')
  })

  it('renders an explicit empty state', () => {
    const wrapper = mount(AttentionList, { props: { items: [] } })
    expect(wrapper.text()).toContain('当前周期没有请假或调课记录')
  })
})
