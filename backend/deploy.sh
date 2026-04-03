#!/bin/bash
# 部署考勤系统后端到狐蒂云 ECS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REMOTE_HOST="root@114.134.184.210"
REMOTE_PORT="22"
REMOTE_DIR="/root/attendance-system"

echo "🚀 开始部署考勤系统后端..."

# 本地语法检查
echo "📋 本地语法检查..."
cd "$PROJECT_ROOT/backend"
python3 -m py_compile main.py database.py webhook.py
echo "✅ 语法检查通过"

# 上传后端
echo "📤 上传后端文件到服务器..."
scp -P "$REMOTE_PORT" "$PROJECT_ROOT/backend/main.py" "$PROJECT_ROOT/backend/database.py" "$PROJECT_ROOT/backend/webhook.py" "$PROJECT_ROOT/backend/requirements.txt" "$REMOTE_HOST:$REMOTE_DIR/backend/"
echo "✅ 后端上传成功"

# 上传前端
echo "📤 上传前端文件到服务器..."
scp -P "$REMOTE_PORT" "$PROJECT_ROOT/frontend/index.html" "$PROJECT_ROOT/frontend/app.js" "$PROJECT_ROOT/frontend/api.js" "$PROJECT_ROOT/frontend/session.js" "$PROJECT_ROOT/frontend/actions.js" "$PROJECT_ROOT/frontend/heatmap.js" "$PROJECT_ROOT/frontend/data-tools.js" "$REMOTE_HOST:$REMOTE_DIR/frontend/"
echo "✅ 前端上传成功"

# 安装依赖
echo "📦 更新服务器依赖..."
ssh -p "$REMOTE_PORT" "$REMOTE_HOST" "cd $REMOTE_DIR/backend && python3 -m pip install -r requirements.txt"
echo "✅ 依赖更新完成"

# 重启服务
echo "🔄 重启服务..."
ssh -p "$REMOTE_PORT" "$REMOTE_HOST" "systemctl restart attendance.service || (cd $REMOTE_DIR/backend && pkill -f 'python.*main.py' && nohup python3 main.py > /var/log/attendance.log 2>&1 &)"
echo "✅ 服务重启成功"

echo "🎉 部署完成！"
