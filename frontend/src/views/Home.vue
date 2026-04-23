<script setup>
import { onMounted, ref, computed, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import * as durationApi from "../api/duration";
import { clearToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();
const profile = ref(null);
const loading = ref(true);
const todayDuration = ref(0);
const beatPercent = ref(null);
const studyDays = ref(0);
const hitokoto = ref("");
const hitokotoLoading = ref(false);

// 动态问候语
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了，注意休息";
  if (hour < 9) return "早上好，开始学习吧";
  if (hour < 12) return "上午好，保持专注";
  if (hour < 14) return "中午好，适当休息";
  if (hour < 18) return "下午好，继续加油";
  if (hour < 22) return "晚上好，充实的一天";
  return "夜深了，早点休息";
});

// 当前日期
const currentDate = computed(() => {
  const now = new Date();
  const weekDays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const weekDay = weekDays[now.getDay()];
  return `${month}月${day}日 ${weekDay}`;
});

// 格式化学习时长
const formattedDuration = computed(() => {
  const hours = Math.floor(todayDuration.value / 60);
  const minutes = todayDuration.value % 60;
  if (hours > 0) {
    return { value: hours, unit: "小时", extra: `${minutes}分钟` };
  }
  return { value: minutes, unit: "分钟", extra: "" };
});

// 数字动画
const animatedDuration = ref(0);
function animateNumber(target, duration = 1000) {
  const startTime = performance.now();
  const startValue = 0;
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // 缓动函数
    const easeOutQuart = 1 - Math.pow(1 - progress, 4);
    animatedDuration.value = Math.floor(easeOutQuart * target);
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  requestAnimationFrame(update);
}

async function load() {
  loading.value = true;
  try {
    const [profileRes, durationRes] = await Promise.all([
      userApi.fetchProfile(),
      durationApi.getDailyDuration(new Date().toISOString().split("T")[0]).catch(() => null)
    ]);
    
    if (profileRes.data.code === 200) {
      profile.value = profileRes.data.data;
    }
    
    if (durationRes?.data?.code === 200) {
      todayDuration.value = durationRes.data.data.total_minutes || 0;
      beatPercent.value = durationRes.data.data.beat_percent;
      animateNumber(todayDuration.value);
    }
  } catch {
    ui.showToast("加载用户信息失败");
  } finally {
    loading.value = false;
  }
}

// 获取一言
async function fetchHitokoto() {
  hitokotoLoading.value = true;
  try {
    const res = await fetch("https://v1.hitokoto.cn/?c=k&encode=json");
    const data = await res.json();
    hitokoto.value = data.hitokoto;
  } catch {
    hitokoto.value = "学习是最好的投资，坚持就是最大的天赋。";
  } finally {
    hitokotoLoading.value = false;
  }
}

onMounted(() => {
  load();
  fetchHitokoto();
});

async function onLogout() {
  try {
    await userApi.logout();
  } catch {
    /* 仍清理本地态 */
  } finally {
    clearToken();
    await router.replace("/login");
  }
}
</script>

<template>
  <div class="wrap">
    <!-- 顶部导航 -->
    <header class="top">
      <div class="brand">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#2d6a4f"/>
            <path d="M8 22V10h4v12H8zm6-8v8h4v-8h-4zm6-4v12h4V10h-4z" fill="white"/>
          </svg>
        </div>
        <div>
          <h2>线上伴学</h2>
          <p class="tagline">安静专注，云端相伴</p>
        </div>
      </div>
      <nav class="nav">
        <router-link to="/personal" class="nav-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
          </svg>
          个人中心
        </router-link>
        <button type="button" class="ghost" @click="onLogout">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16,17 21,12 16,7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出
        </button>
      </nav>
    </header>

    <main class="main">
      <!-- 欢迎区域 -->
      <section class="hero card animate-item">
        <div class="hero-content">
          <div class="hero-text">
            <p class="date">{{ currentDate }}</p>
            <h3>{{ greeting }}</h3>
            <p v-if="profile" class="lead">
              {{ profile.nickname }}
            </p>
            <p v-else class="lead skeleton-text" style="width: 120px; height: 24px;"></p>
          </div>
          <div class="hero-avatar" v-if="profile">
            <div class="avatar" :style="{ backgroundImage: profile.avatar ? `url(${profile.avatar})` : 'none' }">
              <span v-if="!profile.avatar">{{ profile.nickname?.charAt(0) || '?' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 数据统计卡片 -->
      <section class="stats-grid">
        <div class="stat-card primary animate-item">
          <div class="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">今日学习</span>
            <div class="stat-value">
              <span class="stat-number">{{ animatedDuration }}</span>
              <span class="stat-unit">{{ formattedDuration.unit }}</span>
            </div>
            <span v-if="formattedDuration.extra" class="stat-extra">{{ formattedDuration.extra }}</span>
          </div>
        </div>
        
        <div class="stat-card secondary animate-item">
          <div class="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">击败用户</span>
            <div class="stat-value">
              <span class="stat-number">{{ beatPercent !== null ? beatPercent : '--' }}</span>
              <span class="stat-unit">%</span>
            </div>
            <span class="stat-extra">继续保持</span>
          </div>
        </div>
      </section>

      <!-- 快捷入口 -->
      <section class="quick-grid">
        <router-link class="tile animate-item" to="/study-room">
          <div class="tile-icon study">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              <line x1="8" y1="6" x2="16" y2="6"/>
              <line x1="8" y1="10" x2="14" y2="10"/>
            </svg>
          </div>
          <div class="tile-info">
            <span class="tile-title">进入自习室</span>
            <span class="tile-desc">开始今日学习</span>
          </div>
          <div class="tile-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9,18 15,12 9,6"/>
            </svg>
          </div>
        </router-link>

        <router-link class="tile animate-item" to="/rank">
          <div class="tile-icon rank">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <div class="tile-info">
            <span class="tile-title">学习排行</span>
            <span class="tile-desc">查看榜单</span>
          </div>
          <div class="tile-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9,18 15,12 9,6"/>
            </svg>
          </div>
        </router-link>

        <router-link class="tile animate-item" to="/personal">
          <div class="tile-icon personal">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="8" r="4"/>
              <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
            </svg>
          </div>
          <div class="tile-info">
            <span class="tile-title">个人中心</span>
            <span class="tile-desc">管理资料</span>
          </div>
          <div class="tile-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9,18 15,12 9,6"/>
            </svg>
          </div>
        </router-link>
      </section>

      <!-- 励志语录 -->
      <section class="quote-card card animate-item">
        <div class="quote-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" opacity="0.3">
            <path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z"/>
          </svg>
        </div>
        <p class="quote-text" :class="{ 'skeleton': hitokotoLoading }">
          {{ hitokotoLoading ? '' : hitokoto }}
        </p>
        <button class="quote-refresh" @click="fetchHitokoto" :disabled="hitokotoLoading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'spinning': hitokotoLoading }">
            <path d="M23 4v6h-6"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>
      </section>
    </main>
  </div>
</template>

<style scoped>
.wrap {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}

/* 动画入场 */
.animate-item {
  opacity: 0;
  animation: fadeInUp 0.5s ease forwards;
}

.animate-item:nth-child(1) { animation-delay: 0s; }
.animate-item:nth-child(2) { animation-delay: 0.1s; }
.animate-item:nth-child(3) { animation-delay: 0.15s; }

.stats-grid .animate-item:nth-child(1) { animation-delay: 0.1s; }
.stats-grid .animate-item:nth-child(2) { animation-delay: 0.15s; }

.quick-grid .animate-item:nth-child(1) { animation-delay: 0.2s; }
.quick-grid .animate-item:nth-child(2) { animation-delay: 0.25s; }
.quick-grid .animate-item:nth-child(3) { animation-delay: 0.3s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 顶部导航 */
.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  flex-shrink: 0;
}

h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: var(--color-text, #1c2533);
}

.tagline {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
}

.nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary, #374151);
  transition: all 0.2s ease;
  text-decoration: none;
}

.nav-link:hover {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
  text-decoration: none;
}

.ghost {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  background: #fff;
  border-radius: 10px;
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  color: var(--color-text-secondary, #374151);
  transition: all 0.2s ease;
}

.ghost:hover {
  border-color: var(--color-error, #ef4444);
  color: var(--color-error, #ef4444);
  background: #fef2f2;
}

/* 主要内容 */
.main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transition: all 0.25s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

/* Hero 区域 */
.hero {
  background: linear-gradient(135deg, var(--color-primary, #2d6a4f) 0%, var(--color-primary-light, #40916c) 100%);
  color: #fff;
  border: none;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.hero-text {
  flex: 1;
}

.date {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 6px;
}

.hero h3 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
}

.lead {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.hero-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 3px solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  background-size: cover;
  background-position: center;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  transition: all 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card.primary {
  background: var(--color-primary-bg, #e8f5e9);
  border-color: transparent;
}

.stat-card.primary .stat-icon {
  background: var(--color-primary, #2d6a4f);
  color: #fff;
}

.stat-card.secondary {
  background: var(--color-secondary-bg, #fff3e0);
  border-color: transparent;
}

.stat-card.secondary .stat-icon {
  background: var(--color-secondary, #f57c00);
  color: #fff;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
  font-weight: 500;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text, #1c2533);
  line-height: 1;
}

.stat-unit {
  font-size: 14px;
  color: var(--color-text-secondary, #374151);
  font-weight: 500;
}

.stat-extra {
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
}

/* 快捷入口网格 */
.quick-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tile {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 16px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--color-text, #1c2533);
  font-weight: 600;
  transition: all 0.2s ease;
  text-decoration: none;
}

.tile:hover {
  border-color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
  box-shadow: var(--shadow-md);
  transform: translateX(4px);
  text-decoration: none;
}

.tile-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tile-icon.study {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
}

.tile-icon.rank {
  background: var(--color-secondary-bg, #fff3e0);
  color: var(--color-secondary, #f57c00);
}

.tile-icon.personal {
  background: #e3f2fd;
  color: #1976d2;
}

.tile-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tile-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.tile-desc {
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
  font-weight: 400;
}

.tile-arrow {
  color: var(--color-text-muted, #6b7280);
  opacity: 0.5;
  transition: all 0.2s ease;
}

.tile:hover .tile-arrow {
  opacity: 1;
  color: var(--color-primary, #2d6a4f);
  transform: translateX(4px);
}

/* 励志语录卡片 */
.quote-card {
  position: relative;
  padding: 24px 56px 24px 24px;
}

.quote-icon {
  position: absolute;
  top: 16px;
  left: 16px;
  color: var(--color-primary, #2d6a4f);
}

.quote-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text-secondary, #374151);
  font-style: italic;
  min-height: 1.7em;
}

.quote-text.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  width: 80%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.quote-refresh {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--color-bg, #f6f7fb);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6b7280);
  transition: all 0.2s ease;
}

.quote-refresh:hover:not(:disabled) {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
}

.quote-refresh:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.quote-refresh .spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 骨架屏 */
.skeleton-text {
  background: linear-gradient(90deg, rgba(255,255,255,0.3) 25%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0.3) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  display: inline-block;
}

/* 响应式布局 */
@media (max-width: 640px) {
  .wrap {
    padding: 20px 16px 32px;
  }
  
  .top {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .brand {
    justify-content: center;
  }
  
  .nav {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .hero h3 {
    font-size: 20px;
  }
  
  .stat-number {
    font-size: 28px;
  }
}
</style>
