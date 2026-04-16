# 隐私化在线伴学详细设计
> 提示：本文件 `7` 节及之后为最终接口/信令规范；前文仅为概览或示例，具体实现必须以“最终规范”章节为准。

## 1. 功能详细设计

### 1.1 核心功能

* 默认开启摄像头、关闭麦克风

* 三种隐私模式：原画面/仅手部/背景模糊

* 摄像头手动开关

* WebSocket 实时同步成员状态

* 视频流本地处理，不上传服务器

### 1.2 合规要求

* 不存储、不转发、不留存视频流

* 不强制开启摄像头

* 权限拒绝可继续以纯音频模式陪伴

## 2. UI 交互建议

* 伴学页面：多宫格视频布局

* 视频角落：切换隐私模式、摄像头开关

* 无摄像头权限：显示占位图

* 网络断开：自动重连 3 次

## 3. 接口与实时信令

### 3.1 POST /api/room/privacy

请求：{ "room\_id":"", "privacy\_mode": "hand" }

响应：{ "code":200 }



### 3.2 POST /api/room/camera

请求：{ "room\_id":"", "camera": 0 }

响应：{ "code":200 }



### 3.3 WebSocket 信令

* user\_join：用户进入

* user\_leave：用户离开

* camera\_change：摄像头开关

* privacy\_change：隐私模式切换

## 4. 数据模型

* 表：room\_user（privacy\_mode、camera 字段）

* 无视频数据落地

## 5. 开发计划

* 第3周：摄像头权限、视频渲染、模式切换

* 第3–4周：WebSocket 同步、重连机制

* 第4周：合规校验、异常降级、埋点上报

## 6. 验证方法

* 权限拒绝可正常进入房间

* 三种模式切换实时生效

* 关闭摄像头显示占位图

* 断网后自动重连并恢复状态

* 确认视频流仅本地处理不上传

## 7. 隐私模式状态机与默认值（最终规范）
### 7.1 隐私模式枚举（privacy_mode）
严格枚举（其他值返回 `400`）：
* `original`：原画（不做隐私处理）
* `hand`：仅手部可见（其余画面按实现做遮挡/裁剪）
* `blur`：背景模糊（人脸/背景按实现模糊策略）

状态机：
* `original <-> hand <-> blur`（任意时刻可切换至上述任意一种）
* `privacy_mode` 与 `camera` 独立：
  * 即使 `camera=0`，服务器也会保存用户选择的 `privacy_mode`
  * 当 `camera` 再打开时，前端应使用最近一次的 `privacy_mode` 渲染

### 7.2 摄像头默认与麦克风约束（MVP 强制）
* 默认：`camera=1` 且 `privacy_mode=blur`
* 麦克风：MVP 默认始终 `off`（不实现麦克风开关接口；埋点 `mic_status` 固定为 `off`）
* 不强制开启摄像头：
  * 若前端申请摄像头权限失败，仍允许进入房间并以纯音频/静默方式陪伴
  * 前端必须将服务器状态同步为 `camera=0`（调用 `POST /api/room/camera` 或不再调用并以 `camera=0` 写入为准）

### 7.3 合规边界（不可省略）
* 视频流仅在前端本地处理与渲染
* 服务端不接收、不存储、不转发原始视频帧
* 服务端只保存以下“状态字段”到 `room_user`：
  * `privacy_mode`
  * `camera`

## 8. REST 接口最终规范（请求/响应/校验/错误/并发）
所有 REST 响应与错误码以 `user-management-design.md` 的章节为准（400/401/403/409/429/500）。

### 8.1 POST /api/room/privacy
请求头：
* `Authorization: Bearer {token}`

请求：
{
  "room_id": "",
  "privacy_mode": "hand|blur|original"
}

校验：
* `privacy_mode` 必须属于 7.1 枚举，否则 `400`
* 用户必须为房间活跃成员：存在 `room_user(room_id,user_id)` 且 `leave_time IS NULL`
  * 否则 `403`

写入（MySQL）：
* 更新 `room_user.privacy_mode = privacy_mode`

写入后广播（WebSocket）：
* 向房间内所有已连接成员发送：
{
  "type": "privacy_change",
  "data": {
    "room_id": "",
    "user_id": "",
    "privacy_mode": "hand|blur|original"
  }
}

响应：
{
  "code": 200,
  "msg": "隐私模式更新成功",
  "data": { "room_id": "", "privacy_mode": "" }
}

错误：
* 400：privacy_mode 非法
* 401：缺少/无效 Token
* 403：非房间成员
* 500：内部错误

### 8.2 POST /api/room/camera
请求头：
* `Authorization: Bearer {token}`

请求：
{
  "room_id": "",
  "camera": 0|1
}

校验：
* `camera` 必须为整数 0 或 1，否则 `400`
* 用户必须为房间活跃成员，否则 `403`

写入（MySQL）：
* 更新 `room_user.camera = camera`

广播（WebSocket）：
{
  "type": "camera_change",
  "data": {
    "room_id": "",
    "user_id": "",
    "camera": 0|1
  }
}

前端行为要求（AI 实现必须体现，不可自由发挥）：
* 若 `camera=0`：
  * 前端停止渲染视频流，显示占位图
  * 不请求后续视频帧
* 若 `camera=1`：
  * 前端尝试请求摄像头权限
  * 若权限拒绝：前端必须同步调用该接口写入 `camera=0`，并维持纯音频模式进入房间

响应：
{
  "code": 200,
  "msg": "摄像头状态更新成功",
  "data": { "room_id": "", "camera": 0|1 }
}

错误：
* 400：camera 非法
* 401/403：鉴权/非成员错误
* 500：内部错误

## 9. WebSocket 信令（成员同步 + 重连恢复）
### 9.1 WebSocket 接入约定
* WebSocket URL（实现可等价，但消息与流程必须一致）：`/ws/room`
* 客户端连接成功后，必须发送消息：
{
  "type": "ws_join_room",
  "room_id": ""
}
服务端收到后加入该房间订阅，并立即回传快照（见 9.2）

### 9.2 重连恢复：快照消息
服务端 -> 客户端：
{
  "type": "room_state_snapshot",
  "data": {
    "room_id": "",
    "members": [
      {
        "user_id": "",
        "privacy_mode": "original|hand|blur",
        "camera": 0|1
      }
    ]
  }
}

客户端断网重连策略（来自 PRD/AI-pro 的约束）：
* 断开后最多重连 3 次
* 重连间隔：500ms、1000ms、2000ms
* 重连成功后必须再次发送 `ws_join_room` 以刷新快照
* 重连次数应累积用于埋点 `reconnect_count`

### 9.3 广播事件（服务器触发）
服务端 -> 客户端（用于同步成员进入/离开/状态变化）：
* `user_join`：同 `RoomCreateAttend.md` 11.1 的广播结构
* `user_leave`：同 `RoomCreateAttend.md` 11.4 的广播结构
* `camera_change`：见 8.2
* `privacy_change`：见 8.1

## 10. 视频隐私降级（来自 PRD：切换失败自动回退）
当用户切换到 `hand` 或 `blur` 后，若前端本地隐私渲染/处理失败：
1) 前端立刻降级为 `original` 渲染
2) 前端必须调用：
   * `POST /api/room/privacy`，将 `privacy_mode` 写回 `original`
3) 服务器将广播 `privacy_change`，以保证房间成员视图一致

## 11. PRD 埋点映射（在线伴学关键路径，最终强制）
公共埋点字段（PRD 6.1，必带）：`user_id, phone, token_status, page, room_id, theme, device, network, timestamp`

在线伴学埋点（PRD 6.5）：
* `camera_status`：以当前 `room_user.camera` 为准，取值 `on/off`
* `mic_status`：MVP 固定为 `off`
* `privacy_mode`：取值 `original/hand/blur`
* `video_auth_result`：由前端摄像头权限请求结果决定，取值 `allow/deny`
* `stream_status`：由前端视频流生命周期决定，取值 `normal/abort/reconnect`
* `reconnect_count`：断网重连次数（0 起）

异常埋点（PRD 6.7）：
* 失败时 `error_type` 取 PRD 枚举：`auth/network/db/websocket`
* `api_name` 填实际接口：`room/privacy`、`room/camera`、或 `ws/room`

## 12. 与项目结构目录的对应关系（用于 AI 落地开发）
* REST 路由入口：`backend/controllers/room_controller.py`
  * `POST /api/room/privacy`
  * `POST /api/room/camera`
* WebSocket：`backend/ws/server.py`
  * 处理 `ws_join_room`、并广播 `user_join/user_leave/camera_change/privacy_change`
* 业务层：`backend/services/room_service.py`
* 数据层：`backend/models/room_user.py`（更新 `privacy_mode/camera`）
