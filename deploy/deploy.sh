#!/bin/bash
# 考勤系统部署脚本

set -e

echo "🚀 开始部署考勤管理系统..."

# 配置
ATTENDANCE_DIR="/opt/attendance"
BACKUP_DIR="/opt/attendance-backup-$(date +%Y%m%d-%H%M%S)"

# 1. 备份旧版本
if [ -d "$ATTENDANCE_DIR" ]; then
    echo "📦 备份旧版本到 $BACKUP_DIR"
    cp -r "$ATTENDANCE_DIR" "$BACKUP_DIR"
fi

# 2. 创建目录
echo "📁 创建目录..."
mkdir -p "$ATTENDANCE_DIR"/{backend,frontend,data}

# 3. 复制文件
echo "📋 复制文件..."
cp -r ~/attendance-system/backend/* "$ATTENDANCE_DIR/backend/"
cp ~/attendance-system/frontend/index.html "$ATTENDANCE_DIR/frontend/"

# 4. 安装 Python 依赖
echo "📦 安装 Python 依赖..."
cd "$ATTENDANCE_DIR/backend"
pip3 install -r requirements.txt -q

# 5. 创建 systemd 服务
echo "⚙️ 创建 systemd 服务..."
cat > /etc/systemd/system/attendance.service << EOF
[Unit]
Description=考勤管理系统后端服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$ATTENDANCE_DIR/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable attendance.service

# 6. 配置 Nginx
echo "🌐 配置 Nginx..."
cat > /etc/nginx/sites-available/attendance << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root /opt/attendance/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/attendance
nginx -t && systemctl reload nginx

# 7. 启动服务
echo "🚀 启动服务..."
systemctl restart attendance.service

# 8. 检查状态
echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo ""
echo "📍 访问地址：http://$(hostname -I | awk '{print $1}')"
echo "🔧 后端状态：systemctl status attendance"
echo "📋 查看日志：journalctl -u attendance -f"
echo ""
echo "👤 默认管理员账号:"
echo "   用户名：admin"
echo "   密码：admin123"
echo ""
echo "⚠️  首次登录请修改密码！"
echo "=========================================="
