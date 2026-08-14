import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createPinia } from 'pinia'
import { templatesApi } from '@/api/templates'
import type { Student, Template } from '@/api/types'
import TemplateFormModal from './TemplateFormModal.vue'

vi.mock('@/api/templates', () => ({ templatesApi: { create: vi.fn(), update: vi.fn(), remove: vi.fn() } }))
const students: Student[] = [{ id: 3, name: '林沐', color: '#7c3aed', hourly_rate: 200, phone: null, note: null, archived: 0, created_at: '', updated_at: '' }]
const template: Template = { id: 4, student_id: 3, day_of_week: 1, start_time: '16:00', duration_hours: 1, effective_from: '2026-08-10', effective_to: null, repeat_interval: 1 }

function mountModal(props: { mode: 'edit'; students: Student[]; selectedStudentId: number; template: Template }) {
  return mount(TemplateFormModal, {
    attachTo: document.body,
    props,
    global: { plugins: [createPinia()] },
  })
}

describe('TemplateFormModal', () => {
  afterEach(() => { vi.clearAllMocks(); document.body.innerHTML = '' })

  it('explains future lesson impact before deleting', async () => {
    const wrapper = mountModal({ mode: 'edit', students, selectedStudentId: 3, template })
    await nextTick()
    ;(document.body.querySelector('[data-action="delete-template"]') as HTMLButtonElement).click()
    await nextTick()
    expect(document.body.textContent).toContain('取消所有未来待上课时')
    expect(templatesApi.remove).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('locks duplicate deletion while pending', async () => {
    vi.mocked(templatesApi.remove).mockImplementation(() => new Promise(() => {}))
    const wrapper = mountModal({ mode: 'edit', students, selectedStudentId: 3, template })
    await nextTick()
    ;(document.body.querySelector('[data-action="delete-template"]') as HTMLButtonElement).click()
    await nextTick()
    ;(document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement).click()
    await nextTick()
    expect((document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement).disabled).toBe(true)
    expect(templatesApi.remove).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
