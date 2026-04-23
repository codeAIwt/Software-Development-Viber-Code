<script setup>
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import * as durationApi from "../api/duration";
import { clearToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();
const profile = ref(null);
const nicknameDraft = ref("");
const saving = ref(false);
const showTagsDialog = ref(false);
const selectedTags = ref([]);
const loading = ref(true);

// 学习统计
const todayDuration = ref(0);
const totalDuration = ref(0);
const beatPercent = ref(null);

// 热门标签列表，由系统动态下发
const tags = ref([]);

// 格式化时长
const formattedTodayDuration = computed(() => {
  const hours = Math.floor(todayDuration.value / 60);
  const minutes = todayDuration.value % 60;
  if (hours > 0) return `${hours}小时${minutes}分钟`;
  return `${minutes}分钟`;
});

async function load() {
  loading.value = true;
  try {
    const [profileRes, tagsRes, durationRes] = await Promise.all([
      userApi.fetchProfile(),
      userApi.fetchSystemTags().catch(() => ({ data: { code: 200, data: [] } })),
      durationApi.getDailyDuration(new Date().toISOString().split("T")[0]).catch(() => null)
    ]);

    if (profileRes.data.code !== 200) {
      ui.showToast(profileRes.data.msg || "获取资料失败");
      return;
    }

    profile.value = profileRes.data.data;
    nicknameDraft.value = profileRes.data.data.nickname || "";
    selectedTags.value = profileRes.data.data.tags || [];

    if (tagsRes.data.code === 200) {
      tags.value = tagsRes.data.data;
    }

    if (durationRes?.data?.code === 200) {
      todayDuration.value = durationRes.data.data.total_minutes || 0;
      beatPercent.value = durationRes.data.data.beat_percent;
    }
  } catch (e) {
    ui.showToast("网络错误：无法获取资源");
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function saveNickname() {
  if (!nicknameDraft.value.trim()) {
    ui.showToast("昵称不能为空");
    return;
  }
  saving.value = true;
  try {
    const { data } = await userApi.updateNickname(nicknameDraft.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "保存失败");
      return;
    }
    profile.value = { ...profile.value, nickname: data.data.nickname };
    ui.showToast("昵称已更新");
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "网络错误");
  } finally {
    saving.value = false;
  }
}

async function onLogout() {
  try {
    await userApi.logout();
  } finally {
    clearToken();
    await router.replace("/login");
  }
}

// 打开标签选择弹窗
function openTagsDialog() {
  showTagsDialog.value = true;
}

// 关闭标签选择弹窗
function closeTagsDialog() {
  showTagsDialog.value = false;
}

// 切换标签选择
function toggleTag(tag) {
  const index = selectedTags.value.indexOf(tag);
  if (index > -1) {
    selectedTags.value.splice(index, 1);
  } else {
    selectedTags.value.push(tag);
  }
}

// 保存标签
async function saveTags() {
  saving.value = true;
  try {
    const { data } = await userApi.updateTags(selectedTags.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "保存失败");
      return;
    }
    profile.value = { ...profile.value, tags: selectedTags.value };
    ui.showToast("标签更新成功");
    showTagsDialog.value = false;
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "网络错误");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="wrap">
    <!-- 顶部导航 -->
    <header class="bar">
      <router-link to="/home" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15,18 9,12 15,6"/>
        </svg>
        返回
      </router-link>
      <h2>个人中心</h2>
      <div class="spacer"></div>
    </header>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="profile-header-skeleton">
        <div class="skeleton avatar-lg-skeleton"></div>
        <div class="skeleton-content">
          <div class="skeleton text-lg-skeleton"></div>
          <div class="skeleton text-sm-skeleton"></div>
        </div>
      </div>
      <div class="stats-skeleton">
        <div class="skeleton stat-skeleton"></div>
        <div class="skeleton stat-skeleton"></div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-else-if="profile" class="content">
      <!-- 个人信息卡片 -->
      <section class="profile-header animate-item">
        <div class="profile-bg">
          <svg viewBox="0 0 400 200" preserveAspectRatio="none">
            <defs>
              <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#2d6a4f"/>
                <stop offset="100%" style="stop-color:#40916c"/>
              </linearGradient>
            </defs>
            <rect fill="url(#headerGrad)" width="400" height="200"/>
            <circle cx="350" cy="50" r="80" fill="rgba(255,255,255,0.05)"/>
            <circle cx="50" cy="150" r="60" fill="rgba(255,255,255,0.05)"/>
          </svg>
        </div>
        <div class="profile-content">
          <div class="avatar-wrapper">
            <div class="avatar" :style="{ backgroundImage: profile.avatar ? `url(${profile.avatar})` : 'none' }">
              <span v-if="!profile.avatar">{{ profile.nickname?.charAt(0) || '?' }}</span>
            </div>
            <button class="avatar-edit" title="更换头像">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </button>
          </div>
          <div class="profile-info">
            <h3>{{ profile.nickname }}</h3>
            <p class="phone">{{ profile.phone }}</p>
          </div>
        </div>
      </section>

      <!-- 学习统计 -->
      <section class="stats-grid animate-item">
        <div class="stat-card">
          <div class="stat-icon time">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">今日学习</span>
            <span class="stat-value">{{ formattedTodayDuration }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon rank">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">击败用户</span>
            <span class="stat-value">{{ beatPercent !== null ? `${beatPercent}%` : '--' }}</span>
          </div>
        </div>
      </section>

      <!-- 设置区域 -->
      <section class="settings-section animate-item">
        <!-- 昵称修改 -->
        <div class="setting-item">
          <div class="setting-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            <span>修改昵称</span>
          </div>
          <div class="setting-content">
            <div class="input-group">
              <input 
                v-model="nicknameDraft" 
                maxlength="20" 
                placeholder="请输入昵称"
              />
              <button 
                class="btn-save" 
                :disabled="saving || !nicknameDraft.trim()" 
                @click="saveNickname"
              >
                {{ saving ? "保存中" : "保存" }}
              </button>
            </div>
          </div>
        </div>

        <!-- 学习标签 -->
        <div class="setting-item">
          <div class="setting-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
            <span>学习标签</span>
          </div>
          <div class="setting-content">
            <div class="tags-display">
              <span 
                v-for="(tag, index) in profile.tags" 
                :key="index" 
                class="tag"
                :class="`tag-${index % 4}`"
              >
                {{ tag }}
              </span>
              <button class="tag-add" @click="openTagsDialog">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 更多功能 -->
      <section class="menu-section animate-item">
        <router-link to="/rank" class="menu-item">
          <div class="menu-icon rank">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <span>学习排行榜</span>
          <svg class="arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9,18 15,12 9,6"/>
          </svg>
        </router-link>
        <router-link to="/study-room" class="menu-item">
          <div class="menu-icon study">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <span>自习室</span>
          <svg class="arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9,18 15,12 9,6"/>
          </svg>
        </router-link>
      </section>

      <!-- 退出登录 -->
      <section class="logout-section animate-item">
        <button class="btn-logout" @click="onLogout">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16,17 21,12 16,7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出登录
        </button>
      </section>
    </div>

    <!-- 标签选择弹窗 -->
    <Transition name="dialog">
      <div v-if="showTagsDialog" class="dialog-overlay" @click.self="closeTagsDialog">
        <div class="dialog">
          <div class="dialog-header">
            <h3>选择学习标签</h3>
            <button class="dialog-close" @click="closeTagsDialog">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="dialog-body">
            <div class="tags-select">
              <button
                v-for="tag in tags"
                :key="tag"
                class="tag-option"
                :class="{ active: selectedTags.includes(tag) }"
                @click="toggleTag(tag)"
              >
                {{ tag }}
                <svg v-if="selectedTags.includes(tag)" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="btn-secondary" @click="closeTagsDialog">取消</button>
            <button class="btn-primary" :disabled="saving" @click="saveTags">
              {{ saving ? "保存中..." : "保存" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.wrap {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 18px 40px;
}

/* 动画 */
.animate-item {
  opacity: 0;
  animation: fadeInUp 0.4s ease forwards;
}

.animate-item:nth-child(1) { animation-delay: 0s; }
.animate-item:nth-child(2) { animation-delay: 0.1s; }
.animate-item:nth-child(3) { animation-delay: 0.15s; }
.animate-item:nth-child(4) { animation-delay: 0.2s; }
.animate-item:nth-child(5) { animation-delay: 0.25s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 顶部导航 */
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 10px;
  color: var(--color-text-secondary, #374151);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
  text-decoration: none;
}

h2 {
  flex: 1;
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.spacer {
  width: 80px;
}

/* 骨架屏 */
.skeleton-wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 12px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.profile-header-skeleton {
  height: 180px;
  border-radius: 20px;
  background: linear-gradient(90deg, #e8e8e8 25%, #ddd 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.stats-skeleton {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-skeleton {
  height: 80px;
}

/* 内容区域 */
.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 个人信息头部 */
.profile-header {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
}

.profile-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
}

.profile-bg svg {
  width: 100%;
  height: 100%;
}

.profile-content {
  position: relative;
  padding: 60px 24px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-wrapper {
  position: relative;
}

.avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--color-primary, #2d6a4f);
  border: 4px solid #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  background-size: cover;
  background-position: center;
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--color-border, #e6eaf2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6b7280);
  transition: all 0.2s ease;
}

.avatar-edit:hover {
  border-color: var(--color-primary, #2d6a4f);
  color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
}

.profile-info {
  text-align: center;
}

.profile-info h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text, #1c2533);
}

.phone {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.stat-card {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.time {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
}

.stat-icon.rank {
  background: var(--color-secondary-bg, #fff3e0);
  color: var(--color-secondary, #f57c00);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text, #1c2533);
}

/* 设置区域 */
.settings-section {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 20px;
  overflow: hidden;
}

.setting-item {
  padding: 20px;
  border-bottom: 1px solid var(--color-border, #e6eaf2);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.setting-header svg {
  color: var(--color-text-muted, #6b7280);
}

.input-group {
  display: flex;
  gap: 10px;
}

.input-group input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  background: var(--color-bg-input, #f9fafb);
  font-size: 15px;
  transition: all 0.2s ease;
}

.input-group input:focus {
  outline: none;
  border-color: var(--color-primary, #2d6a4f);
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}

.btn-save {
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-save:hover:not(:disabled) {
  background: var(--color-primary-dark, #1b4332);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 标签显示 */
.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid;
}

.tag-0 {
  background: var(--color-primary-bg, #e8f5e9);
  border-color: #c8e6c9;
  color: var(--color-primary, #2d6a4f);
}

.tag-1 {
  background: var(--color-secondary-bg, #fff3e0);
  border-color: #ffe0b2;
  color: #e65100;
}

.tag-2 {
  background: #fce4ec;
  border-color: #f8bbd0;
  color: #ad1457;
}

.tag-3 {
  background: #e0f2f1;
  border-color: #b2dfdb;
  color: #00695c;
}

.tag-add {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px dashed var(--color-border-light, #d7dbe4);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6b7280);
  transition: all 0.2s ease;
}

.tag-add:hover {
  border-color: var(--color-primary, #2d6a4f);
  border-style: solid;
  color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
}

/* 菜单区域 */
.menu-section {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 20px;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  color: var(--color-text, #1c2533);
  text-decoration: none;
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--color-border, #e6eaf2);
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: var(--color-bg, #f6f7fb);
  text-decoration: none;
}

.menu-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-icon.rank {
  background: var(--color-secondary-bg, #fff3e0);
  color: var(--color-secondary, #f57c00);
}

.menu-icon.study {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
}

.menu-item span {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
}

.arrow {
  color: var(--color-text-muted, #6b7280);
}

/* 退出登录 */
.logout-section {
  padding-top: 8px;
}

.btn-logout {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--color-error, #ef4444);
  border-radius: 14px;
  background: #fff;
  color: var(--color-error, #ef4444);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-logout:hover {
  background: #fef2f2;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.15);
}

/* 弹窗 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  padding: 20px;
}

.dialog {
  background: #fff;
  border-radius: 20px;
  width: min(500px, 100%);
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border, #e6eaf2);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.dialog-close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6b7280);
  transition: all 0.2s ease;
}

.dialog-close:hover {
  background: var(--color-bg, #f6f7fb);
  color: var(--color-text, #1c2533);
}

.dialog-body {
  padding: 24px;
  overflow-y: auto;
}

.tags-select {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 20px;
  background: var(--color-bg-input, #f9fafb);
  color: var(--color-text-secondary, #374151);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-option:hover {
  border-color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
}

.tag-option.active {
  border-color: var(--color-primary, #2d6a4f);
  background: var(--color-primary, #2d6a4f);
  color: #fff;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid var(--color-border, #e6eaf2);
}

.btn-secondary {
  padding: 12px 24px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 12px;
  background: #fff;
  color: var(--color-text-secondary, #374151);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  border-color: var(--color-primary, #2d6a4f);
  color: var(--color-primary, #2d6a4f);
}

.btn-primary {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark, #1b4332);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 弹窗动画 */
.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.3s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .dialog,
.dialog-leave-to .dialog {
  transform: scale(0.95) translateY(20px);
}

/* 响应式 */
@media (max-width: 640px) {
  .wrap {
    padding: 20px 16px 32px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    flex-direction: row;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .btn-save {
    width: 100%;
  }
}
</style>
