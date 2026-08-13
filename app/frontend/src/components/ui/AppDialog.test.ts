import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import AppDialog from './AppDialog.vue'

describe('AppDialog', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('exposes an accessible title and closes from its close action', async () => {
    const wrapper = mount(AppDialog, {
      attachTo: document.body,
      props: { open: true, title: '编辑课程', description: '调整课程时间' },
      slots: { default: '<button>表单内容</button>' },
    })
    await nextTick()

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog).not.toBeNull()
    expect(dialog?.getAttribute('aria-labelledby')).toBeTruthy()
    expect(dialog?.textContent).toContain('编辑课程')

    const close = document.body.querySelector('[data-action="close-dialog"]') as HTMLButtonElement
    await close.click()
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:open')).toEqual([[false]])
    wrapper.unmount()
  })

  it('keeps close controls disabled while an operation is pending', async () => {
    const wrapper = mount(AppDialog, {
      attachTo: document.body,
      props: { open: true, title: '保存中', closeDisabled: true },
    })
    await nextTick()

    const close = document.body.querySelector('[data-action="close-dialog"]') as HTMLButtonElement
    expect(close.disabled).toBe(true)
    wrapper.unmount()
  })
})
