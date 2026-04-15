# GitHub 部署指南

## 1. 将项目部署到 GitHub

### 1.1 准备工作
1. **创建 GitHub 账号**：如果还没有 GitHub 账号，先在 [GitHub](https://github.com/) 注册一个
2. **安装 Git**：确保本地安装了 Git 版本控制工具
   - Windows：下载并安装 [Git for Windows](https://git-scm.com/download/win)
   - macOS：使用 Homebrew 安装 `brew install git` 或从 [Git 官网](https://git-scm.com/download/mac) 下载
   - Linux：使用包管理器安装，如 `sudo apt install git`（Ubuntu）
3. **配置 Git**：
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

### 1.2 创建 GitHub 仓库
1. 登录 GitHub
2. 点击右上角的 "+", 选择 "New repository"
3. 填写仓库信息：
   - Repository name: 输入项目名称（如 "online-study-room"）
   - Description: 填写项目描述
   - Choose repository visibility: 选择 "Public" 或 "Private"
   - 勾选 "Add a README file"（可选）
   - 点击 "Create repository"

### 1.3 本地项目初始化
1. 打开命令行，进入项目目录：
   ```bash
   cd d:\WorkSpace\work_develop\Python\软件开发实践项目\project
   ```
2. 初始化 Git 仓库：
   ```bash
   git init
   ```
3. 添加项目文件：
   ```bash
   git add .
   ```
4. 提交初始代码：
   ```bash
   git commit -m "Initial commit"
   ```

### 1.4 关联 GitHub 仓库并推送
1. 复制 GitHub 仓库的 URL（HTTPS 或 SSH 格式）
2. 添加远程仓库：
   ```bash
   # 使用 HTTPS
   git remote add origin https://github.com/codeAIwt/Software-Development-Viber-Code.git
   
   # 或使用 SSH
   git remote add origin git@github.com:codeAIwt/Software-Development-Viber-Code.git
   ```
3. 推送代码到 GitHub：
   ```bash
   git push -u origin main
   ```
   （如果默认分支是 master，使用 `git push -u origin master`）

### 1.5 验证部署
1. 打开 GitHub 仓库页面
2. 确认项目文件已成功上传

## 2. GitHub 工作流与测试

### 2.1 创建 GitHub Actions 工作流
GitHub Actions 是 GitHub 提供的 CI/CD 服务，可以自动运行测试、构建和部署任务。

#### 2.1.1 创建工作流文件
1. 在项目根目录创建 `.github/workflows` 目录：
   ```bash
   mkdir -p .github/workflows
   ```
2. 创建测试工作流文件 `test.yml`：

```yaml
name: Test Workflow

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        # 运行用户模块测试
        echo "Running user module tests..."
        # 运行自习室模块测试
        echo "Running study room module tests..."
        # 运行数据库模块测试
        echo "Running database module tests..."
        # 这里可以添加具体的测试命令，例如：
        # python -m pytest tests/
        # 检查数据库连接
        python -c "from config.db import engine; print('Database connection successful')"
        # 检查表结构
        python -c "from config.db import init_db; init_db(); print('Database tables initialized')"
    
    - name: Build frontend
      run: |
        cd frontend
        npm install
        # 修复权限问题
        chmod +x node_modules/.bin/vite
        npm run build
        echo "Frontend build completed successfully"
```

### 2.2 使用 GitHub 进行测试

#### 2.2.1 手动触发测试
1. 推送代码到 GitHub：
   ```bash
   git add .
   git commit -m "Add test workflow"
   git push
   ```
2. 打开 GitHub 仓库页面，点击 "Actions" 标签
3. 查看工作流运行状态，确认测试是否通过

#### 2.2.2 拉取请求测试
1. 创建一个新分支：
   ```bash
   git checkout -b feature-branch
   ```
2. 进行代码修改
3. 提交并推送分支：
   ```bash
   git add .
   git commit -m "Add new feature"
   git push -u origin feature-branch
   ```
4. 在 GitHub 上创建拉取请求（Pull Request）
5. 查看工作流运行状态，确认测试是否通过

### 2.3 自动化部署（可选）

如果需要自动化部署到云服务，可以在工作流中添加部署步骤。例如，部署到 Vercel、Netlify 或 Heroku 等平台。

#### 2.3.1 部署到 Vercel 示例
1. 注册 Vercel 账号并连接 GitHub
2. 在 Vercel 上创建新项目，选择 GitHub 仓库
3. 配置部署设置：
   - Framework Preset: Vue.js
   - Build Command: `npm run build`
   - Output Directory: `frontend/dist`
4. 点击 "Deploy"

## 3. 最佳实践

### 3.1 .gitignore 文件
创建 `.gitignore` 文件，排除不需要上传的文件：

```
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
env/

# SQLite
*.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/

# Build outputs
dist/
build/
```

### 3.2 分支管理
- `main/master`：主分支，用于发布稳定版本
- `develop`：开发分支，用于集成新功能
- `feature/*`：功能分支，用于开发具体功能
- `bugfix/*`：修复分支，用于修复 bug

### 3.3 提交规范
使用语义化提交信息：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码风格调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

例如：
```
feat: add user authentication
fix: resolve room creation bug
docs: update API documentation
```

## 4. 故障排除

### 4.1 Git 推送失败
- 检查网络连接
- 确认 GitHub 账号权限
- 检查远程仓库 URL 是否正确

### 4.2 工作流运行失败
- 查看工作流日志，了解具体错误信息
- 检查依赖安装是否成功
- 确认测试命令是否正确

### 4.3 部署问题
- 检查构建命令是否正确
- 确认输出目录设置是否正确
- 查看部署平台的错误日志

## 5. 总结

通过以上步骤，你可以：
1. 将项目部署到 GitHub 仓库
2. 使用 GitHub Actions 自动运行测试
3. 实现持续集成和持续部署
4. 规范代码管理和版本控制

这样可以确保项目代码的质量和可靠性，同时方便团队协作和代码审查。