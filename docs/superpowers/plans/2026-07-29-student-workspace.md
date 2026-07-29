# 学生工作台重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将学生页面重构为响应式双栏工作台，接入学生详情统计，并提升固定课表模板的浏览和编辑效率。

**Architecture:** DashboardPage 继续负责请求与弹窗编排；StudentsPanel 只负责可搜索的学生目录；新增 StudentOverview 展示详情；TemplateManager 只负责模板列表。搜索、选择归一化、模板排序和周期文案集中到纯函数模块。

**Tech Stack:** Vue 3、TypeScript、Pinia、Vitest、Vue Test Utils、Tailwind CSS

---

### Task 1: 学生工作台纯逻辑

**Files:**
- Create: `app/frontend/src/lib/studentWorkspace.ts`
- Create: `app/frontend/src/lib/studentWorkspace.test.ts`

- [x] **Step 1: 写失败测试**

覆盖：

```ts
filterStudents(students, '')
filterStudents(students, '林')
filterStudents(students, '138')
normalizeSelectedStudentId(students, missingId)
sortTemplates(templates)
formatRepeatInterval(1)
formatRepeatInterval(2)
formatRepeatInterval(4)
```

- [x] **Step 2: 运行测试确认模块不存在**

```powershell
npm test -- src/lib/studentWorkspace.test.ts
```

预期：FAIL，无法解析 `studentWorkspace`。

- [x] **Step 3: 实现纯函数**

导出：

```ts
filterStudents(students: Student[], query: string): Student[]
normalizeSelectedStudentId(students: Student[], selectedId: number | null): number | null
sortTemplates(templates: Template[]): Template[]
formatRepeatInterval(interval?: number): string
```

- [x] **Step 4: 运行测试**

预期：全部 PASS。

### Task 2: 可搜索学生目录

**Files:**
- Modify: `app/frontend/src/components/students/StudentsPanel.vue`
- Create: `app/frontend/src/components/students/StudentsPanel.test.ts`

- [x] **Step 1: 写失败组件测试**

验证：

```text
显示学生数量和搜索框
按姓名及电话过滤
点击卡片只发出 select-student
点击编辑只发出 edit-student
无匹配结果显示空状态
```

- [x] **Step 2: 运行测试确认当前行为不符合**

```powershell
npm test -- src/components/students/StudentsPanel.test.ts
```

- [x] **Step 3: 实现目录组件**

新增事件：

```ts
(e: 'edit-student', value: number): void
```

学生卡使用按钮语义和 `aria-current`，编辑按钮阻止冒泡。

- [x] **Step 4: 运行测试**

预期：全部 PASS。

### Task 3: 学生详情概览

**Files:**
- Create: `app/frontend/src/components/students/StudentOverview.vue`
- Create: `app/frontend/src/components/students/StudentOverview.test.ts`

- [x] **Step 1: 写失败组件测试**

验证：

```text
正确显示姓名、单价、电话和备注
显示本月收入、课时、课程、请假和模板数
缺少电话或备注时显示明确占位
加载失败时显示重试按钮并发出 retry
点击编辑发出 edit-student
```

- [x] **Step 2: 运行测试确认组件不存在**

- [x] **Step 3: 实现详情组件**

Props：

```ts
student: StudentDetail | null
loading: boolean
error: string
currencySymbol: string
```

Emits：

```ts
edit-student(studentId)
retry
```

- [x] **Step 4: 运行测试**

预期：全部 PASS。

### Task 4: 模板时间卡片

**Files:**
- Modify: `app/frontend/src/components/students/TemplateManager.vue`
- Create: `app/frontend/src/components/students/TemplateManager.test.ts`

- [x] **Step 1: 写失败组件测试**

验证模板排序、重复周期、生效范围、空状态、新增和重试事件。

- [x] **Step 2: 运行测试确认新展示行为失败**

- [x] **Step 3: 实现模板组件**

新增 Props：

```ts
loading?: boolean
error?: string
```

新增事件：

```ts
(e: 'retry'): void
```

新增模板按钮在没有选中学生时禁用。

- [x] **Step 4: 运行测试**

预期：全部 PASS。

### Task 5: Dashboard 数据编排与响应式布局

**Files:**
- Modify: `app/frontend/src/pages/DashboardPage.vue`
- Modify: `app/frontend/src/pages/DashboardPage.test.ts`

- [x] **Step 1: 扩展失败测试**

验证：

```text
学生选择只更新 selectedStudentId
选中学生后请求详情和模板
详情失败与模板失败分别展示局部错误
编辑事件才打开 StudentFormModal
```

- [x] **Step 2: 运行测试确认失败**

- [x] **Step 3: 实现数据状态**

新增：

```ts
selectedStudentDetail
studentDetailLoading
studentDetailError
templatesLoading
templatesError
loadStudentWorkspace(studentId)
```

学生刷新后使用 `normalizeSelectedStudentId` 校正选择。

- [x] **Step 4: 实现布局**

桌面：

```text
320px StudentsPanel | StudentOverview + TemplateManager
```

手机：

```text
StudentsPanel
StudentOverview
TemplateManager
```

- [x] **Step 5: 运行全量测试与构建**

```powershell
npm test
npm run build
```

预期：全部通过。

### Task 6: 双端浏览器验收与提交

**Files:**
- Modify as needed: `app/frontend/src/components/students/*.vue`
- Modify as needed: `app/frontend/src/pages/DashboardPage.vue`

- [x] **Step 1: 在 1440×900 验证双栏布局**

- [x] **Step 2: 在 390×844 验证列表、详情和模板顺序**

- [x] **Step 3: 验证学生选择不自动打开编辑表单**

- [x] **Step 4: 运行最终测试和构建**

- [x] **Step 5: 提交第二阶段实现**
