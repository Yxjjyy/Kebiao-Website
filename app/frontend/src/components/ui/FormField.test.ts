import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import FormField from './FormField.vue'

describe('FormField', () => {
  it('connects a field to hint and error text', () => {
    const wrapper = mount(FormField, {
      props: {
        forId: 'lesson-date',
        label: '日期',
        hint: '选择上课日期',
        error: '日期无效',
        required: true,
      },
      slots: { default: '<input id="lesson-date">' },
    })

    expect(wrapper.get('label').attributes('for')).toBe('lesson-date')
    expect(wrapper.get('[role="alert"]').text()).toBe('日期无效')
    expect(wrapper.text()).toContain('必填')
  })
})
