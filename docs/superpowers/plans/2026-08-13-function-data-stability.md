# Function and Data Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可诊断、可重试且数据一致的前后端基础，验证课程事务、数据库恢复、日期统计和 PWA 更新在失败与边界场景下保持正确。

**Architecture:** 先在 Axios 与 FastAPI 中间件建立统一请求编号和错误语义，业务页面只消费稳定的 `AppError`。课程服务使用不提交的内部操作组合单条与批量事务；数据库恢复拆为验证、备份和原子替换服务；日期工具以项目时区为唯一业务日期来源；Service Worker 明确区分 API、导航和哈希静态资源。

**Tech Stack:** Vue 3、TypeScript、Axios、Vitest、FastAPI、SQLAlchemy、SQLite、pytest、FastAPI TestClient、Service Worker Cache API

---

## 文件职责与实施边界

- `app/frontend/src/api/error.ts`：集中式 `AppError` 类型和 Axios 错误归类。
- `app/frontend/src/api/requestId.ts`：生成前端逻辑请求编号。
- `app/frontend/src/api/client.ts`：请求编号、GET 重试和写请求不重试策略。
- `app/frontend/src/components/ui/ErrorNotice.vue`：简明错误、主动重试和折叠诊断详情。
- `app/frontend/src/pages/DashboardPage.vue`：保留旧数据并忽略过期响应。
- `app/backend/app/middleware/request_context.py`：请求编号、响应头和日志。
- `app/backend/tests/conftest.py`：临时 SQLite、真实 FastAPI 应用和 TestClient fixture。
- `app/backend/app/services/lesson_service.py`：状态矩阵、跨午夜冲突和批量事务。
- `app/backend/app/services/restore_service.py`：上传验证、一致性备份和原子替换。
- `app/backend/app/timeutil.py` 与前端 `src/lib/date.ts`：项目时区业务日期。
- `app/frontend/public/sw.js`：API 旁路、导航网络优先、静态资源缓存优先和版本清理。
- `app/frontend/src/composables/useServiceWorkerUpdate.ts`：非阻断更新提示与用户确认激活。

本计划不改 systemd、Caddy、Gunicorn worker 或生产部署脚本，这些属于第六阶段。

---

### Task 1: 前端集中错误模型

**Files:**
- Create: `app/frontend/src/api/error.ts`
- Create: `app/frontend/src/api/error.test.ts`
- Modify: `app/frontend/src/lib/formError.ts`
- Modify: `app/frontend/src/lib/formError.test.ts`

- [ ] **Step 1: 写错误归类失败测试**

构造 Axios 风格异常，断言无响应为 `network`、`ECONNABORTED` 为 `timeout`、422 为 `validation`、409 或 `time_conflict` 为 `conflict`、503 为 `server`，并覆盖 `status`、`requestId`、`detail`、`retryable`。

```ts
expect(toAppError({ code: 'ECONNABORTED', config: { headers: { 'X-Request-ID': 'req-timeout' } } }))
  .toMatchObject({ kind: 'timeout', requestId: 'req-timeout', retryable: true })
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/api/error.test.ts src/lib/formError.test.ts`

Expected: FAIL，`toAppError` 尚不存在。

- [ ] **Step 3: 实现稳定类型与映射**

```ts
export type AppErrorKind = 'network' | 'timeout' | 'server' | 'validation' | 'conflict' | 'unknown'
export interface AppError {
  kind: AppErrorKind
  message: string
  status?: number
  requestId: string
  detail?: unknown
  retryable: boolean
}
export function toAppError(error: unknown): AppError
```

课程冲突文案复用结构化 conflicts；`parseFormError` 改为消费 `toAppError`，保持现有组件的字符串契约。

- [ ] **Step 4: 运行测试、构建并提交**

Run: `cd app/frontend && npm test -- --run src/api/error.test.ts src/lib/formError.test.ts && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/api/error.ts app/frontend/src/api/error.test.ts app/frontend/src/lib/formError.ts app/frontend/src/lib/formError.test.ts
git commit -m "feat: centralize frontend API errors"
```

---

### Task 2: 请求编号与 GET 自动重试

**Files:**
- Create: `app/frontend/src/api/requestId.ts`
- Create: `app/frontend/src/api/requestId.test.ts`
- Modify: `app/frontend/src/api/client.ts`
- Create: `app/frontend/src/api/client.test.ts`

- [ ] **Step 1: 写请求行为失败测试**

用 Axios 自定义 adapter 和 fake timers 覆盖：首次逻辑请求生成 `X-Request-ID`；GET 的网络错误、超时、502/503/504 最多重试两次；所有尝试使用相同编号；POST/PATCH/DELETE 只调用一次；主动取消不重试。

```ts
expect(adapter).toHaveBeenCalledTimes(3)
expect(adapter.mock.calls.map(([config]) => config.headers['X-Request-ID']))
  .toEqual(['req-fixed', 'req-fixed', 'req-fixed'])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/api/requestId.test.ts src/api/client.test.ts`

Expected: FAIL，当前客户端没有请求编号和重试策略。

- [ ] **Step 3: 实现拦截器与重试元数据**

扩展 Axios config 的 `requestId` 和 `retryCount`。请求拦截器仅在编号缺失时生成；响应拦截器仅对 GET 和允许错误递增计数，退避 150ms、300ms，使用 `api.request(config)` 重试并沿用编号。

- [ ] **Step 4: 运行 API、全量测试与构建**

Run: `cd app/frontend && npm test -- --run src/api && npm test -- --run && npm run build`

Expected: PASS，写请求 adapter 调用次数始终为 1。

- [ ] **Step 5: 提交检查点**

```powershell
git add app/frontend/src/api/requestId.ts app/frontend/src/api/requestId.test.ts app/frontend/src/api/client.ts app/frontend/src/api/client.test.ts
git commit -m "feat: add diagnostic GET retry policy"
```

---

### Task 3: 后端请求上下文与测试基础设施

**Files:**
- Create: `app/backend/app/middleware/__init__.py`
- Create: `app/backend/app/middleware/request_context.py`
- Modify: `app/backend/app/main.py`
- Create: `app/backend/tests/conftest.py`
- Create: `app/backend/tests/test_request_context.py`

- [ ] **Step 1: 建立临时应用 fixture**

使用 `tmp_path / "test.db"` 创建 SQLite engine，运行 `Base.metadata.create_all()`，覆盖 `get_db`。测试应用挂载真实路由和请求中间件，但不启动 scheduler。fixture 形态固定为：

```py
@pytest.fixture
def client(test_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(test_app) as value:
        yield value
```

- [ ] **Step 2: 写请求编号失败测试**

覆盖客户端编号被回传、缺失编号由后端生成、非法超长编号被替换；使用 `caplog` 断言日志包含编号、方法、路径、状态码和耗时。

- [ ] **Step 3: 运行测试确认失败**

Run: `cd app/backend && python -m pytest tests/test_request_context.py -q`

Expected: FAIL，中间件和应用工厂不存在。

- [ ] **Step 4: 实现中间件与应用工厂**

新增 `create_app(*, start_background_jobs: bool = True) -> FastAPI`，生产全局 `app = create_app()`；测试调用 `create_app(start_background_jobs=False)`。中间件接受 `[A-Za-z0-9._-]{1,128}`，否则生成 `uuid4().hex`。

- [ ] **Step 5: 运行后端基线并提交**

Run: `cd app/backend && python -m pytest -q && python -m compileall app`

Expected: PASS。

```powershell
git add app/backend/app/main.py app/backend/app/middleware app/backend/tests/conftest.py app/backend/tests/test_request_context.py
git commit -m "feat: trace requests across the API"
```

---

### Task 4: 页面旧数据、诊断详情与过期响应

**Files:**
- Create: `app/frontend/src/components/ui/ErrorNotice.vue`
- Create: `app/frontend/src/components/ui/ErrorNotice.test.ts`
- Modify: `app/frontend/src/components/stats/StatsPanel.vue`
- Modify: `app/frontend/src/components/students/StudentOverview.vue`
- Modify: `app/frontend/src/components/students/TemplateManager.vue`
- Modify: `app/frontend/src/pages/DashboardPage.vue`
- Modify: `app/frontend/src/pages/DashboardPage.test.ts`

- [ ] **Step 1: 写错误详情组件失败测试**

默认只显示简明文案；点击“查看详情”后显示类型、状态码、请求编号和 detail；点击“重新加载”发出 retry。

- [ ] **Step 2: 写页面稳定性失败测试**

覆盖课表刷新失败保留原 lessons；学生详情与模板刷新失败保留最后成功数据；快速切换周、学生和统计区间时晚到旧响应不覆盖新数据；取消错误不显示提示。

- [ ] **Step 3: 运行测试确认失败**

Run: `cd app/frontend && npm test -- --run src/components/ui/ErrorNotice.test.ts src/pages/DashboardPage.test.ts`

Expected: FAIL，当前学生详情和模板 catch 会清空数据，课表没有请求序号。

- [ ] **Step 4: 接入 `AppError` 和请求序号**

页面错误 ref 改为 `AppError | null`；各加载函数使用 `toAppError`。为课表、学生详情、模板和统计分别维护递增 token，仅当前 token 可更新数据、错误和 loading；取消属于正常控制流。

- [ ] **Step 5: 迁移错误呈现**

三个业务组件使用 `ErrorNotice`，继续通过 retry 事件通知父页面；存在旧数据时错误条位于数据上方，不替换内容。

- [ ] **Step 6: 运行页面、全量测试、构建并提交**

Run: `cd app/frontend && npm test -- --run src/pages/DashboardPage.test.ts src/components/ui/ErrorNotice.test.ts && npm test -- --run && npm run build`

Expected: PASS。

```powershell
git add app/frontend/src/components/ui/ErrorNotice.vue app/frontend/src/components/ui/ErrorNotice.test.ts app/frontend/src/components/stats/StatsPanel.vue app/frontend/src/components/students/StudentOverview.vue app/frontend/src/components/students/TemplateManager.vue app/frontend/src/pages/DashboardPage.vue app/frontend/src/pages/DashboardPage.test.ts
git commit -m "feat: preserve data through request failures"
```

---

### Task 5: 课程状态、冲突和批量事务

**Files:**
- Modify: `app/backend/app/services/lesson_service.py`
- Modify: `app/backend/app/schemas/lesson.py`
- Create: `app/backend/tests/test_lesson_service.py`
- Create: `app/backend/tests/test_lesson_routes.py`

- [ ] **Step 1: 写状态矩阵失败测试**

参数化覆盖设计文档中的允许转换、幂等同状态和非法转换。非法转换断言 409 与 `invalid_status_transition`，并断言数据库状态不变。

- [ ] **Step 2: 写冲突和事务失败测试**

覆盖普通重叠、首尾相接、跨午夜与次日课程、恢复冲突、调课排除原课程、模板重复生成；批量第二项失败时断言第一项没有被提交。

```py
with pytest.raises(HTTPException):
    lesson_service.bulk_action(db, lesson_ids=[valid.id, invalid.id], action="complete")
db.expire_all()
assert db.get(Lesson, valid.id).status == "待上"
```

- [ ] **Step 3: 运行测试确认缺陷**

Run: `cd app/backend && python -m pytest tests/test_lesson_service.py tests/test_lesson_routes.py -q`

Expected: FAIL，当前循环调用单条函数时提前 commit，跨午夜只查询同一天。

- [ ] **Step 4: 提取不提交的内部操作**

实现 `_transition_lesson`、`_cancel_lesson`、`_restore_lesson`、`_delete_lesson`，内部只 mutate/flush。公开单条函数成功后 commit；批量函数先加载并验证全部 ID，再统一 commit，异常时 rollback。

- [ ] **Step 5: 实现跨午夜冲突范围**

将课程转换为 `[datetime start, datetime end)`，候选查询 `on_date - 1` 至 `on_date + 1` 后逐个比较；首尾相接继续不冲突。

- [ ] **Step 6: 运行课程、完整后端测试并提交**

Run: `cd app/backend && python -m pytest tests/test_lesson_service.py tests/test_lesson_routes.py -q && python -m pytest -q`

Expected: PASS。

```powershell
git add app/backend/app/services/lesson_service.py app/backend/app/schemas/lesson.py app/backend/tests/test_lesson_service.py app/backend/tests/test_lesson_routes.py
git commit -m "feat: enforce transactional lesson rules"
```

---

### Task 6: 数据库恢复安全

**Files:**
- Modify: `app/backend/app/config.py`
- Create: `app/backend/app/services/restore_service.py`
- Modify: `app/backend/app/routers/backup.py`
- Create: `app/backend/tests/test_restore_service.py`
- Create: `app/backend/tests/test_backup_routes.py`

- [ ] **Step 1: 写验证与不变性失败测试**

覆盖非 SQLite、损坏文件、缺核心表、超体积、完整性失败、备份失败和替换失败。每个失败用例记录原库哈希，调用后断言哈希不变且无临时文件残留。

- [ ] **Step 2: 写成功恢复失败测试**

构造含核心表和 `alembic_version` 的合法 SQLite 文件，恢复后断言新数据可读、旧库副本名包含 `YYYYMMDD-HHMMSS`、返回路径存在。

- [ ] **Step 3: 运行测试确认直接覆盖缺陷**

Run: `cd app/backend && python -m pytest tests/test_restore_service.py tests/test_backup_routes.py -q`

Expected: FAIL，当前路由不验证内容并直接覆盖目标路径。

- [ ] **Step 4: 实现恢复服务**

增加 `MAX_RESTORE_BYTES` 配置；服务提供 `validate_sqlite(path)`、`create_consistent_backup(source, target)`、`restore_database(upload, db_path, max_bytes)`。临时文件使用 `NamedTemporaryFile(dir=db_path.parent, delete=False)`，替换使用 `os.replace`。

- [ ] **Step 5: 缩减路由并验证**

路由只校验确认头、调用服务，并把验证错误映射为 422、操作错误映射为 500；不再把完整上传读入内存。

Run: `cd app/backend && python -m pytest tests/test_restore_service.py tests/test_backup_routes.py -q && python -m pytest -q`

Expected: PASS。

- [ ] **Step 6: 提交检查点**

```powershell
git add app/backend/app/config.py app/backend/app/services/restore_service.py app/backend/app/routers/backup.py app/backend/tests/test_restore_service.py app/backend/tests/test_backup_routes.py
git commit -m "feat: restore SQLite databases atomically"
```

---

### Task 7: 项目时区和统计边界

**Files:**
- Modify: `app/backend/app/timeutil.py`
- Modify: `app/backend/app/services/stats_service.py`
- Create: `app/backend/tests/test_timeutil.py`
- Modify: `app/backend/tests/test_stats_service.py`
- Modify: `app/frontend/src/lib/date.ts`
- Create: `app/frontend/src/lib/date.test.ts`
- Modify: `app/frontend/src/pages/DashboardPage.vue`

- [ ] **Step 1: 写日期边界失败测试**

后端覆盖 Asia/Shanghai 与 UTC 日期不同、周一/周日起始、月末、跨年和闰年。前端用 `formatInTimeZone` 断言同一时刻在项目时区得到正确业务日期。

- [ ] **Step 2: 写统计口径回归测试**

为四种课程状态构造固定数据，断言预计收入、实际收入、有效课时、完成率、请假数、调课数和历史同期，并覆盖零分母。

- [ ] **Step 3: 运行测试确认本地时区依赖**

Run: `cd app/backend && python -m pytest tests/test_timeutil.py tests/test_stats_service.py -q`

Run: `cd app/frontend && npm test -- --run src/lib/date.test.ts`

Expected: FAIL，前端直接使用浏览器时区，后端 TZ 在导入时固定。

- [ ] **Step 4: 注入业务时区并统一口径**

后端 `now(timezone_name: str | None = None)` 动态解析配置或显式参数；`today()` 调用它。前端新增 `getBusinessTodayIso(timezone, instant = new Date())`，Dashboard 使用设置时区。后端统一 `ACTIVE_STATUSES`、`EARNED_STATUSES` 和零分母完成率规则。

- [ ] **Step 5: 运行前后端完整回归并提交**

Run: `cd app/backend && python -m pytest -q`

Run: `cd app/frontend && npm test -- --run && npm run build`

Expected: PASS。

```powershell
git add app/backend/app/timeutil.py app/backend/app/services/stats_service.py app/backend/tests/test_timeutil.py app/backend/tests/test_stats_service.py app/frontend/src/lib/date.ts app/frontend/src/lib/date.test.ts app/frontend/src/pages/DashboardPage.vue
git commit -m "feat: align business dates and statistics"
```

---

### Task 8: PWA 缓存与更新流程

**Files:**
- Modify: `app/frontend/public/sw.js`
- Create: `app/frontend/public/offline.html`
- Create: `app/frontend/src/lib/serviceWorkerPolicy.ts`
- Create: `app/frontend/src/lib/serviceWorkerPolicy.test.ts`
- Create: `app/frontend/src/composables/useServiceWorkerUpdate.ts`
- Create: `app/frontend/src/composables/useServiceWorkerUpdate.test.ts`
- Modify: `app/frontend/src/main.ts`
- Modify: `app/frontend/src/components/layout/AppShell.vue`

- [ ] **Step 1: 写缓存策略失败测试**

请求分类纯函数断言 `/api/*` 为 `network-only`，带哈希 JS/CSS 为 `cache-first`，导航为 `network-first`，其他资源为 `network-first`。

- [ ] **Step 2: 写更新协调失败测试**

模拟 registration.waiting、updatefound 和 controllerchange；新版本只显示提示，不自动刷新；用户确认后只发送一次 `SKIP_WAITING`，controllerchange 只刷新一次。

- [ ] **Step 3: 运行测试确认旧行为失败**

Run: `cd app/frontend && npm test -- --run src/lib/serviceWorkerPolicy.test.ts src/composables/useServiceWorkerUpdate.test.ts`

Expected: FAIL，当前安装立即 `skipWaiting()` 且所有 GET 都缓存优先。

- [ ] **Step 4: 实现缓存策略**

缓存名改为 `kebiao-static-v2`；安装预缓存离线页、manifest、图标但不主动激活；API 直接 fetch；导航网络失败回退 offline；哈希资产缓存优先；activate 删除 `kebiao-cache-v1` 和所有非当前缓存。

- [ ] **Step 5: 接入更新提示**

`useServiceWorkerUpdate` 暴露 `updateAvailable`、`applyUpdate()`、`dismissUpdate()`；AppShell 显示“新版本已就绪”，用户点击更新才激活。表单操作中不自动刷新。

- [ ] **Step 6: 运行 PWA、全量测试、构建并提交**

Run: `cd app/frontend && npm test -- --run src/lib/serviceWorkerPolicy.test.ts src/composables/useServiceWorkerUpdate.test.ts && npm test -- --run && npm run build`

Expected: PASS，构建产物包含 `offline.html` 与新 `sw.js`。

```powershell
git add app/frontend/public/sw.js app/frontend/public/offline.html app/frontend/src/lib/serviceWorkerPolicy.ts app/frontend/src/lib/serviceWorkerPolicy.test.ts app/frontend/src/composables/useServiceWorkerUpdate.ts app/frontend/src/composables/useServiceWorkerUpdate.test.ts app/frontend/src/main.ts app/frontend/src/components/layout/AppShell.vue
git commit -m "feat: prevent stale PWA API data"
```

---

### Task 9: 核心联调、调度幂等与第五阶段验收

**Files:**
- Create: `app/backend/tests/test_scheduler_jobs.py`
- Create: `app/backend/tests/test_core_integration.py`
- Create: `app/frontend/src/api/contracts.test.ts`
- Modify: `docs/superpowers/plans/2026-08-13-function-data-stability.md`

- [ ] **Step 1: 写调度幂等测试**

固定时间后连续执行两次自动完成和滚动生成；第一次返回实际影响数，第二次返回 0；断言课程状态和模板实例不重复。

- [ ] **Step 2: 写真实应用核心集成测试**

通过 TestClient 执行创建学生、创建课程、制造冲突、完成/请假/恢复、批量失败回滚、查询统计和无效恢复；断言前端依赖字段和结构化错误稳定存在。

- [ ] **Step 3: 写前端契约测试**

用自定义 Axios adapter 返回集成层固定 JSON，验证各 API 包装器解析结果以及 `toAppError` 对结构化错误的映射。

- [ ] **Step 4: 运行分层验证**

Run: `cd app/backend && python -m pytest -q && python -m compileall app`

Run: `cd app/frontend && npm test -- --run && npm run build`

Expected: 全部 PASS，零失败。

- [ ] **Step 5: 执行 PWA 浏览器验收**

使用生产构建和 Playwright，验证在线加载、离线页、API 不进入 Cache Storage、从 `kebiao-cache-v1` 升级、更新提示和用户确认刷新；桌面 1440×900 与移动 390×844 各执行一次。

- [ ] **Step 6: 执行差异与数据安全检查**

Run: `git diff --check && git status --short`

确认测试没有写入 `app/backend/data` 或开发数据库，构建产物、临时恢复文件和 Vite 生成文件不进入提交。

- [ ] **Step 7: 记录验收并提交**

在本计划末尾记录测试数量、构建结果、浏览器视口、PWA 场景和非阻断项。

```powershell
git add app/backend/tests/test_scheduler_jobs.py app/backend/tests/test_core_integration.py app/frontend/src/api/contracts.test.ts docs/superpowers/plans/2026-08-13-function-data-stability.md
git commit -m "test: verify phase five stability"
```

---

## 最终验收清单

- [ ] GET 网络、超时、502、503、504 最多重试两次，逻辑请求编号保持一致。
- [ ] 写请求和主动取消请求不自动重试。
- [ ] 前后端响应头和日志可通过请求编号关联。
- [ ] 刷新失败保留旧数据，过期响应不能覆盖新数据。
- [ ] 课程状态矩阵、跨午夜冲突和批量事务有自动化覆盖。
- [ ] 恢复无效数据库不会修改当前数据库或遗留临时文件。
- [ ] 项目时区、周/月/年/闰年和统计口径通过回归测试。
- [ ] Service Worker 不缓存 API，升级删除 `kebiao-cache-v1`。
- [ ] 前端、后端、集成、调度、PWA 和生产构建均通过。
- [ ] 未引入登录鉴权，也未修改第六阶段部署进程模型。
