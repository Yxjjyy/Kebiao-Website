# 部署到阿里云 ECS Ubuntu 22.04

## 前置条件

- 阿里云 ECS 实例（Ubuntu 22.04），已通过 Workbench 远程连接
- （推荐）一个域名，DNS 解析到 ECS 公网 IP
- 安全组规则：开放 22 (SSH)、80 (HTTP)、443 (HTTPS)

## 第一步：上传项目

在本地 Windows 上将项目打包上传到服务器：

```bash
# 在项目根目录 D:\Desktop\课表网站\ 执行
tar --exclude='node_modules' --exclude='.venv' --exclude='dist' --exclude='__pycache__' \
    -czf kebiao.tar.gz backend frontend deploy

# 通过 scp 上传（在 Windows Terminal 或 Git Bash 中执行）
scp kebiao.tar.gz root@你的服务器公网IP:/tmp/
```

或者通过阿里云 Workbench 的"文件上传"功能，上传打包好的 `kebiao.tar.gz` 到 `/tmp/`。

在服务器上解压：

```bash
mkdir -p /home/kebiao/app
tar -xzf /tmp/kebiao.tar.gz -C /home/kebiao/app/
chown -R root:root /home/kebiao/app
```

## 第二步：环境初始化

在服务器上以 root 用户执行：

```bash
chmod +x /home/kebiao/app/deploy/setup-server.sh
bash /home/kebiao/app/deploy/setup-server.sh
```

这个脚本会自动安装：Caddy、Node.js 20、Python venv、systemd 服务，并创建 `kebiao` 用户。

## 第三步：配置生产环境变量

```bash
# 复制生产环境配置模板
cp /home/kebiao/app/deploy/.env.production /home/kebiao/app/backend/.env

# 编辑配置
vim /home/kebiao/app/backend/.env
```

**必改项** — `CORS_ORIGINS` 改为你的前端地址：
```env
# 如果有域名（推荐）
CORS_ORIGINS=https://你的域名.com
# 如果只使用 IP
CORS_ORIGINS=http://你的公网IP
```

## 第四步：配置 Caddy

```bash
sudo cp /home/kebiao/app/deploy/Caddyfile /etc/caddy/Caddyfile
sudo vim /etc/caddy/Caddyfile
```

修改 `your-domain.com` 为你的真实域名。如果没有域名，注释掉有域名的部分，取消最后 IP 部分的注释。

```bash
# 验证配置
caddy validate --config /etc/caddy/Caddyfile

# 重载 Caddy
sudo systemctl reload caddy
```

## 第五步：构建前端 & 启动后端

```bash
# 构建前端
cd /home/kebiao/app/frontend
npm install
npm run build

# 启动后端服务
sudo systemctl start kebiao-backend
sudo systemctl status kebiao-backend

# 查看日志确认正常
sudo journalctl -u kebiao-backend -f
```

## 第六步：验证部署

```bash
# 健康检查
curl http://127.0.0.1:8000/api/v1/health

# 通过域名访问（如果有配置 Caddy）
curl https://你的域名.com/api/v1/health
```

浏览器访问 `https://你的域名.com` 或 `http://你的公网IP` 查看前端页面。

## 日常运维

**项目更新：**
```bash
# 上传新版本代码到服务器后
sudo bash /home/kebiao/app/deploy/deploy.sh
```

**查看日志：**
```bash
# 后端日志
sudo journalctl -u kebiao-backend --since "10 min ago"

# Caddy 访问日志
sudo tail -f /var/log/caddy/kebiao-access.log
```

**数据库备份：**
```bash
# 手动备份
sudo bash /home/kebiao/app/deploy/backup.sh

# 设置每日凌晨 3 点自动备份
crontab -u kebiao -e
# 添加: 0 3 * * * /home/kebiao/app/deploy/backup.sh
```

## 文件结构（服务器上）

```
/home/kebiao/
├── app/
│   ├── backend/          # FastAPI 后端
│   │   ├── .venv/        # Python 虚拟环境
│   │   ├── .env          # 生产环境配置
│   │   └── app/          # 应用代码
│   ├── frontend/         # Vue 前端
│   │   └── dist/         # 构建产物
│   └── deploy/           # 部署脚本
├── data/
│   └── app.db            # SQLite 数据库
└── backups/              # 数据库备份
```
