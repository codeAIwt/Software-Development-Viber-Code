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
        <router-link class="tile" to="/study-room">进入自习室模块</router-link>
        <router-link class="tile" to="/rank">学习时长排行</router-link>
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
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.2px;
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
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}
.ghost:hover {
  border-color: #2d6a4f;
  color: #2d6a4f;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.1);
}
.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  background: #fff;
  border: 1px solid #e6eaf2;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(28, 37, 51, 0.03);
  transition: box-shadow 0.25s ease;
}
.card:hover {
  box-shadow: 0 6px 18px rgba(28, 37, 51, 0.06);
}
.hero h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
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
  gap: 14px;
}
.tile {
  background: #fff;
  border: 1px solid #e3e7ef;
  border-radius: 16px;
  padding: 20px 22px;
  color: #1c2533;
  font-weight: 600;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.tile::before {
  content: '';
  position: absolute;
  left: 0;
  top: 16px;
  bottom: 16px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #2d6a4f;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.tile::after {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 26px;
  opacity: 0.25;
  transition: opacity 0.2s ease;
  pointer-events: none;
}
.tile:nth-child(1)::after {
  content: '📚';
}
.tile:nth-child(2)::after {
  content: '🏆';
}
.tile:nth-child(2) {
  border-color: #ffe0b2;
}
.tile:nth-child(2)::before {
  background: #f57c00;
}
.tile:hover {
  border-color: #2d6a4f;
  background: #f1f8f4;
  box-shadow: 0 4px 14px rgba(45, 106, 79, 0.1);
  transform: translateY(-1px);
}
.tile:nth-child(2):hover {
  border-color: #f57c00;
  background: #fff8e1;
  box-shadow: 0 4px 14px rgba(245, 124, 0, 0.1);
}
.tile:hover::before {
  opacity: 1;
}
.tile:hover::after {
  opacity: 0.45;
}
.tile.muted {
  color: #6b7280;
}
</style>