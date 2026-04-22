<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import { clearToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();
const profile = ref(null);
const nicknameDraft = ref("");
const saving = ref(false);
const showTagsDialog = ref(false);
const selectedTags = ref([]);

// 热门标签列表，由系统动态下发
const tags = ref([]);

async function load() {
  try {
    const [profileRes, tagsRes] = await Promise.all([
      userApi.fetchProfile(),
      userApi
        .fetchSystemTags()
        .catch(() => ({ data: { code: 200, data: [] } })),
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
  } catch (e) {
    ui.showToast("网络错误：无法获取资源");
  }
}

onMounted(load);

async function saveNickname() {
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
    <header class="bar">
      <router-link to="/home">返回首页</router-link>
      <h2>个人中心</h2>
    </header>

    <section v-if="profile" class="card">
      <div class="row">
        <div
          class="avatar"
          :style="{ backgroundImage: `url(${profile.avatar})` }"
        />
        <div>
          <p class="name">{{ profile.nickname }}</p>
          <p class="muted">{{ profile.phone }}</p>
        </div>
      </div>

      <div class="field">
        <label>昵称</label>
        <div class="inline">
          <input v-model="nicknameDraft" maxlength="20" />
          <button
            type="button"
            class="primary"
            :disabled="saving"
            @click="saveNickname"
          >
            {{ saving ? "保存中…" : "保存" }}
          </button>
        </div>
      </div>

      <div class="field">
        <label>学习标签</label>
        <div class="tags-container">
          <span v-for="(tag, index) in profile.tags" :key="index" class="tag">
            {{ tag }}
          </span>
          <button type="button" class="tag add-tag" @click="openTagsDialog">
            +
          </button>
        </div>
      </div>

      <div class="stats muted">
        <p>今日时长与击败百分比：MVP 后续接入</p>
      </div>

      <button type="button" class="danger" @click="onLogout">退出登录</button>
    </section>

    <!-- 标签选择弹窗 -->
    <div v-if="showTagsDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>选择学习标签</h3>
        <div class="tags-container dialog-tags">
          <button
            v-for="tag in tags"
            :key="tag"
            class="tag"
            :class="{ active: selectedTags.includes(tag) }"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
        <div class="dialog-actions">
          <button type="button" class="secondary" @click="closeTagsDialog">
            取消
          </button>
          <button
            type="button"
            class="primary"
            :disabled="saving"
            @click="saveTags"
          >
            {{ saving ? "保存中..." : "保存" }}
          </button>
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
.bar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}
h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(28, 37, 51, 0.03);
}
.row {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
}
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: #e8ebf3 center/cover no-repeat;
  border: 1px solid #e5e8f0;
  box-shadow: 0 2px 6px rgba(28, 37, 51, 0.06);
}
.name {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
}
.muted {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
label {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}
.inline {
  display: flex;
  gap: 10px;
  align-items: center;
}
input {
  flex: 1;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
  transition: all 0.2s ease;
  font-size: 15px;
}
input:focus {
  outline: none;
  border-color: #2d6a4f;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}
.primary {
  border: none;
  border-radius: 10px;
  padding: 10px 16px;
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
.stats {
  margin: 10px 0 16px;
  font-size: 13px;
}
.danger {
  width: 100%;
  border: 1px solid #ef4444;
  background: #fff5f5;
  color: #b91c1c;
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}
.danger:hover {
  background: #fef2f2;
  border-color: #dc2626;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

/* 标签样式 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.tag {
  padding: 5px 12px;
  border: 1px solid #e3e7ef;
  border-radius: 20px;
  background: #f7f8fb;
  color: #4b5565;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  transition: all 0.2s ease;
  font-weight: 500;
}
.tag:nth-child(4n+1) {
  background: #e8f5e9;
  border-color: #c8e6c9;
  color: #2d6a4f;
}
.tag:nth-child(4n+2) {
  background: #fff3e0;
  border-color: #ffe0b2;
  color: #e65100;
}
.tag:nth-child(4n+3) {
  background: #fce4ec;
  border-color: #f8bbd0;
  color: #ad1457;
}
.tag:nth-child(4n+4) {
  background: #e0f2f1;
  border-color: #b2dfdb;
  color: #00695c;
}

.add-tag {
  border: 1px dashed #d7dbe4;
  background: #f9fafb;
  color: #6b7280;
  cursor: pointer;
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.add-tag:hover {
  border-color: #2d6a4f;
  border-style: solid;
  color: #2d6a4f;
  background: #e8f5e9;
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

.dialog-tags {
  margin-bottom: 20px;
}

.dialog-tags .tag {
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dialog-tags .tag:hover {
  border-color: #2d6a4f;
  background: #e8f5e9;
}

.dialog-tags .tag.active {
  border-color: #2d6a4f;
  background: #2d6a4f;
  color: #fff;
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
</style>
