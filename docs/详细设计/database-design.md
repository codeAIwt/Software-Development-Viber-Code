# 数据库详细设计文档

> 提示：本文件新增的 `10+` 节为 Redis/定时任务/一致性等“最终实现规范”；表结构章节仍作为数据模型基础。

## 1. 概述

本文档为线上伴学（轻量化线上自习室）系统的数据库详细设计，包含**逻辑结构设计、物理结构设计、数据表定义、索引设计、存储策略**。

技术栈：MySQL 8.0 + Redis 7.0

架构：B/S 架构

开发框架：Vue3 + Python FastAPI

---

## 2. 数据库设计规范

- 所有表使用 InnoDB 引擎
- 字符集：utf8mb4
- 排序规则：utf8mb4unicodeci
- 主键统一使用 id，关联字段统一使用 xxxid
- 时间字段统一使用 datetime 或 date
- 布尔状态使用 tinyint(1)，1=有效/开启，0=无效/关闭

---

## 3. 逻辑结构设计（ER 图说明）

### 3.1 实体与关系

1. **用户（user）**

可创建多个自习室、加入多个自习室、拥有多条学习时长记录。

1. **自习室（studyroom）**

由一个用户创建，包含多个成员，状态随人数变化。

1. **自习室成员（roomuser）**

用户与自习室的多对多关联表，表示用户加入某房间。

1. **学习时长（studyduration）**

每个用户每天一条记录，存储当日学习时长与击败百分比。

### 3.2 实体关系

- 1 对 N：user → studyroom（一个用户可创建多个房间）
- 1 对 N：user → studyduration（一个用户可有多日时长）
- N 对 N：user ↔ studyroom（通过 roomuser 关联）

---

## 4. 物理结构设计

### 4.1 库名

`online_study`

### 4.2 存储引擎

所有表：InnoDB

### 4.3 字符集

utf8mb4（支持表情符号，兼容昵称/头像）

### 4.4 数据文件策略

- 业务数据：MySQL 本地磁盘
- 热点缓存：Redis 内存存储
- 文件资源：头像 URL 存入数据库，文件存静态资源目录

---

## 5. 数据表详细设计

### 5.1 user（用户信息表）

**用途**：存储用户账号、密码、昵称、头像等核心信息

**引擎**：InnoDB

**字符集**：utf8mb4


| 字段            | 类型           | 约束              | 默认值   | 说明           |
| ------------- | ------------ | --------------- | ----- | ------------ |
| id            | char(32)     | PRIMARY KEY     | —     | 用户唯一ID（UUID） |
| phone         | varchar(11)  | NOT NULL UNIQUE | —     | 注册手机号（登录账号）  |
| password      | varchar(64)  | NOT NULL        | —     | BCrypt 加密密码  |
| nickname      | varchar(20)  | NOT NULL        | —     | 用户昵称         |
| avatar        | varchar(255) | NOT NULL        | 默认URL | 头像地址         |
| registertime  | datetime     | NOT NULL        | —     | 注册时间         |
| lastlogintime | datetime     | NULL            | NULL  | 最后登录时间       |
| tags          | varchar(255) | NULL            | —     | 学习标签，逗号分隔     |
| is_first_login | tinyint(1)   | NOT NULL        | 1     | 是否首次登录，1=是 0=否 |


**索引**

- PRIMARY KEY (`id`)
- UNIQUE KEY `uk_phone` (`phone`)

---

### 5.2 studyroom（自习室表）

**用途**：存储自习室基础信息、主题、人数、状态

**引擎**：InnoDB

**字符集**：utf8mb4


| 字段            | 类型          | 约束          | 默认值   | 说明                  |
| ------------- | ----------- | ----------- | ----- | ------------------- |
| id            | char(32)    | PRIMARY KEY | —     | 自习室ID（UUID）         |
| theme         | varchar(20) | NOT NULL    | —     | 学习主题：考研/期末/考公/语言    |
| maxpeople     | tinyint     | NOT NULL    | —     | 最大人数 1-8            |
| currentpeople | tinyint     | NOT NULL    | 1     | 当前人数                |
| status        | varchar(10) | NOT NULL    | idle  | 状态：idle/full/closed |
| creatorid     | char(32)    | NOT NULL    | —     | 创建者用户ID             |
| createtime    | datetime    | NOT NULL    | NOW() | 创建时间                |
| tags          | varchar(255) | NULL        | —     | 自习室标签，逗号分隔         |


**索引**

- PRIMARY KEY (`id`)
- KEY `idx_theme_status` (`theme`, `status`)

---

### 5.3 roomuser（自习室成员关联表）

**用途**：记录用户加入/离开房间、隐私模式、摄像头状态

**引擎**：InnoDB

**字符集**：utf8mb4


| 字段          | 类型          | 约束                        | 默认值      | 说明                    |
| ----------- | ----------- | ------------------------- | -------- | --------------------- |
| id          | bigint      | PRIMARY KEY AUTOINCREMENT | —        | 自增ID                  |
| roomid      | char(32)    | NOT NULL                  | —        | 自习室ID                 |
| userid      | char(32)    | NOT NULL                  | —        | 用户ID                  |
| jointime    | datetime    | NOT NULL                  | NOW()    | 加入时间                  |
| leavetime   | datetime    | NULL                      | NULL     | 离开时间                  |
| privacymode | varchar(10) | NOT NULL                  | original | 模式：original/hand/blur |
| camera      | tinyint(1)  | NOT NULL                  | 1        | 摄像头：1开启 0关闭           |


**索引**

- PRIMARY KEY (`id`)
- UNIQUE KEY `uk_room_user` (`room_id`, `user_id`)

---

### 5.4 studyduration（用户学习时长表）

**用途**：记录用户每日学习时长、全平台击败百分比

**引擎**：InnoDB

**字符集**：utf8mb4


| 字段           | 类型           | 约束                        | 默认值   | 说明                |
| ------------ | ------------ | ------------------------- | ----- | ----------------- |
| id           | bigint       | PRIMARY KEY AUTOINCREMENT | —     | 自增ID              |
| userid       | char(32)     | NOT NULL                  | —     | 用户ID              |
| studydate    | date         | NOT NULL                  | —     | 学习日期（yyyy-MM-dd）  |
| totalminutes | int          | NOT NULL                  | 0     | 当日总学习时长（分钟）       |
| beatpercent  | decimal(5,2) | NULL                      | NULL  | 击败百分比（0.00100.00） |
| createtime   | datetime     | NOT NULL                  | NOW() | 记录生成时间            |


**索引**

- PRIMARY KEY (`id`)
- UNIQUE KEY `uk_user_date` (`user_id`, `study_date`)

---

## 6. 索引设计总览


| 表名            | 索引类型 | 索引字段               | 用途         |
| ------------- | ---- | ------------------ | ---------- |
| user          | 唯一索引 | phone              | 登录、查重      |
| studyroom     | 普通索引 | theme + status     | 自习室列表筛选、匹配 |
| roomuser      | 唯一索引 | roomid + userid    | 防重复加入      |
| studyduration | 唯一索引 | userid + studydate | 每日时长唯一记录   |


---

## 7. 数据存储与读写策略

### 7.1 MySQL（持久化存储）

- 用户信息
- 自习室信息
- 房间成员关系
- 学习时长历史记录

### 7.2 Redis（缓存/高并发）

- 用户登录 Token
- 自习室实时状态
- 排行榜（击败百分比）
- 分布式锁（防并发超员）
- 匹配队列

### 7.3 实时数据（不落地）

- WebSocket 同步房间状态、视频状态
- 视频流仅前端本地处理，不上传数据库

---

## 8. 数据生命周期与清理策略

- studyduration：永久保存
- studyroom：closed 状态 7 天后可归档
- roomuser：离开 24 小时后可清理冗余记录
- user：用户不注销则永久保存

---

## 9. 数据库约束与安全

- 密码必须加密存储
- 手机号唯一，防止重复注册
- 房间人数不允许超过 maxpeople
- 外键逻辑由业务层保证，不设置物理外键以提升性能
- 所有写操作加事务控制

## 10. Redis 设计（与详细设计对齐，最终规范）

本节约定 Redis key 名称/数据结构，供 `RoomCreateAttend.md / Privacy-oriented-room.md` 的实现调用。

### 10.1 认证会话（JWT + Redis 校验态）

- Key：`auth:session:{jti}`
- 类型：String 或 Hash
- Value：`{ "user_id": "..." }`
- TTL：与 JWT `exp` 一致
- 失效判定：不存在 => `401`

### 10.2 房间状态缓存与列表

1. 房间元信息

- Key：`room:meta:{room_id}`
- 类型：Hash
- 字段：
  - `theme`
  - `max_people`
  - `current_people`
  - `status`（idle/full/closed）
  - `creator_id`
  - `updated_ts_ms`

1. 按主题空闲房间集合

- Key：`rooms:idle:{theme}`
- 类型：Sorted Set
- member：`room_id`
- score：`updated_ts_ms`

清理规则：

- 当房间 `status` 变为 `full` 或 `closed`，必须从对应 `rooms:idle:{theme}` 移除该 `room_id`

### 10.3 自动匹配等待队列与邀请去重

1. 等待用户（同主题空闲用户）

- Key：`match:waiting_users:{theme}`
- 类型：Sorted Set
- member：`user_id`
- score：`enqueue_ts_ms`（用于匹配时排序）

过期清理：

- `WAITING_ACTIVE_WINDOW_MS=600000`
- 清理命令：`ZREMRANGEBYSCORE match:waiting_users:{theme} 0 (now_ms- WAITING_ACTIVE_WINDOW_MS)`

1. 邀请去重标记

- Key：`match:invite:{room_id}:{user_id}`
- 类型：String
- TTL：`INVITE_TTL_MS=60000`

### 10.4 分布式锁（并发安全）

锁统一使用：`SET key value NX PX`

- `lock:room_join:{room_id}`
- `lock:room_leave:{room_id}`
参数（与详细设计一致）：
- `LOCK_TTL_MS=3000`
- `LOCK_WAIT_MS=1000`

### 10.5 排行榜缓存（击败百分比）

定时任务计算后写入：

- Key：`rank:beat:{study_date}`
- 类型：Hash
- 字段：`user_id -> beat_percent`（字符串化的 decimal）
- TTL：`48h`

说明：当用户当日 `total_minutes==0`，其 `beat_percent` 写入 `NULL` 或不写入字段；前端显示无数据提示。

## 11. 每日 04:00 定时任务（学习时长统计与击败百分比计算）

调度文件（用于 AI 落地实现）：`backend/schedule/duration_schedule.py`

执行时间：

- 每日 04:00 执行
- 统计日期：`study_date = (服务器当前日期 - 1 天)`

计算目标：

- 更新 `study_duration.beat_percent`（decimal(5,2)）
- 刷新 Redis 排行榜缓存（见 10.5）

计算口径（严格遵循 PRD）：

1. 有效人数：

- `effective_users = COUNT(*) where total_minutes > 0`

1. 对每个用户：

- 若 `total_minutes == 0` => `beat_percent = NULL`
- 否则：
  - `less_count = COUNT(*) where total_minutes < current_user.total_minutes`
  - `beat_percent = less_count / effective_users * 100`

1. 精度与取值：

- 四舍五入到两位小数，范围 `0.00 ~ 100.00`
- 写入 MySQL 字段 `beat_percent`

写入步骤：

1. 批量读取 `study_duration`（study_date）
2. 计算并批量更新 MySQL
3. 写入 Redis `rank:beat:{study_date}`（Hash 字段）

防重执行：

- 使用分布式锁（推荐）：`lock:duration_schedule:{study_date}`
- 锁 TTL >= 任务最长耗时

## 12. 学习时长数据写入异常约束（与 PRD 5.3 一致）

尽管时长采集不在本 4 份 md 里单独展开，但数据库层必须满足以下约束，供 `duration_controller.py` 与相关服务实现：

1. 超长截断：

- 单次写入或累计后的 `total_minutes` 必须截断到 `<= 1440`

1. 同日多次合并：

- 同一 `user_id + study_date`：
  - 使用 upsert 将 `total_minutes = total_minutes + new_minutes`
  - 合并完成后再做 `<= 1440` 截断

1. 非法空值：

- `total_minutes` 必须为非负整数；非法值直接拒绝写入并返回 `400`

## 13. 与详细设计的强一致性要求（用于实现约束）

1. 读缓存不可信时的修复：

- `GET /api/room/list` 主要依赖 Redis，但当 `room:meta:{room_id}` 缺失或与 DB 不一致时：
  - 以 MySQL 为准补写 Redis（重建 `rooms:idle:{theme}` 或更新 `room:meta`）

1. DB/Redis 更新顺序：

- Join/Create/Leave 的 MySQL 事务必须先提交
- 提交成功后再更新 Redis
- 若 Redis 更新失败：允许在下次请求中触发“读缓存修复”（见第 1 点）

## 14. 索引补充（提升关键查询效率，避免歧义）

为了满足：

- join 前检查用户是否为活跃成员
- 定时任务按 study_date 拉取
建议补充索引（AI 实现必须按此加）：
- `room_user`：新增索引 `idx_room_user_user_id (user_id)`
- `study_duration`：新增索引 `idx_study_duration_study_date (study_date)`

## 15. MVP：房间活跃成员的 privacy_mode/camera 写入默认值

为避免“依赖表默认值”造成实现歧义，本项目规定：

- 当创建者或用户通过 `POST /api/room/create`、`POST /api/room/join` 成为房间活跃成员（即 `room_user.leave_time IS NULL`）时：
  - 必须显式写入 `room_user.privacy_mode = 'blur'`
  - 必须显式写入 `room_user.camera = 1`
- `room_user.privacy_mode` 表结构默认值 `original` 仅作为兜底，不得用于 MVP 的业务逻辑。

## 16. 与项目结构目录的对应关系（用于 AI 落地开发）

- MySQL 数据库连接：`backend/config/db.py`
- Redis 连接/封装：`backend/utils/cache.py`
- 排行榜与时长统计调度：`backend/schedule/duration_schedule.py`
- 学习时长数据层：`backend/models/study_duration.py`
- 房间数据层：`backend/models/study_room.py`、`backend/models/room_user.py`
- AI检测服务：`backend/services/ai_service.py`

## 17. AI检测功能设计

### 17.1 功能概述

AI检测功能用于检测用户是否在摄像头前方，防止用户在自习室中但人不在的情况。当检测到用户不在摄像头前方时，系统会自动将用户从自习室中退出。

### 17.2 技术方案

- **前端实现**：使用Canvas进行摄像头画面截图，每1分钟截取一次摄像头画面，将截图发送到后端进行AI分析。
- **后端实现**：使用ResNet-18模型分析画面中是否有人，返回分析结果给前端，当检测到无人时，调用退出房间API。

### 17.3 数据流程

1. 前端每1分钟自动截图并发送到后端
2. 后端使用ResNet-18模型对图像进行分析
3. 根据分析结果判断是否有人在摄像头前
4. 如果检测到无人，自动将用户从自习室中退出

### 17.4 性能优化

- 使用轻量级的ResNet-18模型，确保检测速度
- 调整检测间隔，避免过于频繁的检测影响系统性能
- 对图像进行压缩，减少传输数据量

### 17.5 隐私保护

- AI检测仅在本地进行，不上传用户图像到云端
- 检测完成后，图像数据会被立即销毁
- 检测结果仅用于判断用户是否在摄像头前，不做其他用途

### 17.6 故障处理

- 当AI检测失败时，系统会继续运行，不会影响自习室的正常使用
- 当网络连接不稳定时，系统会暂停AI检测，待网络恢复后重新开始