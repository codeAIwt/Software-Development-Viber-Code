# 自习室创建/加入/退出详细设计
> 提示：本文件 `7` 节及之后为最终接口/状态机/Redis/信令规范；前文仅为概览或示例，具体实现必须以“最终规范”章节为准。

## 1. 功能详细设计

### 1.1 功能列表

* 创建自习室（主题+人数）

* 自习室列表（按主题筛选）

* 加入自习室（校验状态/人数）

* 退出自习室（更新状态/人数）

* 自动匹配同主题学习搭子

* 房间状态：idle → full → closed

### 1.2 业务规则

* 人数 1-8 人

* 同一用户不可重复进入同一房间

* 满员后无法加入

* 创建者退出后房间可继续存在，无人则关闭

## 2. UI 交互建议

* 创建弹窗：主题下拉、人数输入框

* 自习室列表：主题、当前/最大人数、加入按钮

* 加入成功直接进入伴学页面

* 满员提示：房间已满

* 退出返回自习室列表

## 3. 接口协议描述

### 3.1 POST /api/room/create

请求头：Authorization

请求：

{

&#x20; "theme": "考研",

&#x20; "max\_people": 4

}

响应：{ "code":200, "msg":"创建成功", "data":{ "room\_id":"" } }



### 3.2 GET /api/room/list

参数：theme（可选）

响应：空闲自习室数组



### 3.3 POST /api/room/join

请求：{ "room\_id":"" }

响应：{ "code":200, "msg":"加入成功" }



### 3.4 POST /api/room/leave

请求：{ "room\_id":"" }

响应：{ "code":200, "msg":"退出成功" }



## 4. 数据模型

* 主表：study\_room、room\_user

* 缓存：Redis 队列做匹配与分布式锁

## 5. 开发计划

* 第2周：创建、列表、加入、退出接口

* 第3周：房间状态机、匹配逻辑、并发锁

* 第4周：WebSocke 状态同步、埋点、异常修复

## 6. 验证方法

* 人数超出范围创建失败

* 重复加入失败

* 多人并发加入最后1个位置仅1人成功

* 退出后人数正确递减

* 空房间自动标记为 closed

## 7. 枚举、ID 格式与通用约束（最终规范）
### 7.1 学习主题（theme）
MVP 允许的枚举值（严格枚举，其他值返回 `400`）：
* `考研`
* `期末`
* `考公`
* `语言`

### 7.2 自习室状态（status）
严格枚举：
* `idle`：有成员但未满员
* `full`：已满员（不可再加入）
* `closed`：关闭（不可再加入、列表默认不返回）

### 7.3 ID 格式
* `room_id` / `user_id`：均为 `char(32)` 的 UUID（不含短横线，32 位十六进制字符）

### 7.4 认证
所有 REST 接口都必须携带：
* 请求头：`Authorization: Bearer {token}`

鉴权规则以 `user-management-design.md` 的“JWT + Redis 校验态”章节为准。

### 7.5 数据一致性前提
* `study_room.current_people` 与 `room_user` 的“活跃成员（leave_time 为 NULL）”必须一致
* 任何变更 `current_people` 的操作必须在事务内完成，并结合 Redis 分布式锁避免并发超卖

## 8. 状态机定义（无歧义）
### 8.1 自习室状态机
状态迁移规则（仅以成员数量为准）：
1. 创建：
   * 插入 creator 作为第一个成员后：
     * 若 `max_people == 1` => `status=full`
     * 否则 `status=idle`
2. 加入：
   * 若房间为 `full/closed` => 拒绝加入
   * 若加入成功后 `current_people == max_people` => `status=full`
   * 否则 => `status=idle`
3. 退出：
   * 加入/退出都以 `room_user.leave_time` 为准：离开即将 `leave_time` 写入当前时间
   * 若离开后 `current_people == 0` => `status=closed`
   * 否则 => `status=idle`（`full` 不会因为离开而保持，因为离开后必小于 max）

“创建者退出后房间可继续存在，无人则关闭”：
* `leave` 不区分 creator；只要 `current_people > 0`，房间保持存在（`idle/full`），直到 `current_people` 变为 0 进入 `closed`

### 8.2 加入/退出流程状态机（服务端可见）
* 用户在房间中的活跃状态：`room_user.leave_time IS NULL`
* 入房：INSERT 新记录（若记录已存在则视为冲突）
* 离房：UPDATE 记录并设置 `leave_time`

## 9. Redis 键/队列/锁（最终规范，AI 不得随意改名）
### 9.1 Redis 数据结构
1) 房间元信息（缓存，用于列表/状态读取）
* Key：`room:meta:{room_id}`
* 类型：Hash
* 字段（字符串/数字均可）：
  * `theme`
  * `max_people`
  * `current_people`
  * `status`
  * `creator_id`
  * `updated_ts_ms`

2) 按主题的空闲房间队列（列表与匹配邀请使用）
* Key：`rooms:idle:{theme}`
* 类型：Sorted Set
* member：`room_id`
* score：`updated_ts_ms`（用于“最新活跃”排序；列表不做强依赖）

3) 自动匹配等待队列（同主题空闲用户）
* Key：`match:waiting_users:{theme}`
* 类型：Sorted Set
* member：`user_id`
* score：`enqueue_ts_ms`（用户最近一次请求列表页的时间）

4) 邀请去重标记（防止同一用户被同一房间反复邀请）
* Key：`match:invite:{room_id}:{user_id}`
* 类型：String（值固定为 `1`）
* 生命周期：TTL=`INVITE_TTL_MS`

### 9.2 Redis 分布式锁
1) 加入超卖防护锁
* Key：`lock:room_join:{room_id}`
* 获取方式：SETNX + PX
* 参数（固定配置，AI 不得漏实现）：
  * 锁 TTL：`LOCK_TTL_MS=3000`
  * 等待上限：`LOCK_WAIT_MS=1000`

2) 退出并发防护锁
* Key：`lock:room_leave:{room_id}`
* 获取方式：SETNX + PX
* 参数（与加入锁一致）：
  * 锁 TTL：`LOCK_TTL_MS=3000`
  * 等待上限：`LOCK_WAIT_MS=1000`

### 9.3 自动匹配参数（固定配置）
* `WAITING_ACTIVE_WINDOW_MS=600000`（等待队列有效窗口 10 分钟）
* `INVITE_TTL_MS=60000`（邀请去重 TTL 1 分钟）

等待队列清理逻辑（在匹配/创建后触发）：
* 删除过期用户：
  * `ZREMRANGEBYSCORE match:waiting_users:{theme} 0 (now_ms- WAITING_ACTIVE_WINDOW_MS)`

## 10. WebSocket 信令（用于自动匹配邀请与房间成员同步）
说明：本模块只规定消息类型与载荷；鉴权/连接方式以实现约定为准（token 必须可用于服务端鉴别）。

### 10.1 服务端 -> 客户端（自动匹配邀请）
事件：`room_invite`
载荷：
{
  "type": "room_invite",
  "data": {
    "room_id": "",
    "theme": "",
    "inviter_user_id": "",
    "max_people": 1,
    "expire_ts_ms": 0
  }
}
说明：
* `expire_ts_ms` = 当前时间 + `INVITE_TTL_MS`
* 被邀请用户在点击后，前端调用 `POST /api/room/join` 并带 `match_type="auto"`

### 10.2 服务端 -> 客户端（加入/退出广播）
1) `user_join`（用于同步成员初始隐私状态）
{
  "type": "user_join",
  "data": {
    "room_id": "",
    "user_id": "",
    "privacy_mode": "original|hand|blur",
    "camera": 0|1
  }
}
2) `user_leave`
{
  "type": "user_leave",
  "data": {
    "room_id": "",
    "user_id": ""
  }
}

## 11. REST 接口最终规范（请求/响应/校验/并发/错误）
统一响应体见 `user-management-design.md` 的“通用响应体与错误码约定”章节。

### 11.1 POST /api/room/create
请求头：
* `Authorization: Bearer {token}`

请求：
{
  "theme": "考研",
  "max_people": 4
}

校验：
* `theme` 必须属于枚举（见 7.1）
* `max_people` 为整数，范围 `1-8`
* 用户参与状态不做限制（允许多房间），但会从匹配等待队列中剔除本主题（见 12.2）

事务（MySQL）：
1. 写入 `study_room`：
   * `status`：若 `max_people==1` => full，否则 idle
   * `current_people`：初始化为 1
   * `creator_id`：当前用户
2. 写入 `room_user`（creator 活跃成员）：
   * `privacy_mode`：MVP 默认写入 `blur`
   * `camera`：1
   * `leave_time`：NULL

Redis 更新（MySQL 成功后执行）：
* `HSET room:meta:{room_id}` 写入元信息
* 若 `status=idle`：`ZADD rooms:idle:{theme} updated_ts_ms room_id`

自动匹配邀请（在 Redis 更新后执行）：
* `remaining_slots = max_people - 1`
* 清理等待队列过期用户
* 从 `match:waiting_users:{theme}` 取 `remaining_slots` 个用户（按 enqueue_ts_ms 最小优先，即最早进入等待队列的用户）：
  * `candidates = ZRANGE match:waiting_users:{theme} 0 (remaining_slots-1)`
* 对每个候选用户：
  * 若 `SETNX match:invite:{room_id}:{user_id} 1 EX INVITE_TTL_MS` 成功，则发送 `room_invite`

响应（成功）：
{
  "code": 200,
  "msg": "创建成功",
  "data": {
    "room_id": "",
    "room_status": "idle|full",
    "max_people": 4,
    "current_people": 1
  }
}

错误：
* 400：theme/max_people 非法
* 401/403：鉴权/越权错误（按通用规则）
* 500：数据库/内部错误

埋点：
* `room_create_success`：成功写入

### 11.2 GET /api/room/list
请求头：
* `Authorization: Bearer {token}`

查询参数：
* `theme`（可选）：若存在则只能取枚举值

校验：
* 若传 `theme`：必须属于 7.1 枚举，否则 400

行为：
1) 列表返回（Redis 优先 + 强制数量/排序约束）：
   * 若传 `theme`：
     * `LIST_ROOMS_LIMIT=50`
     * 取房间顺序：`room_ids = ZREVRANGE rooms:idle:{theme} 0 (LIST_ROOMS_LIMIT-1)`
     * 每个 `room_id` 读取 `room:meta:{room_id}` 返回房间信息；返回的 `status` 必须为 `idle`
     * 若 `room:meta:{room_id}` 缺失：以 MySQL 为准重建 `room:meta` 后继续返回
   * 若不传 `theme`：
     * 对四个允许主题（`考研/期末/考公/语言`）分别执行
     * `LIST_ROOMS_LIMIT_PER_THEME=10`
     * 合并后截断为最多 `LIST_ROOMS_LIMIT=50`
     * 仍只返回 `status=idle`
2) 自动匹配等待队列入队（前置条件）：
   * 仅当请求中提供 `theme` 且当前用户当前未处于任何活跃房间时，才入队
   * 活跃房间判定：存在 `room_user` 记录且 `leave_time IS NULL`
   * 入队操作：
     * 清理等待队列过期成员
     * `ZADD match:waiting_users:{theme} now_ms user_id`（更新 score）

响应：
{
  "code": 200,
  "msg": "OK",
  "data": {
    "rooms": [
      {
        "room_id": "",
        "theme": "",
        "current_people": 1,
        "max_people": 4,
        "status": "idle"
      }
    ]
  }
}

错误：
* 400：theme 非法
* 401/403：鉴权错误
* 500：内部错误

### 11.3 POST /api/room/join
请求头：
* `Authorization: Bearer {token}`

请求：
{
  "room_id": "",
  "match_type": "manual|auto"
}
说明：
* `match_type` 用于埋点（manual=用户手动从列表加入；auto=收到邀请加入）
* 若客户端不传，默认视为 `manual`

事务 + 并发控制（最终强制）：
1) 获取锁：`lock:room_join:{room_id}`（等待上限 1000ms）
   * 获取失败 => 返回 `409`，`match_fail_reason="timeout"`
2) MySQL 事务中：
   * 校验 `study_room.status != closed`
   * 校验 `current_people < max_people`
   * 校验是否已在房间中：若存在 `room_user(room_id,user_id)` 则返回 `409`
   * 插入 `room_user`：
     * `privacy_mode`：写入 `blur`
     * `camera`：1
     * `leave_time`：NULL
   * 更新 `study_room.current_people += 1`
   * 更新 `study_room.status`：
     * 若新 current_people == max_people => `full`
     * 否则 => `idle`

Redis 更新（事务成功后执行）：
* 更新 `room:meta:{room_id}.current_people/status`
* 若房间变为 `full`：从 `rooms:idle:{theme}` 移除该 room_id
* 若房间仍为 `idle`：`ZADD rooms:idle:{theme} now_ms room_id`（更新 score）

匹配等待队列剔除：
* 先读取该 `room_id` 对应的 `theme`（从 `room:meta:{room_id}` 或 MySQL `study_room.theme`）
* 从 `match:waiting_users:{theme}` 中删除当前用户（避免重复匹配）

WebSocket 广播：
* 向房间内所有已连接成员发送 `user_join`（含 privacy_mode/camera）

响应（成功）：
{
  "code": 200,
  "msg": "加入成功",
  "data": {
    "room_id": "",
    "match_type": "manual|auto",
    "privacy_mode": "blur",
    "camera": 1
  }
}

错误（必须与埋点字段兼容）：
* 404：房间不存在或状态为 closed
  * 响应 data：
    * `match_fail_reason="no_room"`
* 409：房间满员或已在房间内
  * data：
    * 满员场景：`match_fail_reason="full"`
    * 已加入场景：不返回 `match_fail_reason` 字段（因为该场景不是 PRD 的匹配失败原因枚举）
* 409：锁获取超时
  * data：`match_fail_reason="timeout"`

埋点（按 PRD 6.3）：
* `room_join_success`：成功写入（1/0）
* `match_type`：使用请求中的字段
* `max_people/current_people/room_status`：加入前或加入后的定义必须固定为“加入成功后最终状态”
* `match_fail_reason`：仅当失败原因属于 PRD 枚举 `no_room/full/timeout` 时返回；其他业务冲突（如已加入）不返回该字段

### 11.4 POST /api/room/leave
请求头：
* `Authorization: Bearer {token}`

请求：
{
  "room_id": ""
}

校验：
* 用户必须为房间活跃成员（存在 `room_user` 且 `leave_time IS NULL`）
  * 否则：返回 `403`

事务 + 并发控制：
* 获取锁：`lock:room_leave:{room_id}`（等待上限同 LOCK_WAIT_MS）
  * 获取失败：返回 `409`，`msg="leave timeout"`
* 更新 `room_user.leave_time=now`
* 更新 `study_room.current_people -= 1`
* 更新 `study_room.status`：
  * 若 current_people==0 => `closed`
  * 否则 => `idle`

Redis 更新：
* 更新 `room:meta:{room_id}`（并读取/使用该房间的 `theme` 用于定位 zset）
* 若关闭：从 `rooms:idle:{theme}` 移除该 room_id
* 若仍为 `idle`：`ZADD rooms:idle:{theme} now_ms room_id`（更新 score）

WebSocket 广播：
* 向房间内其他成员发送 `user_leave`

响应：
{
  "code": 200,
  "msg": "退出成功",
  "data": {
    "room_id": ""
  }
}

错误：
* 403：不在房间中
* 404：房间不存在
* 500：内部错误

## 12. PRD 埋点映射（本模块最终强制）
公共埋点字段（PRD 6.1，必带）：
* `user_id, phone, token_status, page, room_id, theme, device, network, timestamp`

本模块关键事件（PRD 6.3，必实现）：
1) `room_create_success`
* `1/0`：成功为 1
* `max_people`：创建请求中的值
* `current_people`：创建成功后最终值（为 1）
* `room_status`：创建后 `idle|full`

2) `room_join_success`
* 成功为 1，失败为 0
* `match_type`：请求字段 `manual|auto`
* `max_people/current_people/room_status`：加入成功后最终值
* 失败时 `match_fail_reason`：只能取 `no_room/full/timeout`

## 13. 与项目结构目录的对应关系（用于 AI 落地开发）
* 路由入口：`backend/controllers/room_controller.py`
  * `POST /api/room/create`
  * `GET /api/room/list`
  * `POST /api/room/join`
  * `POST /api/room/leave`
* 业务逻辑：`backend/services/room_service.py`
  * 房间创建、列表读取（含 Redis 逻辑）
  * 加入/退出（事务 + Redis 锁）
  * 自动匹配邀请（从 `match:waiting_users:{theme}` 选择候选并发送 `room_invite`）
* 数据层模型：
  * `backend/models/study_room.py`（`study_room` 表）
  * `backend/models/room_user.py`（`room_user` 表）
* Redis 与缓存封装：`backend/utils/cache.py`
  * 房间元信息缓存、匹配队列、分布式锁
* WebSocket：`backend/ws/server.py`
  * 发送 `room_invite`
  * 广播 `user_join/user_leave`
* WebSocket 连接映射：`backend/utils/ws_client.py`
