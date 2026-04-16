<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import { clearToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();
const profile = ref(null);

async function load() {
  try {
    const { data } = await userApi.fetchProfile();
    if (data.code === 200) {
      profile.value = data.data;
    }
  } catch {
    ui.showToast("加载用户信息失败");
  }
}

onMounted(load);

async function onLogout() {
  try {
    await userApi.logout();
  } catch {
    /* 仍清理本地态 */
  } finally {
    clearToken();
    await router.replace("/login");
  }
}
</script>

<template>
  <div class="wrap">
    <header class="top">
      <div>
        <h2>线上伴学</h2>
        <p class="muted">安静专注，云端相伴</p>
      </div>
      <nav class="nav">
        <router-link to="/personal">个人中心</router-link>
        <button type="button" class="ghost" @click="onLogout">退出</button>
      </nav>
    </header>

    <main class="main">
      <section class="hero card">
        <h3>欢迎回来</h3>
        <p v-if="profile" class="lead">
          {{ profile.nickname }}（{{ profile.phone }}）
        </p>
        <p v-else class="lead muted">正在加载资料…</p>
        <p class="hint">Token 已保存在本机，用于后续受限接口调用。</p>
      </section>

      <section class="grid">
        <router-link class="tile" to="/study-room">进入自习室模块（占位）</router-link>
        <div class="tile muted">学习时长排行（即将上线）</div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.wrap {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 20px 40px;
}
.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}
h2 {
  margin: 0;
  font-size: 22px;
}
.muted {
  color: #6b7280;
}
.nav {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 14px;
}
.ghost {
  border: 1px solid #d7dbe4;
  background: #fff;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
}
.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 14px;
  padding: 18px;
}
.hero h3 {
  margin: 0 0 8px;
}
.lead {
  margin: 0 0 10px;
  font-size: 16px;
}
.hint {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.tile {
  background: #fff;
  border: 1px dashed #cfd6e6;
  border-radius: 14px;
  padding: 16px;
  color: #1c2533;
}
.tile.muted {
  color: #6b7280;
}
</style>
