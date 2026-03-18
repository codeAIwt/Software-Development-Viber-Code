# 软件工程实现：产品需求说明（PRD）
> 适配技术栈：Vue + Python + MySQL + Redis + WebSocket
> 架构：C/S 架构
> 本文档可直接用于 AI 编程生成代码

# 一、全局上下文与架构约束
- 前端：Vue
- 后端：Python 3.12.5
- 通信：HTTP + WebSocket
- 数据库：MySQL
- 缓存：Redis
- 强制规范：
  1. 所有接口必须 Token 鉴权
  2. 密码必须加密存储
  3. 前端 + 后端双重校验
  4. 视频流仅本地处理，不上传原始画面
  5. 定时任务每日 04:00 执行

# 二、核心功能（MVP）
## 核心功能 1：用户系统
- 用户故事：作为一名线上自习室用户，我希望能注册、登录、编辑个人信息、退出登录，以便安全使用平台功能。
- 页面交互与执行步骤：
  1. 未登录用户访问核心页面自动跳转至 /login。
  2. 注册流程：
     1. 进入 /register 页面，填写手机号、密码、确认密码。
     2. 校验：手机号格式、两次密码一致、手机号未注册。
     3. 后端插入用户表，密码加密，生成默认昵称与头像。
     4. 注册成功自动登录，跳转 /home。
  3. 登录流程：
     1. 进入 /login，填写手机号+密码。
     2. 校验格式与账号正确性。
     3. 生成 Token，前端缓存，跳转首页。
  4. 个人信息编辑：
     1. /personal 页面进入编辑页。
     2. 修改昵称。
     3. 保存后同步更新用户表。
  5. 退出登录：
     1. 点击退出，确认弹窗。
     2. 前端清除 Token，后端销毁登录态。
     3. 跳转登录页。

## 核心功能 2：全应用自习时长激励排行榜
- 用户故事：作为学习者，我希望查看自己的日自习时长与全平台击败比例，以获得激励。
- 页面交互与执行步骤：
  1. 用户进入 /personal 学习数据模块。
  2. 展示：当日自习时长、日平均时长、击败 XX% 用户在用户个人信息界面。
  3. 击败比例计算规则：
     - 按时长分段统计用户分布
     - 击败率 = 时长低于当前用户的人数 / 总有效人数 × 100%
  4. 每日 04:00 定时任务统计全平台数据。
  5. 结果存入 Redis 缓存，前端拉取展示。
  6. 无学习数据则显示提示文案。

## 核心功能 3：学习主题匹配及自习室创建/加入
- 用户故事：我希望按学习主题创建/加入自习室，系统自动匹配同主题搭子。
- 页面交互与执行步骤：
  1. 进入 /study-room 页面，可创建或加入自习室。
  2. 创建自习室：
     1. 选择主题（考研/期末/考公/语言等）。
     2. 设置人数上限:1-8 人(至少1人)。
     3. 校验主题与人数合法性。
     4. 创建自习室，状态设为 idle。
     5. 系统自动匹配同主题空闲用户并推送邀请。
  3. 加入自习室：
     1. 展示空闲自习室列表(显示当期人数/人数上限)，支持主题筛选。
     2. 点击加入，校验房间状态与剩余位置。
     3. 校验通过则加入房间，更新房间人数。
  4. 成功后跳转 /study-room/[id] 伴学页面。

## 核心功能 4：隐私化在线伴学
- 用户故事：我希望开启视频闭麦伴学，并可使用手部模式/背景模糊保护隐私。
- 页面交互与执行步骤：
  1. 进入自习室房间，申请摄像头权限。
  2. 默认：摄像头开启，麦克风关闭。
  3. 提供三种模式切换：原画面 / 仅手部 / 背景模糊。
  4. 视频流本地实时处理，不上传原始画面。
  5. 模式选择同步至后端房间成员表。
  6. 可随时开关摄像头，关闭后显示占位图。

# 三、MySQL 数据领域模型
## 表 1：用户表 user
| 字段            | 类型         | 约束              | 说明                 |
|-----------------|-------------|-------------------|----------------------|
| id              | char(32)    | PK                | 用户ID               |
| phone           | varchar(11) | NOT NULL, UNIQUE  | 手机号               |
| password        | varchar(64) | NOT NULL          | 加密密码             |
| nickname        | varchar(20) | NOT NULL          | 昵称                 |
| avatar          | varchar(255)| NOT NULL          | 头像URL              |
| register_time   | datetime    | NOT NULL          | 注册时间             |
| last_login_time | datetime    | NULL              | 最后登录时间         |

## 表 2：学习时长表 study_duration
| 字段            | 类型         | 约束              | 说明                 |
|-----------------|-------------|-------------------|----------------------|
| id              | bigint      | PK, AI            | 自增ID               |
| user_id         | char(32)    | NOT NULL          | 用户ID               |
| study_date      | date        | NOT NULL          | 日期                 |
| total_minutes   | int         | NOT NULL DEFAULT 0| 当日总时长（分钟）|
| avg_daily       | float       | NULL              | 日均时长             |
| beat_percent    | decimal(5,2)| NULL              | 击败百分比           |
| create_time     | datetime    | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| UNIQUE KEY(user_id, study_date) |

## 表 3：自习室表 study_room
| 字段            | 类型         | 约束              | 说明                 |
|-----------------|-------------|-------------------|----------------------|
| id              | char(32)    | PK                | 房间ID               |
| theme           | varchar(20) | NOT NULL          | 学习主题             |
| max_people      | tinyint     | NOT NULL          | 最大人数 1-8         |
| current_people  | tinyint     | NOT NULL DEFAULT 1| 当前人数             |
| status          | varchar(10) | NOT NULL          | idle/full/closed     |
| creator_id      | char(32)    | NOT NULL          | 创建者ID             |
| create_time     | datetime    | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

## 表 4：自习室成员表 room_user
| 字段            | 类型         | 约束              | 说明                 |
|-----------------|-------------|-------------------|----------------------|
| id              | bigint      | PK, AI            | 自增ID               |
| room_id         | char(32)    | NOT NULL          | 房间ID               |
| user_id         | char(32)    | NOT NULL          | 用户ID               |
| join_time       | datetime    | DEFAULT CURRENT_TIMESTAMP | 加入时间 |
| leave_time      | datetime    | NULL              | 离开时间             |
| privacy_mode    | varchar(10) | DEFAULT 'original'| original/hand/blur  |
| camera          | tinyint     | DEFAULT 1         | 1开启 0关闭          |
| UNIQUE KEY(room_id, user_id) |

# 四、核心状态机
## 1. 自习室状态机
idle（空闲） ↔ full（满员） → closed（关闭）

## 2. 加入自习室状态机
未加入 → 校验中 → 已加入 / 加入失败
已加入 → 离开 → 已离开

## 3. 创建自习室状态机
未创建 → 创建中 → 已创建 / 创建失败
已创建 → 满员 → full
已创建 → 关闭/超时 → closed

## 4. 隐私模式状态机
original ↔ hand ↔ blur

# 五、防御性边界与异常流
## 5.1 权限与越权
- 未登录访问核心接口 → 401 → 跳转登录
- 越权查看他人数据 → 403 拦截
- 高频请求 → IP 限流
- 无效 Token → 强制登出

## 5.2 并发异常
- 多人同时加入最后一个位置 → Redis 锁保证仅一人成功
- 定时任务重复执行 → 分布式锁防止并发
- 房间人数异常 → 自动修复 current_people ≤ max_people

## 5.3 数据异常
- 时长超过 24h → 自动截断为 1440 分钟
- 同一用户同一天多条时长 → 自动合并
- 缓存与数据库不一致 → 自动刷新缓存
- 空值/非法参数 → 前后端双重拦截

## 5.4 音视频异常
- 无摄像头权限 → 提示并允许纯音频陪伴
- 切换模式失败 → 自动降级为原画面
- WebSocket 断开 → 自动重连 3 次
