/**
 * 自习室：创建 / 列表 / 加入 / 退出
 * 契约与 ``详细设计/RoomCreateAttend.md`` §11 一致；需携带 Bearer Token。
 */
import client from "./client";

/**
 * POST /api/room/create — body: { theme,/**
 * 创建自习室
 */
export function createRoom(theme, maxPeople, tags = []) {
  return client.post("/room/create", {
    theme,
    max_people: maxPeople,
    tags
  });
}

/**
 * GET /api/room/list — params: { theme? }
 */
export function listRooms(theme) {
  const params = theme ? { theme } : {};
  return client.get("/room/list", { params });
}

/**
 * POST /api/room/join — body: { room_id, match_type? }
 */
export function joinRoom(roomId, matchType = "manual") {
  return client.post("/room/join", { room_id: roomId, match_type: matchType });
}

/**
 * POST /api/room/leave — body: { room_id }
 */
export function leaveRoom(roomId) {
  return client.post("/room/leave", { room_id: roomId });
}

/**
 * GET /api/room/info/{room_id} — 获取房间信息
 */
export function getRoomInfo(roomId) {
  return client.get(`/room/info/${roomId}`);
}

/**
 * PUT /api/room/update/{room_id} — 更新房间信息
 */
export function updateRoom(roomId, theme) {
  return client.put(`/room/update/${roomId}`, { theme });
}

/**
 * DELETE /api/room/destroy/{room_id} — 销毁房间
 */
export function destroyRoom(roomId) {
  return client.delete(`/room/destroy/${roomId}`);
}

/**
 * POST /api/room/detect-person — 检测摄像头前是否有人
 */
export function detectPerson(image, roomId, userId) {
  return client.post("/room/detect-person", {
    image,
    room_id: roomId,
    user_id: userId
  });
}