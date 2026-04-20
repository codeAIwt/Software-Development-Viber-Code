<script setup>
import { useRoute, useRouter } from "vue-router";
import PrivacyMode from "../components/PrivacyMode.vue";
import * as studyRoomApi from "../api/studyRoom";
import { useUiStore } from "../store";
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { startCamera, stopCamera, checkCameraPermission } from "../utils/video";
import { getToken } from "../utils/auth";
import * as userApi from "../api/user";

const route = useRoute();
const router = useRouter();
const ui = useUiStore();

const leaveLoading = ref(false);
const cameraError = ref(false);
const cameraLoading = ref(true);
const videoRef = ref(null);
const canvasRef = ref(null);

// 摄像头状态
const cameraOn = ref(true);

// 隐私模式
const privacyMode = ref('blur'); // blur 或 hand 或 off
const privacyModes = [
  { value: 'blur', label: '模糊模式' },
  { value: 'hand', label: '手部遮挡模式' },
  { value: 'off', label: '关闭隐私模式' }
];

// 视频显示状态
const videoVisible = ref(true);

// 房间信息
const roomInfo = ref({
  creator_id: '',
  created_ts_ms: '',
  theme: '',
  max_people: 0,
  current_people: 0,
  status: '',
  tags: [],
  users: []
});

// 视频流管理
const videoStreams = ref(new Map()); // userId -> MediaStream
const localStream = ref(null);
const ws = ref(null);
const peerConnections = ref(new Map()); // userId -> RTCPeerConnection

// 视频网格布局
const videoGridClass = computed(() => {
  const count = roomInfo.value.users.length;
  if (count === 1) return 'video-grid-1';
  if (count === 2) return 'video-grid-2';
  if (count === 3 || count === 4) return 'video-grid-4';
  if (count === 5 || count === 6) return 'video-grid-6';
  return 'video-grid-8';
});

// 用户信息映射
const userInfoMap = ref(new Map());
const loadingUserInfo = ref(false);

// 当前用户是否是创建者
const isCreator = computed(() => {
  const currentUserId = localStorage.getItem('user_id');
  return currentUserId === roomInfo.value.creator_id;
});

// 修改主题相关
const showThemeDialog = ref(false);
const newTheme = ref('');
const updatingTheme = ref(false);

// 销毁房间相关
const showDestroyDialog = ref(false);
const destroying = ref(false);

// 学习时长弹窗
const showDurationDialog = ref(false);
const studyDuration = ref(0);

// AI检测配置
const aiDetectionInterval = ref(10000); // 检测间隔，单位毫秒，默认1分钟
const aiDetectionEnabled = ref(true); // 是否启用AI检测
const aiDetectionTimer = ref(null); // 检测定时器

// 创建者信息
const creatorInfo = ref(null);
const loadingCreatorInfo = ref(false);

// 时间信息
const joinTime = ref(Date.now());
const currentTime = ref(Date.now());
const timer = ref(null);
// 房间信息轮询定时器 id
const roomInfoTimer = ref(null);

// 计算属性
const roomDuration = computed(() => {
  if (!roomInfo.value.created_ts_ms) return '00:00';
  const duration = currentTime.value - parseInt(roomInfo.value.created_ts_ms);
  return formatDuration(duration);
});

const userDuration = computed(() => {
  const duration = currentTime.value - joinTime.value;
  return formatDuration(duration);
});

const joinTimeStr = computed(() => {
  return new Date(joinTime.value).toLocaleString();
});

const createTimeStr = computed(() => {
  if (!roomInfo.value.created_ts_ms) return '未知';
  return new Date(parseInt(roomInfo.value.created_ts_ms)).toLocaleString();
});

// 格式化时间
function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// 获取用户信息
async function getUserInfo(userId) {
  if (userInfoMap.value.has(userId)) {
    return userInfoMap.value.get(userId);
  }
  
  try {
    const { data } = await userApi.fetchUserInfo(userId);
    if (data.code === 200) {
      userInfoMap.value.set(userId, data.data);
      return data.data;
    }
  } catch (e) {
    console.error(`获取用户 ${userId} 信息失败:`, e);
  }
  return null;
}

// 获取房间信息
async function fetchRoomInfo() {
  try {
    // 若路由中无房间 ID，则不再请求（防止在路由变更后继续请求 undefined）
    const roomId = route.params.id;
    if (!roomId) return;

    const { data } = await studyRoomApi.getRoomInfo(roomId);
    if (data.code === 200) {
      // 如果后端表示房间已关闭，停止轮询并返回房间列表
      if (data.data?.status === 'closed') {
        if (roomInfoTimer.value) {
          clearInterval(roomInfoTimer.value);
          roomInfoTimer.value = null;
        }
        ui.showToast('房间已关闭，返回房间列表');
        stopCamera();
        if (ws.value) try { ws.value.close(); } catch (err) {}
        cleanupPeerConnections();
        router.push('/study-room');
        return;
      }

      roomInfo.value = data.data;
      // 获取创建者信息
      if (roomInfo.value.creator_id) {
        loadingCreatorInfo.value = true;
        const { data: creatorData } = await userApi.fetchUserInfo(roomInfo.value.creator_id);
        if (creatorData.code === 200) {
          creatorInfo.value = creatorData.data;
        }
        loadingCreatorInfo.value = false;
      }

      // 获取房间内所有用户的信息
      if (roomInfo.value.users && roomInfo.value.users.length > 0) {
        loadingUserInfo.value = true;
        for (const userId of roomInfo.value.users) {
          await getUserInfo(userId);
        }
        loadingUserInfo.value = false;
      }
    }
  } catch (e) {
    const status = e.response?.status;
    // 房间不存在或已被删除（404），停止轮询并跳回房间列表
    if (status === 404) {
      if (roomInfoTimer.value) {
        clearInterval(roomInfoTimer.value);
        roomInfoTimer.value = null;
      }
      ui.showToast('房间不存在或已关闭，返回房间列表');
      stopCamera();
      if (ws.value) try { ws.value.close(); } catch (err) {}
      cleanupPeerConnections();
      router.push('/study-room');
      return;
    }
    console.error('获取房间信息失败:', e);
  }
}

// 启动摄像头
async function initCamera() {
  cameraLoading.value = true;
  cameraError.value = false;
  try {
    // 检查浏览器是否支持摄像头功能
    const isSupported = await checkCameraPermission();
    if (!isSupported) {
      throw new Error('浏览器不支持摄像头功能');
    }
    
    const stream = await startCamera(videoRef.value);
    localStream.value = stream;
    // 启动隐私模式处理
    applyPrivacyMode();
  } catch (error) {
    cameraError.value = true;
    if (error.message === '浏览器不支持摄像头功能') {
      ui.showToast('浏览器不支持摄像头功能');
    } else {
      ui.showToast('无法访问摄像头，请检查权限设置');
    }
  } finally {
    cameraLoading.value = false;
  }
}

// 初始化WebSocket连接
function initWebSocket() {
  const roomId = route.params.id;
  const userId = localStorage.getItem('user_id');
  
  // 使用与后端WebSocket服务相同的协议和主机
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/room/${roomId}?user_id=${userId}`;
  
  ws.value = new WebSocket(wsUrl);
  
  ws.value.onopen = () => {
    console.log('WebSocket connected');
    // 发送加入房间消息
    ws.value.send(JSON.stringify({
      type: 'join',
      user_id: userId,
      room_id: roomId
    }));
  };
  
  ws.value.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    await handleWebSocketMessage(message);
  };
  
  ws.value.onclose = () => {
    console.log('WebSocket disconnected');
    // 清理资源
    cleanupPeerConnections();
  };
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

// 处理WebSocket消息
async function handleWebSocketMessage(message) {
  const { type, user_id, data } = message;
  
  switch (type) {
    case 'user_join':
      await handleUserJoin(user_id);
      break;
    case 'user_leave':
      handleUserLeave(user_id);
      break;
    case 'offer':
      await handleOffer(user_id, data);
      break;
    case 'answer':
      await handleAnswer(user_id, data);
      break;
    case 'ice_candidate':
      await handleIceCandidate(user_id, data);
      break;
    default:
      console.log('Unknown message type:', type);
  }
}

// 处理用户加入
async function handleUserJoin(userId) {
  // 创建PeerConnection
  const pc = createPeerConnection(userId);
  
  // 添加本地流
  if (localStream.value) {
    localStream.value.getTracks().forEach(track => {
      pc.addTrack(track, localStream.value);
    });
  }
  
  // 创建offer
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  
  // 发送offer
  ws.value.send(JSON.stringify({
    type: 'offer',
    target_user_id: userId,
    data: offer
  }));
}

// 处理用户离开
function handleUserLeave(userId) {
  // 清理PeerConnection
  const pc = peerConnections.value.get(userId);
  if (pc) {
    pc.close();
    peerConnections.value.delete(userId);
  }
  
  // 移除视频流
  videoStreams.value.delete(userId);
}

// 处理offer
async function handleOffer(userId, offer) {
  // 创建PeerConnection
  const pc = createPeerConnection(userId);
  
  // 添加本地流
  if (localStream.value) {
    localStream.value.getTracks().forEach(track => {
      pc.addTrack(track, localStream.value);
    });
  }
  
  // 设置远程描述
  await pc.setRemoteDescription(new RTCSessionDescription(offer));
  
  // 创建answer
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  
  // 发送answer
  ws.value.send(JSON.stringify({
    type: 'answer',
    target_user_id: userId,
    data: answer
  }));
}

// 处理answer
async function handleAnswer(userId, answer) {
  const pc = peerConnections.value.get(userId);
  if (pc) {
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
  }
}

// 处理ICE候选
async function handleIceCandidate(userId, candidate) {
  const pc = peerConnections.value.get(userId);
  if (pc) {
    await pc.addIceCandidate(new RTCIceCandidate(candidate));
  }
}

// 创建PeerConnection
function createPeerConnection(userId) {
  const pc = new RTCPeerConnection({
    iceServers: [
      {
        urls: ['stun:stun.l.google.com:19302']
      }
    ]
  });
  
  // 处理ICE候选
  pc.onicecandidate = (event) => {
    if (event.candidate) {
      ws.value.send(JSON.stringify({
        type: 'ice_candidate',
        target_user_id: userId,
        data: event.candidate
      }));
    }
  };
  
  // 处理远程流
  pc.ontrack = (event) => {
    videoStreams.value.set(userId, event.streams[0]);
  };
  
  // 存储PeerConnection
  peerConnections.value.set(userId, pc);
  
  return pc;
}

// 清理PeerConnections
function cleanupPeerConnections() {
  peerConnections.value.forEach(pc => {
    pc.close();
  });
  peerConnections.value.clear();
  videoStreams.value.clear();
}

// 应用隐私模式
function applyPrivacyMode() {
  if (!videoRef.value || !canvasRef.value) return;
  
  const video = videoRef.value;
  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');
  
  // 设置canvas尺寸
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  
  function draw() {
    if (!cameraOn.value) return;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    if (privacyMode.value === 'blur') {
      // 模糊模式
      ctx.filter = 'blur(10px)';
      ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height);
      ctx.filter = 'none';
    } else if (privacyMode.value === 'hand') {
      // 手部遮挡模式（简化实现，在画面中上方添加黑色长矩形遮挡）
      ctx.fillStyle = 'black';
      ctx.fillRect(0, 0, canvas.width, canvas.height * 0.6); // 上方60%区域
    }
    // off模式不做处理，直接显示原始画面
    
    requestAnimationFrame(draw);
  }
  
  draw();
}

// 切换视频显示状态
function toggleVideo() {
  videoVisible.value = !videoVisible.value;
}

// 初始化AI检测
function initAiDetection() {
  if (aiDetectionEnabled.value) {
    aiDetectionTimer.value = setInterval(async () => {
      await captureAndDetect();
    }, aiDetectionInterval.value);
  }
}

// 截图并检测
async function captureAndDetect() {
  if (!videoRef.value || !cameraOn.value) return;
  
  try {
    // 创建临时Canvas用于截图
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = videoRef.value.videoWidth || 640;
    tempCanvas.height = videoRef.value.videoHeight || 480;
    const tempCtx = tempCanvas.getContext('2d');
    
    // 绘制当前视频帧
    tempCtx.drawImage(videoRef.value, 0, 0, tempCanvas.width, tempCanvas.height);
    
    // 转换为Base64
    const base64Image = tempCanvas.toDataURL('image/jpeg');
    
    // 发送到后端进行检测
    const { data } = await studyRoomApi.detectPerson(base64Image, route.params.id, localStorage.getItem('user_id'));
    if (data.code === 200) {
      if (!data.data.has_person) {
        // 检测到无人，自动退出房间
        await onLeave();
      }
    }
  } catch (error) {
    console.error('AI检测失败:', error);
  }
}

// 切换隐私模式
function changePrivacyMode(mode) {
  privacyMode.value = mode;
  applyPrivacyMode();
}

async function onLeave() {
  const roomId = route.params.id;
  leaveLoading.value = true;
  try {
    // 先停止房间信息轮询，避免在后端处理退出时继续请求旧房间信息
    if (roomInfoTimer.value) {
      clearInterval(roomInfoTimer.value);
      roomInfoTimer.value = null;
    }

    // 先停止摄像头
    stopCamera();

    const { data } = await studyRoomApi.leaveRoom(roomId);
    if (data.code !== 200) {
      ui.showToast(data.msg || "退出失败");
      return;
    }
    
    // 显示学习时长弹窗
    studyDuration.value = data.data.study_duration;
    showDurationDialog.value = true;
    
    // 3秒后跳转到房间列表
    setTimeout(() => {
      router.push("/study-room");
    }, 3000);
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "退出失败");
  } finally {
    leaveLoading.value = false;
  }
}

// 打开修改主题对话框
function openThemeDialog() {
  newTheme.value = roomInfo.value.theme;
  showThemeDialog.value = true;
}

// 关闭修改主题对话框
function closeThemeDialog() {
  showThemeDialog.value = false;
}

// 修改主题
async function updateTheme() {
  if (!newTheme.value) {
    ui.showToast('请选择主题');
    return;
  }
  
  updatingTheme.value = true;
  try {
    const { data } = await studyRoomApi.updateRoom(route.params.id, newTheme.value);
    if (data.code === 200) {
      roomInfo.value = data.data;
      ui.showToast('主题修改成功');
      closeThemeDialog();
    } else {
      ui.showToast(data.msg || '修改失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || '修改失败');
  } finally {
    updatingTheme.value = false;
  }
}

// 打开销毁房间对话框
function openDestroyDialog() {
  showDestroyDialog.value = true;
}

// 关闭销毁房间对话框
function closeDestroyDialog() {
  showDestroyDialog.value = false;
}

// 销毁房间
async function destroyRoom() {
  destroying.value = true;
  try {
    // 停止轮询，避免销毁期间继续请求老房间信息
    if (roomInfoTimer.value) {
      clearInterval(roomInfoTimer.value);
      roomInfoTimer.value = null;
    }

    const { data } = await studyRoomApi.destroyRoom(route.params.id);
    if (data.code === 200) {
      stopCamera();
      ui.showToast('房间已销毁');
      router.push('/study-room');
    } else {
      ui.showToast(data.msg || '销毁失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || '销毁失败');
  } finally {
    destroying.value = false;
    closeDestroyDialog();
  }
}

// 获取当前用户信息
async function fetchCurrentUserInfo() {
  try {
    const { data } = await userApi.fetchCurrentUser();
    if (data.code === 200) {
      // 存储用户ID到localStorage
      localStorage.setItem('user_id', data.data.id);
    }
  } catch (e) {
    console.error('获取当前用户信息失败:', e);
  }
}

// 组件挂载时启动摄像头和获取房间信息
onMounted(async () => {
  await fetchCurrentUserInfo();
  await fetchRoomInfo();
  await initCamera();
  initWebSocket();
  
  // 启动定时器
  timer.value = setInterval(() => {
    currentTime.value = Date.now();
  }, 1000);
  
  // 定期刷新房间信息，以获取最新的用户列表
  roomInfoTimer.value = setInterval(async () => {
    await fetchRoomInfo();
  }, 5000); // 每5秒刷新一次
  
  // 初始化AI检测
  initAiDetection();

  // 在页面关闭/刷新时尝试让后端把用户从房间移除
  function handleBeforeUnload(e) {
    try {
      const roomId = route.params.id;
      const token = getToken();
      if (!roomId) return;

      // 停止本地轮询与摄像头
      if (roomInfoTimer.value) {
        clearInterval(roomInfoTimer.value);
        roomInfoTimer.value = null;
      }
      stopCamera();
      if (ws.value) try { ws.value.close(); } catch (err) {}
      cleanupPeerConnections();

      // 尝试使用 fetch keepalive 发送退出请求（sendBeacon 无法携带 Authorization header）
      const payload = JSON.stringify({ room_id: roomId });
      if (token && navigator && navigator.sendBeacon === undefined) {
        // 如果没有 sendBeacon，则仍尝试 fetch keepalive
        try {
          fetch('/api/room/leave', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: payload,
            keepalive: true,
          });
        } catch (err) {
          // 忽略错误
        }
      } else {
        try {
          fetch('/api/room/leave', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: payload,
            keepalive: true,
          });
        } catch (err) {
          // 忽略
        }
      }
    } catch (err) {
      // ignore
    }
  }

  window.addEventListener('beforeunload', handleBeforeUnload);
});

// 组件卸载时清理资源
onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value);
  }
  if (aiDetectionTimer.value) {
    clearInterval(aiDetectionTimer.value);
  }
  
  // 关闭WebSocket连接
  if (ws.value) {
    ws.value.close();
  }
  
  // 清理PeerConnections
  cleanupPeerConnections();
  
  // 停止房间信息轮询
  if (roomInfoTimer.value) {
    clearInterval(roomInfoTimer.value);
    roomInfoTimer.value = null;
  }

  // 移除 beforeunload 监听
  try {
    window.removeEventListener('beforeunload', handleBeforeUnload);
  } catch (err) {}

  // 停止摄像头
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
        <p><strong>主题：</strong>{{ roomInfo.theme }}</p>
        <p><strong>人数：</strong>{{ roomInfo.current_people }}/{{ roomInfo.max_people }}</p>
        <p><strong>状态：</strong>{{ roomInfo.status }}</p>
        <p><strong>创建者：</strong>{{ loadingCreatorInfo ? '加载中...' : (creatorInfo?.nickname || '未知') }}</p>
        <p><strong>创建时间：</strong>{{ createTimeStr }}</p>
        <p><strong>房间持续时间：</strong>{{ roomDuration }}</p>
        <p><strong>您的加入时间：</strong>{{ joinTimeStr }}</p>
        <p><strong>您的学习时长：</strong>{{ userDuration }}</p>
        <!-- 显示房间内所有用户 -->
        <p><strong>房间成员：</strong></p>
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
        <button class="secondary" @click="toggleVideo">
          {{ videoVisible ? '隐藏视频' : '显示视频' }}
        </button>
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
        {{ leaveLoading ? "退出中…" : "退出房间" }}
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
          <button type="button" class="secondary" @click="closeThemeDialog">
            取消
          </button>
          <button type="button" class="primary" :disabled="updatingTheme" @click="updateTheme">
            {{ updatingTheme ? "修改中..." : "修改" }}
          </button>
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
          <button type="button" class="secondary" @click="closeDestroyDialog">
            取消
          </button>
          <button type="button" class="danger" :disabled="destroying" @click="destroyRoom">
            {{ destroying ? "销毁中..." : "销毁" }}
          </button>
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

.room-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.room-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.room-tag {
  padding: 4px 10px;
  border: 1px solid #d7dbe4;
  border-radius: 12px;
  background: #f9fafb;
  color: #6b7280;
  font-size: 12px;
}

.room-users {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
  margin-bottom: 8px;
}

.user-tag {
  padding: 4px 10px;
  border: 1px solid #3b82f6;
  border-radius: 12px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
}

.creator-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
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
}

.dialog {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: min(500px, 90%);
}

.dialog h3 {
  margin: 0 0 16px;
  font-size: 18px;
  text-align: center;
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
}

.control select {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
}

.secondary {
  padding: 10px 24px;
  border: 1px solid #d7dbe4;
  border-radius: 10px;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  font-weight: 600;
}

.primary {
  padding: 10px 24px;
  border: 1px solid #3b82f6;
  border-radius: 10px;
  background: #3b82f6;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.danger {
  padding: 10px 24px;
  border: 1px solid #ef4444;
  border-radius: 10px;
  background: #ef4444;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.danger:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.camera-container {
  position: relative;
  width: 100%;
  height: 300px;
  border: 1px solid #e6eaf2;
  border-radius: 10px;
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
}
.camera-error {
  text-align: center;
  color: #ef4444;
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
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
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
  border-radius: 10px;
  overflow: hidden;
  background-color: #f9fafb;
  display: flex;
  flex-direction: column;
}

.video-header {
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
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

.danger {
  width: 100%;
  border: 1px solid #ef4444;
  background: #fff5f5;
  color: #b91c1c;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  font-weight: 700;
}
.primary {
  border: 1px solid #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 10px;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 600;
}
.danger:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
p {
  margin: 0;
}
.muted {
  color: #6b7280;
  font-size: 13px;
}

.duration-value {
  font-size: 24px;
  font-weight: 700;
  color: #3b82f6;
  text-align: center;
  margin: 16px 0;
}
</style>