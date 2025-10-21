# Ansible Web UI

🎨 现代化的 Ansible Web 用户界面，采用玻璃态设计风格的自动化管理平台

## ✨ 特性

- 🎯 直观的 Web 界面管理 Ansible 资源
- 🔐 完整的用户认证和权限管理
- 📦 项目、Playbook、Role 统一管理
- 🖥️ 实时执行监控和日志查看
- 🎨 现代化玻璃态 UI 设计
- 🚀 高性能异步架构

## 🛠️ 技术栈

### 后端
- FastAPI - 现代化 Python Web 框架
- SQLAlchemy - ORM 数据库管理
- Celery - 异步任务队列
- Ansible Runner - Ansible 执行引擎

### 前端
- React + TypeScript
- Vite - 快速构建工具
- TailwindCSS - 样式框架
- 玻璃态设计风格

## 📦 安装

### 环境要求
- Python >= 3.12
- Node.js >= 18
- Redis (用于任务队列)

### 后端安装

```bash
# 使用 uv 安装依赖
uv sync

# 激活虚拟环境
.\.venv\Scripts\activate

# 初始化数据库
.\.venv\Scripts\python.exe scripts/init_db.py

# 启动服务
.\.venv\Scripts\python.exe start_server.py
```

### 前端安装

```bash
cd frontend
npm install
npm run dev
```

## 🚀 快速开始

1. 配置环境变量（复制 `.env.example` 到 `.env`）
2. 启动 Redis 服务
3. 初始化数据库
4. 启动后端服务
5. 启动前端开发服务器
6. 访问 http://localhost:5173

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！
