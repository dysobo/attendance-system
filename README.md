# 考勤管理系统

班组考勤管理工具，覆盖排班、调休、加班、审批、消息推送、备份恢复和年度热力图展示。

- 当前版本：`V4.4`
- 仓库地址：`https://github.com/dysobo/attendance-system`
- 前端访问路径：`/kq/`
- 后端 API：`/api/*`

## V4.4 重点更新

- 安全收口：补齐多处接口鉴权与成员越权限制，新增 `/api/me`
- 备份增强：导出支持敏感字段开关，导入改为更安全的恢复流程
- 前端模块化：从单个内联脚本拆分为 `app.js / api.js / session.js / actions.js / heatmap.js / data-tools.js`
- Webhook 收口：配置、保存、发送逻辑统一到 `backend/webhook.py`
- 仪表盘体验优化：近期排班支持移动端卡片、电话号码点击拨号
- 列表体验升级：排班管理、调休申请、加班记录在手机微信中统一改为卡片化展示
- 审批留痕升级：调休申请、加班记录新增“审批意见”持久化存储，并同步展示到桌面表格和手机卡片
- 消息卡片升级：企业微信与 Webhook 通知统一为无 emoji 文本模板，字段对齐更稳定
- 管理员列表优化：调休申请、加班记录统一按申请日期倒序显示
- 热力图升级：新增年度摘要、完整图例、浅色科技风样式、手机微信点击查看
- 微信指令申请：已绑定企业微信的成员可直接发送“记加班 4h 今天 设备调试”或“调休 1h 明天 看牙”创建申请
- 微信快捷审批：管理员可直接发送“同意 已处理”或“不同意 工时不足”审批最近一条待处理申请

## 功能概览

### 用户与权限

- 用户登录、JWT 鉴权、修改密码
- 管理员可新增用户、编辑用户、重置密码、切换角色、删除用户
- 组员仅可访问自己的调休、加班、个人排班等数据

### 排班管理

- 管理员新增、编辑、删除排班
- 支持班次：`早班 / 晚班 / 休息`
- 同一用户同一天排班唯一
- 首页展示未来 30 天近期排班
- 移动端近期排班使用卡片展示，电话可直接点击拨打

### 调休申请

- 组员提交调休申请，按小时记录
- 管理员审批、驳回、编辑、删除
- 仅统计已批准数据进入年度汇总和热力图

### 加班记录

- 组员登记加班，按小时记录
- 管理员确认、拒绝、编辑、删除
- 首页和统计页可查看累计加班情况

### 消息推送

- 支持 Webhook 推送
- 支持企业微信配置、测试推送、回调处理、用户绑定
- 支持调休审批结果、加班确认结果等通知场景
- 支持企业微信文本指令创建加班、调休申请
- 支持管理员通过企业微信文本指令快速审批最近一条待处理申请

### 统计与可视化

- 仪表盘汇总卡片
- 年度加班/调休热力图
- 月度统计导出
- 备份导出与导入

## 项目结构

```text
attendance-system/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── webhook.py
│   ├── requirements.txt
│   ├── deploy.sh
│   ├── test_api_security.py
│   └── test_push_format.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── api.js
│   ├── session.js
│   ├── actions.js
│   ├── heatmap.js
│   ├── data-tools.js
│   └── index.html
├── deploy/
│   └── deploy.sh
└── README.md
```

## 技术栈

### 前端

- Vue 3
- Element Plus
- 原生 CSS

### 后端

- FastAPI
- SQLAlchemy
- SQLite
- JWT

### 部署

- Nginx
- systemd
- uvicorn

## 本地启动

### 1. 安装后端依赖

```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. 启动后端

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 打开前端

前端是静态文件，直接通过 Nginx 或任意静态文件服务托管 `frontend/` 即可。生产环境入口为：

```text
frontend/index.html
```

## 生产部署

当前线上环境实际使用：

- 部署目录：`/opt/attendance`
- 前端目录：`/opt/attendance/frontend`
- 后端目录：`/opt/attendance/backend`
- 服务名：`attendance.service`
- Nginx 访问路径：`/kq/`

可参考：

- [deploy/deploy.sh](deploy/deploy.sh)
- [backend/deploy.sh](backend/deploy.sh)

### 典型部署流程

```bash
cd /opt/attendance/backend
python3 -m pip install -r requirements.txt
systemctl restart attendance.service
nginx -t && systemctl reload nginx
```

## 主要 API

### 认证与用户

- `POST /api/login`
- `GET /api/me`
- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/{id}`
- `POST /api/users/{id}/reset-password`
- `PUT /api/users/{id}/role`
- `DELETE /api/users/{id}`
- `POST /api/auth/change-password`

### 排班

- `GET /api/shifts`
- `GET /api/shifts/team`
- `POST /api/shifts`
- `PUT /api/shifts/{id}`
- `DELETE /api/shifts/{id}`
- `POST /api/shifts/{id}/notify`

### 调休

- `GET /api/time-off`
- `POST /api/time-off`
- `PUT /api/time-off/{id}`
- `DELETE /api/time-off/{id}`
- `POST /api/time-off/{id}/approve`

### 加班

- `GET /api/overtime`
- `POST /api/overtime`
- `PUT /api/overtime/{id}`
- `DELETE /api/overtime/{id}`
- `POST /api/overtime/{id}/approve`

### 统计与数据

- `GET /api/stats/summary`
- `GET /api/stats/my-summary`
- `GET /api/export/monthly`
- `GET /api/backup/export`
- `POST /api/backup/import`

### 推送与企业微信

- `GET /api/webhook/config`
- `POST /api/webhook/config`
- `POST /api/webhook/test`
- `GET /api/wechat/config`
- `POST /api/wechat/config`
- `GET /api/wechat/bind`
- `POST /api/wechat/bind`
- `POST /api/wechat/test-push`
- `GET /api/wechat/callback`
- `POST /api/wechat/callback`

## 测试与检查

当前仓库内已补充基础安全回归测试：

- [backend/test_api_security.py](backend/test_api_security.py)

常用检查命令：

```bash
python -m py_compile backend/main.py backend/database.py backend/webhook.py
node --check frontend/app.js
node --check frontend/heatmap.js
```

## 当前已知问题

以下问题已经识别，但尚未在 V4.4 中彻底解决：

- 密码存储仍是 SHA256，下一步应切换到 `bcrypt`
- `backend/main.py` 仍然偏大，企业微信相关逻辑还可继续拆分

## 更新记录

### V4.4 · 2026-04-07

- 企业微信回调新增文本消息处理，可直接识别“记加班 / 调休”指令
- 按 `wechat_user_id` 自动识别发送人并创建待审批申请
- 指令支持 `今天 / 明天 / 后天 / YYYY-MM-DD` 日期格式，时长支持 `0.5h` 步长
- 指令处理成功或失败后会回推确认消息
- 管理员可直接发送“同意 / 不同意 + 原因”快速审批最近一条待处理申请
- 首页右下角版本号升级为 V4.4
- 后端 API 版本升级为 4.4.0

### V4.3 · 2026-04-07

- 企业微信消息卡片去除 emoji 混排，统一标题和正文字段格式
- Webhook 通知标题和正文统一为文本模板
- 管理员调休申请列表改为按申请日期倒序显示
- 管理员加班记录列表补充稳定的倒序排序规则
- 调休和加班页面新增排序说明
- 首页右下角版本号升级为 V4.3
- 后端 API 版本升级为 4.3.0

### V4.2 · 2026-04-04

- 调休申请新增审批意见列
- 加班记录新增审批意见列
- 手机卡片同步展示审批意见
- 后端数据库新增 `admin_comment` 持久化字段
- 备份导入导出纳入审批意见字段
- 首页右下角版本号升级为 V4.2
- 后端 API 版本升级为 4.2.0

### V4.1 · 2026-04-04

- 排班管理页新增移动端卡片视图
- 调休申请页新增移动端卡片视图
- 加班记录页新增移动端卡片视图
- 首页、排班、调休、加班四处移动端风格统一
- 首页右下角版本号升级为 V4.1
- 后端 API 版本升级为 4.1.0

### V4.0 · 2026-04-03

- 完成接口鉴权与越权限制修复
- 完成备份导入导出安全增强
- 完成前端脚本模块化拆分
- 完成 Webhook 模块统一
- 完成近期排班移动端卡片化与电话直拨
- 完成年度热力图浅色科技风改版与手机微信兼容

## 版权说明

- 版权归项目维护者所有
- 当前仓库用于内部业务场景
