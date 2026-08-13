import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import InlineAlert from './InlineAlert.vue'

describe('InlineAlert', () => {
  it('announces errors immediately', () => {
    const wrapper = mount(InlineAlert, {
      props: { tone: 'error', message: '保存失败' },
    })

    expect(wrapper.attributes('role')).toBe('alert')
    expect(wrapper.text()).toContain('保存失败')
  })

  it('uses a polite status for success feedback', () => {
    const wrapper = mount(InlineAlert, {
      props: { tone: 'success', message: '保存成功' },
    })

    expect(wrapper.attributes('role')).toBe('status')
    expect(wrapper.attributes('aria-live')).toBe('polite')
  })
})
