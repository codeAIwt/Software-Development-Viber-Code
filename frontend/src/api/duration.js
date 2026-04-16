/** 时长 / 排行榜接口 */
import axios from "axios";
import { getToken } from "../utils/auth";

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

/**
 * GET /api/duration/daily — 获取每日学习时长
 */
export function getDailyDuration(studyDate) {
  const params = studyDate ? { study_date: studyDate } : {};
  return client.get("/duration/daily", { params });
}

/**
 * GET /api/duration/weekly — 获取最近7天学习时长
 */
export function getWeeklyDuration() {
  return client.get("/duration/weekly");
}

/**
 * GET /api/duration/rank — 获取学习时长排行榜
 */
export function getRankList(studyDate, limit = 10) {
  const params = {
    limit,
  };
  if (studyDate) {
    params.study_date = studyDate;
  }
  return client.get("/duration/rank", { params });
}