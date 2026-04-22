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
  margin-bottom: 16px;
}

h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.card {
  margin-bottom: 18px;
  padding: 18px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e6eaf2;
  box-shadow: 0 2px 8px rgba(28, 37, 51, 0.03);
}

.personal-info {
  background: #e8f5e9;
  color: #1b4332;
  border: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.personal-info h3 {
  color: #1b4332;
  margin-bottom: 16px;
  font-weight: 600;
}

.personal-duration {
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  opacity: 0.9;
}

.duration-item .value {
  font-weight: 700;
  font-size: 1.05em;
}

.no-record {
  text-align: center;
  padding: 20px;
}

.no-record p {
  margin: 0;
  font-size: 1.05em;
  font-weight: 500;
}

.no-record .hint {
  font-size: 0.9em;
  opacity: 0.8;
  margin-top: 8px;
  font-weight: 400;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.empty .hint {
  font-size: 0.9em;
  opacity: 0.8;
  margin-top: 8px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e6eaf2;
  transition: all 0.2s ease;
}

.rank-item:hover {
  border-color: #d0d5e3;
  box-shadow: 0 4px 16px rgba(28, 37, 51, 0.06);
  transform: translateY(-1px);
}

.rank-item:has(.top-1) {
  border-left: 3px solid #f9a825;
}
.rank-item:has(.top-2) {
  border-left: 3px solid #bdbdbd;
}
.rank-item:has(.top-3) {
  border-left: 3px solid #a1887f;
}

.rank-item:last-child {
  margin-bottom: 0;
}

.rank-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #6c757d;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  margin-right: 14px;
  flex-shrink: 0;
}

.rank-number.top-1 {
  background: #f9a825;
  color: #fff;
  box-shadow: 0 2px 8px rgba(249, 168, 37, 0.3);
  width: 42px;
  height: 42px;
  font-size: 16px;
}

.rank-number.top-2 {
  background: #bdbdbd;
  color: #fff;
  width: 40px;
  height: 40px;
  font-size: 15px;
}

.rank-number.top-3 {
  background: #a1887f;
  color: #fff;
  width: 38px;
  height: 38px;
  font-size: 14px;
}

.rank-info {
  flex: 1;
  min-width: 0;
}

.user-id {
  font-weight: 600;
  margin-bottom: 4px;
  color: #1c2533;
}

.duration-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6b7280;
  gap: 8px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-selector label {
  font-weight: 500;
  font-size: 14px;
}

.date-selector input {
  padding: 8px 12px;
  border: 1px solid #d7dbe4;
  border-radius: 10px;
  font-size: 14px;
  background: #f9fafb;
  transition: all 0.2s ease;
}

.date-selector input:focus {
  outline: none;
  border-color: #2d6a4f;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}

.personal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.personal-header h3 {
  margin: 0;
  color: #1b4332;
  font-weight: 600;
}

.btn-refresh {
  padding: 6px 14px;
  border: 1px solid #2d6a4f;
  border-radius: 10px;
  background: #fff;
  color: #2d6a4f;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: #2d6a4f;
  color: #fff;
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>