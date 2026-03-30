# 考勤管理系统

班组考勤管理工具，支持排班管理、调休申请、加班记录、消息推送等功能。

---

## 📋 项目信息

- **项目名称**: 考勤管理系统 (Attendance Management System)
- **版本**: v1.4.2
- **开发时间**: 2026-03-30
- **GitHub**: github.com/dysobo/attendance-system

---

## 🎯 功能特性

### 1️⃣ 用户管理 🔐
- **登录/登出**: 用户名 + 密码认证，JWT Token 30 天有效期
- **记住登录**: 自动保存登录状态，下次访问无需重新登录
- **修改密码**: 用户可随时修改个人密码
- **角色权限**: 
  - 管理员（admin）：完整权限，可管理用户、排班、审批
  - 组员（member）：仅可查看和操作个人数据
- **用户管理**（管理员专用）:
  - 添加新用户（设置用户名、密码、角色）
  - 删除用户（删除前确认）
  - 修改用户角色（admin ↔ member）
  - 重置用户密码

### 2️⃣ 排班管理 📅（管理员专用）
- **发布排班**: 为班组成员设置每日班次
- **班次类型**: 早班、晚班、休息
- **编辑排班**: 修改已发布的排班信息
- **删除排班**: 删除错误的排班记录
- **智能校验**: 同一人同一天只能有一个排班
- **备注功能**: 可为排班添加备注说明
- **批量操作**: 支持连续多天快速排班

### 3️⃣ 调休申请 🏖️
- **提交申请**: 员工可申请调休（按小时计算）
- **最小单位**: 0.5 小时（支持 0.5、1.0、1.5 等）
- **选择日期**: 选择需要调休的日期
- **填写事由**: 说明调休原因
- **状态跟踪**: pending（待审批）→ approved（已批准）/ rejected（已拒绝）
- **审批流程**（管理员）:
  - 查看待审批列表
  - 批准/拒绝申请
  - 填写审批意见
- **编辑/删除**: 管理员可编辑或删除任何申请
- **权限隔离**: 组员只能查看自己的申请

### 4️⃣ 加班记录 🕐
- **登记加班**: 员工可登记加班记录（按小时计算）
- **最小单位**: 0.5 小时
- **选择日期**: 选择加班日期
- **填写事由**: 说明加班原因
- **状态跟踪**: pending（待确认）→ approved（已确认）
- **确认流程**（管理员）:
  - 查看待确认列表
  - 确认/拒绝加班记录
- **编辑/删除**: 管理员可编辑或删除任何记录
- **权限隔离**: 组员只能查看自己的记录

### 5️⃣ 消息推送 📱（Webhook）
- **推送场景**:
  - 员工提交调休申请 → 通知管理员
  - 员工登记加班 → 通知管理员
  - 调休审批完成 → 通知申请人
  - 加班确认完成 → 通知申请人
- **自定义配置**:
  - 推送地址（Webhook URL）
  - 通道 ID（如飞书群、钉钉群等）
- **测试推送**: 一键测试推送是否正常
- **推送内容**: 包含申请人、日期、时长、事由等详细信息

### 6️⃣ 数据统计 📊
- **仪表盘概览**:
  - 已批准调休时长
  - 待审批调休数量
  - 累计加班时长
  - 待确认加班数量
- **近期排班**: 未来 30 天排班预览
- **个人统计**:
  - 调休汇总（已批准/已拒绝/待审批）
  - 加班汇总（已确认/待确认）
  - 出勤天数统计
- **数据导出**: 支持查看历史数据

### 7️⃣ 数据可视化 🔥（v1.4.2 新增）
- **考勤热力图**: GitHub 贡献图风格
- **月份分组**: 12 个月份横向排列，清晰直观
- **颜色深浅**: 根据加班/调休时长自动着色
- **图例说明**: 下方居中显示，清晰易懂
- **精确对齐**: 月份标签按实际周数精确计算
- **交互提示**: 鼠标悬停显示详细数据
- **响应式布局**: 自适应不同屏幕尺寸

### 8️⃣ 移动端适配 📱
- **响应式布局**: 自动适配手机、平板、电脑
- **侧滑菜单**: 移动端便捷导航
- **触摸优化**: 按钮大小适合手指操作
- **表格滚动**: 宽表格支持横向滑动
- **对话框适配**: 弹窗在移动端友好显示
- **字体自适应**: 不同屏幕自动调整字号

### 9️⃣ 安全特性 🛡️
- **密码加密**: SHA256 加密存储
- **Token 认证**: JWT Token，30 天有效期
- **权限隔离**: 组员只能访问个人数据
- **操作确认**: 删除操作需二次确认
- **会话管理**: 支持多设备登录
- **HTTPS 支持**: 生产环境可启用 HTTPS

### 🔟 系统管理 ⚙️
- **服务管理**: systemd 守护进程，开机自启
- **日志记录**: 完整的操作日志
- **数据备份**: 支持手动/自动备份数据库
- **数据恢复**: 可从备份快速恢复
- **版本管理**: Git 版本控制，支持回退

---

## 🏗️ 技术架构

### 前端
- **框架**: Vue 3 (全局构建版本)
- **UI 库**: Element Plus
- **样式**: 自定义 CSS + 渐变主题
- **部署**: Nginx 静态文件托管

### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **ORM**: SQLAlchemy
- **认证**: JWT Token
- **密码加密**: SHA256
- **部署**: systemd 服务 + uvicorn

### 服务器
- **系统**: Linux (PVE 虚拟机)
- **Web 服务器**: Nginx (反向代理)
- **进程管理**: systemd

---

## 📁 项目结构

```
attendance-system/
├── backend/                    # 后端代码
│   ├── main.py                # FastAPI 主程序
│   ├── database.py            # 数据库模型
│   ├── webhook.py             # Webhook 推送模块
│   ├── attendance.db          # SQLite 数据库
│   ├── webhook_config.json    # Webhook 配置
│   └── requirements.txt       # Python 依赖
├── frontend/                   # 前端代码
│   ├── index.html             # 单页应用
│   ├── index-fixed.html       # 修复版本
│   ├── index-heatmap-optimized.html  # 热力图优化版
│   └── index-backup-*.html    # 备份文件
├── deploy/                     # 部署脚本
│   └── deploy.sh              # 一键部署脚本
└── README.md                   # 项目说明
```

---

## 🗄️ 数据库设计

### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(50) | 用户名（唯一） |
| password | VARCHAR(100) | 密码（SHA256） |
| role | VARCHAR(20) | 角色（admin/member） |
| created_at | DATETIME | 创建时间 |

### 排班表 (shifts)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID（外键） |
| date | DATE | 排班日期 |
| shift_type | VARCHAR(20) | 班次（早班/晚班/休息） |
| note | VARCHAR(200) | 备注 |
| created_at | DATETIME | 创建时间 |

### 调休申请表 (time_off_requests)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID（外键） |
| date | DATE | 调休日期 |
| hours | FLOAT | 时长（小时） |
| reason | TEXT | 事由 |
| status | VARCHAR(20) | 状态（pending/approved/rejected） |
| approved_by | INTEGER | 审批人 ID |
| created_at | DATETIME | 申请时间 |
| updated_at | DATETIME | 更新时间 |

### 加班记录表 (overtime_records)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID（外键） |
| date | DATE | 加班日期 |
| hours | FLOAT | 时长（小时） |
| reason | TEXT | 事由 |
| status | VARCHAR(20) | 状态（pending/approved） |
| approved_by | INTEGER | 确认人 ID |
| created_at | DATETIME | 创建时间 |

---

## 🔌 API 接口

### 认证接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/login` | POST | 用户登录 |
| `/api/users` | GET/POST | 用户列表/添加用户 |
| `/api/users/{id}` | DELETE | 删除用户 |
| `/api/users/{id}/role` | PUT | 修改用户角色 |
| `/api/users/{id}/reset-password` | POST | 重置密码 |
| `/api/auth/change-password` | POST | 修改密码 |

### 排班接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/shifts` | GET/POST | 排班列表/添加排班 |
| `/api/shifts/{id}` | PUT/DELETE | 编辑/删除排班 |

### 调休接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/time-off` | GET/POST | 调休列表/申请调休 |
| `/api/time-off/{id}` | PUT/DELETE | 编辑/删除调休 |
| `/api/time-off/{id}/approve` | POST | 审批调休 |

### 加班接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/overtime` | GET/POST | 加班列表/登记加班 |
| `/api/overtime/{id}` | PUT/DELETE | 编辑/删除加班 |
| `/api/overtime/{id}/approve` | POST | 确认加班 |

### 统计接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stats/my-summary` | GET | 个人统计汇总 |

### Webhook 接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/webhook/config` | GET/POST | 获取/保存配置 |
| `/api/webhook/test` | POST | 测试推送 |

---

## 🚀 部署说明

### 环境要求
- Python 3.9+
- Node.js 18+ (可选，仅开发)
- Nginx
- systemd

### 部署步骤

1. **上传项目到服务器**
```bash
scp -r attendance-system root@您的服务器 IP:/root/
```

2. **安装 Python 依赖**
```bash
cd /root/attendance-system/backend
pip3 install -r requirements.txt --break-system-packages
```

3. **配置 Nginx**
```nginx
server {
    listen 8888;
    server_name _;
    
    location /kq/ {
        alias /root/attendance-system/frontend/;
        index index.html;
        try_files $uri $uri/ /kq/index.html;
    }
    
    location /kq/api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **创建 systemd 服务**
```ini
[Unit]
Description=考勤管理系统后端服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/attendance-system/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **启动服务**
```bash
systemctl daemon-reload
systemctl enable attendance.service
systemctl start attendance.service
systemctl restart nginx
```

---

## 📱 使用指南

### 管理员操作

1. **登录**: 使用 admin 账号登录
2. **排班管理**: 发布、编辑、删除排班
3. **用户管理**: 添加/删除用户、修改角色、重置密码
4. **审批调休**: 批准/拒绝员工的调休申请
5. **确认加班**: 确认/拒绝员工的加班记录
6. **编辑记录**: 编辑/删除调休和加班记录
7. **消息推送**: 配置 Webhook 推送地址

### 组员操作

1. **登录**: 使用个人账号登录
2. **查看排班**: 查看自己的排班
3. **申请调休**: 提交调休申请（按小时）
4. **登记加班**: 提交加班记录（按小时）
5. **查看记录**: 查看自己的调休和加班记录
6. **修改密码**: 修改个人密码

---

## 📊 后续规划

### 1️⃣ 成员独立推送 📅
- [ ] 为每个成员配置独立的推送通道
- [ ] 审批结果推送给申请人
- [ ] 排班变更推送给相关人员

### 2️⃣ 月末汇总推送 📈
- [ ] 每月最后一天自动汇总
- [ ] 个人调休/加班统计
- [ ] 班组整体统计
- [ ] 推送给管理员和成员

### 3️⃣ 班组汇总报表 📋
- [ ] 月度报表（Excel/PDF）
- [ ] 调休/加班统计图表
- [ ] 出勤率分析
- [ ] 导出功能

### 4️⃣ 年度个人统计 📊
- [ ] 年度调休/加班汇总
- [ ] 个人考勤报告
- [ ] 趋势分析图表
- [ ] 可打印版本

### 5️⃣ 待定功能 💡
- [ ] 请假类型分类（病假/事假/年假）
- [ ] 考勤规则配置（迟到/早退）
- [ ] 打卡功能（可选）
- [ ] 日历视图
- [ ] 数据导入/导出
- [ ] 多班组支持
- [ ] 移动端 App（可选）

---

## 🔐 安全说明

1. **密码安全**: 使用 SHA256 加密存储
2. **Token 认证**: JWT Token 30 天有效期
3. **权限隔离**: 组员只能查看自己的数据
4. **操作确认**: 删除操作有确认对话框
5. **HTTPS**: 建议生产环境启用 HTTPS

---

## 🛠️ 维护命令

### 查看服务状态
```bash
ssh root@服务器 IP -p 端口 "systemctl status attendance.service"
```

### 重启服务
```bash
ssh root@服务器 IP -p 端口 "systemctl restart attendance.service"
```

### 查看日志
```bash
ssh root@服务器 IP -p 端口 "journalctl -u attendance.service -f"
```

### 备份数据库
```bash
ssh root@服务器 IP -p 端口 "cp /path/to/attendance/backend/attendance.db /root/attendance-backup-$(date +%Y%m%d).db"
```

### 恢复数据库
```bash
ssh root@服务器 IP -p 端口 "cp /root/attendance-backup-20260330.db /path/to/attendance/backend/attendance.db && systemctl restart attendance.service"
```

---

## 📞 技术支持

- **服务器**: ECS 云服务器
- **部署路径**: /path/to/attendance/
- **前端路径**: /path/to/attendance/frontend/
- **后端路径**: /path/to/attendance/backend/
- **数据库**: /path/to/attendance/backend/attendance.db

---

## 📝 更新日志

### v1.4.3 (2026-03-30) - 修复推送配置丢失 Bug 🐛

**🔧 Bug 修复**
- ✅ 修复 Webhook 配置文件路径错误导致配置自动关闭的问题
- ✅ 配置文件改为相对路径（backend/webhook_config.json）
- ✅ 保存配置时自动创建目录
- ✅ 配置持久化正常，重启不丢失

**问题原因**：
- 原路径 `/opt/attendance/backend/webhook_config.json` 目录不存在
- 保存配置时写入失败，重启后读取默认值 enabled: false

---

### v1.4.2 (2026-03-30) - 首个正式发布版本 🎉

**🎨 数据可视化**
- ✅ 新增考勤热力图（GitHub 贡献图风格）
- ✅ 按月份分组显示，12 个月横向排列
- ✅ 颜色深浅自动根据加班/调休时长着色
- ✅ 图例从右下角优化为下方居中
- ✅ 月份标签按实际周数精确对齐
- ✅ 鼠标悬停显示详细数据

**📱 用户体验优化**
- ✅ 移动端响应式布局全面优化
- ✅ 侧滑菜单交互更流畅
- ✅ 对话框和弹窗适配移动端
- ✅ 表格横向滚动更顺滑

**🔧 系统改进**
- ✅ 后端 API 性能优化
- ✅ 数据库查询效率提升
- ✅ 权限校验逻辑完善
- ✅ 错误提示更友好

**📦 技术栈**
- 前端：Vue 3 + Element Plus
- 后端：FastAPI + SQLite + SQLAlchemy
- 认证：JWT Token
- 部署：Nginx + systemd

---

## ©️ 版权说明

- **版权所有**: © 2026 波仔和他的小龙虾
- **许可证**: 本软件为内部使用，未经授权不得用于商业用途
- **保留所有权利**

---

**最后更新**: 2026-03-30  
**维护人员**: 波仔和他的小龙虾 🦞
