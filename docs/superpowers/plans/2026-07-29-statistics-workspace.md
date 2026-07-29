# 数据统计工作台重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将统计页重构为响应式决策流工作台，提供准确的经营指标、同期比较、趋势、学生贡献、异常关注和学生联动。

**Architecture:** 后端在现有统计服务上补充聚合字段和明确区间的同期比较，不修改数据库；前端将 `StatsPanel` 拆为四个展示组件，并把计算逻辑集中到 `statsWorkspace.ts`。`DashboardPage` 单独编排统计请求、竞态保护、错误保留、重试、导出反馈和学生查询参数。

**Tech Stack:** FastAPI、SQLAlchemy、Pydantic、Pytest、Vue 3、TypeScript、Vue Router、Vitest、Vue Test Utils、Tailwind CSS、SVG

---

## 文件结构

### 后端

- `app/backend/tests/test_stats_service.py`：统计口径和同期区间服务测试。
- `app/backend/app/schemas/stats.py`：扩展 `RangeStats` 响应类型。
- `app/backend/app/services/stats_service.py`：聚合指标、活跃学生和明确区间同期比较。
- `app/backend/app/routers/stats.py`：接收比较区间参数。
- `API.md`：同步统计接口参数和响应字段。

### 前端

- `app/frontend/src/lib/statsWorkspace.ts`：完成率、增长文案、趋势点、贡献比例和移动端记录裁剪。
- `app/frontend/src/lib/statsWorkspace.test.ts`：纯函数测试。
- `app/frontend/src/components/stats/StatsMetricGrid.vue`：四项核心指标。
- `app/frontend/src/components/stats/StatsMetricGrid.test.ts`：指标组件测试。
- `app/frontend/src/components/stats/StatsTrendChart.vue`：桌面双指标、手机单指标趋势图。
- `app/frontend/src/components/stats/StatsTrendChart.test.ts`：趋势图测试。
- `app/frontend/src/components/stats/StudentContribution.vue`：学生贡献列表和跳转事件。
- `app/frontend/src/components/stats/StudentContribution.test.ts`：贡献组件测试。
- `app/frontend/src/components/stats/AttentionList.vue`：异常记录、展开和空状态。
- `app/frontend/src/components/stats/AttentionList.test.ts`：异常组件测试。
- `app/frontend/src/components/stats/StatsPanel.vue`：决策流布局和子组件事件编排。
- `app/frontend/src/components/stats/StatsPanel.test.ts`：整体布局、错误和重试测试。
- `app/frontend/src/api/types.ts`：扩展 `RangeStats` 类型。
- `app/frontend/src/api/stats.ts`：同期比较区间参数。
- `app/frontend/src/pages/DashboardPage.vue`：独立统计请求、竞态、错误、导出和学生查询参数。
- `app/frontend/src/pages/DashboardPage.test.ts`：统计页面集成测试。

---

### Task 1: 后端范围统计口径

**Files:**
- Create: `app/backend/tests/test_stats_service.py`
- Modify: `app/backend/app/schemas/stats.py`
- Modify: `app/backend/app/services/stats_service.py`

- [ ] **Step 1: 写范围统计失败测试**

在 `app/backend/tests/test_stats_service.py` 创建内存数据库，并覆盖四种课程状态、学生去重和原有字段兼容：

```python
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Lesson, Student
from app.services import stats_service


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def add_student(db: Session, name: str) -> Student:
    student = Student(name=name, color="#7c3aed", hourly_rate=200)
    db.add(student)
    db.flush()
    return student


def add_lesson(
    db: Session,
    student_id: int,
    status: str,
    price: float,
    start_time: str,
) -> None:
    db.add(
        Lesson(
            student_id=student_id,
            date=date(2026, 7, 15),
            start_time=start_time,
            duration_hours=1,
            status=status,
            price=price,
        )
    )


def test_range_stats_exposes_decision_metrics(db: Session):
    active = add_student(db, "林晓")
    leave_only = add_student(db, "周然")
    moved_only = add_student(db, "顾宁")
    add_lesson(db, active.id, "已完成", 200, "09:00")
    add_lesson(db, active.id, "待上", 200, "10:00")
    add_lesson(db, leave_only.id, "请假", 300, "11:00")
    add_lesson(db, moved_only.id, "已调课", 400, "12:00")
    db.commit()

    result = stats_service.range_stats(
        db,
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 31),
        granularity="day",
    )

    assert result.total_income == 200
    assert result.total_hours == 2
    assert result.total_lessons == 2
    assert result.completed_lessons == 1
    assert result.pending_lessons == 1
    assert result.leave_count == 1
    assert result.reschedule_count == 1
    assert result.active_students == 2
```

- [ ] **Step 2: 运行测试确认响应字段不存在**

Run:

```powershell
cd app/backend
python -m pytest tests/test_stats_service.py::test_range_stats_exposes_decision_metrics -v
```

Expected: FAIL，`RangeStats` 没有 `completed_lessons` 等字段。

- [ ] **Step 3: 扩展 Pydantic 响应**

在 `app/backend/app/schemas/stats.py` 的 `RangeStats` 中加入：

```python
class RangeStats(BaseModel):
    from_date: date
    to_date: date
    granularity: str
    total_income: float
    total_hours: float
    total_lessons: int
    completed_lessons: int
    pending_lessons: int
    leave_count: int
    reschedule_count: int
    active_students: int
    buckets: list[RangeBucket]
```

- [ ] **Step 4: 实现状态聚合和活跃学生去重**

在 `range_stats()` 中查询区间内全部状态课程；保留有效课程 bucket 口径，并用明确集合生成新增字段：

```python
all_rows = db.execute(
    select(Lesson).where(
        Lesson.date >= from_date,
        Lesson.date <= to_date,
    )
).scalars().all()

active_rows = [row for row in all_rows if row.status in ACTIVE_STATUSES]
completed = [row for row in all_rows if row.status == "已完成"]
pending = [row for row in all_rows if row.status == "待上"]
leave_rows = [row for row in all_rows if row.status == "请假"]
rescheduled_rows = [row for row in all_rows if row.status == "已调课"]
active_student_ids = {
    row.student_id
    for row in all_rows
    if row.status in ("待上", "已完成", "请假")
}
```

Bucket 构建必须继续区分收入和有效课程：

```python
buckets: dict[str, dict] = {}
for row in completed:
    key = _bucket_key(row.date, granularity)
    bucket = buckets.setdefault(
        key,
        {"income": 0.0, "hours": 0.0, "lesson_count": 0},
    )
    bucket["income"] += row.price
for row in active_rows:
    key = _bucket_key(row.date, granularity)
    bucket = buckets.setdefault(
        key,
        {"income": 0.0, "hours": 0.0, "lesson_count": 0},
    )
    bucket["hours"] += row.duration_hours
    bucket["lesson_count"] += 1
```

返回模型时使用：

```python
return RangeStats(
    from_date=from_date,
    to_date=to_date,
    granularity=granularity,
    total_income=float(sum(row.price for row in completed)),
    total_hours=float(sum(row.duration_hours for row in active_rows)),
    total_lessons=len(active_rows),
    completed_lessons=len(completed),
    pending_lessons=len(pending),
    leave_count=len(leave_rows),
    reschedule_count=len(rescheduled_rows),
    active_students=len(active_student_ids),
    buckets=bucket_list,
)
```

- [ ] **Step 5: 运行范围统计测试**

Run:

```powershell
cd app/backend
python -m pytest tests/test_stats_service.py::test_range_stats_exposes_decision_metrics -v
```

Expected: PASS。

- [ ] **Step 6: 提交后端范围统计**

```powershell
git add app/backend/tests/test_stats_service.py app/backend/app/schemas/stats.py app/backend/app/services/stats_service.py
git commit -m "feat: extend range statistics metrics"
```

---

### Task 2: 明确区间的同期比较

**Files:**
- Modify: `app/backend/tests/test_stats_service.py`
- Modify: `app/backend/app/services/stats_service.py`
- Modify: `app/backend/app/routers/stats.py`
- Modify: `API.md`

- [ ] **Step 1: 写同期区间失败测试**

在 `app/backend/tests/test_stats_service.py` 增加：

```python
@pytest.mark.parametrize(
    ("from_date", "to_date", "period", "expected"),
    [
        (
            date(2026, 7, 29),
            date(2026, 7, 29),
            "day",
            (date(2026, 7, 28), date(2026, 7, 28)),
        ),
        (
            date(2026, 7, 27),
            date(2026, 7, 29),
            "week",
            (date(2026, 7, 20), date(2026, 7, 22)),
        ),
        (
            date(2026, 7, 1),
            date(2026, 7, 29),
            "month",
            (date(2026, 6, 1), date(2026, 6, 29)),
        ),
        (
            date(2026, 7, 1),
            date(2026, 7, 31),
            "month",
            (date(2026, 6, 1), date(2026, 6, 30)),
        ),
    ],
)
def test_previous_period_uses_matching_natural_range(
    from_date: date,
    to_date: date,
    period: str,
    expected: tuple[date, date],
):
    assert stats_service.previous_period(from_date, to_date, period) == expected


def test_comparison_uses_requested_historical_range(db: Session):
    student = add_student(db, "林晓")
    db.add_all(
        [
            Lesson(
                student_id=student.id,
                date=date(2026, 6, 10),
                start_time="09:00",
                duration_hours=1,
                status="已完成",
                price=100,
            ),
            Lesson(
                student_id=student.id,
                date=date(2026, 7, 10),
                start_time="09:00",
                duration_hours=2,
                status="已完成",
                price=200,
            ),
        ]
    )
    db.commit()

    result = stats_service.comparison(
        db,
        period="month",
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 31),
    )

    assert result.current_income == 200
    assert result.previous_income == 100
    assert result.income_growth_pct == 100
```

- [ ] **Step 2: 运行测试确认新签名和辅助函数不存在**

Run:

```powershell
cd app/backend
python -m pytest tests/test_stats_service.py -v
```

Expected: FAIL，`previous_period` 不存在，`comparison()` 不接受 `from_date` 与 `to_date`。

- [ ] **Step 3: 实现上一等价自然周期**

在 `stats_service.py` 新增：

```python
def previous_period(
    from_date: date,
    to_date: date,
    period: str,
) -> tuple[date, date]:
    if from_date > to_date:
        raise ValueError("from_date 不能晚于 to_date")
    elapsed_days = (to_date - from_date).days
    if period == "day":
        previous = from_date - timedelta(days=1)
        return previous, previous
    if period == "week":
        previous_start = from_date - timedelta(days=7)
        return previous_start, previous_start + timedelta(days=elapsed_days)
    if period == "month":
        previous_anchor = from_date - timedelta(days=1)
        previous_start = month_start(previous_anchor)
        previous_end = min(
            previous_start + timedelta(days=elapsed_days),
            month_end(previous_anchor),
        )
        return previous_start, previous_end
    raise ValueError("period 必须为 day/week/month")
```

将 `comparison` 签名改为：

```python
def comparison(
    db: Session,
    period: str = "week",
    from_date: date | None = None,
    to_date: date | None = None,
) -> ComparisonStats:
```

区间选择和返回值使用完整逻辑：

```python
if (from_date is None) != (to_date is None):
    raise ValueError("from_date 和 to_date 必须同时提供")

if from_date is None or to_date is None:
    today_ = today()
    if period == "day":
        current_start = current_end = today_
    elif period == "week":
        current_start, current_end = week_start(today_), today_
    elif period == "month":
        current_start, current_end = month_start(today_), today_
    else:
        raise ValueError("period 必须为 day/week/month")
else:
    current_start, current_end = from_date, to_date

previous_start, previous_end = previous_period(
    current_start,
    current_end,
    period,
)
current_income = _sum_in_range(
    db, current_start, current_end, EARNED_STATUSES
)[0]
previous_income = _sum_in_range(
    db, previous_start, previous_end, EARNED_STATUSES
)[0]
_, current_hours, current_lessons = _sum_in_range(
    db, current_start, current_end
)
_, previous_hours, previous_lessons = _sum_in_range(
    db, previous_start, previous_end
)
return ComparisonStats(
    period=period,
    current_income=current_income,
    previous_income=previous_income,
    income_growth_pct=_growth_pct(current_income, previous_income),
    current_hours=current_hours,
    previous_hours=previous_hours,
    hours_growth_pct=_growth_pct(current_hours, previous_hours),
    current_lessons=current_lessons,
    previous_lessons=previous_lessons,
)
```

- [ ] **Step 4: 扩展路由参数**

在 `app/backend/app/routers/stats.py`：

```python
@router.get("/comparison", response_model=ComparisonStats)
def stats_comparison(
    period: str = Query("week", pattern="^(day|week|month)$"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    if (from_date is None) != (to_date is None):
        raise HTTPException(status_code=422, detail="from 和 to 必须同时提供")
    return stats_service.comparison(
        db,
        period=period,
        from_date=from_date,
        to_date=to_date,
    )
```

同时从 FastAPI 导入 `HTTPException`。

- [ ] **Step 5: 更新 API 文档**

在 `API.md`：

- 将 `/stats/range` 响应补充 `completed_lessons`、`pending_lessons`、`leave_count`、`reschedule_count`、`active_students`。
- 将 `/stats/comparison` 参数写为 `from`、`to`、`period=day|week|month`。
- 说明缺少 `from` 和 `to` 时保留当前周期兼容行为。

- [ ] **Step 6: 运行后端测试**

Run:

```powershell
cd app/backend
python -m pytest tests/test_stats_service.py -v
```

Expected: 所有统计服务测试 PASS。

- [ ] **Step 7: 提交同期比较**

```powershell
git add app/backend/tests/test_stats_service.py app/backend/app/services/stats_service.py app/backend/app/routers/stats.py API.md
git commit -m "feat: compare explicit statistics periods"
```

---

### Task 3: 前端统计类型与纯逻辑

**Files:**
- Create: `app/frontend/src/lib/statsWorkspace.ts`
- Create: `app/frontend/src/lib/statsWorkspace.test.ts`
- Modify: `app/frontend/src/api/types.ts`
- Modify: `app/frontend/src/api/stats.ts`

- [ ] **Step 1: 写纯函数失败测试**

在 `statsWorkspace.test.ts` 覆盖：

```ts
import { describe, expect, it } from 'vitest'
import {
  calculateCompletionRate,
  contributionPercent,
  fillTrendPoints,
  formatGrowth,
  visibleAttentionItems,
} from './statsWorkspace'

describe('statistics workspace helpers', () => {
  it('calculates completion rate with leave in the denominator', () => {
    expect(calculateCompletionRate(6, 2, 2)).toBe(60)
    expect(calculateCompletionRate(0, 0, 0)).toBe(0)
  })

  it('formats comparable growth without inventing zero-baseline growth', () => {
    expect(formatGrowth(12.45)).toEqual({ label: '较上期 ↑12.5%', tone: 'positive' })
    expect(formatGrowth(-4)).toEqual({ label: '较上期 ↓4.0%', tone: 'negative' })
    expect(formatGrowth(0)).toEqual({ label: '与上期持平', tone: 'neutral' })
    expect(formatGrowth(null)).toEqual({ label: '上期暂无数据', tone: 'muted' })
  })

  it('fills missing daily trend points', () => {
    const points = fillTrendPoints(
      {
        from_date: '2026-07-01',
        to_date: '2026-07-03',
        granularity: 'day',
        total_income: 200,
        total_hours: 2,
        total_lessons: 2,
        completed_lessons: 1,
        pending_lessons: 1,
        leave_count: 0,
        reschedule_count: 0,
        active_students: 1,
        buckets: [
          { bucket: '2026-07-01', income: 200, hours: 1, lesson_count: 1 },
          { bucket: '2026-07-03', income: 0, hours: 1, lesson_count: 1 },
        ],
      },
    )
    expect(points.map((point) => point.bucket)).toEqual([
      '2026-07-01',
      '2026-07-02',
      '2026-07-03',
    ])
    expect(points[1].income).toBe(0)
  })

  it('normalizes contribution and mobile attention defaults', () => {
    expect(contributionPercent(250, 500)).toBe(50)
    expect(contributionPercent(0, 0)).toBe(0)
    expect(visibleAttentionItems([1, 2, 3, 4], false)).toEqual([1, 2, 3])
    expect(visibleAttentionItems([1, 2, 3, 4], true)).toHaveLength(4)
  })
})
```

- [ ] **Step 2: 运行测试确认模块不存在**

Run:

```powershell
cd app/frontend
npm test -- --run src/lib/statsWorkspace.test.ts
```

Expected: FAIL，无法解析 `statsWorkspace`。

- [ ] **Step 3: 扩展前端类型和 API**

在 `RangeStats` 增加与后端一致的五个字段：

```ts
completed_lessons: number
pending_lessons: number
leave_count: number
reschedule_count: number
active_students: number
```

将比较 API 改为：

```ts
comparison: (
  from: string,
  to: string,
  period: 'day' | 'week' | 'month',
) =>
  api
    .get<ComparisonStats>('/stats/comparison', {
      params: { from, to, period },
    })
    .then((response) => response.data),
```

- [ ] **Step 4: 实现纯函数**

在 `statsWorkspace.ts` 导出：

```ts
import type { RangeStats, RangeBucket } from '@/api/types'

export type GrowthTone = 'positive' | 'negative' | 'neutral' | 'muted'

export function calculateCompletionRate(
  completed: number,
  pending: number,
  leave: number,
): number {
  const denominator = completed + pending + leave
  return denominator ? Math.round((completed / denominator) * 100) : 0
}

export function formatGrowth(value: number | null): {
  label: string
  tone: GrowthTone
} {
  if (value === null) return { label: '上期暂无数据', tone: 'muted' }
  if (value > 0) return { label: `较上期 ↑${value.toFixed(1)}%`, tone: 'positive' }
  if (value < 0) return { label: `较上期 ↓${Math.abs(value).toFixed(1)}%`, tone: 'negative' }
  return { label: '与上期持平', tone: 'neutral' }
}

export function contributionPercent(value: number, maximum: number): number {
  if (maximum <= 0) return 0
  return Math.round(Math.max(0, Math.min(1, value / maximum)) * 100)
}

export function visibleAttentionItems<T>(items: T[], expanded: boolean): T[] {
  return expanded ? items : items.slice(0, 3)
}
```

`fillTrendPoints(range)` 对 `day` 粒度在 `from_date` 到 `to_date` 之间补零；`week` 和 `month` 粒度保留后端自然 bucket 顺序：

```ts
const emptyBucket = (bucket: string): RangeBucket => ({
  bucket,
  income: 0,
  hours: 0,
  lesson_count: 0,
})

export function fillTrendPoints(range: RangeStats): RangeBucket[] {
  const ordered = [...range.buckets].sort((left, right) =>
    left.bucket.localeCompare(right.bucket),
  )
  if (range.granularity !== 'day') return ordered

  const byDate = new Map(ordered.map((bucket) => [bucket.bucket, bucket]))
  const cursor = new Date(`${range.from_date}T00:00:00`)
  const end = new Date(`${range.to_date}T00:00:00`)
  const result: RangeBucket[] = []
  while (cursor <= end) {
    const iso = [
      cursor.getFullYear(),
      String(cursor.getMonth() + 1).padStart(2, '0'),
      String(cursor.getDate()).padStart(2, '0'),
    ].join('-')
    result.push(byDate.get(iso) ?? emptyBucket(iso))
    cursor.setDate(cursor.getDate() + 1)
  }
  return result
}
```

- [ ] **Step 5: 运行纯函数测试和类型检查**

Run:

```powershell
cd app/frontend
npm test -- --run src/lib/statsWorkspace.test.ts
npx vue-tsc --noEmit
```

Expected: 测试和类型检查 PASS。

- [ ] **Step 6: 提交前端统计基础**

```powershell
git add app/frontend/src/lib/statsWorkspace.ts app/frontend/src/lib/statsWorkspace.test.ts app/frontend/src/api/types.ts app/frontend/src/api/stats.ts
git commit -m "feat: add statistics workspace helpers"
```

---

### Task 4: 核心指标和趋势组件

**Files:**
- Create: `app/frontend/src/components/stats/StatsMetricGrid.vue`
- Create: `app/frontend/src/components/stats/StatsMetricGrid.test.ts`
- Create: `app/frontend/src/components/stats/StatsTrendChart.vue`
- Create: `app/frontend/src/components/stats/StatsTrendChart.test.ts`

- [ ] **Step 1: 写指标组件失败测试**

测试使用一个完整 `RangeStats` 和 `ComparisonStats`，验证：

```ts
expect(wrapper.text()).toContain('实际收入')
expect(wrapper.text()).toContain('¥1,200')
expect(wrapper.text()).toContain('有效课时')
expect(wrapper.text()).toContain('10h')
expect(wrapper.text()).toContain('课程完成率')
expect(wrapper.text()).toContain('60%')
expect(wrapper.text()).toContain('活跃学生')
expect(wrapper.text()).toContain('4')
expect(wrapper.text()).toContain('较上期 ↑20.0%')
```

再增加零课程断言：

```ts
expect(wrapper.text()).toContain('暂无课程')
```

- [ ] **Step 2: 运行指标测试确认组件不存在**

```powershell
cd app/frontend
npm test -- --run src/components/stats/StatsMetricGrid.test.ts
```

Expected: FAIL，组件不存在。

- [ ] **Step 3: 实现 `StatsMetricGrid.vue`**

Props：

```ts
defineProps<{
  range: RangeStats | null
  comparison: ComparisonStats | null
  currencySymbol: string
}>()
```

组件使用 `calculateCompletionRate()`、`formatGrowth()`、`formatCurrency()` 和 `formatHours()`。四张卡使用：

```ts
const metrics = computed(() => {
  const range = props.range
  const denominator = (range?.completed_lessons ?? 0)
    + (range?.pending_lessons ?? 0)
    + (range?.leave_count ?? 0)
  return [
    {
      id: 'income',
      label: '实际收入',
      value: formatCurrency(range?.total_income ?? 0, props.currencySymbol),
      detail: formatGrowth(props.comparison?.income_growth_pct ?? null).label,
    },
    {
      id: 'hours',
      label: '有效课时',
      value: formatHours(range?.total_hours ?? 0),
      detail: formatGrowth(props.comparison?.hours_growth_pct ?? null).label,
    },
    {
      id: 'completion',
      label: '课程完成率',
      value: `${calculateCompletionRate(
        range?.completed_lessons ?? 0,
        range?.pending_lessons ?? 0,
        range?.leave_count ?? 0,
      )}%`,
      detail: denominator
        ? `已完成 ${range?.completed_lessons ?? 0} / 共 ${denominator} 节`
        : '暂无课程',
    },
    {
      id: 'students',
      label: '活跃学生',
      value: String(range?.active_students ?? 0),
      detail: '本期覆盖学生',
    },
  ]
})
```

```vue
<div class="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
  <article
    v-for="metric in metrics"
    :key="metric.id"
    :data-testid="`metric-${metric.id}`"
    class="glass-strong min-w-0 p-3.5 md:p-4"
  >
    <p class="text-xs text-[var(--text-dim)]">{{ metric.label }}</p>
    <strong class="mt-2 block truncate text-xl tracking-[-0.04em] md:text-2xl">
      {{ metric.value }}
    </strong>
    <p class="mt-1 text-[11px] text-[var(--text-dim)]">{{ metric.detail }}</p>
  </article>
</div>
```

收入和课时显示同期文案；完成率显示“已完成 X / 共 Y 节”；活跃学生显示“本期覆盖学生”。

- [ ] **Step 4: 写趋势组件失败测试**

验证：

- 无数据时显示“当前周期暂无趋势数据”。
- 有数据时渲染 `data-testid="income-line"` 和 `data-testid="hours-line"`。
- 手机指标按钮发出或切换 `income`、`hours`。
- 趋势点按钮具有 `aria-label`，包含日期、收入和课时。

示例：

```ts
expect(wrapper.get('[data-testid="income-line"]').exists()).toBe(true)
expect(wrapper.get('[data-testid="hours-line"]').exists()).toBe(true)
expect(wrapper.getAll('[data-testid="trend-point"]')[0].attributes('aria-label'))
  .toContain('2026-07-01')
```

- [ ] **Step 5: 运行趋势测试确认组件不存在**

```powershell
cd app/frontend
npm test -- --run src/components/stats/StatsTrendChart.test.ts
```

Expected: FAIL。

- [ ] **Step 6: 实现 `StatsTrendChart.vue`**

Props：

```ts
defineProps<{
  range: RangeStats | null
  currencySymbol: string
}>()
```

内部状态：

```ts
const mobileMetric = ref<'income' | 'hours'>('income')
const points = computed(() => props.range ? fillTrendPoints(props.range) : [])
```

使用固定 `640 × 220` viewBox 和以下坐标计算：

```ts
const chart = computed(() => {
  const width = 640
  const height = 220
  const padX = 32
  const padY = 24
  const incomeMax = Math.max(...points.value.map((point) => point.income), 1)
  const hoursMax = Math.max(...points.value.map((point) => point.hours), 1)
  const x = (index: number) =>
    padX + index * ((width - padX * 2) / Math.max(points.value.length - 1, 1))
  const y = (value: number, maximum: number) =>
    height - padY - (value / maximum) * (height - padY * 2)
  const path = (metric: 'income' | 'hours') =>
    points.value
      .map((point, index) => {
        const value = metric === 'income' ? point.income : point.hours
        const maximum = metric === 'income' ? incomeMax : hoursMax
        return `${index ? 'L' : 'M'} ${x(index)} ${y(value, maximum)}`
      })
      .join(' ')
  return { width, height, padX, padY, incomeMax, hoursMax, x, y, path }
})
```

- 收入面积线和 `data-testid="income-line"`。
- 课时虚线和 `data-testid="hours-line"`。
- 每个 SVG 趋势点使用 `<circle tabindex="0" role="button">`，提供日期、收入和课时组成的 `aria-label`。
- `lg` 以上同时显示两条线；移动端根据 `mobileMetric` 隐藏次要线。

不要引入 ECharts 或新的依赖。

- [ ] **Step 7: 运行两个组件测试**

```powershell
cd app/frontend
npm test -- --run src/components/stats/StatsMetricGrid.test.ts src/components/stats/StatsTrendChart.test.ts
```

Expected: PASS。

- [ ] **Step 8: 提交指标和趋势**

```powershell
git add app/frontend/src/components/stats/StatsMetricGrid.vue app/frontend/src/components/stats/StatsMetricGrid.test.ts app/frontend/src/components/stats/StatsTrendChart.vue app/frontend/src/components/stats/StatsTrendChart.test.ts
git commit -m "feat: add statistics metrics and trends"
```

---

### Task 5: 学生贡献和关注记录组件

**Files:**
- Create: `app/frontend/src/components/stats/StudentContribution.vue`
- Create: `app/frontend/src/components/stats/StudentContribution.test.ts`
- Create: `app/frontend/src/components/stats/AttentionList.vue`
- Create: `app/frontend/src/components/stats/AttentionList.test.ts`

- [ ] **Step 1: 写学生贡献失败测试**

验证：

```ts
expect(wrapper.text()).toContain('林晓')
expect(wrapper.text()).toContain('¥800')
expect(wrapper.text()).toContain('4h')
expect(wrapper.get('[data-testid="student-contribution"]').attributes('aria-label'))
  .toBe('查看林晓学生详情')
await wrapper.get('[data-testid="student-contribution"]').trigger('click')
expect(wrapper.emitted('select-student')).toEqual([[1]])
```

同时验证空数组显示“当前周期暂无学生贡献数据”。

- [ ] **Step 2: 实现 `StudentContribution.vue`**

Props 与事件：

```ts
defineProps<{
  ranking: StudentStatsRow[]
  currencySymbol: string
}>()

defineEmits<{
  (event: 'select-student', studentId: number): void
}>()
```

最大收入取：

```ts
const maximumIncome = computed(
  () => Math.max(...props.ranking.map((row) => row.total_income), 0),
)
```

每行使用按钮语义，贡献条宽度来自 `contributionPercent()`。

- [ ] **Step 3: 写关注记录失败测试**

传入四条记录并验证：

```ts
expect(wrapper.getAll('[data-testid="attention-item"]')).toHaveLength(3)
await wrapper.get('[data-action="expand-attention"]').trigger('click')
expect(wrapper.getAll('[data-testid="attention-item"]')).toHaveLength(4)
```

空数组显示“当前周期没有请假或调课记录”。请假与调课必须同时显示文字标签，不能只靠颜色。

- [ ] **Step 4: 实现 `AttentionList.vue`**

Props：

```ts
defineProps<{
  items: LeaveItem[]
}>()
```

状态与列表：

```ts
const expanded = ref(false)
const visibleItems = computed(() => visibleAttentionItems(props.items, expanded.value))
```

展开按钮只在 `items.length > 3` 时出现；切换文案为“展开全部 / 收起”。

- [ ] **Step 5: 运行两个组件测试**

```powershell
cd app/frontend
npm test -- --run src/components/stats/StudentContribution.test.ts src/components/stats/AttentionList.test.ts
```

Expected: PASS。

- [ ] **Step 6: 提交决策辅助组件**

```powershell
git add app/frontend/src/components/stats/StudentContribution.vue app/frontend/src/components/stats/StudentContribution.test.ts app/frontend/src/components/stats/AttentionList.vue app/frontend/src/components/stats/AttentionList.test.ts
git commit -m "feat: add statistics decision panels"
```

---

### Task 6: 重组统计面板

**Files:**
- Modify: `app/frontend/src/components/stats/StatsPanel.vue`
- Create: `app/frontend/src/components/stats/StatsPanel.test.ts`

- [ ] **Step 1: 写决策流布局失败测试**

测试 `StatsPanel`：

- 渲染 `StatsMetricGrid`、`StatsTrendChart`、`StudentContribution`、`AttentionList`。
- 周期按钮发出 `change-range`。
- 重试按钮发出 `retry`。
- 学生事件继续发出 `select-student`。
- 加载失败但存在旧数据时仍渲染子组件和局部警告。
- 首次加载且无数据时显示骨架。

事件声明必须为：

```ts
const emit = defineEmits<{
  (event: 'change-range', range: 'today' | 'week' | 'month'): void
  (event: 'export-range'): void
  (event: 'prev-period'): void
  (event: 'next-period'): void
  (event: 'go-current-period'): void
  (event: 'retry'): void
  (event: 'select-student', studentId: number): void
}>()
```

- [ ] **Step 2: 运行测试确认旧组件不符合新接口**

```powershell
cd app/frontend
npm test -- --run src/components/stats/StatsPanel.test.ts
```

Expected: FAIL。

- [ ] **Step 3: 替换旧内联图表**

删除 `StatsPanel.vue` 中的旧趋势坐标、排行 SVG、hover 状态和内联指标卡，新增 Props：

```ts
loading: boolean
error: string
```

使用以下决策流组件连接：

```vue
<div class="space-y-4">
  <header class="glass-strong flex flex-wrap items-center justify-between gap-3 p-3 md:p-4">
    <div>
      <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-dim)]">Business pulse</p>
      <h2 class="mt-1 text-xl font-extrabold">经营概览</h2>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="rangeOption in (['today', 'week', 'month'] as const)"
        :key="rangeOption"
        class="min-h-11 rounded-xl px-3 text-xs"
        @click="emit('change-range', rangeOption)"
      >
        {{ rangeOption === 'today' ? '今日' : rangeOption === 'week' ? '本周' : '本月' }}
      </button>
      <button class="btn-primary min-h-11 text-xs" @click="emit('export-range')">导出 Excel</button>
    </div>
  </header>
  <div v-if="error" class="glass flex items-center justify-between gap-3 p-3 text-sm text-red-600">
    <span>{{ error }}</span>
    <button data-action="retry-stats" class="btn-ghost btn-sm" @click="emit('retry')">重新加载</button>
  </div>
  <StatsMetricGrid :comparison="comparison" :currency-symbol="currencySymbol" :range="range" />
  <StatsTrendChart :currency-symbol="currencySymbol" :range="range" />
  <div class="grid gap-4 lg:grid-cols-[minmax(0,1.45fr)_minmax(280px,.85fr)]">
    <StudentContribution
      :currency-symbol="currencySymbol"
      :ranking="ranking"
      @select-student="emit('select-student', $event)"
    />
    <AttentionList :items="leaveItems" />
  </div>
</div>
```

- [ ] **Step 4: 运行统计面板和所有统计组件测试**

```powershell
cd app/frontend
npm test -- --run src/components/stats
```

Expected: 全部 PASS。

- [ ] **Step 5: 提交统计面板**

```powershell
git add app/frontend/src/components/stats/StatsPanel.vue app/frontend/src/components/stats/StatsPanel.test.ts
git commit -m "feat: compose statistics decision workspace"
```

---

### Task 7: Dashboard 统计编排、竞态与学生联动

**Files:**
- Modify: `app/frontend/src/pages/DashboardPage.vue`
- Modify: `app/frontend/src/pages/DashboardPage.test.ts`

- [ ] **Step 1: 扩展路由和统计失败测试**

在测试路由加入：

```ts
{ path: '/stats', component: DashboardPage }
```

新增测试：

1. 进入 `/stats` 时 `statsApi.range` 和 `statsApi.comparison` 使用同一个明确区间。
2. 今日比较传入 `period: 'day'`。
3. 两次快速切换中，先发请求后返回的旧结果不能覆盖新结果。
4. 刷新失败时 `StatsPanel` 仍收到旧数据和错误。
5. `retry` 重新加载当前区间。
6. `select-student(2)` 导航到 `/students?student=2`。
7. 直接进入 `/students?student=2` 时选择学生 2。
8. 导出失败显示“导出失败，请稍后重试”。

使用可控 Promise 验证竞态：

```ts
function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}
```

- [ ] **Step 2: 运行页面测试确认失败**

```powershell
cd app/frontend
npm test -- --run src/pages/DashboardPage.test.ts
```

Expected: FAIL，统计仍与 `loadDashboard()` 绑定，比较 API 使用旧签名。

- [ ] **Step 3: 添加独立统计状态**

在 `DashboardPage.vue` 新增：

```ts
const statsLoading = ref(false)
const statsError = ref('')
let statsRequestId = 0
```

从 `loadDashboard()` 的 `Promise.all` 中移出 `statsApi.range`、`statsApi.comparison`、`statsApi.students` 和 `statsApi.leave` 四个调用。

课表首页仍可加载 `statsApi.today()`，但统计区间数据只由 `loadStatistics()` 维护。

- [ ] **Step 4: 实现带竞态保护的 `loadStatistics()`**

```ts
async function loadStatistics() {
  const requestId = ++statsRequestId
  const range = getStatsRange(statsOffset.value)
  const period = statRange.value === 'today' ? 'day' : statRange.value
  statsLoading.value = true
  statsError.value = ''
  try {
    const [nextRange, nextComparison, nextRanking, nextLeave] = await Promise.all([
      statsApi.range(toIsoDate(range.start), toIsoDate(range.end), range.granularity),
      statsApi.comparison(toIsoDate(range.start), toIsoDate(range.end), period),
      statsApi.students(toIsoDate(range.start), toIsoDate(range.end)),
      statsApi.leave(toIsoDate(range.start), toIsoDate(range.end)),
    ])
    if (requestId !== statsRequestId) return
    rangeStats.value = nextRange
    comparisonStats.value = nextComparison
    ranking.value = nextRanking
    leaveItems.value = nextLeave
  } catch {
    if (requestId === statsRequestId) {
      statsError.value = '当前区间更新失败，请稍后重试'
    }
  } finally {
    if (requestId === statsRequestId) {
      statsLoading.value = false
    }
  }
}
```

- [ ] **Step 5: 调整统计监听和进入页面加载**

用单个 watcher 处理统计范围，范围变化时先复位 offset，避免重复请求：

```ts
watch(
  [statRange, statsOffset],
  async ([nextRange, nextOffset], [previousRange]) => {
    if (nextRange !== previousRange && nextOffset !== 0) {
      statsOffset.value = 0
      return
    }
    if (activeTab.value === 'stats') {
      await loadStatistics()
    }
  },
)
```

在现有路由 watcher 中，切换到统计页时加载当前区间：

```ts
watch(
  () => route.path,
  async (path) => {
    activeTab.value = tabFromPath(path)
    if (activeTab.value === 'stats') {
      await loadStatistics()
    }
  },
  { immediate: true },
)
```

删除原来由 `statRange` 和 `statsOffset` 调用 `loadDashboard()` 的两个 watcher。

- [ ] **Step 6: 实现学生查询参数联动**

导入 `useRouter`：

```ts
const router = useRouter()
```

处理排行：

```ts
function openStudentWorkspace(studentId: number) {
  router.push({ path: '/students', query: { student: String(studentId) } })
}
```

学生列表成功后先读取：

```ts
const requestedStudentId = Number(route.query.student)
const querySelection = Number.isInteger(requestedStudentId)
  ? studentRows.find((student) => student.id === requestedStudentId)?.id ?? null
  : null
selectedStudentId.value = normalizeSelectedStudentId(
  studentRows,
  querySelection ?? selectedStudentId.value,
)
```

同时监听 `route.query.student`，支持在已加载学生后通过路由更新选择。

- [ ] **Step 7: 添加导出错误反馈**

在 `downloadMonthReport()` 开始时清除导出错误；catch 时设置：

```ts
statsError.value = '导出失败，请稍后重试'
```

不要在请求失败时创建下载链接。

- [ ] **Step 8: 连接 `StatsPanel` 新接口**

```html
<StatsPanel
  :comparison="comparisonStats"
  :currency-symbol="currencySymbol"
  :error="statsError"
  :is-current-period="isCurrentStatsPeriod"
  :leave-items="leaveItems"
  :loading="statsLoading"
  :range="rangeStats"
  :ranking="ranking"
  :stat-range="statRange"
  :stats-offset="statsOffset"
  :stats-period-label="statsPeriodLabel"
  :today="todayStats"
  @change-range="statRange = $event"
  @export-range="downloadMonthReport"
  @go-current-period="goToCurrentStatsPeriod"
  @next-period="nextStatsPeriod"
  @prev-period="prevStatsPeriod"
  @retry="loadStatistics"
  @select-student="openStudentWorkspace"
/>
```

- [ ] **Step 9: 运行 Dashboard 测试和全量前端测试**

```powershell
cd app/frontend
npm test -- --run src/pages/DashboardPage.test.ts
npm test -- --run
```

Expected: 全部 PASS。

- [ ] **Step 10: 提交页面编排**

```powershell
git add app/frontend/src/pages/DashboardPage.vue app/frontend/src/pages/DashboardPage.test.ts
git commit -m "feat: orchestrate statistics workspace"
```

---

### Task 8: 最终验证与双端浏览器验收

**Files:**
- Verify: `app/frontend/src/components/stats/*.vue`
- Verify: `app/frontend/src/pages/DashboardPage.vue`
- Verify: `app/backend/app/services/stats_service.py`
- Update: `docs/superpowers/plans/2026-07-29-statistics-workspace.md`

- [ ] **Step 1: 运行后端测试**

```powershell
cd app/backend
python -m pytest -v
```

Expected: 所有后端测试 PASS。

- [ ] **Step 2: 运行前端测试和生产构建**

```powershell
cd app/frontend
npm test -- --run
npm run build
```

Expected: 所有 Vitest 测试 PASS，Vue TypeScript 检查和 Vite 构建成功。

- [ ] **Step 3: 启动后端和前端**

使用项目虚拟环境或先安装 `app/backend/requirements.txt`，然后：

```powershell
cd app/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另一个进程：

```powershell
cd app/frontend
npm run dev -- --host 127.0.0.1
```

- [ ] **Step 4: 验收 1440×900**

打开 `http://127.0.0.1:5173/stats`，确认：

- 四项指标单行排列。
- 趋势图同时显示收入和课时。
- 学生贡献与需要关注为 `60% / 40%` 双栏。
- 周期切换、前后周期、回到当期和导出入口可见。
- 页面无横向溢出。
- 点击学生贡献进入对应学生工作台且学生已选中。

- [ ] **Step 5: 验收 390×844**

确认：

- 指标为两列。
- 周期和日期导航分行且触控区域不小于 44px。
- 趋势可以在收入和课时之间切换。
- 学生贡献使用列表和进度条。
- 关注记录默认三条，可展开。
- 底部导航无遮挡，无横向溢出。

- [ ] **Step 6: 验收错误与暗色模式**

- 暂停后端或拦截统计请求，确认最后成功数据被保留并出现重试提示。
- 恢复后端并点击重试，确认错误消失。
- 切换暗色主题，确认指标、图表、增长语义色和焦点状态可读。
- 模拟导出失败，确认显示“导出失败，请稍后重试”。

- [ ] **Step 7: 差异检查和工作区确认**

```powershell
git diff --check
git status --short
```

Expected: 无空白错误；只包含第三阶段预期文件。

- [ ] **Step 8: 更新计划并提交最终调整**

将本计划已完成步骤改为 `[x]`。如果浏览器验收产生代码调整，重新运行受影响测试和完整构建后提交：

```powershell
git add app/backend app/frontend API.md docs/superpowers/plans/2026-07-29-statistics-workspace.md
git commit -m "feat: complete statistics workspace"
```
