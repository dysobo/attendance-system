# GitHub 推送指南

## 方法一：手动创建仓库（推荐）

### 1. 在 GitHub 创建仓库

1. 打开 https://github.com/new
2. 填写信息：
   - **Repository name**: `attendance-system`
   - **Description**: `考勤管理系统 - 班组考勤管理工具`
   - **Visibility**: 🔒 Private（私有）
3. 点击 "Create repository"

### 2. 推送代码

```bash
cd /root/.openclaw/workspace/attendance-system

# 添加 remote（如果还没添加）
git remote add origin git@github.com:dysobo/attendance-system.git

# 推送到 GitHub
git push -u origin main
```

### 3. 查看项目

打开：https://github.com/dysobo/attendance-system

---

## 方法二：使用 GitHub CLI（需要认证）

### 1. 认证 GitHub

```bash
gh auth login
# 按提示完成认证
```

### 2. 创建并推送

```bash
cd /root/.openclaw/workspace/attendance-system
gh repo create attendance-system --private --source=. --remote=origin --push
```

---

## 后续更新流程

### 本地修改后推送

```bash
cd /root/.openclaw/workspace/attendance-system

# 查看变更
git status

# 添加变更
git add -A

# 提交
git commit -m "V1.x - 更新说明"

# 推送到 GitHub
git push origin main

# 查看提交历史
git log --oneline
```

### 版本标签

```bash
# 创建版本标签
git tag -a v1.3 -m "V1.3 - 考勤管理系统"

# 推送标签到 GitHub
git push origin v1.3

# 查看所有标签
git tag -l
```

---

## 仓库结构

```
attendance-system/
├── README.md              # 项目说明
├── VERSIONS.md            # 版本历史
├── .gitignore             # Git 忽略文件
├── backend/               # 后端代码
│   ├── main.py           # FastAPI 主程序
│   ├── database.py       # 数据库模型
│   ├── webhook.py        # Webhook 推送
│   └── requirements.txt  # Python 依赖
├── frontend/              # 前端代码
│   └── index.html        # 单页应用
├── deploy/                # 部署脚本
│   └── deploy.sh         # 一键部署
└── project-info.html      # 项目说明网页
```

---

## 备份策略

### 本地备份
- `/opt/attendance/frontend/index-backup-v*.html`

### GitHub 备份
- 所有代码提交到 GitHub
- 每次更新后推送
- 使用标签标记版本

### 回滚方法
```bash
# 查看历史版本
git log --oneline

# 回滚到特定版本
git checkout v1.3

# 推送回滚
git push -f origin main
```

---

## 协作开发

### 添加协作者
1. 打开仓库 Settings
2. 点击 "Collaborators"
3. 添加 GitHub 用户名

### 分支管理
```bash
# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature
```

---

**创建时间**: 2026-03-30  
**维护人员**: 波仔和他的小龙虾 🦞
