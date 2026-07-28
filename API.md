# API 接口文档

所有 API 路由前缀：`/api/v1`

---

## 数据库表结构

### students（学生）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 自增主键 |
| name | VARCHAR(64) | 是 | 学生姓名 |
| color | VARCHAR(16) | 是 | UI 显示颜色 (默认 #4C7DFF) |
| hourly_rate | FLOAT | 是 | 每小时课时费 |
| phone | VARCHAR(32) | 否 | 电话 |
| note | TEXT | 否 | 备注 |
| archived | INTEGER | 是 | 是否归档 (0=否, 1=是) |
| created_at | DATETIME | 是 | 创建时间 |
| updated_at | DATETIME | 是 | 更新时间 |

### schedule_templates（课表模板）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 自增主键 |
| student_id | INTEGER | 是 | FK -> students.id (CASCADE) |
| day_of_week | INTEGER | 是 | 星期几 (0=周一, 6=周日) |
| start_time | VARCHAR(5) | 是 | 开始时间 "HH:MM" |
| duration_hours | FLOAT | 是 | 时长 (小时) |
| effective_from | DATE | 是 | 生效起始日期 |
| effective_to | DATE | 否 | 生效结束日期 (null=无限期) |
| repeat_interval | INTEGER | 是 | 重复间隔 (1=每周,2=双周,最多4) |
| created_at | DATETIME | 是 | 创建时间 |
| updated_at | DATETIME | 是 | 更新时间 |

### lessons（课程实例）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | 自增主键 |
| student_id | INTEGER | 是 | FK -> students.id (CASCADE) |
| template_id | INTEGER | 否 | FK -> schedule_templates.id (SET NULL) |
| date | DATE | 是 | 上课日期 |
| start_time | VARCHAR(5) | 是 | 开始时间 "HH:MM" |
| duration_hours | FLOAT | 是 | 时长 |
| status | VARCHAR(8) | 是 | 状态: 待上/已完成/请假/已调课 |
| price | FLOAT | 是 | 课时费 (hourly_rate * duration_hours) |
| note | TEXT | 否 | 备注 |
| rescheduled_from_id | INTEGER | 否 | 调课来源课程 ID |
| rescheduled_to_id | INTEGER | 否 | 调课目标课程 ID |
| created_at | DATETIME | 是 | 创建时间 |
| updated_at | DATETIME | 是 | 更新时间 |

### settings（系统设置，单行 id=1）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| timezone | VARCHAR(32) | Asia/Shanghai | 时区 |
| week_start | INTEGER | 1 | 周起始日 (1=周一) |
| currency_symbol | VARCHAR(4) | ¥ | 货币符号 |
| generate_weeks_ahead | INTEGER | 12 | 课表向前生成周数 |
| default_duration_hours | FLOAT | 1.0 | 默认课时长 |
| visible_time_start | VARCHAR(5) | 07:00 | 日历可见起始时间 |
| visible_time_end | VARCHAR(5) | 22:00 | 日历可见结束时间 |
| theme | VARCHAR(8) | auto | 主题 (auto/light/dark) |

### user_profile（用户信息，单行 id=1）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| display_name | VARCHAR(64) | 老师 | 显示名称 |
| avatar_color | VARCHAR(16) | #4C7DFF | 头像颜色 |

---

## API 路由

### 健康检查

**GET** `/api/v1/health`

响应：
```json
{ "status": "ok" }
```

---

### 学生管理

**GET** `/api/v1/students` — 获取学生列表

参数：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| archived | bool | false | 是否查询已归档学生 |

响应：
```json
[
  {
    "id": 1,
    "name": "张三",
    "color": "#4C7DFF",
    "hourly_rate": 200.0,
    "phone": "13800138000",
    "note": "",
    "archived": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

**POST** `/api/v1/students` — 创建学生

请求：
```json
{
  "name": "张三",
  "color": "#4C7DFF",
  "hourly_rate": 200.0,
  "phone": "13800138000",
  "note": ""
}
```

---

**GET** `/api/v1/students/{student_id}` — 获取学生详情

响应包含学生信息、本月统计（课时数、收入）和模板数量。

---

**PATCH** `/api/v1/students/{student_id}` — 更新学生信息

参数：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| recalc_mode | string | "none" | 重新计算课程价格: today/tomorrow/none |

请求体同创建接口（部分更新即可）。

---

**POST** `/api/v1/students/{student_id}/archive` — 归档学生

**POST** `/api/v1/students/{student_id}/unarchive` — 取消归档

**DELETE** `/api/v1/students/{student_id}` — 删除学生

注意：如果学生有关联课程，返回 409 错误。

---

### 课表模板

**GET** `/api/v1/templates` — 获取模板列表

参数：
| 参数 | 类型 | 说明 |
|------|------|------|
| student_id | int | 按学生筛选（可选） |

---

**POST** `/api/v1/templates` — 创建模板

请求：
```json
{
  "student_id": 1,
  "day_of_week": 1,
  "start_time": "14:00",
  "duration_hours": 1.5,
  "effective_from": "2024-03-01",
  "effective_to": null,
  "repeat_interval": 1
}
```

创建模板时会自动生成 `generate_weeks_ahead` 周内的课程实例。

---

**PATCH** `/api/v1/templates/{template_id}` — 更新模板

请求体同创建接口。额外参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| apply_mode | string | 对已有课程的处理策略 |

---

**DELETE** `/api/v1/templates/{template_id}` — 删除模板

参数：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cancel_future | bool | true | 是否同时取消未来课程 |

---

### 课程管理

**GET** `/api/v1/lessons` — 获取课程列表

参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | date | 是 | 开始日期 |
| to | date | 是 | 结束日期 |
| student_id | int | 否 | 按学生筛选 |

响应：
```json
[
  {
    "id": 1,
    "student_id": 1,
    "student_name": "张三",
    "student_color": "#4C7DFF",
    "template_id": 2,
    "date": "2024-03-04",
    "start_time": "14:00",
    "duration_hours": 1.5,
    "status": "待上",
    "price": 300.0,
    "note": "",
    "rescheduled_from_id": null,
    "rescheduled_to_id": null
  }
]
```

---

**POST** `/api/v1/lessons` — 创建单次课程

请求：
```json
{
  "student_id": 1,
  "date": "2024-03-10",
  "start_time": "15:00",
  "duration_hours": 1.0,
  "note": ""
}
```

会自动检测时间冲突，冲突时返回 409。

---

**POST** `/api/v1/lessons/bulk` — 批量操作

请求：
```json
{
  "lesson_ids": [1, 2, 3],
  "action": "complete"
}
```

`action` 可选值：
- `complete` — 标记为已完成
- `cancel` — 标记为请假
- `restore` — 恢复为待上
- `delete` — 删除课程

---

**PATCH** `/api/v1/lessons/{lesson_id}` — 更新课程

部分更新课程信息，会自动重新计算价格。

---

**POST** `/api/v1/lessons/{lesson_id}/reschedule` — 调课

请求：
```json
{
  "date": "2024-03-11",
  "start_time": "16:00",
  "note": "临时调整"
}
```

将原课程标记为"已调课"，创建新课程。

---

**POST** `/api/v1/lessons/{lesson_id}/cancel` — 请假

将课程状态改为"请假"。

---

**POST** `/api/v1/lessons/{lesson_id}/restore` — 恢复

将已请假/已调课的课程恢复为"待上"。

---

**DELETE** `/api/v1/lessons/{lesson_id}` — 删除课程

---

### 统计

**GET** `/api/v1/stats/today` — 今日概览

响应：
```json
{
  "total_lessons": 5,
  "completed_lessons": 3,
  "pending_lessons": 2,
  "today_income": 600.0,
  "today_hours": 3.0
}
```

---

**GET** `/api/v1/stats/range` — 范围统计

参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | date | 是 | 开始日期 |
| to | date | 是 | 结束日期 |
| granularity | string | 否 | day/week/month |

---

**GET** `/api/v1/stats/students` — 学生排名

参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | date | 是 | 开始日期 |
| to | date | 是 | 结束日期 |

---

**GET** `/api/v1/stats/leave` — 请假/调课列表

参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | date | 是 | 开始日期 |
| to | date | 是 | 结束日期 |

---

**GET** `/api/v1/stats/comparison` — 环比统计

参数：
| 参数 | 类型 | 说明 |
|------|------|------|
| period | string | week/week-over-week / month/month-over-month |

---

### 导出

**GET** `/api/v1/export/xlsx` — 导出 Excel 报表

参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | date | 是 | 开始日期 |
| to | date | 是 | 结束日期 |

返回 `.xlsx` 文件，包含 3 个工作表（按学生、按日期、汇总）。

---

### 备份与恢复

**GET** `/api/v1/backup` — 下载数据库备份

响应：SQLite 数据库文件的二进制流下载。

---

**POST** `/api/v1/restore` — 恢复数据库

请求头：
| 请求头 | 值 | 说明 |
|--------|-----|------|
| X-Confirm-Restore | yes | 必须设置此头确认恢复操作 |

请求体：multipart/form-data，字段名 `file`，上传 `.db` 文件。

---

### 设置

**GET** `/api/v1/settings` — 获取系统设置

**PATCH** `/api/v1/settings` — 更新系统设置

请求体（部分更新）：
```json
{
  "timezone": "Asia/Shanghai",
  "theme": "dark",
  "generate_weeks_ahead": 8
}
```

---

**GET** `/api/v1/profile` — 获取用户信息

**PATCH** `/api/v1/profile` — 更新用户信息

请求体：
```json
{
  "display_name": "王老师",
  "avatar_color": "#FF6B6B"
}
```
