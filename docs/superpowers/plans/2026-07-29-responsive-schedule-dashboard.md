# 响应式课表工作台 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有课表首页更新为已确认的 Lumina 响应式双端设计，并实现手机端点击课程后通过底部面板更新状态。

**Architecture:** 保留 FastAPI 接口与 DashboardPage 的数据加载边界，把展示派生逻辑提取为纯函数，把头部、桌面概览和移动操作面板拆为独立 Vue 组件。ScheduleBoard 继续承载课表视图，但桌面显示周网格、手机显示单日课程流。

**Tech Stack:** Vue 3、TypeScript、Tailwind CSS、Vitest、Vue Test Utils、Vite

---

### Task 1: 建立前端测试基线与课表派生逻辑

**Files:**
- Modify: `app/frontend/package.json`
- Modify: `app/frontend/vite.config.ts`
- Create: `app/frontend/src/lib/scheduleDashboard.ts`
- Create: `app/frontend/src/lib/scheduleDashboard.test.ts`

- [ ] **Step 1: 安装测试依赖并加入测试脚本**

运行：

```powershell
npm install -D vitest @vue/test-utils jsdom
```

在 `package.json` 中加入：

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 2: 写纯逻辑失败测试**

测试必须覆盖：

```ts
expect(getGreeting(8)).toBe('早上好')
expect(getGreeting(14)).toBe('下午好')
expect(getGreeting(21)).toBe('晚上好')
expect(getCompletionRate([{ status: '已完成' }, { status: '待上' }])).toBe(50)
expect(resolveSelectedDate(weekDays, todayInWeek)).toBe(todayInWeek)
expect(resolveSelectedDate(weekDays, todayOutsideWeek)).toBe(weekDays[0])
expect(findNextLesson(lessons, now)?.id).toBe(expectedLessonId)
```

- [ ] **Step 3: 运行测试并确认因模块不存在而失败**

运行：

```powershell
npm test -- src/lib/scheduleDashboard.test.ts
```

预期：FAIL，提示无法解析 `scheduleDashboard`。

- [ ] **Step 4: 实现最小纯函数**

导出：

```ts
getGreeting(hour: number): string
getCompletionRate(lessons: Pick<Lesson, 'status'>[]): number
resolveSelectedDate(weekDays: string[], todayIso: string): string
findNextLesson(lessons: Lesson[], now: Date): Lesson | null
```

- [ ] **Step 5: 运行测试并确认通过**

运行：

```powershell
npm test -- src/lib/scheduleDashboard.test.ts
```

预期：全部 PASS。

### Task 2: 实现移动课程操作面板

**Files:**
- Create: `app/frontend/src/components/schedule/MobileLessonActionsSheet.vue`
- Create: `app/frontend/src/components/schedule/MobileLessonActionsSheet.test.ts`

- [ ] **Step 1: 写组件失败测试**

覆盖以下行为：

```ts
// 待上课程显示：完成、请假、调课、编辑、加入日历、删除
// 已完成课程显示：恢复待上、编辑、加入日历、删除
// 点击“完成”发出 complete 事件并携带 lesson
// 点击遮罩或关闭按钮发出 close 事件
```

- [ ] **Step 2: 运行测试并确认因组件不存在而失败**

运行：

```powershell
npm test -- src/components/schedule/MobileLessonActionsSheet.test.ts
```

预期：FAIL，提示无法解析组件。

- [ ] **Step 3: 实现底部面板**

组件 props：

```ts
lesson: Lesson | null
currencySymbol: string
```

组件 emits：

```ts
close
complete(lesson)
restore(lesson)
cancel(lesson)
reschedule(lesson)
edit(lesson)
delete(lesson)
```

面板必须有遮罩、拖拽提示条、课程摘要、状态相关操作、44px 最小触控高度与 safe-area 底部间距。

- [ ] **Step 4: 运行组件测试并确认通过**

运行：

```powershell
npm test -- src/components/schedule/MobileLessonActionsSheet.test.ts
```

预期：全部 PASS。

### Task 3: 重构手机周视图为单日任务流

**Files:**
- Modify: `app/frontend/src/components/schedule/ScheduleBoard.vue`
- Create: `app/frontend/src/components/schedule/ScheduleBoard.test.ts`

- [ ] **Step 1: 写组件失败测试**

覆盖：

```ts
// 手机日期条默认选中今天
// 点击日期只显示该日课程
// 点击课程发出 open-mobile-actions
// 空日期显示“今天没有课程”
```

- [ ] **Step 2: 运行测试并确认新行为失败**

运行：

```powershell
npm test -- src/components/schedule/ScheduleBoard.test.ts
```

预期：FAIL，当前组件仍渲染七个折叠日并发出 `select-lesson`。

- [ ] **Step 3: 实现单日课程流**

保留桌面周网格；将 `< lg` 分支改为：

```text
周范围标题
七天日期条
当前日期课程计数/完成计数
按时间排序的课程卡片
```

新增事件：

```ts
(e: 'open-mobile-actions', lesson: Lesson): void
```

移除手机卡片内的状态按钮，保留状态徽章、备注摘要、时间与课时。

- [ ] **Step 4: 运行组件测试并确认通过**

运行：

```powershell
npm test -- src/components/schedule/ScheduleBoard.test.ts
```

预期：全部 PASS。

### Task 4: 增加 Lumina 页面头部与桌面概览

**Files:**
- Create: `app/frontend/src/components/schedule/ScheduleDashboardHeader.vue`
- Create: `app/frontend/src/components/schedule/ScheduleOverview.vue`
- Modify: `app/frontend/src/pages/DashboardPage.vue`

- [ ] **Step 1: 写头部与概览组件失败测试**

验证：

```ts
// 显示动态问候和教师姓名
// 今日摘要显示总课程数与完成率
// 点击“新建课程”发出 create
// 下一节课为空时显示明确空状态
```

- [ ] **Step 2: 运行测试并确认组件不存在**

运行：

```powershell
npm test -- src/components/schedule/ScheduleDashboardHeader.test.ts src/components/schedule/ScheduleOverview.test.ts
```

预期：FAIL。

- [ ] **Step 3: 实现组件并接入 DashboardPage**

`DashboardPage` 新增：

```ts
const mobileActionLesson = ref<Lesson | null>(null)
```

并将现有课表主体组织为：

```text
ScheduleDashboardHeader
桌面：[课表主体 | ScheduleOverview]
手机：课表主体 + 悬浮新建按钮
MobileLessonActionsSheet
```

状态成功后必须：

```ts
mobileActionLesson.value = null
await loadDashboard()
```

- [ ] **Step 4: 运行相关测试**

运行：

```powershell
npm test
```

预期：全部 PASS。

### Task 5: 应用 Lumina 外壳与设计令牌

**Files:**
- Modify: `app/frontend/src/styles/globals.css`
- Modify: `app/frontend/src/components/layout/AppShell.vue`
- Modify: `app/frontend/src/components/layout/MobileTabBar.vue`
- Modify: `app/frontend/src/pages/DashboardPage.vue`

- [ ] **Step 1: 更新设计令牌**

将主色、柔光背景、按钮、玻璃卡片、阴影和焦点环切换到紫粉体系，同时保留 success/warning/danger 语义色和暗色模式映射。

- [ ] **Step 2: 更新桌面侧栏**

加入 Lumina 渐变品牌标识、V3 导航选中态和本月已完成摘要；导航按钮保持键盘焦点可见。

- [ ] **Step 3: 更新移动底栏**

使用左右留白的悬浮玻璃容器、圆角与 active 渐变图标背景；保留 safe-area 与四个路由入口。

- [ ] **Step 4: 更新课表工具栏**

将日期导航、月/周/日切换、导出与批量操作置于新的卡片层级，不移除任何已有操作。

- [ ] **Step 5: 构建验证**

运行：

```powershell
npm run build
```

预期：TypeScript 与 Vite 构建成功，无错误。

### Task 6: 浏览器双端验收

**Files:**
- Modify as needed: `app/frontend/src/**/*.vue`
- Modify as needed: `app/frontend/src/styles/globals.css`

- [ ] **Step 1: 启动前后端**

运行前端开发服务器与现有后端，确认 API 可访问。

- [ ] **Step 2: 验收桌面端**

在 1440×900 检查：

```text
Lumina 侧栏
问候区与新建按钮
周网格和右侧概览
无横向溢出
原有拖拽、切换与批量入口可见
```

- [ ] **Step 3: 验收手机端**

在 390×844 检查：

```text
今日摘要和七天日期条
单日课程流
悬浮新建按钮
悬浮底部导航
课程点击后底部操作面板
44px 触控区域与 safe-area
```

- [ ] **Step 4: 运行最终验证**

运行：

```powershell
npm test
npm run build
```

预期：全部通过。
