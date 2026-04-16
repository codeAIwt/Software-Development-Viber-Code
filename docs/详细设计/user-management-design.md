# 用户系统详细设计
> 提示：本文件新增的 `7+` 节为最终接口/错误码/鉴权与埋点规范；前文为概览或示例，具体实现必须以“最终规范”章节为准。

## 1. 功能详细设计

### 1.1 功能范围

* 用户注册（手机号+密码）

* 用户登录（JWT 鉴权）

* 退出登录

* 个人信息展示

* 登录态拦截与权限校验

### 1.2 业务规则

* 手机号唯一，格式 11 位数字

* 密码 6-16 位字母数字组合

* 注册自动生成默认昵称与头像

* 所有核心接口必须携带 Token

## 2. UI 交互建议

* 登录页：手机号、密码、登录按钮、去注册入口

* 注册页：手机号、密码、确认密码、同意协议勾选框

* 个人中心：昵称、头像、今日时长、击败百分比、退出登录按钮

* 未登录访问核心页自动跳转登录

## 3. 接口协议描述

### 3.1 POST /api/user/register

请求：

{

&#x20; "phone": "13800138000",

&#x20; "password": "a123456"

}

响应：

{

&#x20; "code": 200,

&#x20; "msg": "注册成功",

&#x20; "data": { "user\_id": "", "token": "" }

}



### 3.2 POST /api/user/login

请求：

{

&#x20; "phone": "13800138000",

&#x20; "password": "a123456"

}

响应：

{

&#x20; "code": 200,

&#x20; "msg": "登录成功",

&#x20; "data": { "user\_id": "", "token": "" }

}



### 3.3 POST /api/user/logout

请求头：Authorization: Bearer {token}

响应：{ "code": 200, "msg": "退出成功" }



### 3.4 GET /api/user/profile

请求头：Authorization

响应：用户信息



## 4. 数据模型

* 主表：user

* 缓存：Redis 存储 Token

* 无额外依赖表

## 5. 开发计划

* 第1周：user 表、注册/登录接口、密码加密、JWT 工具

* 第2周：个人中心、路由守卫、登录态校验

* 第3周：限流、异常处理、埋点接入

## 6. 验证方法

* 重复手机号注册拦截

* 密码错误/格式错误校验

* 无 Token / 非法 Token 访问返回 401

* 退出后 Token 失效

## 7. 通用响应体与错误码约定（最终规范）
所有 REST 接口的响应必须统一为：
{
  "code": 200,
  "msg": "OK",
  "data": { }
}

约定：
* 成功：`code=200`
* 失败：`code` 为对应错误码，`data` 为空对象 `{}` 或省略

错误码语义（用于后续所有详细设计文件的 `code/msg`）：
* 400：参数非法（格式/范围/枚举不通过）
* 401：缺少 Token / Token 无效 / Token 过期
* 403：越权操作（资源不属于当前用户）
* 409：业务冲突（如重复注册/已加入等）
* 429：速率限制触发
* 500：未预期服务端错误（数据库/内部异常）

错误响应示例：
{
  "code": 400,
  "msg": "phone 格式错误",
  "data": {}
}

## 8. JWT 与 Redis 校验态（约束，不可省略）
1) 登录成功：
* 后端生成 JWT：
  * `sub`：用户 ID
  * `jti`：唯一令牌标识（随机 UUID 或安全随机字符串）
  * `exp`：过期时间
* Redis 写入有效会话：
  * Key：`auth:session:{jti}`
  * Value：`{ "user_id": "..." }`
  * TTL：与 JWT `exp` 余量一致（到期即失效）
* 返回：
  * `data.user_id`
  * `data.token`（JWT 字符串）

2) 鉴权中间件（所有核心接口）：
* 校验 JWT 签名与过期时间
* 取出 `jti`
* 查询 `auth:session:{jti}`：
  * 不存在 => `401`

3) 退出登录：
* 取出请求 Token 的 `jti`
* 删除 Redis：`DEL auth:session:{jti}`
* 返回 `200`

## 9. 输入校验规则（前后端双重校验）
### 9.1 phone
* 正则：`^[0-9]{11}$`
* 唯一：同一 `phone` 不允许重复注册（MySQL UNIQUE）

### 9.2 password
* 长度：6-16
* 允许字符：字母/数字
* 正则：`^[A-Za-z0-9]{6,16}$`
* 密码加密必须使用 BCrypt：
  * 使用配置常量 `BCRYPT_COST=10`（实现时可通过后端配置读取，但不得漏用 BCrypt）
  * 注册/更新时：将客户端 password 通过 BCrypt 生成 hash，写入 MySQL `user.password`
  * 登录校验：使用 BCrypt 对比（check）客户端明文与存储 hash

### 9.3 nickname
* 去除首尾空格后长度：1-20
* 允许任意 Unicode 字符，但必须非空且不能全空白

## 10. 速率限制（MVP 默认配置，AI 不得随意改名/漏实现）
对 `POST /api/user/register` 与 `POST /api/user/login` 进行 IP 限流：
* `RATE_LIMIT_REGISTER_IP_MAX=10`（次/分钟）
* `RATE_LIMIT_LOGIN_IP_MAX=20`（次/分钟）

Redis 限流键（固定窗口到分钟）：
* `rl:ip:register:{ip}:{yyyyMMddHHmm}`
* `rl:ip:login:{ip}:{yyyyMMddHHmm}`

触发时返回：
* `429`，`msg="too many requests"`

## 11. 与 PRD 埋点字段的对齐要求
本模块埋点事件必须携带 PRD 公共埋点字段：
* `user_id, phone, token_status, page, room_id, theme, device, network, timestamp`

并触发以下事件（按 PRD）：
* `register_success`
* `login_success`
* `logout_type`（本 MVP：`manual`）
* `edit_type`（本 MVP：`nickname`）

失败分支埋点：
* `error_type`：按 PRD 枚举填 `auth/network/db/websocket`
* `api_name`：填具体接口名，如 `user/login`、`user/profile/nickname`

## 12. 额外接口：昵称更新（用于 AI 生成实现）
### PUT /api/user/profile/nickname
请求头：Authorization
请求：
{
  "nickname": "新的昵称"
}
响应：
{
  "code": 200,
  "msg": "昵称更新成功",
  "data": { "user_id": "", "nickname": "" }
}
错误：
* 400：nickname 格式不合法
* 401：缺少/无效 Token
* 403：越权更新
* 429：触发速率限制
* 500：数据库错误

## 13. 与项目结构目录的对应关系（用于落地开发）
> **说明**：若与本仓库 [`项目结构.txt`](../项目结构.txt) 中的路径表述不一致，以实现工程目录 `project/` 下的相对路径为准（如 `project/backend/controllers/user_controller.py`）。

* 路由入口：`backend/controllers/user_controller.py`
* 业务逻辑：`backend/services/user_service.py`
* JWT/鉴权工具：`backend/utils/auth.py`
* Redis 操作封装：`backend/utils/cache.py`
* 数据层模型：`backend/models/user.py`

## 14. 注册默认昵称与头像生成规则（用于避免歧义）
注册成功时，后端必须写入：
* 默认昵称：`用户{phone 最后4位}`
* 默认头像：使用配置常量 `DEFAULT_AVATAR_URL`（写入 `user.avatar`，内容为 URL 字符串）

并保证注册 API 返回：
* `data.user_id`
* `data.token`
