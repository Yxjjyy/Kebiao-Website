import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { lessonsApi } from '@/api/lessons'
import type { Student } from '@/api/types'
import CreateLessonModal from './CreateLessonModal.vue'

vi.mock('@/api/lessons', () => ({
  lessonsApi: { create: vi.fn() },
}))

const students: Student[] = [{
  id: 3,
  name: '林沐',
  color: '#7c3aed',
  hourly_rate: 200,
  phone: null,
  note: null,
  archived: 0,
  created_at: '',
  updated_at: '',
}]

describe('CreateLessonModal', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('shows selected student context and a live estimate', async () => {
    const wrapper = mount(CreateLessonModal, {
      attachTo: document.body,
      props: { students, defaultDuration: 1.5, currencySymbol: '¥', quickCreate: null },
    })
    await nextTick()

    const student = document.body.querySelector('#create-lesson-student') as HTMLSelectElement
    student.value = '3'
    student.dispatchEvent(new Event('change'))
    await nextTick()

    expect(document.body.textContent).toContain('林沐')
    expect(document.body.textContent).toContain('¥300')
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull()
    wrapper.unmount()
  })

  it('disables closing and the submit action while pending', async () => {
    vi.mocked(lessonsApi.create).mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(CreateLessonModal, {
      attachTo: document.body,
      props: { students, defaultDuration: 1, currencySymbol: '¥', quickCreate: null },
    })
    await nextTick()

    const student = document.body.querySelector('#create-lesson-student') as HTMLSelectElement
    student.value = '3'
    student.dispatchEvent(new Event('change'))
    const form = document.body.querySelector('form') as HTMLFormElement
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick()

    expect((document.body.querySelector('[data-action="close-dialog"]') as HTMLButtonElement).disabled).toBe(true)
    expect((document.body.querySelector('[data-action="create-lesson"]') as HTMLButtonElement).disabled).toBe(true)
    wrapper.unmount()
  })
})
