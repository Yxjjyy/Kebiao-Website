import { AxiosError } from 'axios'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createPinia } from 'pinia'
import { templatesApi } from '@/api/templates'
import type { Student, Template } from '@/api/types'
import TemplateFormModal from './TemplateFormModal.vue'

vi.mock('@/api/templates', () => ({ templatesApi: { create: vi.fn(), update: vi.fn(), remove: vi.fn() } }))
const students: Student[] = [{ id: 3, name: '林沐', color: '#7c3aed', hourly_rate: 200, phone: null, note: null, archived: 0, created_at: '', updated_at: '' }]
const template: Template = { id: 4, student_id: 3, day_of_week: 1, start_time: '16:00', duration_hours: 1, effective_from: '2026-08-10', effective_to: null, repeat_interval: 1 }

function mountModal(props: { mode: 'create' | 'edit'; students: Student[]; selectedStudentId: number; template: Template | null }) {
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

  it('reports how many future lessons were rebuilt', async () => {
    vi.mocked(templatesApi.update).mockResolvedValue({ template, regenerated_lessons: 2 })
    const wrapper = mountModal({ mode: 'edit', students, selectedStudentId: 3, template })
    await nextTick()

    document.body.querySelector('form')?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()

    expect(document.body.textContent).toContain('已重建 2 节课时')
    wrapper.unmount()
  })

  it('keeps the dialog open and shows a time conflict', async () => {
    const conflict = new AxiosError('conflict', '409', undefined, undefined, {
      data: {
        detail: {
          error: 'time_conflict',
          conflicts: [{
            id: 1,
            student_id: 3,
            student_name: '林沐',
            date: '2026-08-10',
            start_time: '16:00',
            duration_hours: 1,
          }],
        },
      },
      status: 409,
      statusText: 'Conflict',
      headers: {},
      config: {} as never,
    })
    vi.mocked(templatesApi.create).mockRejectedValue(conflict)
    const wrapper = mountModal({ mode: 'create', students, selectedStudentId: 3, template: null })
    await nextTick()

    document.body.querySelector('form')?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()

    expect(document.body.textContent).toContain('时间冲突：林沐 · 2026-08-10 16:00')
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull()
    wrapper.unmount()
  })
})
