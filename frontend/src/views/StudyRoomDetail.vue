<script setup>
import { useRoute, useRouter } from 'vue-router';
import PrivacyMode from '../components/PrivacyMode.vue';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { getToken } from '../utils/auth';
import * as studyRoomApi from '../api/studyRoom';
import * as userApi from '../api/user';
import { useUiStore } from '../store';

import { useCamera } from '../composables/useCamera';
import { useRoomData } from '../composables/useRoomData';
import { useAiDetection } from '../composables/useAiDetection';
import { useRoomSignaling } from '../composables/useRoomSignaling';

const route = useRoute();
const router = useRouter();
const ui = useUiStore();

// UI state
const leaveLoading = ref(false);
const isLeaving = ref(false);
const videoRef = ref(null);
const canvasRef = ref(null);
const privacyMode = ref('off');
const currentUserId = ref(localStorage.getItem('user_id'));
const privacyModes = [
  { value: 'blur', label: '模糊模式' },
  { value: 'hand', label: '手部遮挡模式' },
  { value: 'off', label: '关闭隐私模式' }
];
const videoVisible = ref(true);

const showThemeDialog = ref(false);
const newTheme = ref('');
const updatingTheme = ref(false);
const showDestroyDialog = ref(false);
const destroying = ref(false);
const showDurationDialog = ref(false);
const studyDuration = ref(0);

// time
const joinTime = ref(Date.now());
const currentTime = ref(Date.now());
const timer = ref(null);

// room data (API + polling)
const {
  roomInfo,
  userInfoMap,
  loadingUserInfo,
  creatorInfo,
  loadingCreatorInfo,
  fetchRoomInfo,
  startPolling,
  stopPolling,
  leaveRoom,
  updateRoom,
  destroyRoom: destroyRoomApi,
} = useRoomData();

// camera composable
const {
  localStream,
  cameraOn,
  cameraError,
  cameraLoading,
  initCamera,
  stopCamera,
  applyPrivacyMode,
} = useCamera(videoRef, canvasRef, privacyMode);

// signaling (websocket + webRTC)
const { videoStreams, peerConnections, connectRoom, closeRoom, sendSignal, cleanupPeerConnections } = useRoomSignaling(() => localStream.value);

// AI detection (will call onLeave when no person detected)
const ai = useAiDetection({
  videoRef,
  enabled: true,
  intervalMs: 63000,
  detectFn: studyRoomApi.detectPerson,
  roomIdGetter: () => route.params.id,
  userIdGetter: () => currentUserId.value,
  onNoPerson: async () => { await onLeave(); },
});

// computed
const videoGridClass = computed(() => {
  const count = roomInfo.value.users.length;
  if (count === 1) return 'video-grid-1';
  if (count === 2) return 'video-grid-2';
  if (count === 3 || count === 4) return 'video-grid-4';
  if (count === 5 || count === 6) return 'video-grid-6';
  return 'video-grid-8';
});

const isCreator = computed(() => currentUserId.value === roomInfo.value.creator_id);

const roomDuration = computed(() => {
  if (!roomInfo.value.created_ts_ms) return '00:00';
  const duration = currentTime.value - parseInt(roomInfo.value.created_ts_ms);
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
});

const userDuration = computed(() => {
  const duration = currentTime.value - joinTime.value;
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
});

const joinTimeStr = computed(() => new Date(joinTime.value).toLocaleString());
const createTimeStr = computed(() => (roomInfo.value.created_ts_ms ? new Date(parseInt(roomInfo.value.created_ts_ms)).toLocaleString() : '未知'));

function toggleVideo() { videoVisible.value = !videoVisible.value; }
function changePrivacyMode(mode) { privacyMode.value = mode; applyPrivacyMode(); }

async function onLeave() {
  if (isLeaving.value) return;
  isLeaving.value = true;
  const roomId = route.params.id;
  leaveLoading.value = true;
  try {
    ai.stop();
    stopPolling();
    stopCamera();
    const res = await leaveRoom(roomId);
    const data = res.data;
    if (data.code !== 200) {
      ui.showToast(data.msg || '退出失败');
      return;
    }
    studyDuration.value = data.data.study_duration;
    showDurationDialog.value = true;
    setTimeout(() => router.push('/study-room'), 3000);
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || '退出失败');
  } finally {
    leaveLoading.value = false;
  }
}

function openThemeDialog() { newTheme.value = roomInfo.value.theme; showThemeDialog.value = true; }
function closeThemeDialog() { showThemeDialog.value = false; }

async function updateTheme() {
  if (!newTheme.value) { ui.showToast('请选择主题'); return; }
  updatingTheme.value = true;
  try {
    console.debug('[StudyRoomDetail] updateTheme: sending update', { roomId: route.params.id, theme: newTheme.value });
    const { data } = await updateRoom(route.params.id, newTheme.value);
    console.debug('[StudyRoomDetail] updateTheme: response', data);
    if (data.code === 200) {
      Object.assign(roomInfo.value, data.data);
      ui.showToast('主题修改成功');
      closeThemeDialog();
    } else ui.showToast(data.msg || '修改失败');
  } catch (e) {
    console.error('[StudyRoomDetail] updateTheme error', e);
    ui.showToast(e.response?.data?.msg || e.message || '修改失败');
  } finally { updatingTheme.value = false; }
}

function openDestroyDialog() { showDestroyDialog.value = true; }
function closeDestroyDialog() { showDestroyDialog.value = false; }

async function destroyRoom() {
  destroying.value = true;
  try {
    console.debug('[StudyRoomDetail] destroyRoom: sending destroy', { roomId: route.params.id });
    stopPolling();
    const { data } = await destroyRoomApi(route.params.id);
    console.debug('[StudyRoomDetail] destroyRoom: response', data);
    if (data.code === 200) {
      stopCamera();
      ui.showToast('房间已销毁');
      router.push('/study-room');
    } else ui.showToast(data.msg || '销毁失败');
  } catch (e) {
    console.error('[StudyRoomDetail] destroyRoom error', e);
    ui.showToast(e.response?.data?.msg || e.message || '销毁失败');
  } finally { destroying.value = false; closeDestroyDialog(); }
}

async function fetchCurrentUserInfo() {
  try {
    const { data } = await userApi.fetchCurrentUser();
    if (data.code === 200) {
      // 后端返回字段为 user_id
      localStorage.setItem('user_id', data.data.user_id);
      currentUserId.value = data.data.user_id;
    }
  } catch (e) { console.error('获取当前用户信息失败:', e); }
}

// beforeunload handler
async function handleBeforeUnload() {
  try {
    const roomId = route.params.id;
    const token = getToken();
    if (!roomId) return;
    
    // 停止所有组件
    stopPolling();
    stopCamera();
    closeRoom();
    cleanupPeerConnections();
    
    // 使用同步XMLHttpRequest确保请求能发送出去
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/room/leave', false); // 同步请求
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.send(JSON.stringify({ room_id: roomId }));
    } catch (err) {
      console.error('同步离开请求失败:', err);
      // 备用方案：使用navigator.sendBeacon
      try {
        const blob = new Blob([JSON.stringify({ room_id: roomId })], { type: 'application/json' });
        navigator.sendBeacon('/api/room/leave', blob);
      } catch (beaconErr) {
        console.error('sendBeacon也失败:', beaconErr);
      }
    }
  } catch (err) {
    console.error('beforeunload处理错误:', err);
  }
}

onMounted(async () => {
  await fetchCurrentUserInfo();
  const res = await fetchRoomInfo(route.params.id);
  if (res && res.closed) { ui.showToast('房间已关闭'); router.push('/study-room'); return; }
  await initCamera();

  // init signaling (websocket + webRTC)
  const roomId = route.params.id;
  const userId = currentUserId.value;
  connectRoom(roomId, userId, { onError: (e) => console.error(e) });

  timer.value = setInterval(() => { currentTime.value = Date.now(); }, 1000);

  // start polling with callback
  startPolling(route.params.id, 5000, () => {
    if (isLeaving.value) return;
    ui.showToast('房间已关闭，返回房间列表');
    stopCamera();
    closeRoom();
    cleanupPeerConnections();
    router.push('/study-room');
  });

  ai.start();
  
  // 添加页面可见性变化监听
  document.addEventListener('visibilitychange', handleVisibilityChange);
  
  // 添加beforeunload事件监听
  window.addEventListener('beforeunload', handleBeforeUnload);
});

// 页面可见性变化处理
function handleVisibilityChange() {
  if (document.visibilityState === 'hidden') {
    // 页面隐藏时（如切换到其他标签页），发送离开请求
    handleBeforeUnload();
  }
}

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value);
  ai.stop();
  closeRoom();
  cleanupPeerConnections();
  stopPolling();
  try { 
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    window.removeEventListener('beforeunload', handleBeforeUnload); 
  } catch (err) {}
  stopCamera();
});
</script>

<template>
  <div class="wrap">
    <header class="bar">
      <h2>房间 {{ route.params.id }}</h2>
    </header>
    <PrivacyMode label="隐私模式与伴学能力在后续迭代接入。" />

    <!-- 房间信息区域 -->
    <div class="card">
      <h3>房间信息</h3>
      <div class="room-info">
        <p class="info-theme"><strong>主题</strong><span>{{ roomInfo.theme }}</span></p>
        <p class="info-stat"><strong>人数</strong><span>{{ roomInfo.current_people }}/{{ roomInfo.max_people }}</span></p>
        <p class="info-stat"><strong>状态</strong><span>{{ roomInfo.status }}</span></p>
        <p class="info-creator"><strong>创建者</strong><span>{{ loadingCreatorInfo ? '加载中...' : (creatorInfo?.nickname || '未知') }}</span></p>
        <p class="info-time"><strong>创建时间</strong><span>{{ createTimeStr }}</span></p>
        <p class="info-time"><strong>持续时间</strong><span>{{ roomDuration }}</span></p>
        <p class="info-time"><strong>加入时间</strong><span>{{ joinTimeStr }}</span></p>
        <p class="info-duration"><strong>学习时长</strong><span class="highlight">{{ userDuration }}</span></p>
        <!-- 显示房间内所有用户 -->
        <p class="info-members"><strong>房间成员</strong></p>
        <div class="room-users">
          <span v-for="(userId, index) in roomInfo.users" :key="index" class="user-tag">
            {{ loadingUserInfo ? '加载中...' : (userInfoMap.get(userId)?.nickname || userId) }}
          </span>
        </div>
        <!-- 显示房间标签 -->
        <div v-if="roomInfo.tags && roomInfo.tags.length > 0" class="room-tags">
          <span v-for="(tag, index) in roomInfo.tags" :key="index" class="room-tag">
            {{ tag }}
          </span>
        </div>
        <!-- 创建者权限按钮 -->
        <div v-if="isCreator" class="creator-actions">
          <button class="primary" type="button" @click="openThemeDialog">修改主题</button>
          <button class="danger" type="button" @click="openDestroyDialog">销毁房间</button>
        </div>
      </div>
    </div>

    <!-- 摄像头显示区域 -->
    <div class="card">
      <h3>摄像头</h3>
      <div class="camera-controls">
        <div class="privacy-mode-selector">
          <label>隐私模式：</label>
          <select v-model="privacyMode" @change="changePrivacyMode(privacyMode)">
            <option v-for="mode in privacyModes" :key="mode.value" :value="mode.value">
              {{ mode.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- 多人视频网格 -->
      <div class="video-grid" :class="videoGridClass" v-if="videoVisible">
        <!-- 本地视频 -->
        <div class="video-item" v-if="!cameraError">
          <div class="video-header">
            <span>我</span>
          </div>
          <video
            ref="videoRef"
            class="camera-video"
            autoplay
            playsinline
            :style="{ display: privacyMode === 'off' ? 'block' : 'none' }"
          ></video>
          <canvas
            ref="canvasRef"
            class="camera-canvas"
            v-if="privacyMode !== 'off'"
          ></canvas>
          <div class="camera-loading" v-if="cameraLoading">
            <p>正在启动摄像头...</p>
          </div>
        </div>

        <!-- 远程视频 -->
        <div
          v-for="(stream, userId) in videoStreams"
          :key="userId"
          class="video-item"
        >
          <div class="video-header">
            <span>{{ userInfoMap.get(userId)?.nickname || userId }}</span>
          </div>
          <video
            :ref="el => { if (el) el.srcObject = stream }"
            class="remote-video"
            autoplay
            playsinline
          ></video>
        </div>
      </div>

      <div class="camera-off" v-if="!cameraError && !videoVisible">
        <p>视频已隐藏（摄像头仍在运行）</p>
      </div>
      <div class="camera-error" v-else-if="cameraError">
        <p>无法访问摄像头</p>
        <button class="primary" @click="initCamera">重试</button>
      </div>
    </div>

    <div class="card">
      <p class="muted">当前为 MVP：只验证创建/加入/退出链路与状态机。</p>
      <button class="danger" type="button" :disabled="leaveLoading" @click="onLeave">
        {{ leaveLoading ? '退出中…' : '退出房间' }}
      </button>
    </div>

    <!-- 修改主题对话框 -->
    <div v-if="showThemeDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>修改房间主题</h3>
        <div class="dialog-content">
          <label class="control">
            <span>主题</span>
            <select v-model="newTheme">
              <option value="考研">考研</option>
              <option value="期末">期末</option>
              <option value="考公">考公</option>
              <option value="语言">语言</option>
            </select>
          </label>
        </div>
        <div class="dialog-actions">
          <button type="button" class="secondary" @click="closeThemeDialog">取消</button>
          <button type="button" class="primary" :disabled="updatingTheme" @click="updateTheme">{{ updatingTheme ? '修改中...' : '修改' }}</button>
        </div>
      </div>
    </div>

    <!-- 销毁房间对话框 -->
    <div v-if="showDestroyDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>销毁房间</h3>
        <div class="dialog-content">
          <p>确定要销毁这个房间吗？这将会把所有成员强制退出。</p>
        </div>
        <div class="dialog-actions">
          <button type="button" class="secondary" @click="closeDestroyDialog">取消</button>
          <button type="button" class="danger" :disabled="destroying" @click="destroyRoom">{{ destroying ? '销毁中...' : '销毁' }}</button>
        </div>
      </div>
    </div>

    <!-- 学习时长弹窗 -->
    <div v-if="showDurationDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>学习时长</h3>
        <div class="dialog-content">
          <p>您在自习室中的学习时长为：</p>
          <p class="duration-value">{{ studyDuration }} 分钟</p>
          <p class="muted">3秒后自动返回房间列表</p>
        </div>
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
  gap: 16px;
}
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
}
h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}
.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(28, 37, 51, 0.03);
}

.room-info {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.room-info > * {
  margin: 0;
}

/* 主题大卡片 - 整行 */
.info-theme {
  grid-column: 1 / -1;
  background: #e8f5e9;
  color: #1b4332;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.info-theme strong {
  font-size: 13px;
  opacity: 0.85;
  font-weight: 500;
}
.info-theme span {
  font-size: 22px;
  font-weight: 700;
}

/* 统计卡片 */
.info-stat {
  background: #fafbff;
  border: 1px solid #eef1f7;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.info-stat strong {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.info-stat span {
  font-size: 18px;
  font-weight: 700;
  color: #1c2533;
}

/* 创建者卡片 */
.info-creator {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-creator strong {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.info-creator span {
  font-size: 14px;
  color: #1c2533;
  font-weight: 600;
}

/* 时间信息卡片 */
.info-time {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-time strong {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.info-time span {
  font-size: 14px;
  color: #1c2533;
  font-weight: 600;
}

/* 学习时长突出显示 */
.info-duration {
  grid-column: 1 / -1;
  background: #fff3e0;
  color: #1b4332;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.info-duration strong {
  font-size: 13px;
  opacity: 0.85;
  font-weight: 500;
}
.info-duration .highlight {
  font-size: 28px;
  font-weight: 700;
}

/* 成员标签 */
.info-members {
  grid-column: 1 / -1;
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-members strong {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

/* 房间成员标签容器 */
.room-users {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 房间标签容器 */
.room-tags {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

/* 房间标签 */
.room-tag {
  padding: 4px 10px;
  border: 1px solid #e3e7ef;
  border-radius: 20px;
  background: #f7f8fb;
  color: #6b7280;
  font-size: 12px;
  transition: all 0.2s ease;
}

/* 成员标签 */
.user-tag {
  padding: 5px 12px;
  border: 1px solid #2d6a4f;
  border-radius: 20px;
  background: #e8f5e9;
  color: #1d4ed8;
  font-size: 12px;
  transition: all 0.2s ease;
  font-weight: 500;
}

/* 创建者操作按钮 */
.creator-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.dialog {
  background: #fff;
  border-radius: 18px;
  padding: 28px;
  width: min(500px, 90%);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
}

.dialog h3 {
  margin: 0 0 18px;
  font-size: 18px;
  text-align: center;
  font-weight: 700;
}

.dialog-content {
  margin-bottom: 20px;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.control select {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
  font-size: 14px;
  transition: all 0.2s ease;
}

.control select:focus {
  outline: none;
  border-color: #2d6a4f;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}

.secondary {
  padding: 10px 24px;
  border: 1px solid #d7dbe4;
  border-radius: 10px;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}
.secondary:hover {
  border-color: #2d6a4f;
  color: #2d6a4f;
  background: #f1f8f4;
}

.primary {
  padding: 10px 24px;
  border: 1px solid #2d6a4f;
  border-radius: 10px;
  background: #2d6a4f;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 3px 10px rgba(45, 106, 79, 0.2);
}
.primary:hover:not(:disabled) {
  background: #1b4332;
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(45, 106, 79, 0.3);
}
.primary:active:not(:disabled) {
  transform: translateY(0);
}
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.danger {
  padding: 10px 24px;
  border: 1px solid #ef4444;
  border-radius: 10px;
  background: #ef4444;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 3px 10px rgba(239, 68, 68, 0.2);
}
.danger:hover:not(:disabled) {
  background: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(239, 68, 68, 0.3);
}
.danger:active:not(:disabled) {
  transform: translateY(0);
}
.danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.camera-container {
  position: relative;
  width: 100%;
  height: 300px;
  border: 1px solid #e6eaf2;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
}
.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.camera-canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.camera-off {
  text-align: center;
  color: #6b7280;
  padding: 20px;
}
.camera-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 10px;
}
.privacy-mode-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}
.privacy-mode-selector select {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
  font-size: 14px;
  transition: all 0.2s ease;
}
.privacy-mode-selector select:focus {
  outline: none;
  border-color: #2d6a4f;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}
.camera-error {
  text-align: center;
  color: #ef4444;
  padding: 20px;
}
.camera-error p {
  margin-bottom: 10px;
}
.camera-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  color: #6b7280;
}

/* 视频网格布局 */
.video-grid {
  display: grid;
  gap: 10px;
  margin-top: 12px;
  width: 100%;
  min-height: 300px;
}

.video-grid-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.video-grid-2 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
}

.video-grid-4 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.video-grid-6 {
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.video-grid-8 {
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

.video-item {
  position: relative;
  border: 1px solid #e6eaf2;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f9fafb;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 6px rgba(28, 37, 51, 0.04);
  transition: box-shadow 0.2s ease;
}

.video-item:hover {
  box-shadow: 0 4px 12px rgba(28, 37, 51, 0.08);
}

.video-header {
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  z-index: 1;
}

.camera-video, .remote-video, .camera-canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
  flex: 1;
}

p {
  margin: 0;
}
.muted {
  color: #6b7280;
  font-size: 13px;
}

.duration-value {
  font-size: 28px;
  font-weight: 700;
  color: #2d6a4f;
  text-align: center;
  margin: 16px 0;
}
</style>