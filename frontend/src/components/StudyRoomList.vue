<script setup>
import { onMounted, onUnmounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import * as studyRoomApi from "../api/studyRoom";
import * as userApi from "../api/user";
import { useUiStore } from "../store";

const props = defineProps({
  title: { type: String, default: "自习室列表" },
});

const router = useRouter();
const ui = useUiStore();

// 基础主题列表
const baseThemes = ["考研", "期末", "考公", "语言"];
// 用户标签
const userTags = ref([]);
// 可用标签列表（基础主题 + 用户标签）
const availableTags = ref([]);

// 自习室标签选择相关
const showTagSelectDialog = ref(false);
const selectedRoomTags = ref([]);

// 筛选相关
const selectedTheme = ref("考研");
const maxPeople = ref(2);
const rooms = ref([]);

const loadingList = ref(false);
const creating = ref(false);
const joiningId = ref("");
const loadingTags = ref(false);

// 用户信息映射
const userInfoMap = ref(new Map());
const loadingUserInfo = ref(false);

// 搜索
const searchQuery = ref("");

// 所有可用的主题和标签（用于筛选）
const allAvailableThemes = computed(() => {
  return [...baseThemes, ...userTags.value];
});

// 过滤后的房间列表
const filteredRooms = computed(() => {
  if (!searchQuery.value.trim()) return rooms.value;
  const query = searchQuery.value.toLowerCase();
  return rooms.value.filter(room => 
    room.theme.toLowerCase().includes(query) ||
    room.tags?.some(tag => tag.toLowerCase().includes(query)) ||
    (userInfoMap.value.get(room.creator_id)?.nickname || '').toLowerCase().includes(query)
  );
});

// 加载用户标签
async function loadUserTags() {
  loadingTags.value = true;
  try {
    const { data } = await userApi.fetchProfile();
    if (data.code === 200 && data.data.tags) {
      userTags.value = data.data.tags.filter(
        (tag) => !baseThemes.includes(tag),
      );
      availableTags.value = [...new Set([...baseThemes, ...userTags.value])];
    }
  } catch (e) {
    console.error("加载用户标签失败:", e);
  } finally {
    loadingTags.value = false;
  }
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

async function loadRooms() {
  loadingList.value = true;
  try {
    const { data } = await studyRoomApi.listRooms(null);
    if (data.code === 200) {
      let filteredRooms = data.data.rooms || [];
      filteredRooms = filteredRooms.filter((room) => room.status === "idle");

      if (selectedTheme.value) {
        filteredRooms = filteredRooms.filter((room) => {
          return (
            room.theme === selectedTheme.value ||
            (room.tags && room.tags.includes(selectedTheme.value))
          );
        });
      }

      loadingUserInfo.value = true;
      for (const room of filteredRooms) {
        if (room.creator_id) {
          await getUserInfo(room.creator_id);
        }
      }
      loadingUserInfo.value = false;

      rooms.value = filteredRooms;
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "加载失败");
    loadingUserInfo.value = false;
  } finally {
    loadingList.value = false;
  }
}

function openTagSelectDialog() {
  selectedRoomTags.value = [];
  showTagSelectDialog.value = true;
}

function closeTagSelectDialog() {
  showTagSelectDialog.value = false;
}

function toggleTag(tag) {
  const index = selectedRoomTags.value.indexOf(tag);
  if (index > -1) {
    selectedRoomTags.value.splice(index, 1);
  } else {
    if (selectedRoomTags.value.length < 3) {
      selectedRoomTags.value.push(tag);
    } else {
      ui.showToast("最多选择3个标签");
    }
  }
}

async function onCreate() {
  creating.value = true;
  try {
    if (selectedRoomTags.value.length === 0) {
      ui.showToast("请至少选择一个标签");
      creating.value = false;
      return;
    }

    const { data } = await studyRoomApi.createRoom(
      selectedTheme.value,
      maxPeople.value,
      selectedRoomTags.value,
    );
    if (data.code !== 200) {
      ui.showToast(data.msg || "创建失败");
      return;
    }
    router.push(`/study-room/${data.data.room_id}`);
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "创建失败");
  } finally {
    creating.value = false;
    showTagSelectDialog.value = false;
  }
}

async function onJoin(roomId) {
  joiningId.value = roomId;
  try {
    const { data } = await studyRoomApi.joinRoom(roomId, "manual");
    if (data.code !== 200) {
      ui.showToast(data.msg || "加入失败");
      return;
    }
    router.push(`/study-room/${data.data.room_id}`);
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "加入失败");
  } finally {
    joiningId.value = "";
  }
}

// 获取主题图标颜色
function getThemeClass(theme) {
  const themeMap = {
    '考研': 'theme-green',
    '期末': 'theme-orange',
    '考公': 'theme-pink',
    '语言': 'theme-purple'
  };
  return themeMap[theme] || 'theme-green';
}

let refreshTimer = null;

onMounted(async () => {
  await loadUserTags();
  await loadRooms();
  refreshTimer = setInterval(async () => {
    await loadRooms();
  }, 5000);
});

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<template>
  <section class="panel">
    <!-- 头部 -->
    <div class="head">
      <div class="head-info">
        <h3>{{ props.title }}</h3>
        <span class="room-count">{{ filteredRooms.length }} 个房间</span>
      </div>
      <button class="btn-create" :disabled="creating" @click="openTagSelectDialog">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        {{ creating ? "创建中" : "创建房间" }}
      </button>
    </div>

    <!-- 筛选控制 -->
    <div class="controls">
      <!-- 搜索框 -->
      <div class="search-box">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="搜索房间、标签、创建者..."
        />
      </div>

      <!-- 主题筛选 -->
      <div class="filter-group">
        <label>主题</label>
        <select v-model="selectedTheme" @change="loadRooms">
          <option v-for="t in allAvailableThemes" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>

      <!-- 人数设置 -->
      <div class="filter-group">
        <label>人数上限</label>
        <input v-model.number="maxPeople" type="number" min="1" max="8" />
      </div>
    </div>

    <!-- 房间列表 -->
    <div class="list">
      <!-- 加载骨架屏 -->
      <div v-if="loadingList" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-room">
          <div class="skeleton skeleton-icon"></div>
          <div class="skeleton-content">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-meta"></div>
          </div>
          <div class="skeleton skeleton-btn"></div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredRooms.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            <circle cx="12" cy="10" r="2"/>
          </svg>
        </div>
        <p class="empty-title">暂无空闲房间</p>
        <p class="empty-desc">换个主题试试，或者创建一个新房间</p>
        <button class="btn-create-empty" @click="openTagSelectDialog">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          创建房间
        </button>
      </div>

      <!-- 房间卡片 -->
      <div 
        v-else
        v-for="(room, index) in filteredRooms" 
        :key="room.room_id" 
        class="room-card animate-item"
        :style="{ animationDelay: `${index * 0.05}s` }"
      >
        <div class="room-icon" :class="getThemeClass(room.theme)">
          {{ room.theme.slice(0, 2) }}
        </div>

        <div class="room-info">
          <div class="room-header">
            <span class="room-theme">{{ room.theme }}</span>
            <span class="room-capacity">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              {{ room.current_people }}/{{ room.max_people }}
            </span>
          </div>

          <div class="room-meta">
            <span class="room-creator">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
              </svg>
              {{ userInfoMap.get(room.creator_id)?.nickname || "未知" }}
            </span>
            <span class="room-time">
              {{ room.created_ts_ms ? new Date(parseInt(room.created_ts_ms)).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '' }}
            </span>
          </div>

          <!-- 房间标签 -->
          <div v-if="room.tags && room.tags.length > 0" class="room-tags">
            <span v-for="(tag, idx) in room.tags.slice(0, 3)" :key="idx" class="room-tag">
              {{ tag }}
            </span>
          </div>
        </div>

        <button 
          class="btn-join"
          :disabled="joiningId === room.room_id"
          @click="onJoin(room.room_id)"
        >
          <span v-if="joiningId === room.room_id" class="loading-spinner"></span>
          {{ joiningId === room.room_id ? "" : "加入" }}
        </button>
      </div>
    </div>

    <!-- 标签选择弹窗 -->
    <Transition name="dialog">
      <div v-if="showTagSelectDialog" class="dialog-overlay" @click.self="closeTagSelectDialog">
        <div class="dialog">
          <div class="dialog-header">
            <h3>创建自习室</h3>
            <button class="dialog-close" @click="closeTagSelectDialog">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <p class="dialog-hint">选择标签（最多3个）</p>
            <div class="tags-grid">
              <button
                v-for="tag in availableTags"
                :key="tag"
                class="tag-option"
                :class="{ active: selectedRoomTags.includes(tag) }"
                @click="toggleTag(tag)"
              >
                {{ tag }}
                <svg v-if="selectedRoomTags.includes(tag)" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-secondary" @click="closeTagSelectDialog">取消</button>
            <button 
              class="btn-primary" 
              :disabled="creating || selectedRoomTags.length === 0"
              @click="onCreate"
            >
              <span v-if="creating" class="loading-spinner white"></span>
              {{ creating ? "创建中" : "创建房间" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid var(--color-border, #e6eaf2);
  border-radius: 20px;
  padding: 24px;
}

/* 动画 */
.animate-item {
  opacity: 0;
  animation: fadeInUp 0.4s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 头部 */
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.head-info {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.head h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.room-count {
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.2);
}

.btn-create:hover:not(:disabled) {
  background: var(--color-primary-dark, #1b4332);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.3);
}

.btn-create:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 筛选控制 */
.controls {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 12px;
  background: var(--color-bg-input, #f9fafb);
  transition: all 0.2s ease;
}

.search-box:focus-within {
  border-color: var(--color-primary, #2d6a4f);
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.1);
  background: #fff;
}

.search-box svg {
  color: var(--color-text-muted, #6b7280);
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
  font-weight: 500;
}

.filter-group select,
.filter-group input {
  padding: 10px 14px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 10px;
  background: var(--color-bg-input, #f9fafb);
  font-size: 14px;
  min-width: 100px;
  transition: all 0.2s ease;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: var(--color-primary, #2d6a4f);
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.1);
}

/* 骨架屏 */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-room {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 14px;
  background: var(--color-bg, #f6f7fb);
}

.skeleton {
  background: linear-gradient(90deg, #e8e8e8 25%, #f0f0f0 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-title {
  width: 120px;
  height: 18px;
}

.skeleton-meta {
  width: 200px;
  height: 14px;
}

.skeleton-btn {
  width: 72px;
  height: 40px;
  border-radius: 10px;
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

.empty-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--color-bg, #f6f7fb);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-border-light, #d7dbe4);
}

.empty-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.empty-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
}

.btn-create-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-create-empty:hover {
  background: var(--color-primary-dark, #1b4332);
}

/* 房间列表 */
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.room-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 16px;
  background: var(--color-bg, #f6f7fb);
  border: 1px solid transparent;
  transition: all 0.25s ease;
}

.room-card:hover {
  background: #fff;
  border-color: var(--color-border, #e6eaf2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.room-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

.theme-green {
  background: var(--color-primary-bg, #e8f5e9);
  color: var(--color-primary, #2d6a4f);
}

.theme-orange {
  background: var(--color-secondary-bg, #fff3e0);
  color: #e65100;
}

.theme-pink {
  background: #fce4ec;
  color: #ad1457;
}

.theme-purple {
  background: #f3e5f5;
  color: #6a1b9a;
}

.room-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.room-theme {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text, #1c2533);
}

.room-capacity {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  background: #fff;
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
  font-weight: 500;
}

.room-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
}

.room-creator,
.room-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.room-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.room-tag {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(45, 106, 79, 0.08);
  color: var(--color-primary, #2d6a4f);
  font-size: 12px;
  font-weight: 500;
}

.btn-join {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  padding: 10px 18px;
  border: 2px solid var(--color-primary, #2d6a4f);
  border-radius: 12px;
  background: #fff;
  color: var(--color-primary, #2d6a4f);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-join:hover:not(:disabled) {
  background: var(--color-primary, #2d6a4f);
  color: #fff;
}

.btn-join:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(45, 106, 79, 0.2);
  border-top-color: var(--color-primary, #2d6a4f);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner.white {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
}

@keyframes spin {
  to { transform: rotate(360deg); }
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
  width: min(480px, 100%);
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
}

.dialog-body {
  padding: 24px;
  overflow-y: auto;
}

.dialog-hint {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
}

.tags-grid {
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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
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
  .panel {
    padding: 18px;
    border-radius: 16px;
  }
  
  .head {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .head-info {
    justify-content: space-between;
  }
  
  .btn-create {
    width: 100%;
    justify-content: center;
  }
  
  .controls {
    flex-direction: column;
  }
  
  .search-box {
    min-width: auto;
  }
  
  .filter-group {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  
  .filter-group select,
  .filter-group input {
    flex: 1;
    max-width: 140px;
  }
  
  .room-card {
    flex-wrap: wrap;
  }
  
  .room-info {
    flex: 1 1 calc(100% - 84px);
  }
  
  .btn-join {
    flex: 1 1 100%;
    margin-top: 8px;
  }
}
</style>
