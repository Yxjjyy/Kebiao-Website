import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { backupApi } from '@/api/backup'
import { useSettingsStore } from '@/stores/settings'
import SettingsPanel from './SettingsPanel.vue'

vi.mock('@/api/backup', () => ({ backupApi: { download: vi.fn(), restore: vi.fn() } }))

describe('SettingsPanel', () => {
  beforeEach(() => setActivePinia(createPinia()))
  afterEach(() => { vi.clearAllMocks(); document.body.innerHTML = '' })

  it('locks the settings submit action while saving', async () => {
    const store = useSettingsStore()
    vi.spyOn(store, 'saveProfile').mockImplementation(() => new Promise(() => {}))
    vi.spyOn(store, 'saveSettings').mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(SettingsPanel, { attachTo: document.body })
    await wrapper.get('[data-form="settings"]').trigger('submit')
    await nextTick()
    expect((wrapper.get('[data-action="save-settings"]').element as HTMLButtonElement).disabled).toBe(true)
    expect(wrapper.text()).toContain('保存中')
    wrapper.unmount()
  })

  it('requires an in-app impact confirmation before restoring', async () => {
    const wrapper = mount(SettingsPanel, { attachTo: document.body })
    const file = new File(['backup'], 'backup.db')
    const fileInput = wrapper.get('#restore-file')
    Object.defineProperty(fileInput.element, 'files', { value: [file] })
    await fileInput.trigger('change')
    await wrapper.get('#restore-confirm').setValue('确认恢复')
    await wrapper.get('[data-action="prepare-restore"]').trigger('click')
    await nextTick()
    expect(document.body.textContent).toContain('覆盖当前数据')
    expect(backupApi.restore).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('does not expose token or login maintenance actions', () => {
    const wrapper = mount(SettingsPanel)
    expect(wrapper.text()).not.toContain('令牌')
    expect(wrapper.text()).not.toContain('登录')
  })
})
