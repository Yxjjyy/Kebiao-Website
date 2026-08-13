import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { studentsApi } from '@/api/students'
import type { Student } from '@/api/types'
import StudentFormModal from './StudentFormModal.vue'

vi.mock('@/api/students', () => ({ studentsApi: { create: vi.fn(), update: vi.fn(), archive: vi.fn(), unarchive: vi.fn() } }))

const student: Student = { id: 3, name: '林沐', color: '#7c3aed', hourly_rate: 200, phone: null, note: null, archived: 0, created_at: '', updated_at: '' }

describe('StudentFormModal', () => {
  afterEach(() => { vi.clearAllMocks(); document.body.innerHTML = '' })

  it('uses an accessible dialog and locks closing while saving', async () => {
    vi.mocked(studentsApi.update).mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(StudentFormModal, { attachTo: document.body, props: { mode: 'edit', student, currencySymbol: '¥' } })
    await nextTick()
    ;(document.body.querySelector('form') as HTMLFormElement).dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick()
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull()
    expect((document.body.querySelector('[data-action="save-student"]') as HTMLButtonElement).disabled).toBe(true)
    expect((document.body.querySelector('[data-action="close-dialog"]') as HTMLButtonElement).disabled).toBe(true)
    wrapper.unmount()
  })

  it('exposes a distinct archive action in edit mode', async () => {
    const wrapper = mount(StudentFormModal, { attachTo: document.body, props: { mode: 'edit', student, currencySymbol: '¥' } })
    await nextTick()
    expect(document.body.querySelector('[data-action="toggle-archive"]')).not.toBeNull()
    wrapper.unmount()
  })
})
