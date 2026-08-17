# Lumina 课表系统 — 维护与开发规范（必读）

> 本文档是系统运行、安全加固、开发与部署的**唯一权威依据**。后续任何功能更新、Bug 修复、安全调整都必须遵守本文档约定；修改本文档需同时更新相关实现。

## 1. 系统概览

| 项 | 说明 |
|----|------|
| 域名 | `https://xiaomei.me`（仅 HTTPS） |
| 反向代理 | Caddy v2.11+（`/etc/caddy/Caddyfile`），HTTP 明文入口已停用 |
| 后端 | FastAPI + Gunicorn（1 worker）+ APScheduler，监听 `127.0.0.1:8001` |
| 数据库 | SQLite `/home/kebiao/data/app-v2.db`（源库 `/home/kebiao/data/app.db` 不动） |
| 前端 | Vue 3 + Vite，**由 GitHub Actions 构建**，服务器不跑 Node |
| 进程 | systemd：`kebiao-backend-v2`、`caddy` |
| 日志 | Caddy 访问日志 `/var/log/caddy/kebiao-access.log`；后端 `/var/log/kebiao/*-v2.log`；均配置 logrotate（每日轮转、gzip 压缩、保留 14 天） |
| 备份 | `app/deploy/backup.sh`，cron 每 6 小时（0,6,12,18 点），存 `/home/kebiao/backups/`（保留 7 天） |
| 内存监控 | `app/deploy/mem-watch.sh`（安装到 `/usr/local/bin/`，root cron 每 5 分钟）：MemAvailable<150MB 写告警 `/var/log/kebiao/mem-watch.log` |

## 2. 认证与会话（安全核心）

- 登录：账号 `LOGIN_USERNAME` + 密码 `LOGIN_PASSWORD`（配置在后端 `.env`，**禁止**写入前端包/构建变量/GitHub Actions secret 之外任何前端相关位置）
- 登录成功签发 32 字节随机会话令牌（存 localStorage，服务端只存 **sha256 哈希**）
- 会话有效期 `SESSION_TTL_DAYS=365`，**滑动续期**（每 24h 最多续一次）：已登录设备长期免登录
- 登录限流：同 IP 连续 5 次失败锁定 15 分钟（`app/routers/auth.py`，有界内存计数）
- API 通用限流：`RateLimitMiddleware`（`app/middleware/rate_limit.py`）每 IP 每分钟 120 次，防脚本刷接口（有界内存，每日 03:20 随安全清理任务重置）
- 所有 `/api/v1/*` 路由必须经 `require_session`（例外：`/api/v1/health`、`/api/v1/auth/login`）
- `ACCESS_TOKEN` 仅作**脚本/curl API 钥匙**，已轮换，禁止编译进前端
- 前端 `client.ts` 从 `lib/session.ts` 读令牌；401 统一清除并跳 `/login`

### 会话/密钥管理命令

```bash
# 强制登出所有设备（删除全部会话）
sqlite3 /home/kebiao/data/app-v2.db "DELETE FROM auth_sessions;"
# 查看登录会话
sqlite3 /home/kebiao/data/app-v2.db "SELECT id, ip, user_agent, created_at, expires_at, last_seen_at FROM auth_sessions;"
# 轮换登录密码：改 .env 的 LOGIN_PASSWORD 后重启服务
sudo systemctl restart kebiao-backend-v2
```

## 3. 内存红线（服务器仅 1.6GB 内存，2 核）

**服务器内存环境：MemTotal 1.6GB，swap 2GB。以下为强制约束，违反可能导致系统 OOM 崩溃：**

| # | 约束 |
|---|------|
| 1 | **禁止在服务器执行 npm install / npm run build / 任何 Node 构建**。前端构建只在 GitHub Actions；本地（开发机）可构建 |
| 2 | **禁止整文件/整表载入内存**：日志（104MB+）、大 SQLite 表一律流式/分页处理（`for line in open(...)` 逐行、`LIMIT` 分页） |
| 3 | **gunicorn workers 固定为 1**，`--max-requests 500` 防 worker 内存泄漏；systemd `MemoryMax=512M`，Caddy `MemoryMax=256M` |
| 4 | 内存计数缓存（如登录限流）必须有界 + 定时清理（见 scheduler `_cleanup_security_job`） |
| 5 | 后端测试：优先在开发机跑；服务器跑测试前先 `free -m`（`MemAvailable < 400MB` 则放弃），用 `nice -n 10` + `--maxfail=1` |
| 6 | 部署前检查 `MemAvailable`，低于 300MB 暂停部署（deploy-v2.sh 内置闸门） |
| 7 | 不要在服务器开多个重型工具会话；分析类操作与部署错开执行 |
| 8 | 部署完成后必须检查：健康接口 + `free -m` + swap 使用率 |

## 4. 写操作安全

- **审计**：所有非 GET `/api/v1` 请求由 `AuditMiddleware` 记录到 `audit_logs`（时间/IP/UA/方法/URI/状态/会话ID/请求ID），scheduler 每日 03:20 清理 90 天前记录
- **课程删除是软删除**：`DELETE /lessons/{id}` 将状态置为 `已删除` 并记录 `deleted_from`；`POST /lessons/{id}/restore` 可还原原状态；列表/统计默认排除 `已删除`
- 学生删除走**归档**（`/archive`），禁止直接删学生行
- 查看审计：`sqlite3 /home/kebiao/data/app-v2.db "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50;"`

## 5. 开发与提交规范

1. 后端改动：改完后在开发机（或按第 3 节约束在服务器）跑 `pytest`，全量须绿
2. 前端改动：**不在服务器构建**；push 后由 `build.yml` 构建并发布 dist 到 GitHub Releases（匿名可下载，仅供部署脚本使用）
3. **禁止**把 `LOGIN_PASSWORD`、`ACCESS_TOKEN` 写入前端代码、`.env` 之外的文件或 commit；`build.yml` 不再注入任何前端令牌
4. 数据库结构变更必须写 alembic 迁移（`alembic/versions/00xx_*.py`），并在服务器执行 `alembic upgrade head`
5. 登录/会话/审计/软删除相关功能，修改后必须补充/更新 pytest 用例（`tests/test_auth.py`、`test_audit_middleware.py`、`test_lesson_routes.py`）
6. 提交信息按现有风格（`feat:` / `fix:` / `test:` / `ci:` 等）

## 6. 部署流程（唯一入口：deploy-v2.sh）

```bash
sudo bash /home/kebiao/app-v2/deploy-v2.sh
```

脚本流程：下载 GitHub Releases 前端产物 → 校验版本 → 备份旧 dist → 解压 → 同步后端源码（git pull）→ 增量装依赖 → `alembic upgrade head` → 修复数据库属主 → 重启 `kebiao-backend-v2` → 健康检查。内存闸门内置。

**手工部署（脚本不可用时，按顺序）：**
```bash
cd /home/kebiao/app-v2 && git pull --ff-only origin main
cd app/backend && .venv/bin/pip install -q -r requirements.txt && .venv/bin/alembic upgrade head
sudo systemctl restart kebiao-backend-v2
curl -s http://127.0.0.1:8001/api/v1/health && free -m
```

**回滚：**
```bash
cd /home/kebiao/app-v2 && git checkout <上一个提交> -- app/backend && sudo systemctl restart kebiao-backend-v2
# 前端回滚：恢复 dist.bak.xxx 目录并重启 caddy
```

## 7. 已知影响（升级/维护提示）

- 安全加固上线后：每台设备**首次访问需登录一次**（`yang / 密码`），之后 1 年免登录
- PWA 缓存：前端更新后用户需**刷新两次**才看到新版
- 单 worker 下极端并发能力有限，家庭使用无感；若 API 明显变慢，先查 `free -m` 再考虑调整

## 8. 事故复盘（2026-08-15 恶意修改事件）

- 根因：前端包内硬编码默认令牌 `yang` 且编译进匿名可下载的 GitHub Releases 产物 → 任何人可读 API 并删改数据
- 本次加固内容：真实登录（账号+密码+会话）、令牌轮换、移除前端令牌注入、写操作审计、课程软删除、登录限流、API 通用限流、停用明文 HTTP、内存防护
- 被删数据已从 `backups/app-20260813_191824.db` 恢复（见部署记录）
