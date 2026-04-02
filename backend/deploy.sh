#!/bin/bash
# 部署考勤系统后端到狐蒂云 ECS

echo "🚀 开始部署考勤系统后端..."

# 本地语法检查
echo "📋 本地语法检查..."
cd /root/.openclaw/workspace/attendance-system/backend
python3 -m py_compile main.py
if [ $? -ne 0 ]; then
    echo "❌ 语法检查失败，停止部署"
    exit 1
fi
echo "✅ 语法检查通过"

# 上传到服务器
echo "📤 上传文件到服务器..."
scp -P 22 main.py root@114.134.184.210:/root/attendance-system/backend/
if [ $? -ne 0 ]; then
    echo "❌ 上传失败"
    exit 1
fi
echo "✅ 上传成功"

# 重启服务
echo "🔄 重启服务..."
ssh -p 22 root@114.134.184.210 "cd /root/attendance-system/backend && pkill -f 'python.*main.py' && nohup python3 main.py > /var/log/attendance.log 2>&1 &"
if [ $? -ne 0 ]; then
    echo "❌ 重启失败"
    exit 1
fi
echo "✅ 服务重启成功"

echo "🎉 部署完成！"
