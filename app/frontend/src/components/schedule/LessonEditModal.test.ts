import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { lessonsApi } from '@/api/lessons'
import type { Lesson, Student } from '@/api/types'
import LessonEditModal from './LessonEditModal.vue'

vi.mock('@/api/lessons', () => ({
  lessonsApi: {
    update: vi.fn(),
    cancel: vi.fn(),
    restore: vi.fn(),
    remove: vi.fn(),
  },
}))
vi.mock('@/composables/useCalendar', () => ({ downloadICS: vi.fn() }))

const lesson: Lesson = {
  id: 8, student_id: 3, template_id: null, date: '2026-08-10', start_time: '10:00',
  duration_hours: 1, status: '待上', price: 200, note: null, rescheduled_from_id: null,
  rescheduled_to_id: null, created_at: '', updated_at: '',
}
const students: Student[] = [{
  id: 3, name: '林沐', color: '#7c3aed', hourly_rate: 200, phone: null, note: null,
  archived: 0, created_at: '', updated_at: '',
}]

describe('LessonEditModal', () => {
  afterEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
  })

  it('shows lesson context and opens an in-app delete confirmation', async () => {
    const wrapper = mount(LessonEditModal, {
      attachTo: document.body,
      props: { lesson, students, defaultDuration: 1, currencySymbol: '¥' },
    })
    await nextTick()

    expect(document.body.textContent).toContain('林沐')
    ;(document.body.querySelector('[data-action="delete-lesson"]') as HTMLButtonElement).click()
    await nextTick()

    expect(document.body.textContent).toContain('删除这节课程？')
    expect(lessonsApi.remove).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('locks conflicting actions while saving', async () => {
    vi.mocked(lessonsApi.update).mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(LessonEditModal, {
      attachTo: document.body,
      props: { lesson, students, defaultDuration: 1, currencySymbol: '¥' },
    })
    await nextTick()
    ;(document.body.querySelector('[data-form="lesson-edit"]') as HTMLFormElement)
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick()

    expect((document.body.querySelector('[data-action="save-lesson"]') as HTMLButtonElement).disabled).toBe(true)
    expect((document.body.querySelector('[data-action="delete-lesson"]') as HTMLButtonElement).disabled).toBe(true)
    expect((document.body.querySelector('[data-action="close-dialog"]') as HTMLButtonElement).disabled).toBe(true)
    wrapper.unmount()
  })

  it('prevents duplicate deletion while the confirmed request is pending', async () => {
    vi.mocked(lessonsApi.remove).mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(LessonEditModal, {
      attachTo: document.body,
      props: { lesson, students, defaultDuration: 1, currencySymbol: '¥' },
    })
    await nextTick()
    ;(document.body.querySelector('[data-action="delete-lesson"]') as HTMLButtonElement).click()
    await nextTick()
    ;(document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement).click()
    await nextTick()

    const confirm = document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement
    expect(confirm.disabled).toBe(true)
    expect(confirm.getAttribute('aria-busy')).toBe('true')
    expect(lessonsApi.remove).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
