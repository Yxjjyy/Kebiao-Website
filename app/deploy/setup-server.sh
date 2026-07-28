#!/bin/bash
# ============================================
# 课表项目 — 服务器初始化脚本
# 适用于: 阿里云 ECS Ubuntu 22.04
# 在服务器上以 root 用户执行:
#   chmod +x setup-server.sh
#   sudo ./setup-server.sh
# ============================================
set -euo pipefail

echo "========================================"
echo " 课表项目 — 服务器环境初始化"
echo "========================================"

# ---- 1. 系统更新 & 基础工具 ----
echo ">>> [1/7] 系统更新..."
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq curl wget git sqlite3 acl python3-venv python3-pip

# ---- 2. 安装 Caddy (Web 服务器) ----
echo ">>> [2/7] 安装 Caddy..."
if ! command -v caddy &>/dev/null; then
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" \
        | tee /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq && apt-get install -y -qq caddy
fi

# ---- 3. 安装 Node.js 20 ----
echo ">>> [3/7] 安装 Node.js 20..."
if ! command -v node &>/dev/null || [ "$(node -v | cut -d. -f1 | tr -d 'v')" -lt 18 ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

# ---- 4. 确保 Python 3.10+ ----
echo ">>> [4/7] 检查 Python..."
python3 -c 'import sys; assert sys.version_info >= (3,10), "Need Python 3.10+"' 2>/dev/null || {
    echo "请安装 Python 3.10+ (Ubuntu 22.04 默认 python3 已满足)"
}

# ---- 5. 创建用户和目录 ----
echo ">>> [5/7] 创建用户与目录..."
id -u kebiao &>/dev/null || useradd --system --create-home --shell /bin/bash kebiao
mkdir -p /home/kebiao/app /home/kebiao/data /home/kebiao/backups /var/log/kebiao
chown -R kebiao:kebiao /home/kebiao /var/log/kebiao

# ---- 6. 安装 Python 虚拟环境 ----
echo ">>> [6/7] 创建 Python 虚拟环境..."
cd /home/kebiao/app/backend 2>/dev/null || {
    echo "请先将项目文件上传到 /home/kebiao/app/"
    echo "然后执行: cd /home/kebiao/app/backend && python3 -m venv .venv"
}
# 如果 backend 目录已存在则立即创建 venv
if [ -d /home/kebiao/app/backend ]; then
    cd /home/kebiao/app/backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python -m alembic upgrade head
    chown -R kebiao:kebiao /home/kebiao/app/backend/.venv
fi

# ---- 7. 注册 systemd 服务 ----
echo ">>> [7/7] 注册 systemd 服务..."
if [ -f /home/kebiao/app/deploy/kebiao-backend.service ]; then
    cp /home/kebiao/app/deploy/kebiao-backend.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable kebiao-backend
fi

echo ""
echo "========================================"
echo " 环境初始化完成!"
echo "========================================"
echo ""
echo "接下来请你手动完成:"
echo ""
echo "1. 配置 .env 文件:"
echo "   cp /home/kebiao/app/deploy/.env.production /home/kebiao/app/backend/.env"
echo "   vim /home/kebiao/app/backend/.env  # 修改 CORS_ORIGINS 和你的域名/IP"
echo ""
echo "2. 配置 Caddy:"
echo "   sudo cp /home/kebiao/app/deploy/Caddyfile /etc/caddy/Caddyfile"
echo "   sudo vim /etc/caddy/Caddyfile  # 修改域名"
echo "   sudo systemctl reload caddy"
echo ""
echo "3. 构建前端:"
echo "   cd /home/kebiao/app/frontend && npm install && npm run build"
echo ""
echo "4. 启动后端:"
echo "   sudo systemctl start kebiao-backend"
echo "   sudo systemctl status kebiao-backend"
echo ""
echo "5. (可选) 设置定时备份:"
echo "   crontab -u kebiao -e"
echo "   添加: 0 3 * * * /home/kebiao/app/deploy/backup.sh"
