# 设置与表单体验 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一项目弹窗、表单字段、异步提交、确认操作和错误提示，并将课程创建、编辑、调课、学生、模板和设置流程迁移到可访问的共享交互基础。

**Architecture:** 使用 Reka UI Dialog 建立统一 `AppDialog`，用小型 UI 组件统一字段、提示和异步按钮；业务弹窗仍负责自己的数据与 API。课程流程采用“上下文优先 + 自适应分组”，所有危险操作通过结构化 `ConfirmDialog` 完成。

**Tech Stack:** Vue 3、TypeScript、Reka UI、Tailwind CSS、Vitest、Vue Test Utils、Axios

---

## 文件结构

- `app/frontend/src/lib/formError.ts`：将 Axios、校验和课程冲突转换为统一表单错误。
- `app/frontend/src/lib/formError.test.ts`：错误解析纯函数测试。
- `app/frontend/src/components/ui/AppDialog.vue`：统一弹窗、焦点、关闭和滚动行为。
- `app/frontend/src/components/ui/FormField.vue`：标签、说明和字段错误。
- `app/frontend/src/components/ui/InlineAlert.vue`：成功、警告和错误提示。
- `app/frontend/src/components/ui/AsyncButton.vue`：异步按钮与重复提交保护。
- `app/frontend/src/components/ui/ConfirmDialog.vue`：标准危险操作确认。
- `app/frontend/src/components/ui/*.test.ts`：基础组件行为和无障碍测试。
- `app/frontend/src/components/schedule/LessonTimeFields.vue`：课程日期、时间和课时共享字段。
- `app/frontend/src/components/schedule/*Modal.vue`：迁移创建、编辑、调课和调课范围弹窗。
- `app/frontend/src/components/students/*FormModal.vue`：迁移学生与模板表单。
- `app/frontend/src/components/layout/SettingsPanel.vue`：增加统一保存、备份和恢复状态。
- `app/frontend/src/pages/DashboardPage.vue`：批量与快捷删除确认编排。

---

### Task 1: 统一表单错误模型

**Files:**
- Create: `app/frontend/src/lib/formError.ts`
- Create: `app/frontend/src/lib/formError.test.ts`

- [ ] **Step 1: 写失败测试**

```ts
import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { parseFormError } from './formError'

describe('parseFormError', () => {
  it('formats structured lesson conflicts', () => {
    const error = new AxiosError('conflict', '409', undefined, undefined, {
      data: { detail: { error: 'time_conflict', conflicts: [{ id: 1, student_id: 2, student_name: '林晓', date: '2026-08-10', start_time: '10:00', duration_hours: 1 }] } },
      status: 409,
      statusText: 'Conflict',
      headers: {},
      config: {} as never,
    })
    expect(parseFormError(error)).toContain('林晓 · 2026-08-10 10:00')
  })

  it('uses server detail and a stable fallback', () => {
    expect(parseFormError({ response: { data: { detail: '日期无效' } } })).toBe('日期无效')
    expect(parseFormError(new Error('boom'))).toBe('操作失败，请稍后再试')
  })
})
```

- [ ] **Step 2: 运行测试确认模块不存在**

Run: `cd app/frontend && npm test -- --run src/lib/formError.test.ts`

Expected: FAIL，无法解析 `formError`。

- [ ] **Step 3: 实现纯函数**

```ts
import { AxiosError } from 'axios'
import type { ConflictResponse } from '@/api/types'

export function parseFormError(error: unknown, fallback = '操作失败，请稍后再试'): string {
  const data = error instanceof AxiosError
    ? error.response?.data
    : (error as { response?: { data?: unknown } })?.response?.data
  const detail = (data as { detail?: string | ConflictResponse } | undefined)?.detail
  if (typeof detail === 'string') return detail
  if (detail?.error === 'time_conflict') {
    return `时间冲突：${detail.conflicts.map((item) => `${item.student_name} · ${item.date} ${item.start_time.slice(0, 5)}`).join('；')}`
  }
  return fallback
}
```

- [ ] **Step 4: 运行测试并提交**

Run: `cd app/frontend && npm test -- --run src/lib/formError.test.ts`

Expected: PASS。

```powershell
git add app/frontend/src/lib/formError.ts app/frontend/src/lib/formError.test.ts
git commit -m "feat: unify form error messages"
```

---

### Task 2: 表单展示与异步按钮基础组件

**Files:**
- Create: `app/frontend/src/components/ui/FormField.vue`
- Create: `app/frontend/src/components/ui/FormField.test.ts`
- Create: `app/frontend/src/components/ui/InlineAlert.vue`
- Create: `app/frontend/src/components/ui/InlineAlert.test.ts`
- Create: `app/frontend/src/components/ui/AsyncButton.vue`
- Create: `app/frontend/src/components/ui/AsyncButton.test.ts`

- [ ] **Step 1: 写组件失败测试**

```ts
it('connects a field to hint and error text', () => {
  const wrapper = mount(FormField, { props: { forId: 'lesson-date', label: '日期', hint: '选择上课日期', error: '日期无效', required: true }, slots: { default: '<input id="lesson-date">' } })
  expect(wrapper.get('label').attributes('for')).toBe('lesson-date')
  expect(wrapper.get('[role="alert"]').text()).toBe('日期无效')
})

it('announces inline errors', () => {
  const wrapper = mount(InlineAlert, { props: { tone: 'error', message: '保存失败' } })
  expect(wrapper.attributes('role')).toBe('alert')
})

it('prevents duplicate async actions', async () => {
  const wrapper = mount(AsyncButton, { props: { pending: true, pendingLabel: '保存中' }, slots: { default: '保存' } })
  expect(wrapper.attributes('disabled')).toBeDefined()
  expect(wrapper.text()).toContain('保存中')
})
```

- [ ] **Step 2: 运行测试确认组件不存在**

Run: `cd app/frontend && npm test -- --run src/components/ui`

Expected: FAIL，三个组件无法解析。

- [ ] **Step 3: 实现组件接口**

`FormField.vue` 使用 `forId`、`label`、`hint`、`error`、`required` props，错误节点使用 `role="alert"`；`InlineAlert.vue` 支持 `success | warning | error | info`；`AsyncButton.vue` 原生 `type="submit"`，在 `pending || disabled` 时禁用并设置 `aria-busy`。

```vue
<button :type="type" :disabled="disabled || pending" :aria-busy="pending" :class="buttonClass">
  <span>{{ pending ? pendingLabel : undefined }}</span><slot v-if="!pending" />
</button>
```

- [ ] **Step 4: 运行组件测试和构建**

Run: `cd app/frontend && npm test -- --run src/components/ui && npm run build`

Expected: PASS，构建成功。

- [ ] **Step 5: 提交**

```powershell
git add app/frontend/src/components/ui
git commit -m "feat: add shared form feedback controls"
```

---

### Task 3: 统一弹窗和确认对话框

**Files:**
- Create: `app/frontend/src/components/ui/AppDialog.vue`
- Create: `app/frontend/src/components/ui/AppDialog.test.ts`
- Create: `app/frontend/src/components/ui/ConfirmDialog.vue`
- Create: `app/frontend/src/components/ui/ConfirmDialog.test.ts`

- [ ] **Step 1: 写弹窗行为失败测试**

测试打开时具有 `role="dialog"`、标题关联、Escape 关闭、关闭后焦点归还、`closeDisabled` 阻止关闭，以及确认按钮发出 `confirm`。

```ts
await wrapper.get('[data-action="confirm"]').trigger('click')
expect(wrapper.emitted('confirm')).toHaveLength(1)
expect(wrapper.get('[role="dialog"]').attributes('aria-labelledby')).toBeTruthy()
```

- [ ] **Step 2: 运行测试确认组件不存在**

Run: `cd app/frontend && npm test -- --run src/components/ui/AppDialog.test.ts src/components/ui/ConfirmDialog.test.ts`

Expected: FAIL。

- [ ] **Step 3: 使用 Reka UI 实现 `AppDialog`**

使用 `DialogRoot`、`DialogPortal`、`DialogOverlay`、`DialogContent`、`DialogTitle`、`DialogDescription` 和 `DialogClose`。公开 `open`、`title`、`description`、`size`、`closeDisabled` props，发出 `update:open` 与 `close`，并提供 default/footer slots。

- [ ] **Step 4: 实现 `ConfirmDialog`**

公开 `open`、`title`、`description`、`confirmLabel`、`pending`、`tone`，取消和确认均为明确按钮；pending 时禁止关闭和重复确认。

- [ ] **Step 5: 运行测试和构建并提交**

Run: `cd app/frontend && npm test -- --run src/components/ui && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/ui
git commit -m "feat: standardize accessible dialogs"
```

---

### Task 4: 课程创建和调课流程

**Files:**
- Create: `app/frontend/src/components/schedule/LessonTimeFields.vue`
- Create: `app/frontend/src/components/schedule/LessonTimeFields.test.ts`
- Modify: `app/frontend/src/components/schedule/CreateLessonModal.vue`
- Create: `app/frontend/src/components/schedule/CreateLessonModal.test.ts`
- Modify: `app/frontend/src/components/schedule/RescheduleLessonModal.vue`
- Create: `app/frontend/src/components/schedule/RescheduleLessonModal.test.ts`
- Modify: `app/frontend/src/components/schedule/RescheduleModeModal.vue`

- [ ] **Step 1: 写共享字段和流程失败测试**

覆盖桌面字段分组、创建预估、结构化冲突、pending 禁止关闭、原课/目标课对比、调课范围选择和成功事件。

- [ ] **Step 2: 运行测试确认旧结构不符合要求**

Run: `cd app/frontend && npm test -- --run src/components/schedule/LessonTimeFields.test.ts src/components/schedule/CreateLessonModal.test.ts src/components/schedule/RescheduleLessonModal.test.ts`

Expected: FAIL。

- [ ] **Step 3: 实现 `LessonTimeFields`**

使用 `v-model:date`、`v-model:startTime`、`v-model:durationHours`，通过 `FormField` 渲染日期、时间和课时；父表单决定标题是“日期”还是“新日期”。

- [ ] **Step 4: 迁移创建和调课弹窗**

使用 `AppDialog`、`LessonTimeFields`、`FormField`、`AsyncButton`、`InlineAlert` 和 `parseFormError`。创建弹窗顶部展示已选学生上下文；调课弹窗并列展示原课程与目标安排。

- [ ] **Step 5: 迁移调课范围弹窗**

三个模式按钮保留原事件值 `1 | 2 | 3`，补充 dialog 语义、焦点管理和 44px 操作区域。

- [ ] **Step 6: 运行测试和构建并提交**

Run: `cd app/frontend && npm test -- --run src/components/schedule && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/schedule
git commit -m "feat: refine lesson creation and rescheduling forms"
```

---

### Task 5: 课程编辑与危险操作状态

**Files:**
- Modify: `app/frontend/src/components/schedule/LessonEditModal.vue`
- Create: `app/frontend/src/components/schedule/LessonEditModal.test.ts`

- [ ] **Step 1: 写失败测试**

覆盖摘要上下文、保存 pending、状态 pending、删除确认、确认过程中禁止重复提交、成功刷新及冲突错误。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/components/schedule/LessonEditModal.test.ts`

Expected: FAIL，旧组件仍使用 `window.confirm` 且没有独立 pending 状态。

- [ ] **Step 3: 实现三个独立状态**

```ts
const saving = ref(false)
const statusUpdating = ref<Lesson['status'] | null>(null)
const deleting = ref(false)
const confirmDeleteOpen = ref(false)
```

使用 `AppDialog` 和 `ConfirmDialog`；任何写操作执行时禁用冲突动作，但保留明确的当前操作文案。

- [ ] **Step 4: 运行测试和构建并提交**

Run: `cd app/frontend && npm test -- --run src/components/schedule/LessonEditModal.test.ts && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/schedule/LessonEditModal.vue app/frontend/src/components/schedule/LessonEditModal.test.ts
git commit -m "feat: clarify lesson editing actions"
```

---

### Task 6: 学生与模板表单迁移

**Files:**
- Modify: `app/frontend/src/components/students/StudentFormModal.vue`
- Create: `app/frontend/src/components/students/StudentFormModal.test.ts`
- Modify: `app/frontend/src/components/students/TemplateFormModal.vue`
- Create: `app/frontend/src/components/students/TemplateFormModal.test.ts`

- [ ] **Step 1: 写失败测试**

覆盖新增、编辑、归档/恢复、模板删除确认、提交中禁止关闭、字段错误和成功刷新。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/components/students/StudentFormModal.test.ts src/components/students/TemplateFormModal.test.ts`

Expected: FAIL。

- [ ] **Step 3: 迁移两个表单**

使用共享基础组件，保留原 API 和事件；模板删除改用 `ConfirmDialog`，确认文案明确“将取消所有未来待上课时”。

- [ ] **Step 4: 运行学生组件测试和构建并提交**

Run: `cd app/frontend && npm test -- --run src/components/students && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/students
git commit -m "feat: standardize student and template forms"
```

---

### Task 7: 设置、备份和恢复体验

**Files:**
- Modify: `app/frontend/src/components/layout/SettingsPanel.vue`
- Create: `app/frontend/src/components/layout/SettingsPanel.test.ts`

- [ ] **Step 1: 写失败测试**

覆盖保存 pending、保存失败恢复旧主题、下载 pending、恢复确认文本、恢复 pending、成功和错误提示；断言页面不再出现令牌重置入口。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/components/layout/SettingsPanel.test.ts`

Expected: FAIL。

- [ ] **Step 3: 实现独立异步状态**

```ts
const saving = ref(false)
const downloading = ref(false)
const restoring = ref(false)
const settingsMessage = ref('')
const settingsError = ref('')
```

保存前保留旧设置；任一保存失败时刷新 store 或恢复旧值并显示错误。恢复操作继续要求输入“确认恢复”，使用 `ConfirmDialog` 展示覆盖影响。

- [ ] **Step 4: 删除无效令牌逻辑**

删除 `useAuthStore`、`useRouter`、`resetLocalToken` 及对应界面入口，不修改其他路由行为。

- [ ] **Step 5: 运行测试和构建并提交**

Run: `cd app/frontend && npm test -- --run src/components/layout/SettingsPanel.test.ts && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/layout/SettingsPanel.vue app/frontend/src/components/layout/SettingsPanel.test.ts
git commit -m "feat: improve settings and backup feedback"
```

---

### Task 8: Dashboard 批量与快捷危险操作

**Files:**
- Modify: `app/frontend/src/pages/DashboardPage.vue`
- Modify: `app/frontend/src/pages/DashboardPage.test.ts`

- [ ] **Step 1: 写失败测试**

验证单条快捷删除和批量删除先显示 `ConfirmDialog`；批量确认文案包含数量；pending 时按钮禁用；取消不调用 API；确认后仅调用一次并清空选择。

- [ ] **Step 2: 运行页面测试确认失败**

Run: `cd app/frontend && npm test -- --run src/pages/DashboardPage.test.ts`

Expected: FAIL，旧页面直接批量删除并使用 `window.confirm` 快捷删除。

- [ ] **Step 3: 编排统一确认状态**

```ts
type PendingDangerAction =
  | { kind: 'lesson-delete'; lesson: Lesson }
  | { kind: 'bulk-delete'; lessonIds: number[] }
  | null

const pendingDangerAction = ref<PendingDangerAction>(null)
const dangerSubmitting = ref(false)
```

确认后调用现有单条或批量 API；捕获失败时保留页面数据并显示 `scheduleError`。

- [ ] **Step 4: 运行页面测试和全量前端测试并提交**

Run: `cd app/frontend && npm test -- --run src/pages/DashboardPage.test.ts && npm test -- --run && npm run build`

Expected: 所有测试 PASS，构建成功。

```powershell
git add app/frontend/src/pages/DashboardPage.vue app/frontend/src/pages/DashboardPage.test.ts
git commit -m "feat: confirm destructive schedule actions"
```

---

### Task 9: 无障碍、暗色与双端验收

**Files:**
- Modify: `app/frontend/src/styles/globals.css`
- Modify: `docs/superpowers/plans/2026-08-06-settings-form-experience.md`

- [ ] **Step 1: 运行完整自动化验证**

Run: `cd app/frontend && npm test -- --run && npm run build`

Expected: 全部 PASS，构建成功。

- [ ] **Step 2: 浏览器验收桌面和移动端**

在 1440×900 与 390×844 下依次验证创建课程、编辑课程、调课、学生、模板和设置表单：无横向溢出，操作区无遮挡，触控按钮至少 44px。

- [ ] **Step 3: 验收键盘和焦点**

只使用键盘完成打开、填写、确认和关闭；Tab 不离开当前弹窗；Escape 在非提交状态关闭；关闭后焦点回到触发按钮；错误和 pending 状态可被辅助技术识别。

- [ ] **Step 4: 验收暗色和 reduced motion**

检查明亮、暗色、系统主题和 reduced-motion；文本、边框、危险色、焦点环和禁用状态保持可读。

- [ ] **Step 5: 差异检查并更新计划**

Run: `git diff --check && git status --short`

Expected: 无空白错误，只包含第四阶段预期文件。将完成项改为 `[x]`。

- [ ] **Step 6: 提交最终调整**

```powershell
git add app/frontend docs/superpowers/plans/2026-08-06-settings-form-experience.md
git commit -m "feat: complete settings and form experience"
```
