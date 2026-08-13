import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import type { Lesson } from '@/api/types'
import RescheduleLessonModal from './RescheduleLessonModal.vue'

const lesson: Lesson = {
  id: 8,
  student_id: 3,
  template_id: null,
  date: '2026-08-10',
  start_time: '10:00',
  duration_hours: 1,
  status: '待上',
  price: 200,
  note: null,
  rescheduled_from_id: null,
  rescheduled_to_id: null,
  created_at: '',
  updated_at: '',
  student: { id: 3, name: '林沐', color: '#7c3aed' },
}

describe('RescheduleLessonModal', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('compares the original lesson with the target arrangement', async () => {
    const wrapper = mount(RescheduleLessonModal, {
      attachTo: document.body,
      props: { lesson, defaultDuration: 1, currencySymbol: '¥' },
    })
    await nextTick()

    expect(document.body.textContent).toContain('原课程')
    expect(document.body.textContent).toContain('目标安排')
    expect(document.body.textContent).toContain('林沐')
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull()
    wrapper.unmount()
  })
})
