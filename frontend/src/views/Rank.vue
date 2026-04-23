<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import * as durationApi from '../api/duration';
import { useUiStore } from '../store';

const ui = useUiStore();
const loading = ref(false);
const rankList = ref([]);
const currentDate = ref(new Date().toISOString().split('T')[0]);
const personalDuration = ref({});
const updateInterval = ref(null);
const activeTab = ref('today');

// 超参数：更新间隔（5分钟）
const UPDATE_INTERVAL = 5 * 60 * 1000;

// 计算属性：是否有个人学习记录
const hasPersonalRecord = computed(() => {
  return personalDuration.value && personalDuration.value.total_minutes > 0;
});

// 计算属性：格式化学习时长
const formattedDuration = computed(() => {
  if (!hasPersonalRecord.value) return { value: 0, unit: '分钟' };
  const hours = Math.floor(personalDuration.value.total_minutes / 60);
  const minutes = personalDuration.value.total_minutes % 60;
  if (hours > 0) {
    return { value: hours, unit: '小时', extra: `${minutes}分钟` };
  }
  return { value: minutes, unit: '分钟' };
});

// 计算最大学习时长（用于进度条）
const maxDuration = computed(() => {
  if (rankList.value.length === 0) return 0;
  return Math.max(...rankList.value.map(item => item.total_minutes));
});

// 计算个人排名
const personalRank = computed(() => {
  if (!personalDuration.value?.user_id) return null;
  const index = rankList.value.findIndex(item => item.user_id === personalDuration.value.user_id);
  return index >= 0 ? index + 1 : null;
});

// 格式化时长
function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0) {
    return `${hours}小时${mins}分钟`;
  }
  return `${mins}分钟`;
}

async function loadPersonalDuration() {
  try {
    const { data } = await durationApi.getDailyDuration(currentDate.value);
    if (data.code === 200) {
      personalDuration.value = data.data;
    }
  } catch (error) {
    console.error('获取个人学习时长失败:', error);
    personalDuration.value = {
      total_minutes: 0,
      beat_percent: null
    };
  }
}

async function loadRankList() {
  loading.value = true;
  try {
    const { data } = await durationApi.getRankList(currentDate.value);
    if (data.code === 200) {
      rankList.value = data.data;
    } else {
      ui.showToast(data.msg || '获取排行榜失败');
      rankList.value = [];
    }
  } catch (error) {
    console.error('获取排行榜失败:', error);
    ui.showToast(error.response?.data?.msg || error.message || '获取排行榜失败');
    rankList.value = [];
  } finally {
    loading.value = false;
  }
}

// 手动刷新数据
async function refreshData() {
  await loadAllData();
  ui.showToast('数据已刷新');
  restartAutoUpdate();
}

async function loadAllData() {
  await Promise.all([
    loadPersonalDuration(),
    loadRankList()
  ]);
}

// Tab 切换
function switchTab(tab) {
  activeTab.value = tab;
  // TODO: 后续接入周/月排行数据
}

// 启动定时更新
function startAutoUpdate() {
  stopAutoUpdate();
  updateInterval.value = setInterval(() => {
    loadAllData();
  }, UPDATE_INTERVAL);
}

// 停止定时更新
function stopAutoUpdate() {
  if (updateInterval.value) {
    clearInterval(updateInterval.value);
    updateInterval.value = null;
  }
}

// 重新启动自动更新
function restartAutoUpdate() {
  stopAutoUpdate();
  startAutoUpdate();
}

onMounted(() => {
  loadAllData();
  startAutoUpdate();
});

onUnmounted(() => {
  stopAutoUpdate();
});
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
      <h2>学习排行榜</h2>
      <button class="refresh-btn" @click="refreshData" :disabled="loading">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }">
          <path d="M23 4v6h-6"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
      </button>
    </header>

    <!-- 时间 Tab -->
    <div class="tabs">
      <button 
        class="tab" 
        :class="{ active: activeTab === 'today' }"
        @click="switchTab('today')"
      >
        今日
      </button>
      <button 
        class="tab" 
        :class="{ active: activeTab === 'week' }"
        @click="switchTab('week')"
        disabled
      >
        本周
      </button>
      <button 
        class="tab" 
        :class="{ active: activeTab === 'month' }"
        @click="switchTab('month')"
        disabled
      >
        本月
      </button>
    </div>

    <!-- 日期选择 -->
    <div class="date-card">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      <input 
        type="date" 
        id="study-date" 
        v-model="currentDate" 
        @change="loadAllData"
      />
    </div>

    <!-- 个人学习时长信息卡片 -->
    <div class="personal-card animate-item">
      <div class="personal-header">
        <div class="personal-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
          </svg>
        </div>
        <div class="personal-title">
          <h3>我的学习</h3>
          <span class="personal-rank" v-if="personalRank">
            排名第 {{ personalRank }} 名
          </span>
        </div>
      </div>

      <div v-if="hasPersonalRecord" class="personal-stats">
        <div class="stat-item main">
          <span class="stat-value">{{ formattedDuration.value }}</span>
          <span class="stat-unit">{{ formattedDuration.unit }}</span>
          <span v-if="formattedDuration.extra" class="stat-extra">{{ formattedDuration.extra }}</span>
        </div>
        <div class="stat-item" v-if="personalDuration.beat_percent !== null">
          <div class="beat-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <span>击败 {{ personalDuration.beat_percent }}%</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-personal">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12,6 12,12 16,14"/>
        </svg>
        <p>今日暂无学习记录</p>
        <router-link to="/study-room" class="go-study">去自习室学习</router-link>
      </div>
    </div>

    <!-- 排行榜列表 -->
    <div class="rank-section">
      <div class="section-header">
        <h3>学习时长榜</h3>
        <span class="hint">每5分钟自动更新</span>
      </div>

      <!-- 加载中骨架屏 -->
      <div v-if="loading" class="rank-list">
        <div v-for="i in 5" :key="i" class="rank-item skeleton-item">
          <div class="skeleton rank-num-skeleton"></div>
          <div class="skeleton avatar-skeleton"></div>
          <div class="skeleton-content">
            <div class="skeleton text-skeleton"></div>
            <div class="skeleton bar-skeleton"></div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="rankList.length === 0" class="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <line x1="18" y1="20" x2="18" y2="10"/>
          <line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
        <p class="empty-title">暂无学习记录</p>
        <p class="empty-desc">今天还没有人开始学习哦</p>
      </div>

      <!-- 排行列表 -->
      <div v-else class="rank-list">
        <div 
          v-for="(item, index) in rankList" 
          :key="item.user_id" 
          class="rank-item animate-item"
          :class="{ 
            'top-1': index === 0, 
            'top-2': index === 1, 
            'top-3': index === 2,
            'is-me': item.user_id === personalDuration.user_id
          }"
          :style="{ animationDelay: `${index * 0.05}s` }"
        >
          <!-- 排名 -->
          <div class="rank-num" :class="{ 'medal': index < 3 }">
            <svg v-if="index === 0" width="24" height="24" viewBox="0 0 24 24" fill="#f9a825">
              <path d="M12 2L9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
            </svg>
            <svg v-else-if="index === 1" width="24" height="24" viewBox="0 0 24 24" fill="#9e9e9e">
              <path d="M12 2L9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
            </svg>
            <svg v-else-if="index === 2" width="24" height="24" viewBox="0 0 24 24" fill="#a1887f">
              <path d="M12 2L9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
            </svg>
            <span v-else>{{ index + 1 }}</span>
          </div>

          <!-- 头像 -->
          <div class="rank-avatar">
            {{ (item.nickname || item.user_id || '?').toString().charAt(0).toUpperCase() }}
          </div>

          <!-- 信息 -->
          <div class="rank-info">
            <div class="rank-name">
              <span>{{ item.nickname || `用户${item.user_id}` }}</span>
              <span v-if="item.user_id === personalDuration.user_id" class="me-badge">我</span>
            </div>
            <div class="rank-progress">
              <div 
                class="progress-bar"
                :style="{ width: maxDuration ? `${(item.total_minutes / maxDuration) * 100}%` : '0%' }"
              ></div>
            </div>
          </div>

          <!-- 时长 -->
          <div class="rank-duration">
            <span class="duration-value">{{ formatDuration(item.total_minutes) }}</span>
            <span class="beat-text">击败 {{ item.beat_percent }}%</span>
          </div>
        </div>
      </div>
    </div>
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

.refresh-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6b7280);
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-primary, #2d6a4f);
  color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn .spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Tabs */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 12px;
  padding: 6px;
  border: 1px solid var(--color-border, #e6eaf2);
}

.tab {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-muted, #6b7280);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab:hover:not(:disabled) {
  background: var(--color-bg, #f6f7fb);
}

.tab.active {
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.2);
}

.tab:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 日期选择 */
.date-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 12px;
  margin-bottom: 16px;
}

.date-card svg {
  color: var(--color-text-muted, #6b7280);
}

.date-card input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text, #1c2533);
  cursor: pointer;
}

.date-card input:focus {
  outline: none;
  box-shadow: none;
}

/* 个人卡片 */
.personal-card {
  background: linear-gradient(135deg, var(--color-primary, #2d6a4f) 0%, var(--color-primary-light, #40916c) 100%);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  color: #fff;
}

.personal-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.personal-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.personal-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.personal-rank {
  font-size: 13px;
  opacity: 0.85;
}

.personal-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.stat-item.main {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-value {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
}

.stat-unit {
  font-size: 18px;
  opacity: 0.9;
}

.stat-extra {
  font-size: 14px;
  opacity: 0.8;
}

.beat-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  font-size: 14px;
  font-weight: 600;
}

.beat-badge svg {
  color: #ffd700;
}

.empty-personal {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  text-align: center;
}

.empty-personal svg {
  opacity: 0.6;
}

.empty-personal p {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

.go-study {
  margin-top: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
}

.go-study:hover {
  background: rgba(255, 255, 255, 0.3);
  text-decoration: none;
}

/* 排行榜区域 */
.rank-section {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 20px;
  padding: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}

.hint {
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
}

/* 骨架屏 */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
}

.rank-num-skeleton {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.avatar-skeleton {
  width: 44px;
  height: 44px;
  border-radius: 12px;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.text-skeleton {
  width: 100px;
  height: 14px;
}

.bar-skeleton {
  width: 100%;
  height: 6px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 20px;
  text-align: center;
}

.empty-state svg {
  color: var(--color-border-light, #d7dbe4);
}

.empty-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.empty-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
}

/* 排行列表 */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--color-bg, #f6f7fb);
  transition: all 0.2s ease;
}

.rank-item:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.rank-item.top-1 {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
}

.rank-item.top-2 {
  background: linear-gradient(135deg, #f5f5f5 0%, #e5e5e5 100%);
  border: 1px solid #d4d4d4;
}

.rank-item.top-3 {
  background: linear-gradient(135deg, #fef3e2 0%, #fed7aa 100%);
  border: 1px solid #fdba74;
}

.rank-item.is-me {
  border: 2px solid var(--color-primary, #2d6a4f);
}

.rank-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-border, #e6eaf2);
  color: var(--color-text-muted, #6b7280);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.rank-num.medal {
  background: transparent;
}

.rank-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.rank-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.me-badge {
  padding: 2px 8px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.rank-progress {
  height: 6px;
  background: rgba(45, 106, 79, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary, #2d6a4f) 0%, var(--color-primary-light, #40916c) 100%);
  border-radius: 3px;
  transition: width 0.6s ease;
}

.rank-duration {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.duration-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text, #1c2533);
}

.beat-text {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
}

/* 响应式 */
@media (max-width: 640px) {
  .wrap {
    padding: 20px 16px 32px;
  }
  
  .stat-value {
    font-size: 36px;
  }
  
  .rank-item {
    flex-wrap: wrap;
  }
  
  .rank-info {
    flex: 1 1 calc(100% - 100px);
  }
  
  .rank-duration {
    flex: 1 1 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed var(--color-border, #e6eaf2);
  }
}
</style>
