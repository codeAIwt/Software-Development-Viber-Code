<script setup>
import { ref, onMounted } from 'vue';
import * as userApi from '../api/user';

const loading = ref(false);
const checkInStatus = ref(null);
const checking = ref(false);

const weekDays = ['一', '二', '三', '四', '五', '六', '日'];

async function loadStatus() {
  loading.value = true;
  try {
    const { data } = await userApi.getCheckInStatus();
    if (data.code === 200) {
      checkInStatus.value = data.data;
    }
  } catch (e) {
    console.error('获取打卡状态失败', e);
  } finally {
    loading.value = false;
  }
}

async function handleCheckIn() {
  if (checkInStatus.value?.checked_in_today) return;
  checking.value = true;
  try {
    const { data } = await userApi.checkIn();
    if (data.code === 200) {
      await loadStatus();
    }
  } catch (e) {
    console.error('打卡失败', e);
  } finally {
    checking.value = false;
  }
}

onMounted(loadStatus);
</script>

<template>
  <div class="checkin-card">
    <div class="checkin-header">
      <span class="checkin-title">每日打卡</span>
      <span v-if="checkInStatus?.checked_in_today" class="checkin-badge">已打卡</span>
    </div>

    <div class="week-calendar">
      <div class="week-header">
        <span v-for="(day, index) in weekDays" :key="index" class="week-day">{{ day }}</span>
      </div>
      <div class="calendar-grid">
        <div
          v-for="day in checkInStatus?.week_calendar"
          :key="day.date"
          class="calendar-day"
          :class="{
            'checked': day.checked,
            'today': day.is_today
          }"
        >
          <span class="day-text">{{ new Date(day.date).getDate() }}</span>
        </div>
      </div>
    </div>

    <button
      class="checkin-btn"
      :class="{ 'checked': checkInStatus?.checked_in_today }"
      :disabled="checkInStatus?.checked_in_today || checking"
      @click="handleCheckIn"
    >
      {{ checking ? '打卡中...' : (checkInStatus?.checked_in_today ? '✓ 已打卡' : '立即打卡') }}
    </button>
  </div>
</template>

<style scoped>
.checkin-card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 16px;
  padding: 18px;
}

.checkin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.checkin-title {
  font-size: 16px;
  font-weight: 600;
  color: #1c2533;
}

.checkin-badge {
  background: linear-gradient(135deg, #2d6a4f 0%, #40916c 100%);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.week-calendar {
  margin-bottom: 16px;
}

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 8px;
}

.week-day {
  text-align: center;
  font-size: 12px;
  color: #6b7280;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 8px;
  transition: all 0.2s;
}

.calendar-day.checked {
  background: #3b82f6;
}

.calendar-day.today:not(.checked) {
  border: 2px solid #3b82f6;
}

.day-text {
  font-size: 14px;
  font-weight: 500;
  color: #1c2533;
}

.calendar-day.checked .day-text {
  color: #fff;
}

.checkin-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.checkin-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.checkin-btn:disabled {
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.checkin-btn.checked {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}
</style>
