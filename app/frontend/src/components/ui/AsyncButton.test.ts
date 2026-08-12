import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AsyncButton from './AsyncButton.vue'

describe('AsyncButton', () => {
  it('prevents duplicate async actions', () => {
    const wrapper = mount(AsyncButton, {
      props: { pending: true, pendingLabel: '保存中' },
      slots: { default: '保存' },
    })

    expect(wrapper.attributes('disabled')).toBeDefined()
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.text()).toContain('保存中')
  })

  it('renders the action slot when idle', () => {
    const wrapper = mount(AsyncButton, { slots: { default: '保存设置' } })
    expect(wrapper.text()).toBe('保存设置')
    expect(wrapper.attributes('type')).toBe('submit')
  })
})
