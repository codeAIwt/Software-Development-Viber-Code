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

// 所有可用的主题和标签（用于筛选）
const allAvailableThemes = computed(() => {
  return [...baseThemes, ...userTags.value];
});

// 加载用户标签
async function loadUserTags() {
  loadingTags.value = true;
  try {
    const { data } = await userApi.fetchProfile();
    if (data.code === 200 && data.data.tags) {
      // 过滤掉与基础主题重复的标签
      userTags.value = data.data.tags.filter(
        (tag) => !baseThemes.includes(tag),
      );
      // 合并基础主题和用户标签，去重
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
    // 调用API获取所有房间
    const { data } = await studyRoomApi.listRooms(null);
    if (data.code === 200) {
      let filteredRooms = data.data.rooms || [];

      // 只显示状态为idle的房间
      filteredRooms = filteredRooms.filter((room) => room.status === "idle");

      // 根据选择的主题/标签进行筛选
      if (selectedTheme.value) {
        filteredRooms = filteredRooms.filter((room) => {
          // 检查房间主题是否匹配，或者房间标签中是否包含选择的主题/标签
          return (
            room.theme === selectedTheme.value ||
            (room.tags && room.tags.includes(selectedTheme.value))
          );
        });
      }

      // 加载创建者信息
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

// 打开标签选择弹窗
function openTagSelectDialog() {
  // 重置选中的标签
  selectedRoomTags.value = [];
  showTagSelectDialog.value = true;
}

// 关闭标签选择弹窗
function closeTagSelectDialog() {
  showTagSelectDialog.value = false;
}

// 切换标签选择
function toggleTag(tag) {
  const index = selectedRoomTags.value.indexOf(tag);
  if (index > -1) {
    // 取消选择
    selectedRoomTags.value.splice(index, 1);
  } else {
    // 选择标签，最多选择3个
    if (selectedRoomTags.value.length < 3) {
      selectedRoomTags.value.push(tag);
    } else {
      ui.showToast("最多选择3个标签");
    }
  }
}

// 创建自习室
async function onCreate() {
  creating.value = true;
  try {
    // 检查是否选择了标签
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

// 定期刷新房间列表的定时器
let refreshTimer = null;

onMounted(async () => {
  await loadUserTags();
  await loadRooms();

  // 每5秒刷新一次房间列表
  refreshTimer = setInterval(async () => {
    await loadRooms();
  }, 5000);
});

onUnmounted(() => {
  // 清除定时器
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<template>
  <section class="panel">
    <div class="head">
      <h3>{{ props.title }}</h3>
      <span class="muted">当前主题：{{ selectedTheme }}</span>
    </div>

    <div class="controls">
      <label class="control">
        <span>主题/标签</span>
        <select v-model="selectedTheme" @change="loadRooms">
          <option v-for="t in allAvailableThemes" :key="t" :value="t">
            {{ t }}
          </option>
        </select>
      </label>

      <label class="control">
        <span>人数上限</span>
        <input v-model.number="maxPeople" type="number" min="1" max="8" />
      </label>

      <button
        class="primary"
        :disabled="creating"
        type="button"
        @click="openTagSelectDialog"
      >
        {{ creating ? "创建中…" : "创建房间" }}
      </button>
    </div>

    <div class="list">
      <div v-if="loadingList" class="empty muted">加载中…</div>
      <div v-else-if="rooms.length === 0" class="empty muted">暂无空闲房间</div>

      <div v-for="r in rooms" :key="r.room_id" class="row">
        <div
          class="row-icon"
          :class="{
            'icon-orange': r.theme === '期末',
            'icon-pink': r.theme === '考公',
            'icon-purple': r.theme === '语言',
          }"
        >
          {{ r.theme.slice(0, 2) }}
        </div>
        <div class="info">
          <div class="row-header">
            <span class="row-title">{{ r.theme }}</span>
            <span class="row-capacity"
              >{{ r.current_people }}/{{ r.max_people }} 人</span
            >
          </div>
          <div class="row-meta">
            <span class="status-dot" :class="r.status"></span>
            <span class="status-text">{{ r.status }}</span>
            <span class="divider">·</span>
            <span>{{ userInfoMap.get(r.creator_id)?.nickname || "未知" }}</span>
            <span class="divider">·</span>
            <span>{{
              r.created_ts_ms
                ? new Date(parseInt(r.created_ts_ms)).toLocaleString()
                : "未知"
            }}</span>
          </div>
          <!-- 显示房间标签 -->
          <div v-if="r.tags && r.tags.length > 0" class="room-tags">
            <span v-for="(tag, index) in r.tags" :key="index" class="room-tag">
              {{ tag }}
            </span>
          </div>
        </div>
        <button
          class="join"
          type="button"
          :disabled="joiningId === r.room_id"
          @click="onJoin(r.room_id)"
        >
          {{ joiningId === r.room_id ? "加入中…" : "加入" }}
        </button>
      </div>
    </div>

    <!-- 标签选择弹窗 -->
    <div v-if="showTagSelectDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>选择自习室标签（最多3个）</h3>
        <div class="tags-container">
          <button
            v-for="tag in availableTags"
            :key="tag"
            class="tag"
            :class="{ active: selectedRoomTags.includes(tag) }"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
        <div class="dialog-actions">
          <button type="button" class="secondary" @click="closeTagSelectDialog">
            取消
          </button>
          <button
            type="button"
            class="primary"
            :disabled="creating || selectedRoomTags.length === 0"
            @click="onCreate"
          >
            {{ creating ? "创建中..." : "创建" }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}
.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e6eaf2;
}
h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}
.muted {
  color: #6b7280;
  font-size: 13px;
}
.controls {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}
.control:first-child {
  flex: 1;
  min-width: 140px;
  max-width: 280px;
}
.control:nth-child(2) {
  width: 100px;
  flex-shrink: 0;
}
select,
input {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
  font-size: 14px;
  transition: all 0.2s ease;
}
select:focus,
input:focus {
  outline: none;
  border-color: #2d6a4f;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}
.primary {
  padding: 11px 20px;
  border: none;
  border-radius: 10px;
  background: #2d6a4f;
  color: #fff;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s ease;
  box-shadow: 0 3px 10px rgba(45, 106, 79, 0.2);
  margin-left: auto;
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
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
  background: #fafbff;
  border-radius: 14px;
  border: 1px dashed #cfd6e6;
}
.row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e6eaf2;
  transition: all 0.2s ease;
}
.row:hover {
  border-color: #d0d5e3;
  box-shadow: 0 4px 16px rgba(28, 37, 51, 0.06);
  transform: translateY(-1px);
}
.row-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #e8f5e9;
  color: #2d6a4f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  letter-spacing: 1px;
}
.row-icon.icon-orange {
  background: #fff3e0;
  color: #e65100;
}
.row-icon.icon-pink {
  background: #fce4ec;
  color: #ad1457;
}
.row-icon.icon-purple {
  background: #f3e5f5;
  color: #6a1b9a;
}
.info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.row-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.row-title {
  font-weight: 700;
  color: #1c2533;
  font-size: 16px;
}
.row-capacity {
  font-size: 12px;
  color: #6b7280;
  background: #f7f8fb;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
  flex-shrink: 0;
}
.row-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  flex-wrap: wrap;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bdbdbd;
  display: inline-block;
}
.status-dot.idle {
  background: #4caf50;
}
.divider {
  color: #d7dbe4;
  user-select: none;
}
.join {
  padding: 9px 18px;
  border: 1px solid #2d6a4f;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  color: #2d6a4f;
  font-weight: 700;
  transition: all 0.2s ease;
  flex-shrink: 0;
  font-size: 14px;
}
.join:hover:not(:disabled) {
  background: #2d6a4f;
  color: #fff;
  box-shadow: 0 3px 10px rgba(45, 106, 79, 0.2);
}
.join:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 房间标签样式 */
.room-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 2px;
}

.room-tag {
  padding: 3px 10px;
  border: 1px solid #e3e7ef;
  border-radius: 20px;
  background: #f7f8fb;
  color: #6b7280;
  font-size: 12px;
  transition: all 0.2s ease;
}

/* 弹窗样式 */
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
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
}

.dialog h3 {
  margin: 0 0 18px;
  font-size: 18px;
  text-align: center;
  font-weight: 700;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.tag {
  padding: 8px 16px;
  border: 1px solid #d7dbe4;
  border-radius: 20px;
  background: #f9fafb;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag:hover {
  border-color: #2d6a4f;
  background: #e8f5e9;
  transform: translateY(-1px);
}

.tag.active {
  border-color: #2d6a4f;
  background: #2d6a4f;
  color: #fff;
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.25);
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
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

/* 响应式布局 */
@media (max-width: 640px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  .control:first-child,
  .control:nth-child(2) {
    width: 100%;
    max-width: none;
  }
  .primary {
    margin-left: 0;
    width: 100%;
  }
  .row {
    grid-template-columns: auto 1fr;
    gap: 12px;
  }
  .row .join {
    grid-column: 1 / -1;
    width: 100%;
    text-align: center;
  }
}
</style>
