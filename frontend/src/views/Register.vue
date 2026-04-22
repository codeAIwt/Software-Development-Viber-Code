<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import { setToken } from "../utils/auth";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();

const phone = ref("");
const password = ref("");
const password2 = ref("");
const agreed = ref(false);
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
    ui.showToast("手机号格式不正确，必须为11位纯数字");
    return;
  }
  if (!password.value) {
    ui.showToast("请输入密码");
    return;
  }
  if (!agreed.value) {
    ui.showToast("请先勾选同意协议");
    return;
  }
  if (password.value !== password2.value) {
    ui.showToast("两次密码不一致");
    return;
  }
  loading.value = true;
  try {
    const { data } = await userApi.register(trimmedPhone, password.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "注册失败");
      return;
    }
    setToken(data.data.token);
    ui.showToast("注册成功");
    await router.replace("/tags");
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
      <h1>注册</h1>
      <p class="subtitle">创建账号，开始学习陪伴之旅</p>
      <form class="form" @submit.prevent="onSubmit">
        <label>
          <span>手机号</span>
          <input v-model="phone" type="text" autocomplete="username" placeholder="请输入手机号" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="password" type="password" autocomplete="new-password" placeholder="请输入密码" />
        </label>
        <label>
          <span>确认密码</span>
          <input v-model="password2" type="password" autocomplete="new-password" placeholder="请再次输入密码" />
        </label>
        <label class="inline">
          <input v-model="agreed" type="checkbox" />
          <span>我已阅读并同意《用户协议》与《隐私政策》</span>
        </label>
        <button class="primary" type="submit" :disabled="loading">{{ loading ? "提交中…" : "注册" }}</button>
      </form>
      <p class="footer">
        已有账号？
        <router-link to="/login">去登录</router-link>
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
  background: #f6f7fb;
}
.card {
  width: min(420px, 100%);
  background: #fff;
  border-radius: 18px;
  padding: 32px 30px 24px;
  box-shadow: 0 24px 60px rgba(28, 37, 51, 0.1), 0 8px 20px rgba(28, 37, 51, 0.04);
  border: 1px solid #eceff5;
  transition: box-shadow 0.3s ease;
}
h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
.subtitle {
  margin: 8px 0 24px;
  color: #6b7280;
  font-size: 14px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}
.inline {
  flex-direction: row;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #4b5565;
}
input[type="text"],
input[type="password"] {
  padding: 11px 14px;
  border-radius: 12px;
  border: 1px solid #d7dbe4;
  background: #f9fafb;
  transition: all 0.2s ease;
  font-size: 15px;
}
input[type="text"]:focus,
input[type="password"]:focus {
  outline: none;
  border-color: #2d6a4f;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.12);
}
.primary {
  margin-top: 6px;
  padding: 12px 14px;
  border: none;
  border-radius: 12px;
  background: #2d6a4f;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(45, 106, 79, 0.25);
}
.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(45, 106, 79, 0.35);
}
.primary:active:not(:disabled) {
  transform: translateY(0);
}
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}
.footer {
  margin: 20px 0 0;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}
</style>
