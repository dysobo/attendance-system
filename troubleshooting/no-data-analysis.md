# 考勤系统首页 "No Data" 问题分析报告

## 📋 问题描述
陛下反馈考勤系统首页卡片显示 "No Data"。

## 🔍 已完成的检查

### 1. 服务状态检查 ✅
- 后端服务：正常运行 (`attendance.service` active)
- Nginx 服务：正常运行
- 数据库：存在且有数据（1 个 admin 用户）

### 2. API 路径检查 ✅
- 前端 API_BASE: `/api` (服务器部署版本)
- Nginx 代理配置: `/api/` → `http://127.0.0.1:8000/api/`
- 路径配置正确 ✅

### 3. 数据库数据检查 ⚠️
```sql
SELECT COUNT(*) FROM shifts;            -- 0 条
SELECT COUNT(*) FROM time_off_requests; -- 0 条
SELECT COUNT(*) FROM overtime_records;  -- 0 条
```
**问题**：考勤相关表全部为空，这是首页显示 "No Data" 的根本原因之一。

### 4. API 认证检查 ❌
**发现严重问题**：JWT Token 验证失败

#### 问题根源
- 使用的 `python-jose==3.3.0` 库要求 `sub` 字段必须是**字符串**
- 但代码中传入的是**整数** `user.id`
- 导致 token 生成后无法正确解码验证

#### 代码位置
```python
# /opt/attendance/backend/main.py 第 157 行
token = create_access_token({"sub": user.id, "role": user.role})
#                                              ^^^^^^^^ 应该是 str(user.id)
```

#### 验证测试
```bash
# 整数 sub - 验证失败
jwt.decode(token, SECRET_KEY) → "Subject must be a string"

# 字符串 sub - 验证成功
jwt.decode(token, SECRET_KEY) → {'sub': '1', 'role': 'admin', ...}
```

## 📊 问题汇总

| 优先级 | 问题 | 影响 | 状态 |
|--------|------|------|------|
| P0 | JWT Token sub 字段类型错误 | 用户无法登录，所有 API 调用失败 | 待修复 |
| P1 | 数据库无考勤数据 | 首页卡片显示 No Data | 待确认 |
| P2 | 前后端代码版本不一致 | workspace 与服务器代码不同步 | 待同步 |

## 🔧 修复方案

### 方案 1：修复 JWT Token 问题（P0 - 紧急）

**修改文件**: `/opt/attendance/backend/main.py`

**修改内容**:
```python
# 第 157 行，将:
token = create_access_token({"sub": user.id, "role": user.role})

# 改为:
token = create_access_token({"sub": str(user.id), "role": user.role})
```

**验证步骤**:
1. 重启后端服务：`systemctl restart attendance`
2. 测试登录：`curl -X POST http://localhost/api/login -H "Content-Type: application/json" -d '{"name":"admin","password":"admin123"}'`
3. 使用返回的 token 测试 API：`curl http://localhost/api/stats/my-summary -H "Authorization: Bearer <token>"`

### 方案 2：检查数据来源（P1 - 高优先级）

**需要确认**:
1. 考勤数据应该从哪个系统同步？
2. 是否有数据导入脚本？
3. 是否需要手动录入测试数据？

**建议操作**:
1. 检查是否有数据同步服务
2. 查看历史部署记录
3. 创建测试数据验证前端显示

### 方案 3：代码同步（P2 - 中优先级）

**问题**: workspace 代码与服务器部署代码不一致

**建议**:
1. 将 workspace 代码部署到服务器
2. 或者将服务器修改同步回 workspace
3. 建立版本管理流程

## 📝 执行建议

1. **立即执行**: 修复 JWT Token 问题（方案 1）
2. **随后执行**: 确认数据来源和导入方式（方案 2）
3. **长期优化**: 建立代码同步和版本管理流程（方案 3）

## 🎯 预期结果

修复后：
- 用户可以正常登录
- API 返回正确的统计数据
- 首页卡片显示真实数据（如果有数据）
- 如果数据库确实无数据，显示 "0" 而不是 "No Data"

---
**分析时间**: 2026-04-02 09:00 UTC
**分析人**: 子 Agent
