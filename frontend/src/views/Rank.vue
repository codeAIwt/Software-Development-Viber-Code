<script setup>
import { ref, onMounted } from 'vue';
import * as durationApi from '../api/duration';
import { useUiStore } from '../store';

const ui = useUiStore();
const loading = ref(false);
const rankList = ref([]);
const currentDate = ref(new Date().toISOString().split('T')[0]);

async function loadRankList() {
  loading.value = true;
  try {
    const { data } = await durationApi.getRankList(currentDate.value);
    if (data.code === 200) {
      rankList.value = data.data;
    } else {
      ui.showToast(data.msg || '获取排行榜失败');
    }
  } catch (error) {
    ui.showToast(error.response?.data?.msg || error.message || '获取排行榜失败');
  } finally {
    loading.value = false;
  }
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

onMounted(() => {
  loadRankList();
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
          @change="loadRankList"
        />
      </div>
    </div>

    <div class="card">
      <h3>排行榜</h3>
      <div class="rank-list" v-if="!loading">
        <div v-if="rankList.length === 0" class="empty">
          <p>暂无数据</p>
        </div>
        <div v-else class="rank-item" v-for="(item, index) in rankList" :key="item.user_id">
          <div class="rank-number">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="user-id">{{ item.user_id }}</div>
            <div class="duration-info">
              <span class="total-minutes">{{ item.total_minutes }} 分钟</span>
              <span class="beat-percent">击败 {{ item.beat_percent }}% 用户</span>
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
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

h2 {
  margin: 0;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-selector input {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #e6eaf2;
  border-radius: 10px;
  background: #f9fafb;
}

.rank-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #3b82f6;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 12px;
}

.rank-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-id {
  font-weight: 500;
}

.duration-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.total-minutes {
  font-size: 14px;
  color: #6b7280;
}

.beat-percent {
  font-size: 12px;
  color: #10b981;
  font-weight: 600;
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