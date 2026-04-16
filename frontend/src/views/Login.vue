<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as userApi from "../api/user";
import { setToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const route = useRoute();
const ui = useUiStore();

const phone = ref("");
const password = ref("");
const loading = ref(false);

function validatePhone(phone) {
  const phoneRegex = /^[0-9]{11}$/;
  return phoneRegex.test(phone);
}

async function onSubmit() {
  const trimmedPhone = phone.value.trim();
  if (!trimmedPhone) {
    ui.showToast("请输入手机号");
    return;
  }
  if (!validatePhone(trimmedPhone)) {
    ui.showToast("手机号格式不正确，请重新输入");
    return;
  }
  if (!password.value) {
    ui.showToast("请输入密码");
    return;
  }
  loading.value = true;
  try {
    const { data } = await userApi.login(trimmedPhone, password.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "登录失败");
      return;
    }
    setToken(data.data.token);
    ui.showToast("登录成功");
    
    // 检查是否是首次登录
    if (data.data.is_first_login) {
      // 首次登录，跳转到标签选择页面
      await router.replace("/tags");
    } else {
      // 非首次登录，跳转到首页
      const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/home";
      await router.replace(redirect);
    }
  } catch (e) {
    const msg = e.response?.data?.msg || e.message || "网络错误";
    ui.showToast(msg);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth">
    <div class="card">
      <h1>登录</h1>
      <p class="subtitle">线上伴学 · 轻量化自习室</p>
      <form class="form" @submit.prevent="onSubmit">
        <label>
          <span>手机号</span>
          <input v-model="phone" type="text" autocomplete="username" placeholder="请输入手机号" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </label>
        <button class="primary" type="submit" :disabled="loading">{{ loading ? "登录中…" : "登录" }}</button>
      </form>
      <p class="footer">
        没有账号？
        <router-link to="/register">去注册</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}
.card {
  width: min(420px, 100%);
  background: #fff;
  border-radius: 16px;
  padding: 28px 28px 22px;
  box-shadow: 0 18px 50px rgba(28, 37, 51, 0.08);
  border: 1px solid #eceff5;
}
h1 {
  margin: 0;
  font-size: 22px;
}
.subtitle {
  margin: 8px 0 20px;
  color: #6b7280;
  font-size: 14px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
}
input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
}
input:focus {
  outline: none;
  border-color: #3b5bfd;
  background: #fff;
}
.primary {
  margin-top: 6px;
  padding: 11px 12px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(90deg, #4f6bff, #3b5bfd);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}
.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.footer {
  margin: 18px 0 0;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}
</style>