import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import ConfirmDialog from './ConfirmDialog.vue'

describe('ConfirmDialog', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('emits one explicit confirmation', async () => {
    const wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: {
        open: true,
        title: '删除课程？',
        description: '此操作不可撤销',
        confirmLabel: '删除课程',
      },
    })
    await nextTick()

    const confirm = document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement
    await confirm.click()
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    wrapper.unmount()
  })

  it('prevents confirmation while pending', async () => {
    const wrapper = mount(ConfirmDialog, {
      attachTo: document.body,
      props: {
        open: true,
        title: '正在删除',
        description: '请稍候',
        confirmLabel: '删除课程',
        pending: true,
      },
    })
    await nextTick()

    const confirm = document.body.querySelector('[data-action="confirm"]') as HTMLButtonElement
    expect(confirm.disabled).toBe(true)
    expect(confirm.getAttribute('aria-busy')).toBe('true')
    wrapper.unmount()
  })
})
