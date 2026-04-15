/**
 * 自习室：创建 / 列表 / 加入 / 退出
 * 契约与 ``详细设计/RoomCreateAttend.md`` §11 一致；需携带 Bearer Token。
 */
import axios from "axios";
import { clearToken, getToken } from "../utils/auth";

const client = axios.create({
  baseURL: "/api",
  timeout: 20000,
});

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    if (status === 401) {
      clearToken();
    }
    return Promise.reject(err);
  }
);

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