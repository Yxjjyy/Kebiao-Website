# 课表管理系统 (KeBiao)
一个面向私教/老师的课表管理系统，支持学生管理、课表模板管理、课程自动生成、冲突检测、考勤/收入统计等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python FastAPI |
| ORM | SQLAlchemy + Alembic |
| 数据库 | SQLite |
| 定时任务 | APScheduler |
| 前端框架 | Vue 3 + TypeScript |
| 状态管理 | Pinia |
| 数据请求 | TanStack Vue Query + Axios |
| UI 框架 | Tailwind CSS + Reka UI |
| 图表 | ECharts |
| 反向代理 | Caddy |
| 进程管理 | Gunicorn + Uvicorn + systemd |

## 项目结构

```
kebiao/
├── README.md                     # 本文件
├── API.md                        # 数据库 & API 接口文档
├── app/
│   ├── backend/                  # FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py           # 应用入口
│   │   │   ├── config.py         # 配置管理
│   │   │   ├── database.py       # 数据库连接
│   │   │   ├── deps.py           # FastAPI 依赖
│   │   │   ├── scheduler.py      # 定时任务
│   │   │   ├── timeutil.py       # 时区工具
│   │   │   ├── models/           # SQLAlchemy 数据模型
│   │   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   │   ├── routers/          # API 路由
│   │   │   └── services/         # 业务逻辑层
│   │   ├── alembic/              # 数据库迁移
│   │   ├── requirements.txt      # Python 依赖
│   │   ├── .env.example          # 环境变量模板
│   │   └── .env                  # 当前环境配置
│   ├── frontend/                 # Vue 3 前端
│   │   ├── src/
│   │   │   ├── api/              # API 客户端 & 类型定义
│   │   │   ├── components/       # UI 组件 (schedule/students/stats)
│   │   │   ├── pages/            # 页面组件
│   │   │   ├── stores/           # Pinia 状态管理
│   │   │   ├── composables/      # 组合式函数
│   │   │   ├── lib/              # 工具函数
│   │   │   └── router/           # Vue Router
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── deploy/                   # 部署相关
│       ├── README.md             # 详细部署指南
│       ├── setup-server.sh       # 服务器初始化脚本
│       ├── deploy.sh             # 更新部署脚本
│       ├── backup.sh             # 数据库备份脚本
│       ├── Caddyfile             # Caddy 配置
│       ├── kebiao-backend.service # systemd 服务
│       └── .env.production       # 生产环境变量模板
├── data/
│   └── app.db                    # SQLite 数据库文件
└── backups/                      # 数据库自动备份目录
```

## 本地开发

### 后端

```bash
cd app/backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 中的 CORS_ORIGINS 等

# 初始化数据库
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd app/frontend

npm install
npm run dev
```

浏览器访问 `http://localhost:5173`

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ACCESS_TOKEN` | `yang` | API 访问令牌（Bear token） |
| `DB_PATH` | `./data/app.db` | SQLite 数据库路径 |
| `TIMEZONE` | `Asia/Shanghai` | 应用时区 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的跨域来源（逗号分隔） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

## 定时任务

后端内置两个定时任务（APScheduler），每天自动执行：

1. **自动补完课程** — 每天 00:05，将已过期且状态为"待上"的课程自动标记为"已完成"
2. **课表滚动生成** — 每天 00:10，为所有有效模板生成未来 N 周的课程实例（默认 12 周）

## 部署

详细部署指南请参阅 `app/deploy/README.md`，简要步骤：

1. 将 `app/` 目录上传到服务器 `/home/kebiao/app/`
2. 执行 `bash /home/kebiao/app/deploy/setup-server.sh` 初始化环境
3. 配置 `.env` 和 `Caddyfile`
4. 构建前端：`cd app/frontend && npm install && npm run build`
5. 启动服务：`sudo systemctl start kebiao-backend`

### 更新项目

```bash
# 上传新版本代码后执行
sudo bash /home/kebiao/app/deploy/deploy.sh
```

### 数据库备份

```bash
# 手动备份
sudo bash /home/kebiao/app/deploy/backup.sh

# 自动备份 (cron: 每天凌晨 3 点)
```

## API 文档

完整的 API 接口文档和数据库表结构请参阅 [API.md](./API.md)。

## 维护与开发规范（必读）

安全规则、内存红线（服务器仅 1.6GB 内存）、登录认证、审计/软删除约定、开发与部署流程，
请参阅 [docs/OPERATIONS.md](./docs/OPERATIONS.md)。**后续任何更新修复都必须遵守该文档。**
