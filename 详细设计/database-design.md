# 数据库详细设计文档

## 1. 概述

本文档为线上伴学（轻量化线上自习室）系统的数据库详细设计，包含**逻辑结构设计、物理结构设计、数据表定义、索引设计、存储策略**。

技术栈：MySQL 8.0 + Redis 7.0

架构：B/S 架构

开发框架：Vue3 + Python FastAPI



***



## 2. 数据库设计规范

* 所有表使用 InnoDB 引擎

* 字符集：utf8mb4

* 排序规则：utf8mb4\_unicode\_ci

* 主键统一使用 id，关联字段统一使用 xxx\_id

* 时间字段统一使用 datetime 或 date

* 布尔状态使用 tinyint(1)，1=有效/开启，0=无效/关闭

***



## 3. 逻辑结构设计（ER 图说明）

### 3.1 实体与关系

1. **用户（user）**

可创建多个自习室、加入多个自习室、拥有多条学习时长记录。

2. **自习室（study\_room）**

由一个用户创建，包含多个成员，状态随人数变化。

3. **自习室成员（room\_user）**

用户与自习室的多对多关联表，表示用户加入某房间。

4. **学习时长（study\_duration）**

每个用户每天一条记录，存储当日学习时长与击败百分比。

### 3.2 实体关系

* 1 对 N：user → study\_room（一个用户可创建多个房间）

* 1 对 N：user → study\_duration（一个用户可有多日时长）

* N 对 N：user ↔ study\_room（通过 room\_user 关联）

***



## 4. 物理结构设计

### 4.1 库名

`online_study`



### 4.2 存储引擎

所有表：InnoDB



### 4.3 字符集

utf8mb4（支持表情符号，兼容昵称/头像）



### 4.4 数据文件策略

* 业务数据：MySQL 本地磁盘

* 热点缓存：Redis 内存存储

* 文件资源：头像 URL 存入数据库，文件存静态资源目录

***



## 5. 数据表详细设计

### 5.1 user（用户信息表）

**用途**：存储用户账号、密码、昵称、头像等核心信息

**引擎**：InnoDB

**字符集**：utf8mb4



| 字段                | 类型           | 约束              | 默认值   | 说明           |
| ----------------- | ------------ | --------------- | ----- | ------------ |
| id                | char(32)     | PRIMARY KEY     | —     | 用户唯一ID（UUID） |
| phone             | varchar(11)  | NOT NULL UNIQUE | —     | 注册手机号（登录账号）  |
| password          | varchar(64)  | NOT NULL        | —     | BCrypt 加密密码  |
| nickname          | varchar(20)  | NOT NULL        | —     | 用户昵称         |
| avatar            | varchar(255) | NOT NULL        | 默认URL | 头像地址         |
| register\_time    | datetime     | NOT NULL        | —     | 注册时间         |
| last\_login\_time | datetime     | NULL            | NULL  | 最后登录时间       |



**索引**

* PRIMARY KEY (`id`)

* UNIQUE KEY `uk_phone` (`phone`)

***



### 5.2 study\_room（自习室表）

**用途**：存储自习室基础信息、主题、人数、状态

**引擎**：InnoDB

**字符集**：utf8mb4



| 字段              | 类型          | 约束          | 默认值   | 说明                  |
| --------------- | ----------- | ----------- | ----- | ------------------- |
| id              | char(32)    | PRIMARY KEY | —     | 自习室ID（UUID）         |
| theme           | varchar(20) | NOT NULL    | —     | 学习主题：考研/期末/考公/语言    |
| max\_people     | tinyint     | NOT NULL    | —     | 最大人数 1-8            |
| current\_people | tinyint     | NOT NULL    | 1     | 当前人数                |
| status          | varchar(10) | NOT NULL    | idle  | 状态：idle/full/closed |
| creator\_id     | char(32)    | NOT NULL    | —     | 创建者用户ID             |
| create\_time    | datetime    | NOT NULL    | NOW() | 创建时间                |



**索引**

* PRIMARY KEY (`id`)

* KEY `idx_theme_status` (`theme`, `status`)

***



### 5.3 room\_user（自习室成员关联表）

**用途**：记录用户加入/离开房间、隐私模式、摄像头状态

**引擎**：InnoDB

**字符集**：utf8mb4



| 字段            | 类型          | 约束                          | 默认值      | 说明                    |
| ------------- | ----------- | --------------------------- | -------- | --------------------- |
| id            | bigint      | PRIMARY KEY AUTO\_INCREMENT | —        | 自增ID                  |
| room\_id      | char(32)    | NOT NULL                    | —        | 自习室ID                 |
| user\_id      | char(32)    | NOT NULL                    | —        | 用户ID                  |
| join\_time    | datetime    | NOT NULL                    | NOW()    | 加入时间                  |
| leave\_time   | datetime    | NULL                        | NULL     | 离开时间                  |
| privacy\_mode | varchar(10) | NOT NULL                    | original | 模式：original/hand/blur |
| camera        | tinyint(1)  | NOT NULL                    | 1        | 摄像头：1开启 0关闭           |



**索引**

* PRIMARY KEY (`id`)

* UNIQUE KEY `uk_room_user` (`room_id`, `user_id`)

***



### 5.4 study\_duration（用户学习时长表）

**用途**：记录用户每日学习时长、全平台击败百分比

**引擎**：InnoDB

**字符集**：utf8mb4



| 字段             | 类型           | 约束                          | 默认值   | 说明                  |
| -------------- | ------------ | --------------------------- | ----- | ------------------- |
| id             | bigint       | PRIMARY KEY AUTO\_INCREMENT | —     | 自增ID                |
| user\_id       | char(32)     | NOT NULL                    | —     | 用户ID                |
| study\_date    | date         | NOT NULL                    | —     | 学习日期（yyyy-MM-dd）    |
| total\_minutes | int          | NOT NULL                    | 0     | 当日总学习时长（分钟）         |
| beat\_percent  | decimal(5,2) | NULL                        | NULL  | 击败百分比（0.00\~100.00） |
| create\_time   | datetime     | NOT NULL                    | NOW() | 记录生成时间              |



**索引**

* PRIMARY KEY (`id`)

* UNIQUE KEY `uk_user_date` (`user_id`, `study_date`)

***



## 6. 索引设计总览

| 表名              | 索引类型 | 索引字段                   | 用途         |
| --------------- | ---- | ---------------------- | ---------- |
| user            | 唯一索引 | phone                  | 登录、查重      |
| study\_room     | 普通索引 | theme + status         | 自习室列表筛选、匹配 |
| room\_user      | 唯一索引 | room\_id + user\_id    | 防重复加入      |
| study\_duration | 唯一索引 | user\_id + study\_date | 每日时长唯一记录   |



***



## 7. 数据存储与读写策略

### 7.1 MySQL（持久化存储）

* 用户信息

* 自习室信息

* 房间成员关系

* 学习时长历史记录

### 7.2 Redis（缓存/高并发）

* 用户登录 Token

* 自习室实时状态

* 排行榜（击败百分比）

* 分布式锁（防并发超员）

* 匹配队列

### 7.3 实时数据（不落地）

* WebSocket 同步房间状态、视频状态

* 视频流仅前端本地处理，不上传数据库

***



## 8. 数据生命周期与清理策略

* study\_duration：永久保存

* study\_room：closed 状态 7 天后可归档

* room\_user：离开 24 小时后可清理冗余记录

* user：用户不注销则永久保存

***



## 9. 数据库约束与安全

* 密码必须加密存储

* 手机号唯一，防止重复注册

* 房间人数不允许超过 max\_people

* 外键逻辑由业务层保证，不设置物理外键以提升性能

* 所有写操作加事务控制
