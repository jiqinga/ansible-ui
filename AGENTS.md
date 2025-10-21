# Python环境配置规则

## 虚拟环境管理

### 环境路径配置
- Python解释器路径：`.\.venv\Scripts\python.exe`
- 激活脚本路径：`.\.venv\Scripts\activate`
- 包管理器：uv

### 常用命令模板

#### 基础Python命令
```bash
# 运行Python脚本
.\.venv\Scripts\python.exe your_script.py

# 进入Python交互模式
.\.venv\Scripts\python.exe

# 查看Python版本
.\.venv\Scripts\python.exe --version
```

#### UV包管理命令
```bash
# 添加新依赖
uv add package_name

# 添加开发依赖
uv add --dev package_name

# 移除依赖
uv remove package_name

# 安装所有依赖
uv sync

# 更新依赖
uv lock --upgrade

# 查看已安装包
uv pip list
```

#### 虚拟环境操作
```bash
# 激活虚拟环境
.\.venv\Scripts\activate

# 停用虚拟环境
deactivate

# 重新创建虚拟环境（如果需要）
uv venv --python 3.12
```

## 项目依赖管理

### pyproject.toml配置
- 所有项目依赖都应在pyproject.toml中声明
- 区分生产依赖和开发依赖
- 指定Python版本要求
- 配置项目元数据

### 依赖安装流程
1. 首先确保uv已安装
2. 使用`uv sync`安装所有依赖
3. 激活虚拟环境
4. 验证环境配置正确

## 开发工作流

### 环境检查清单
- [ ] 虚拟环境已激活
- [ ] 使用正确的Python解释器路径
- [ ] 所有依赖已通过uv安装
- [ ] pyproject.toml配置正确

### 故障排除
- 如果遇到包导入问题，检查虚拟环境是否正确激活
- 如果命令找不到，确认使用完整的解释器路径
- 如果依赖冲突，使用`uv lock --upgrade`更新锁文件

# 参考文档在.kiro目录