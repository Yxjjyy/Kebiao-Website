#!/bin/bash
# 课表 v2 部署脚本：GitHub Actions 构建前端，服务器免 Node 部署
set -euo pipefail

APP_DIR=/home/kebiao/app-v2
RELEASE_URL=https://github.com/Yxjjyy/Kebiao-Website/releases/latest/download
DIST_DIR="$APP_DIR/app/frontend/dist"
SERVICE=kebiao-backend-v2
VENV="$APP_DIR/app/backend/.venv/bin"

echo "=== 课表 v2 部署开始 $(date +%F\ %T) ==="

# 1. 下载前端构建产物（公开仓库，匿名免认证）
echo ">>> 下载前端产物..."
curl -sfL --retry 4 --retry-delay 3 --retry-all-errors -o /tmp/kebiao-dist.zip "$RELEASE_URL/kebiao-dist.zip"
curl -sfL --retry 4 --retry-delay 3 --retry-all-errors -o /tmp/build-info.txt "$RELEASE_URL/build-info.txt" || true
[ -f /tmp/build-info.txt ] && grep -E "BUILD_SHA|BUILD_TIME" /tmp/build-info.txt || echo "无 build-info"

# 版本检查：远端构建 SHA 与当前部署版本一致则跳过（无新版本）
CURRENT_SHA=""
[ -f "$APP_DIR/.deployed-sha" ] && CURRENT_SHA=$(cat "$APP_DIR/.deployed-sha")
REMOTE_SHA=$(grep -oE "BUILD_SHA=[0-9a-f]+" /tmp/build-info.txt 2>/dev/null | cut -d= -f2 || true)
if [ -n "$REMOTE_SHA" ] && [ "$CURRENT_SHA" = "$REMOTE_SHA" ]; then
  echo ">>> 已是最新版本 ($REMOTE_SHA)，无需部署"
  exit 0
fi

# 2. 备份当前 dist 并解压新产物
if [ -d "$DIST_DIR" ]; then
  cp -r "$DIST_DIR" "$DIST_DIR.bak.$(date +%Y%m%d_%H%M%S)"
fi
mkdir -p "$DIST_DIR"
rm -rf "$DIST_DIR"/*
unzip -q /tmp/kebiao-dist.zip -d "$APP_DIR/app/frontend"
echo ">>> dist 已更新"

# 记录当前部署版本
echo "${REMOTE_SHA:-unknown}" > "$APP_DIR/.deployed-sha"

# 3. 同步后端源码（.env/.venv/data 被 .gitignore 保护）
echo ">>> 同步后端源码..."
cd "$APP_DIR"
git fetch --quiet origin main
git checkout -f -q -B main origin/main

# 4. 安装后端依赖（增量）
echo ">>> 安装依赖..."
"$VENV/pip" install -q -r "$APP_DIR/app/backend/requirements.txt"

# 5. 数据库迁移
echo ">>> 数据库迁移..."
cd "$APP_DIR/app/backend"
"$VENV/alembic" upgrade head

# 5.1 数据库属主修复：脚本可能以 root 运行，确保 kebiao 用户可写
DB_FILE=$(grep -oE '^DB_PATH=.*' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
if [ -n "$DB_FILE" ] && [ -f "$DB_FILE" ]; then
  sudo chown kebiao:kebiao "$DB_FILE"
  sudo -u kebiao test -w "$DB_FILE" || { echo "!!! 数据库不可写: $DB_FILE"; exit 1; }
  echo ">>> 数据库权限正常: $DB_FILE"
fi

# 6. 重启后端服务
echo ">>> 重启 $SERVICE..."
sudo systemctl restart "$SERVICE"

# 7. 健康检查
sleep 4
if curl -sf http://127.0.0.1:8001/api/v1/health > /dev/null; then
  echo "=== 部署完成，健康检查通过 ==="
else
  echo "!!! 健康检查失败，请检查服务状态: systemctl status $SERVICE"
  exit 1
fi
