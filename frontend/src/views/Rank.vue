<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import * as durationApi from '../api/duration';
import * as roomApi from '../api/studyRoom';
import { useUiStore } from '../store';

const ui = useUiStore();
const loading = ref(false);
const rankList = ref([]);
const currentDate = ref(new Date().toISOString().split('T')[0]);
const personalDuration = ref({});
const roomInfo = ref({});
const updateInterval = ref(null);

// 超参数：更新间隔（5分钟）
const UPDATE_INTERVAL = 5 * 60 * 1000; // 5分钟

// 计算属性：是否有个人学习记录
const hasPersonalRecord = computed(() => {
  return personalDuration.value && personalDuration.value.total_minutes > 0;
});

// 计算属性：格式化学习时长
const formattedDuration = computed(() => {
  if (!hasPersonalRecord.value) return '0分钟';
  const hours = Math.floor(personalDuration.value.total_minutes / 60);
  const minutes = personalDuration.value.total_minutes % 60;
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  }
  return `${minutes}分钟`;
});

async function loadPersonalDuration() {
  try {
    const { data } = await durationApi.getDailyDuration(currentDate.value);
    if (data.code === 200) {
      personalDuration.value = data.data;
      
      // 如果有学习记录，尝试获取房间信息
      if (data.data.total_minutes > 0) {
        await loadRoomInfo();
      }
    }
  } catch (error) {
    console.error('获取个人学习时长失败:', error);
    personalDuration.value = {
      total_minutes: 0,
      beat_percent: null
    };
  }
}

async function loadRoomInfo() {
  try {
    // 这里需要根据实际情况获取房间信息
    // 暂时使用模拟数据
    roomInfo.value = {
      room_id: 'room_001',
      theme: '考研自习室',
      study_time: personalDuration.value.total_minutes
    };
  } catch (error) {
    console.error('获取房间信息失败:', error);
    roomInfo.value = {};
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
  
  // 刷新后重新启动5分钟计时
  restartAutoUpdate();
}

async function loadAllData() {
  await Promise.all([
    loadPersonalDuration(),
    loadRankList()
  ]);
}

// 启动定时更新
function startAutoUpdate() {
  stopAutoUpdate(); // 先停止现有的定时器
  updateInterval.value = setInterval(() => {
    loadAllData();
    ui.showToast('数据已自动更新');
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
    <header class="bar">
      <router-link to="/home">返回首页</router-link>
      <h2>学习时长排行榜</h2>
    </header>

    <div class="card">
      <div class="date-selector">
        <label for="study-date">选择日期：</label>
        <input 
          type="date" 
          id="study-date" 
          v-model="currentDate" 
          @change="loadAllData"
        />
      </div>
    </div>

    <!-- 个人学习时长信息卡片 -->
    <div class="card personal-info">
      <div class="personal-header">
        <h3>我的学习时长</h3>
        <button class="btn-refresh" @click="refreshData" :disabled="loading">
          <span v-if="loading">刷新中...</span>
          <span v-else>刷新</span>
        </button>
      </div>
      <div v-if="hasPersonalRecord" class="personal-duration">
        <div class="duration-item">
          <span class="label">学习时长：</span>
          <span class="value">{{ formattedDuration }}</span>
        </div>
        <div v-if="roomInfo.room_id" class="duration-item">
          <span class="label">房间ID：</span>
          <span class="value">{{ roomInfo.room_id }}</span>
        </div>
        <div v-if="roomInfo.theme" class="duration-item">
          <span class="label">房间主题：</span>
          <span class="value">{{ roomInfo.theme }}</span>
        </div>
        <div v-if="personalDuration.beat_percent !== null" class="duration-item">
          <span class="label">击败百分比：</span>
          <span class="value">{{ personalDuration.beat_percent }}%</span>
        </div>
      </div>
      <div v-else class="no-record">
        <p>暂无学习记录</p>
        <p class="hint">快去自习室开始学习吧！</p>
      </div>
    </div>

    <!-- 排行榜卡片 -->
    <div class="card">
      <h3>学习时长排行榜</h3>
      <div class="rank-list" v-if="!loading">
        <div v-if="rankList.length === 0" class="empty">
          <p>暂无学习记录</p>
          <p class="hint">今天还没有人开始学习哦</p>
        </div>
        <div v-else class="rank-item" v-for="(item, index) in rankList" :key="item.user_id">
          <div class="rank-number" :class="{ 'top-1': index === 0, 'top-2': index === 1, 'top-3': index === 2 }">
            {{ index + 1 }}
          </div>
          <div class="rank-info">
            <div class="user-id">用户ID: {{ item.user_id }}</div>
            <div class="duration-info">
              <span class="total-minutes">总时长: {{ item.total_minutes }} 分钟</span>
              <span class="beat-percent">击败了 {{ item.beat_percent }}% 的用户</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="loading">
        <p>加载中...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 18px;
}

.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

h2 {
  margin: 0;
}

.card {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.personal-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.personal-info h3 {
  color: white;
  margin-bottom: 16px;
}

.personal-duration {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.duration-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.duration-item:last-child {
  border-bottom: none;
}

.duration-item .label {
  font-weight: 500;
}

.duration-item .value {
  font-weight: 600;
  font-size: 1.1em;
}

.no-record {
  text-align: center;
  padding: 20px;
}

.no-record p {
  margin: 0;
  font-size: 1.1em;
}

.no-record .hint {
  font-size: 0.9em;
  opacity: 0.8;
  margin-top: 8px;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty .hint {
  font-size: 0.9em;
  opacity: 0.8;
  margin-top: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #e9ecef;
}

.rank-item:last-child {
  margin-bottom: 0;
}

.rank-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #6c757d;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 12px;
}

.rank-number.top-1 {
  background: #ffd700;
  color: #333;
}

.rank-number.top-2 {
  background: #c0c0c0;
}

.rank-number.top-3 {
  background: #cd7f32;
}

.rank-info {
  flex: 1;
}

.user-id {
  font-weight: 500;
  margin-bottom: 4px;
}

.duration-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9em;
  color: #666;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-selector label {
  font-weight: 500;
}

.date-selector input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
}

.personal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.personal-header h3 {
  margin: 0;
  color: white;
}

.btn-refresh {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.8);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rank-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.rank-number {
  font-size: 1.5rem;
  font-weight: bold;
}

.rank-info {
  display: flex;
  flex-direction: column;
}

.duration-info {
  display: flex;
  gap: 8px;
  font-size: 0.9rem;
  color: #666;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: #6b7280;
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: #6b7280;
}
</style>