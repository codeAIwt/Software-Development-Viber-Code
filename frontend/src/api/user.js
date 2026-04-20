import client from "./client";

export function register(phone, password) {
  return client.post("/user/register", { phone, password });
}

export function login(phone, password) {
  return client.post("/user/login", { phone, password });
}

export function logout() {
  return client.post("/user/logout");
}

export function fetchProfile() {
  return client.get("/user/profile");
}

/**
 * 更新昵称
 */
export function updateNickname(nickname) {
  return client.put("/user/profile/nickname", { nickname });
}

/**
 * 更新标签
 */
export function updateTags(tags) {
  return client.put("/user/profile/tags", { tags });
}

/**
 * 获取用户信息
 */
export function fetchUserInfo(userId) {
  return client.get(`/user/info/${userId}`);
}

/**
 * 获取当前用户信息
 */
export function fetchCurrentUser() {
  return client.get("/user/profile");
}

/**
 * 获取系统配置的标签系统
 */
export function fetchSystemTags() {
  return client.get("/user/tags");
}
