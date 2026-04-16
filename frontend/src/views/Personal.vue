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

    <p v-else class="muted">加载中…</p>
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
  font-size: 20px;
}
.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 14px;
  padding: 18px;
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
}
.name {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 650;
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
}
.inline {
  display: flex;
  gap: 10px;
  align-items: center;
}
input {
  flex: 1;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d7dbe4;
}
.primary {
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  background: #3b5bfd;
  color: #fff;
  cursor: pointer;
}
.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
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
  padding: 10px 12px;
  cursor: pointer;
}

/* 标签样式 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.tag {
  padding: 6px 12px;
  border: 1px solid #d7dbe4;
  border-radius: 16px;
  background: #f9fafb;
  color: #374151;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
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
}

.add-tag:hover {
  border-color: #3b5bfd;
  color: #3b5bfd;
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
}

.dialog {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: min(500px, 90%);
  max-height: 80vh;
  overflow-y: auto;
}

.dialog h3 {
  margin: 0 0 16px;
  font-size: 18px;
  text-align: center;
}

.dialog-tags {
  margin-bottom: 20px;
}

.dialog-tags .tag {
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.dialog-tags .tag:hover {
  border-color: #3b5bfd;
  background: #eff6ff;
}

.dialog-tags .tag.active {
  border-color: #3b5bfd;
  background: #3b5bfd;
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
}
</style>
