<<<<<<< HEAD
# 线上伴学系统

## 项目简介
线上伴学系统是一个基于 Vue + Python + Redis 的在线自习室平台，支持用户创建和加入自习室，记录学习时长，提供实时伴学功能。

## 技术栈
- 前端：Vue 3 + Vite
- 后端：Python 3.12 + FastAPI
- 缓存：Redis
- 数据库：SQLite（默认）/ MySQL
- 认证：JWT

## 核心功能

### 1. 用户系统
- 注册、登录、退出登录
- 个人信息管理
- 用户标签选择和管理（首次登录显示标签选择弹窗，可跳过）

### 2. 自习室管理
- 创建自习室（支持选择主题、人数上限和标签，最多3个标签）
- 列出空闲自习室（支持主题/标签筛选）
- 加入自习室
- 离开自习室
- 记录用户加入和离开时间
- 计算学习时长
- 房间创建者权限：修改房间主题、销毁房间（会强制所有成员退出）

### 3. 学习时长统计
- 记录用户在自习室中的学习时长
- 支持查看个人学习数据

## 项目结构

### 后端结构
```
backend/
├── app.py              # 应用入口
├── controllers/        # 控制器
│   ├── room_controller.py   # 房间相关接口
│   ├── user_controller.py   # 用户相关接口
│   └── duration_controller.py # 学习时长相关接口
├── services/           # 业务逻辑
│   ├── room_service.py      # 房间服务
│   └── user_service.py      # 用户服务
├── models/             # 数据模型
│   ├── user.py              # 用户模型
│   ├── study_room.py        # 自习室模型
│   ├── room_user.py         # 自习室成员模型
│   └── study_duration.py    # 学习时长模型
├── utils/              # 工具函数
│   ├── auth.py              # 认证相关
│   └── cache.py             # Redis缓存操作
└── config/             # 配置
    ├── db.py                # 数据库配置
    └── settings.py          # 应用配置
```

### 前端结构
```
frontend/
├── src/
│   ├── api/            # API调用
│   │   ├── studyRoom.js     # 自习室相关API
│   │   ├── user.js          # 用户相关API
│   │   └── duration.js      # 学习时长相关API
│   ├── components/     # 组件
│   │   ├── StudyRoomList.vue # 自习室列表组件
│   │   └── CommonToast.vue   # 通用提示组件
│   ├── views/          # 页面
│   │   ├── StudyRoom.vue     # 自习室页面
│   │   ├── StudyRoomDetail.vue # 自习室详情页面
│   │   ├── Home.vue          # 首页
│   │   ├── Login.vue         # 登录页面
│   │   ├── Register.vue      # 注册页面
│   │   ├── Personal.vue      # 个人中心页面
│   │   └── Tags.vue          # 标签选择页面
│   └── router/         # 路由
└── dist/               # 构建输出
```

## 接口说明

### 房间相关接口
- `POST /api/room/create` - 创建自习室
- `GET /api/room/list` - 列出自习室
- `POST /api/room/join` - 加入自习室
- `POST /api/room/leave` - 离开自习室
- `GET /api/room/info/{room_id}` - 获取房间信息
- `PUT /api/room/update/{room_id}` - 更新房间信息
- `DELETE /api/room/destroy/{room_id}` - 销毁房间

### 用户相关接口
- `POST /api/user/register` - 注册
- `POST /api/user/login` - 登录
- `GET /api/user/profile` - 获取用户信息
- `PUT /api/user/profile/nickname` - 更新昵称
- `PUT /api/user/profile/tags` - 更新标签

### 学习时长相关接口
- `GET /api/duration/info` - 获取学习时长信息

## 快速开始

### 后端
1. 安装依赖
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. 启动服务
   ```bash
   uvicorn app:app --reload
   ```

### 前端
1. 安装依赖
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器
   ```bash
   npm run dev
   ```

3. 构建生产版本
   ```bash
   npm run build
   ```

## 注意事项
- 本项目使用 Redis 模拟房间状态，实际部署时需要确保 Redis 服务正常运行
-## 数据库功能已接入，默认使用 SQLite，可配置为 MySQL

### 数据库连接信息（开发环境）
- **主机地址**：127.0.0.1（本地连接）/ 数据库服务器 IP（远程连接）
- **端口**：3306
- **数据库名**：SoftwareProject
- **字符集**：utf8mb4（支持表情及全部中文）
- **连接用户名**：UserSoft
- **连接密码**：SoftP0987
- **本地连接 URL**：mysql+pymysql://UserSoft:SoftP0987@127.0.0.1:3306/SoftwareProject?charset=utf8mb4
- **远程连接 URL**：mysql+pymysql://UserSoft:SoftP0987@<数据库服务器IP>:3306/SoftwareProject?charset=utf8mb4

### 账号权限说明
账号 UserSoft 已授予项目开发所需的最小可用权限：
- 对 SoftwareProject 库下所有表：查询 SELECT、新增 INSERT、更新 UPDATE、删除 DELETE、建表/修改表 CREATE, ALTER, DROP、索引管理 INDEX
- 已配置为允许从任何主机（%）连接，支持远程访问

### 远程访问数据库步骤

#### 1. 服务器端配置（数据库所在主机）
1. **确保 MySQL 服务已启动**：
   ```bash
   # Windows
   net start mysql
   
   # Linux
   systemctl start mysql
   ```

2. **配置 MySQL 允许远程连接**：
   - 编辑 MySQL 配置文件（my.cnf 或 my.ini）
   - 找到 `bind-address` 配置项，修改为：
     ```
     bind-address = 0.0.0.0
     ```
   - 重启 MySQL 服务：
     ```bash
     # Windows
     net restart mysql
     
     # Linux
     systemctl restart mysql
     ```

3. **配置防火墙**：
   - 确保防火墙允许 3306 端口的入站连接
   - Windows 防火墙：
     ```
     控制面板 -> 系统和安全 -> Windows Defender 防火墙 -> 高级设置 -> 入站规则 -> 新建规则
     选择端口 -> TCP -> 特定本地端口 -> 3306 -> 允许连接
     ```
   - Linux 防火墙：
     ```bash
     # CentOS/RHEL
     firewall-cmd --add-port=3306/tcp --permanent
     firewall-cmd --reload
     
     # Ubuntu/Debian
     ufw allow 3306/tcp
     ```

#### 2. 客户端连接（成员电脑）
1. **获取数据库服务器 IP 地址**：
   - 在数据库服务器上执行：
     ```bash
     # Windows
     ipconfig
     
     # Linux
     ifconfig
     ```
   - 找到服务器的局域网 IP 地址（如 192.168.1.100）

2. **修改项目配置**：
   - 在 `backend` 目录下创建 `.env` 文件（如果不存在）
   - 添加以下内容：
     ```
     DATABASE_URL=mysql+pymysql://UserSoft:SoftP0987@<数据库服务器IP>:3306/SoftwareProject?charset=utf8mb4
     ```
   - 将 `<数据库服务器IP>` 替换为实际的服务器 IP 地址

3. **测试连接**：
   - 启动后端服务：
     ```bash
     uvicorn app:app --reload
     ```
   - 检查控制台输出，确保数据库连接成功

### 使用默认 SQLite 数据库的步骤

如果无法访问 MySQL 数据库，可以使用默认的 SQLite 数据库作为备选方案。SQLite 是一个文件型数据库，不需要单独安装数据库服务，直接运行即可。

#### 1. 修改数据库配置

**方法一：修改 settings.py 文件**
1. 打开文件：`backend/config/settings.py`
2. 找到以下配置行：
   ```python
   # MySQL 连接字符串
   database_url: str = "mysql+pymysql://UserSoft:SoftP0987@127.0.0.1:3306/SoftwareProject?charset=utf8mb4"
   ```
3. 修改为：
   ```python
   # SQLite 连接字符串
   database_url: str = "sqlite:///./online_study.db"
   ```

**方法二：创建 .env 文件**
1. 在 `backend` 目录下创建 `.env` 文件（如果不存在）
2. 添加以下内容：
   ```
   DATABASE_URL=sqlite:///./online_study.db
   ```
   （注意：如果已经存在 .env 文件，只需要修改 DATABASE_URL 这一行）

#### 2. 启动服务
1. 确保后端依赖已安装：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. 启动后端服务：
   ```bash
   uvicorn app:app --reload
   ```
3. 服务启动时会自动创建 SQLite 数据库文件 `online_study.db` 并初始化表结构

#### 3. 验证连接
- 启动服务后，查看控制台输出，确认没有数据库连接错误
- 数据库文件会生成在 `backend` 目录下，名为 `online_study.db`
- 可以使用 SQLite 工具（如 DB Browser for SQLite）查看数据库内容

#### 4. 注意事项
- SQLite 适用于开发和测试环境，不建议用于生产环境
- SQLite 文件会随着数据量的增加而增大，注意定期清理
- 如果需要切换回 MySQL，只需按照前面的步骤修改数据库配置即可

### 使用注意事项
- 开发前请确保数据库服务器已启动且可访问
- 首次使用请先执行项目初始化 SQL 脚本建表
- 禁止直接在开发库执行危险操作（如 DROP DATABASE）
- 表结构变更统一通过脚本管理，不允许手动随意修改
- 远程连接时，请确保网络环境安全，避免在公共网络中传输敏感信息
- 匹配功能、WebSocket 功能暂未实现
- 摄像机功能已基本实现，支持摄像头的启动、显示和停止，但隐私模式（背景模糊、仅手部模式）尚未实现

## 环境要求

- **Python**：建议 3.10 及以上（与概要设计中 Python 3.12 系 toolchain 兼容）
- **Node.js**：建议 18 LTS 及以上（用于前端）
- 可选：本机 **MySQL / Redis**；默认配置下后端使用 **SQLite** + **fakeredis**，无需单独安装数据库即可本地演示
- 数据库表结构已自动创建，启动服务时会自动初始化

## 后端（Python venv）

在 **`project/backend`** 下使用虚拟环境隔离依赖。

### 1. 创建虚拟环境

**Windows（PowerShell）**，在 `backend` 目录执行：

```powershell
cd backend
python -m venv .venv
```

**Windows（命令提示符 cmd）**：

```bat
cd backend
python -m venv .venv
```

**Linux / macOS**：

```bash
cd backend
python3 -m venv .venv
```

### 2. 激活虚拟环境

**Windows（PowerShell）**：

```powershell
.\.venv\Scripts\Activate.ps1
```

若提示禁止运行脚本，可先执行（当前用户）：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows（cmd）**：

```bat
.venv\Scripts\activate.bat
```

**Linux / macOS**：

```bash
source .venv/bin/activate
```

激活成功后，命令行前一般会出现 `(.venv)` 前缀。

### 3. 安装依赖并启动 API

仍须在 **`backend`** 目录、且 venv 已激活：

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

默认会在本机 **http://127.0.0.1:8000** 提供接口（如 `/api/user/login`）。  
关闭终端或执行 `deactivate` 可退出虚拟环境。

### 4. 可选配置（环境变量 / `.env`）

在 `backend` 目录可放置 `.env`（或通过系统环境变量）覆盖配置中的项，例如：

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | 数据库连接串；默认 `sqlite:///./online_study.db`（文件在 `backend` 当前工作目录下生成），开发环境建议使用：`mysql+pymysql://UserSoft:SoftP0987@127.0.0.1:3306/SoftwareProject?charset=utf8mb4` |
| `redis_url` | 填 `fakeredis` 表示内存模拟 Redis；生产可改为 `redis://127.0.0.1:6379/0` |
| `JWT_SECRET` | JWT 签名密钥，部署前务必修改为强随机字符串 |

## 前端（Vue + Vite）

在 **`project/frontend`** 目录：

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认 **http://127.0.0.1:5173**，同时也可以通过私网地址访问（例如 **http://192.168.1.100:5173**）。  
Vite 已将前缀 **`/api`** 代理到 **http://127.0.0.1:8000**，请先按上一节启动后端，再打开浏览器访问前端页面。

**注意**：由于现代浏览器的安全策略，摄像头访问需要在安全上下文（HTTPS）中进行，或者在本地地址（localhost或127.0.0.1）中进行。如果使用私网地址访问，浏览器可能会阻止摄像头访问。此时，您可以：
1. 使用 **http://localhost:5173** 或 **http://127.0.0.1:5173** 访问
2. 或者在浏览器中为该私网地址启用摄像头访问权限（具体方法因浏览器而异）

生产构建：

```bash
npm run build
```

产物在 `frontend/dist`，需由静态服务器或网关反代，并将 API 指向实际后端地址。

## 文档与 PRD 路径

- 仓库内完整设计见上级目录 `详细设计/`、`产品需求文档/`、`产品概要设计文档/`

## 常见问题

1. **`pip` 找不到**  
   请确认已用 `python -m venv .venv` 创建环境，并在激活 venv 后使用 `python -m pip install -r requirements.txt`。

2. **前端接口报网络错误**  
   确认后端已启动且监听 `8000`，并与 `frontend/vite.config.js` 中的 `proxy` 目标一致。

3. **更换本机 Redis / MySQL**  
   修改 `backend` 的 `.env` 中 `redis_url`、`DATABASE_URL` 后，重新启动 `uvicorn`。

## 阶段性测试

- [第一阶段测试预期](./预期成果文件1阶段.md)（MVP 用户模块）
- [第二阶段测试预期](./预期成果文件2阶段.md)（MVP 自习室模块）
- [第三阶段测试预期](./预期成果文件3阶段.md)（数据库模块）
=======
# Software-Development-Viber-Code
>>>>>>> 95890c42f17cb7d89ff332969ffdc35ee5c6731a
