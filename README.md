# 线上伴学系统

## 项目简介

线上伴学系统是一个基于 Vue 3 + FastAPI + Redis 的在线自习室平台，支持用户创建和加入自习室，记录学习时长，并提供基于 OpenCV 的前置摄像头 AI 伴学监控与 WebSocket 实时状态广播功能。

## 技术栈

- 前端：Vue 3 + Vite + Pinia
- 后端：Python 3.12 + FastAPI
- AI 识别：OpenCV (Haar Cascade)
- 实时通信：WebSocket
- 缓存：Redis（默认使用 fakeredis 模拟）
- 数据库：SQLite（默认）/ MySQL
- 认证：JWT

## 核心功能

### 1. 用户系统

- 注册、登录、退出登录
- 个人信息管理（昵称、头像、标签）
- 用户标签选择和管理（首次登录显示标签选择弹窗，可跳过）
- 每日打卡功能

### 2. 自习室管理

- 创建自习室（支持选择主题、人数上限和标签，最多3个标签）
- 列出空闲自习室（支持主题筛选）
- 加入自习室/离开自习室
- 记录用户加入和离开时间，计算学习时长
- 房间创建者权限：修改房间主题、销毁房间（强制所有成员退出）
- **基于 WebSocket 的操作广播及更新（如用户加入、离开）**
- **基于 OpenCV Haar 级联模型的前置摄像头实时在坐校验检测机制**

### 3. 学习时长统计

- 记录用户在自习室中的学习时长
- 支持查看个人学习数据（日/周/月）
- 学习时长排行榜（日榜、周榜、月榜）
- 击败百分比统计

### 4. 收藏夹功能

- 添加学习资源收藏（标题、URL、标签）
- 按标签筛选收藏
- 更新/删除收藏及标签

## 项目结构

### 后端结构

```
backend/
├── app.py                      # 应用入口，FastAPI 应用创建
├── requirements.txt            # Python 依赖
├── config/                     # 配置模块
│   ├── __init__.py
│   ├── db.py                   # 数据库配置与初始化
│   ├── settings.py             # 应用配置（JWT、Redis 等）
│   └── ws.py                   # WebSocket 配置
├── controllers/                # 控制器层（API 路由）
│   ├── __init__.py
│   ├── user_controller.py      # 用户相关接口
│   ├── room_controller.py      # 自习室相关接口
│   ├── duration_controller.py   # 学习时长相关接口
│   └── bookmark_controller.py   # 收藏夹相关接口
├── services/                   # 业务逻辑层
│   ├── __init__.py
│   ├── user_service.py         # 用户业务逻辑
│   ├── room_service.py         # 自习室业务逻辑
│   ├── duration_service.py      # 学习时长业务逻辑
│   ├── bookmark_service.py      # 收藏夹业务逻辑
│   ├── check_in_service.py      # 打卡业务逻辑
│   └── ai_service.py           # AI 检测服务（OpenCV）
├── models/                     # 数据模型层
│   ├── __init__.py
│   ├── user.py                 # 用户模型
│   ├── study_room.py           # 自习室模型
│   ├── room_user.py            # 自习室成员模型
│   ├── study_duration.py      # 学习时长模型
│   ├── bookmark.py             # 收藏夹模型
│   └── check_in.py             # 打卡记录模型
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── auth.py                 # JWT 认证与权限验证
│   ├── cache.py                # Redis 缓存操作封装
│   └── ws_client.py            # WebSocket 客户端管理
├── ws/                         # WebSocket 服务
│   ├── __init__.py
│   └── server.py               # WebSocket 消息广播逻辑
└── schedule/                   # 定时任务
    ├── __init__.py
    └── duration_schedule.py    # 学习时长定时记录
```

### 前端结构

```
frontend/
├── package.json                # 前端依赖配置
├── vite.config.js             # Vite 构建配置
├── src/
│   ├── main.js                # 应用入口
│   ├── App.vue                # 根组件
│   ├── api/                   # API 调用层
│   │   ├── client.js          # Axios 实例配置
│   │   ├── user.js            # 用户相关 API
│   │   ├── studyRoom.js       # 自习室相关 API
│   │   ├── duration.js        # 学习时长相关 API
│   │   └── bookmark.js        # 收藏夹相关 API
│   ├── components/            # 公共组件
│   │   ├── CommonToast.vue     # 通用提示组件
│   │   ├── PrivacyMode.vue     # 隐私模式切换组件
│   │   ├── StudyRoomList.vue   # 自习室列表组件
│   │   ├── BookmarkPanel.vue   # 收藏夹面板组件
│   │   ├── CheckInCard.vue     # 打卡卡片组件
│   │   └── EditAvatar.vue      # 头像编辑组件
│   ├── views/                 # 页面视图
│   │   ├── Login.vue           # 登录页面
│   │   ├── Register.vue        # 注册页面
│   │   ├── Home.vue            # 首页
│   │   ├── Personal.vue        # 个人中心页面
│   │   ├── Tags.vue            # 标签选择页面
│   │   ├── StudyRoom.vue       # 自习室列表页面
│   │   ├── StudyRoomDetail.vue  # 自习室详情页面
│   │   └── Rank.vue            # 排行榜页面
│   ├── composables/           # 组合式函数（逻辑复用）
│   │   ├── useCamera.js        # 摄像头管理
│   │   ├── useWebSocket.js     # WebSocket 连接管理
│   │   ├── useWebRTC.js        # WebRTC 视频通信
│   │   ├── useRoomData.js      # 房间数据轮询与状态管理
│   │   ├── useAiDetection.js   # AI 检测逻辑封装
│   │   └── useRoomSignaling.js # 房间信令通信管理
│   ├── router/                # 路由配置
│   │   └── index.js
│   ├── store/                 # Pinia 状态管理
│   │   └── index.js
│   └── utils/                 # 工具函数
│       ├── auth.js            # 认证工具
│       ├── video.js           # 视频处理工具
│       └── calc.js            # 计算工具
└── dist/                      # 构建输出目录
```

## API 接口详解

### 用户相关接口 `/api/user`

| 方法   | 路径                           | 说明                   |
|--------|--------------------------------|------------------------|
| POST   | /api/user/register             | 用户注册               |
| POST   | /api/user/login                | 用户登录               |
| POST   | /api/user/logout               | 用户退出登录           |
| GET    | /api/user/profile              | 获取用户个人信息       |
| PUT    | /api/user/profile/nickname     | 更新昵称               |
| PUT    | /api/user/profile/tags         | 更新标签               |
| PUT    | /api/user/profile/avatar       | 更新头像               |
| GET    | /api/user/tags                 | 获取系统标签列表       |
| GET    | /api/user/info/{user_id}       | 获取指定用户信息       |
| POST   | /api/user/check-in             | 用户每日打卡           |
| GET    | /api/user/check-in/status      | 获取打卡状态           |

### 自习室相关接口 `/api/room`

| 方法   | 路径                           | 说明                   |
|--------|--------------------------------|------------------------|
| POST   | /api/room/create               | 创建自习室             |
| GET    | /api/room/list                 | 列出空闲自习室         |
| POST   | /api/room/join                 | 加入自习室             |
| POST   | /api/room/leave                | 离开自习室             |
| GET    | /api/room/info/{room_id}       | 获取房间信息           |
| PUT    | /api/room/update/{room_id}     | 更新房间信息           |
| DELETE | /api/room/destroy/{room_id}   | 销毁房间               |
| POST   | /api/room/detect-person        | AI 人脸检测            |

### 学习时长相关接口 `/api/duration`

| 方法   | 路径                           | 说明                   |
|--------|--------------------------------|------------------------|
| GET    | /api/duration/daily            | 获取每日学习时长       |
| GET    | /api/duration/weekly           | 获取近7天学习时长      |
| GET    | /api/duration/rank             | 获取学习时长排行榜     |
| GET    | /api/duration/rank/weekly      | 获取周排行榜           |
| GET    | /api/duration/rank/monthly     | 获取月排行榜           |
| GET    | /api/duration/period/summary   | 获取时间段学习时长汇总 |

### 收藏夹相关接口 `/api/bookmark`

| 方法   | 路径                           | 说明                   |
|--------|--------------------------------|------------------------|
| POST   | /api/bookmark                  | 创建收藏               |
| GET    | /api/bookmark                  | 获取收藏列表           |
| GET    | /api/bookmark/tags             | 获取所有标签           |
| PUT    | /api/bookmark/{id}/tags        | 更新收藏标签           |
| DELETE | /api/bookmark/{id}             | 删除收藏               |
| DELETE | /api/bookmark/tag/{tag}        | 删除标签               |

### WebSocket 接口

| 路径                              | 说明                         |
|-----------------------------------|------------------------------|
| ws://host/ws/room/{room_id}       | 房间实时通信连接             |

**查询参数：**
- `user_id`: 用户 ID

**消息类型：**
- `user_join`: 用户加入房间
- `user_leave`: 用户离开房间
- `offer/answer/ice_candidate`: WebRTC 信令消息

## 数据库模型

### User 用户表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | String(32)| 主键，用户ID           |
| phone         | String(64)| 手机号（唯一）         |
| password      | String(64)| 密码哈希               |
| nickname      | String(20)| 昵称                   |
| avatar        | String(255)| 头像URL               |
| registertime  | DateTime  | 注册时间                |
| lastlogintime | DateTime  | 最后登录时间            |
| tags          | String(255)| 用户标签               |
| is_first_login| Boolean   | 是否首次登录           |

### StudyRoom 自习室表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | String(32)| 主键，房间ID           |
| theme         | String(20)| 主题                   |
| max_people    | Integer   | 最大人数               |
| current_people| Integer   | 当前人数               |
| status        | String(10)| 状态（idle/active）    |
| creator_id    | String(32)| 创建者ID               |
| create_time   | DateTime  | 创建时间                |
| tags          | String(255)| 标签                   |

### RoomUser 自习室成员表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | Integer   | 主键                   |
| room_id       | String(32)| 房间ID                 |
| user_id       | String(32)| 用户ID                 |
| join_time     | DateTime  | 加入时间                |
| leave_time    | DateTime  | 离开时间                |
| privacy_mode  | String(10)| 隐私模式（blur/none）  |
| camera        | Integer   | 摄像头状态             |

### StudyDuration 学习时长表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | Integer   | 主键                   |
| user_id       | String(32)| 用户ID                 |
| study_date    | Date      | 学习日期               |
| total_minutes | Integer   | 总分钟数               |
| beat_percent  | Numeric   | 击败百分比             |
| create_time   | DateTime  | 创建时间                |

### Bookmark 收藏夹表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | Integer   | 主键                   |
| user_id       | String(32)| 用户ID                 |
| title         | String(200)| 标题                  |
| url           | Text      | URL地址                |
| tags          | String(255)| 标签                   |
| created_time  | DateTime  | 创建时间                |

### CheckIn 打卡记录表
| 字段          | 类型      | 说明                    |
|---------------|-----------|------------------------|
| id            | Integer   | 主键                   |
| user_id       | String(32)| 用户ID                 |
| check_in_date| Date      | 打卡日期               |
| create_time   | DateTime  | 创建时间                |

## 项目状态

✅ **项目已完成** - 所有核心功能均已实现并通过测试

### 功能完成情况

- ✅ 用户系统（注册、登录、个人信息管理、每日打卡）
- ✅ 自习室管理（创建、加入、离开、权限控制）
- ✅ 学习时长统计（自动记录、日/周/月排行榜、击败百分比）
- ✅ AI 伴学监控（摄像头访问、人脸检测）
- ✅ 实时通信（WebSocket 状态同步、WebRTC 信令转发）
- ✅ 收藏夹功能（添加、筛选、更新、删除）
- ✅ 数据库支持（MySQL/SQLite 双数据库支持）
- ✅ CI/CD 自动化测试（GitHub Actions）

## 快速开始

### 后端

1. 创建虚拟环境并安装依赖

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
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

## 环境变量配置

| 变量           | 说明                                                    |
| -------------- | -------------------------------------------------------|
| DATABASE_URL   | 数据库连接串，默认 `sqlite:///./online_study.db`       |
| redis_url      | Redis 连接串，默认 `fakeredis`（内存模拟）              |
| JWT_SECRET     | JWT 签名密钥                                            |

## 局域网运行配置

### 1. 修改前端配置

编辑 `frontend/vite.config.js` 文件：

```javascript
export default defineConfig({
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: "http://[局域网IP]:8000", changeOrigin: true },
      "/ws": { target: "ws://[局域网IP]:8000", ws: true }
    }
  }
});
```

### 2. 启动后端服务

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. 摄像头功能注意事项

由于浏览器安全策略限制，摄像头功能需要在 HTTPS 环境或 localhost 下才能正常工作。

## 技术架构详解

### 后端架构

- **框架**：FastAPI - 高性能异步 Web 框架
- **数据库**：SQLAlchemy ORM，支持 MySQL/SQLite
- **缓存**：Redis（默认 fakeredis 模拟）用于会话和房间状态管理
- **认证**：JWT Token 认证机制
- **实时通信**：WebSocket 支持
- **AI 检测**：OpenCV Haar Cascade 人脸检测

### 前端架构

- **框架**：Vue 3 + Composition API
- **构建工具**：Vite - 快速构建和热重载
- **状态管理**：Pinia - 现代化状态管理
- **路由**：Vue Router 4
- **HTTP 客户端**：Axios
- **实时通信**：原生 WebSocket API + WebRTC

### 数据流架构

```
前端 (Vue) ←→ HTTP API ←→ 后端 (FastAPI) ←→ Redis ←→ 数据库
                    ↑                    ↑
              WebSocket              AI 检测 (OpenCV)
```

## 常见问题

### 安装问题

1. **OpenCV 安装失败**  
   如遇 OpenCV 安装问题，可尝试：
   ```bash
   pip install opencv-python-headless
   ```

### 运行问题

2. **前端接口报网络错误**  
   确认后端已启动且监听 `8000`，并与 `vite.config.js` 中的代理目标一致。

3. **摄像头无法访问**  
   - 确保使用 localhost 或 127.0.0.1 访问
   - 检查浏览器摄像头权限设置

4. **WebSocket 连接失败**  
   - 检查后端 WebSocket 服务是否正常启动
   - 确认防火墙设置允许 WebSocket 连接

## 开发指南

### 代码规范

- 后端：遵循 PEP 8 规范
- 前端：使用 ESLint 代码规范
- 提交信息：使用约定式提交格式

### 测试指南

```bash
# 后端语法检查
cd backend
python -m py_compile app.py

# 前端构建
cd frontend
npm run build
```

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。
