/** 时长 / 排行榜接口 */
import client from "./client";

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

/**
 * GET /api/duration/rank/weekly — 获取周排行榜
 */
export function getWeeklyRankList(weekStart, limit = 10) {
  const params = { limit };
  if (weekStart) {
    params.week_start = weekStart;
  }
  return client.get("/duration/rank/weekly", { params });
}

/**
 * GET /api/duration/rank/monthly — 获取月排行榜
 */
export function getMonthlyRankList(year, month, limit = 10) {
  const params = { limit };
  if (year) {
    params.year = year;
  }
  if (month) {
    params.month = month;
  }
  return client.get("/duration/rank/monthly", { params });
}

/**
 * GET /api/duration/period/summary — 获取时间段学习时长汇总
 */
export function getPeriodSummary(period = 'week') {
  return client.get("/duration/period/summary", {
    params: { period }
  });
}