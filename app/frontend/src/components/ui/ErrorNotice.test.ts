import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ErrorNotice from './ErrorNotice.vue'

const error = {
  kind: 'server' as const,
  message: '服务暂时不可用，请稍后重试',
  status: 503,
  requestId: 'req-503',
  detail: { reason: 'maintenance' },
  retryable: true,
}

describe('ErrorNotice', () => {
  it('keeps diagnostics collapsed by default and expands them on demand', async () => {
    const wrapper = mount(ErrorNotice, { props: { error } })
    expect(wrapper.text()).toContain(error.message)
    expect(wrapper.text()).not.toContain('req-503')

    await wrapper.get('[data-action="toggle-error-details"]').trigger('click')
    expect(wrapper.text()).toContain('server')
    expect(wrapper.text()).toContain('503')
    expect(wrapper.text()).toContain('req-503')
    expect(wrapper.text()).toContain('maintenance')
  })

  it('emits retry from the reload action', async () => {
    const wrapper = mount(ErrorNotice, { props: { error } })
    await wrapper.get('[data-action="retry-error"]').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
