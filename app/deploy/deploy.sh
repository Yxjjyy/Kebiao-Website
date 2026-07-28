#!/bin/bash
set -euo pipefail

APP_DIR=/home/kebiao/app
LOG_DIR=/var/log/kebiao
DATA_DIR=/home/kebiao/data

echo "=== 课表部署脚本 ==="

# 确保目录存在
sudo mkdir -p "$LOG_DIR" "$DATA_DIR"
sudo chown -R kebiao:kebiao "$LOG_DIR" "$DATA_DIR"

# 后端
echo ">>> 更新后端依赖..."
cd "$APP_DIR/backend"
source .venv/bin/activate
pip install -r requirements.txt -q
echo ">>> 数据库迁移..."
alembic upgrade head

# 前端
echo ">>> 构建前端..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build

# 重启服务
echo ">>> 重启后端服务..."
sudo systemctl daemon-reload
sudo systemctl restart kebiao-backend

echo "=== 部署完成 ==="
systemctl status kebiao-backend --no-pager
