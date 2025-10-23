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
- PostgreSQL - 主数据库（开发环境支持 SQLite）
- Celery - 异步任务队列
- Ansible Runner - Ansible 执行引擎

### 前端
- React + TypeScript
- Vite - 快速构建工具
- TailwindCSS - 样式框架
- 玻璃态设计风格

### 存储架构
- **纯数据库存储**: Playbook 和项目文件内容直接存储在数据库中
- **无本地文件系统**: 简化架构，完美支持容器化部署
- **数据一致性**: 单一数据源，无缓存同步问题
- **高性能**: 读取响应时间 < 50ms，支持 50+ 并发用户
- **Docker 友好**: 只需持久化数据库卷，无需额外配置

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

### 开发环境

1. 配置环境变量（复制 `.env.example` 到 `.env`）
2. 启动 Redis 服务
3. 初始化数据库
4. 启动后端服务
5. 启动前端开发服务器
6. 访问 http://localhost:5173

### Docker 部署

#### 使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      # 只需持久化数据库目录
      - ./data:/app/data
    environment:
      # 数据库配置
      - DATABASE_URL=postgresql://user:pass@db:5432/ansible_web_ui
      # 或使用 SQLite（开发环境）
      # - DATABASE_URL=sqlite:///./data/ansible_web_ui.db
      
      # 文件大小限制（可选，默认 10MB）
      - MAX_FILE_SIZE_MB=10
      
      # 数据库连接池配置（可选）
      - DB_POOL_SIZE=20
      - DB_MAX_OVERFLOW=40
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=ansible_web_ui
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - web

volumes:
  postgres_data:
```

#### 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

#### 部署优势

- ✅ **简单**: 只需持久化数据库卷
- ✅ **可靠**: 数据完全在数据库中
- ✅ **无状态**: Web 容器可以随意重启
- ✅ **易扩展**: 支持多个 Web 容器实例

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/ansible_web_ui.db` |
| `MAX_FILE_SIZE_MB` | 单文件最大大小（MB） | `10` |
| `DB_POOL_SIZE` | 数据库连接池大小 | `20` |
| `DB_MAX_OVERFLOW` | 连接池最大溢出连接数 | `40` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379` |

## 💾 数据库备份

### PostgreSQL 备份

```bash
# 备份数据库
docker-compose exec db pg_dump -U user ansible_web_ui > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose exec -T db psql -U user ansible_web_ui < backup_20251023_100000.sql

# 定期备份（添加到 crontab）
0 2 * * * docker-compose exec db pg_dump -U user ansible_web_ui > /backups/ansible_$(date +\%Y\%m\%d).sql
```

### SQLite 备份

```bash
# 备份数据库文件
cp data/ansible_web_ui.db data/backups/ansible_web_ui_$(date +%Y%m%d_%H%M%S).db

# 恢复数据库
cp data/backups/ansible_web_ui_20251023_100000.db data/ansible_web_ui.db

# 定期备份（添加到 crontab）
0 2 * * * cp data/ansible_web_ui.db data/backups/ansible_$(date +\%Y\%m\%d).db
```

### 备份建议

- 📅 **定期备份**: 每天至少备份一次
- 🔒 **异地存储**: 将备份文件存储到远程位置
- 🔄 **备份轮转**: 保留最近 7 天的每日备份，最近 4 周的每周备份
- ✅ **验证备份**: 定期测试备份恢复流程
- 📊 **监控大小**: 监控数据库大小增长趋势

## ⚡ 性能优化

### 数据库优化

#### PostgreSQL 配置

```ini
# postgresql.conf
shared_buffers = 256MB          # 共享缓冲区
effective_cache_size = 1GB      # 有效缓存大小
work_mem = 16MB                 # 工作内存
maintenance_work_mem = 64MB     # 维护工作内存
max_connections = 100           # 最大连接数
```

#### 索引优化

系统已自动创建以下索引：

```sql
-- 项目文件索引
CREATE UNIQUE INDEX idx_project_path ON project_files(project_id, relative_path);
CREATE INDEX idx_project_id ON project_files(project_id);
CREATE INDEX idx_relative_path ON project_files(relative_path);

-- Playbook 索引
CREATE INDEX idx_playbook_filename ON playbooks(filename);
CREATE INDEX idx_playbook_created_at ON playbooks(created_at);
```

#### 连接池配置

```python
# 推荐配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 基础连接池大小
    max_overflow=40,       # 最大溢出连接
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600      # 连接回收时间（1小时）
)
```

### 应用层优化

- ✅ **异步 I/O**: 所有数据库操作使用 async/await
- ✅ **批量操作**: 使用批量插入减少数据库往返
- ✅ **单次查询**: 文件树构建使用单次查询
- ✅ **事务管理**: 批量操作使用事务确保原子性

### 性能指标

| 操作 | 响应时间 P95 | 并发支持 |
|------|-------------|---------|
| 读取文件 | < 50ms | 50+ |
| 写入文件 | < 100ms | 30+ |
| 文件树构建 | < 200ms | 20+ |
| 批量创建 | < 500ms | 10+ |

### 监控建议

- 📊 **数据库性能**: 监控查询执行时间和慢查询
- 🔍 **连接池使用**: 监控连接池使用率
- 💾 **数据库大小**: 监控数据库大小增长
- ⚠️ **错误率**: 监控 4xx 和 5xx 错误率
- 🚀 **响应时间**: 监控 API 响应时间 P50/P95/P99

## 📚 文档

- [API 文档](docs/api-documentation.md) - RESTful API 接口说明（包含项目文件管理 API）
- [存储架构文档](docs/playbook-storage-architecture.md) - Playbook 存储架构设计
- [性能文档](docs/playbook-performance.md) - 性能特征和优化措施
- [性能对比报告](docs/playbook-performance-comparison.md) - 性能测试结果

## 🎯 核心特性

### Playbook 管理
- ✅ **数据库存储**: 所有内容存储在数据库中，无需文件系统
- ✅ **实时同步**: 修改立即对所有用户可见，无缓存不一致
- ✅ **高性能**: 读取响应时间 < 3ms，创建/更新 < 10ms
- ✅ **YAML 验证**: 自动验证 Playbook 语法和结构
- ✅ **版本追踪**: 通过文件哈希追踪内容变更

### 项目文件管理
- ✅ **纯数据库存储**: 项目文件内容存储在数据库中
- ✅ **文件树构建**: 通过路径前缀匹配高效构建目录树
- ✅ **批量操作**: 支持批量创建、移动、删除文件
- ✅ **路径安全**: 防止路径遍历攻击，确保安全性
- ✅ **UTF-8 编码**: 统一使用 UTF-8，支持多语言内容
- ✅ **文件大小限制**: 单文件最大 10MB（可配置）
- ✅ **事务支持**: 批量操作使用事务，确保数据一致性

### 架构优势
- 🎯 **简洁架构**: 纯数据库存储，代码简化 70%
- 🔒 **数据一致性**: 单一数据源，避免缓存同步问题
- 🚀 **易于部署**: 无状态服务，完美支持容器化
- 📊 **易于维护**: 减少故障点，降低维护成本
- 🐳 **Docker 友好**: 只需持久化数据库卷，无需挂载文件系统

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！
