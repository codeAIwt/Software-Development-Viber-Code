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