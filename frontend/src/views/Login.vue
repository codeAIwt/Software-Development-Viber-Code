<script setup>
import { ref, computed } from "vue";
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
const showPassword = ref(false);
const phoneError = ref("");
const passwordError = ref("");
const shakePhone = ref(false);
const shakePassword = ref(false);

// 手机号验证
const isPhoneValid = computed(() => {
  return /^[0-9]{11}$/.test(phone.value.trim());
});

function validatePhone() {
  const trimmed = phone.value.trim();
  if (!trimmed) {
    phoneError.value = "请输入手机号";
    return false;
  }
  if (!/^[0-9]{11}$/.test(trimmed)) {
    phoneError.value = "请输入11位手机号";
    return false;
  }
  phoneError.value = "";
  return true;
}

function validatePassword() {
  if (!password.value) {
    passwordError.value = "请输入密码";
    return false;
  }
  passwordError.value = "";
  return true;
}

function triggerShake(field) {
  if (field === "phone") {
    shakePhone.value = true;
    setTimeout(() => { shakePhone.value = false; }, 500);
  } else {
    shakePassword.value = true;
    setTimeout(() => { shakePassword.value = false; }, 500);
  }
}

async function onSubmit() {
  const phoneValid = validatePhone();
  const passwordValid = validatePassword();
  
  if (!phoneValid) {
    triggerShake("phone");
    return;
  }
  if (!passwordValid) {
    triggerShake("password");
    return;
  }
  
  loading.value = true;
  try {
    const { data } = await userApi.login(phone.value.trim(), password.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "登录失败");
      return;
    }
    setToken(data.data.token);
    ui.showToast("登录成功");
    
    // 检查是否是首次登录
    if (data.data.is_first_login) {
      await router.replace("/tags");
    } else {
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
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="floating-shape shape-1">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <rect width="80" height="80" rx="16" fill="#2d6a4f" opacity="0.08"/>
        </svg>
      </div>
      <div class="floating-shape shape-2">
        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
          <circle cx="30" cy="30" r="30" fill="#f57c00" opacity="0.06"/>
        </svg>
      </div>
      <div class="floating-shape shape-3">
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
          <path d="M50 0L93.3 25v50L50 100 6.7 75V25L50 0z" fill="#2d6a4f" opacity="0.05"/>
        </svg>
      </div>
      <div class="floating-shape shape-4">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="8" fill="#1976d2" opacity="0.06"/>
        </svg>
      </div>
    </div>

    <div class="card">
      <!-- Logo -->
      <div class="logo">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <rect width="48" height="48" rx="12" fill="#2d6a4f"/>
          <path d="M12 34V14h6v20h-6zm9-12v12h6V22h-6zm9-6v18h6V16h-6z" fill="white"/>
        </svg>
      </div>

      <h1>欢迎回来</h1>
      <p class="subtitle">登录线上伴学，开启专注学习之旅</p>

      <form class="form" @submit.prevent="onSubmit">
        <div class="field" :class="{ error: phoneError, shake: shakePhone }">
          <label for="phone">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
              <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
            手机号
          </label>
          <input 
            id="phone"
            v-model="phone" 
            type="text" 
            autocomplete="username" 
            placeholder="请输入11位手机号"
            maxlength="11"
            @blur="validatePhone"
            @input="phoneError = ''"
          />
          <span v-if="phoneError" class="error-msg">{{ phoneError }}</span>
        </div>

        <div class="field" :class="{ error: passwordError, shake: shakePassword }">
          <label for="password">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            密码
          </label>
          <div class="password-wrapper">
            <input 
              id="password"
              v-model="password" 
              :type="showPassword ? 'text' : 'password'" 
              autocomplete="current-password" 
              placeholder="请输入密码"
              @blur="validatePassword"
              @input="passwordError = ''"
            />
            <button 
              type="button" 
              class="toggle-password"
              @click="showPassword = !showPassword"
              tabindex="-1"
            >
              <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
          <span v-if="passwordError" class="error-msg">{{ passwordError }}</span>
        </div>

        <button class="primary" type="submit" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? "登录中" : "登录" }}
        </button>
      </form>

      <div class="divider">
        <span>或</span>
      </div>

      <div class="social-login">
        <button type="button" class="social-btn" disabled title="敬请期待">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c4.8 0 8.691-3.288 8.691-7.342 0-4.054-3.891-7.34-8.691-7.34"/>
          </svg>
          微信登录
        </button>
      </div>

      <p class="footer">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
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
  background: linear-gradient(135deg, #f8faf9 0%, #e8f5e9 50%, #f0f4f8 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.floating-shape {
  position: absolute;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  top: 20%;
  right: 15%;
  animation-delay: 1s;
}

.shape-3 {
  bottom: 15%;
  left: 8%;
  animation-delay: 2s;
}

.shape-4 {
  bottom: 25%;
  right: 10%;
  animation-delay: 3s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}

/* 卡片 */
.card {
  width: min(420px, 100%);
  background: #fff;
  border-radius: 24px;
  padding: 40px 36px 32px;
  box-shadow: 0 24px 60px rgba(28, 37, 51, 0.12), 0 8px 20px rgba(28, 37, 51, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.8);
  position: relative;
  z-index: 1;
  animation: cardEnter 0.5s ease;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.logo {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  letter-spacing: -0.5px;
  color: var(--color-text, #1c2533);
}

.subtitle {
  margin: 10px 0 28px;
  color: var(--color-text-muted, #6b7280);
  font-size: 14px;
  text-align: center;
}

/* 表单 */
.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field.shake {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-secondary, #374151);
  font-weight: 600;
}

label svg {
  color: var(--color-text-muted, #6b7280);
}

input {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1.5px solid var(--color-border-light, #d7dbe4);
  background: var(--color-bg-input, #f9fafb);
  transition: all 0.2s ease;
  font-size: 15px;
  width: 100%;
}

input:focus {
  outline: none;
  border-color: var(--color-primary, #2d6a4f);
  background: #fff;
  box-shadow: 0 0 0 4px rgba(45, 106, 79, 0.1);
}

.field.error input {
  border-color: var(--color-error, #ef4444);
  background: #fef2f2;
}

.field.error input:focus {
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
}

.error-msg {
  font-size: 12px;
  color: var(--color-error, #ef4444);
  display: flex;
  align-items: center;
  gap: 4px;
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  padding-right: 48px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted, #6b7280);
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.toggle-password:hover {
  color: var(--color-primary, #2d6a4f);
}

/* 主按钮 */
.primary {
  margin-top: 8px;
  padding: 14px 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--color-primary, #2d6a4f) 0%, var(--color-primary-light, #40916c) 100%);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.25s ease;
  box-shadow: 0 4px 14px rgba(45, 106, 79, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(45, 106, 79, 0.4);
}

.primary:active:not(:disabled) {
  transform: translateY(0);
}

.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: none;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 分隔线 */
.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0;
  color: var(--color-text-muted, #6b7280);
  font-size: 13px;
}

.divider::before,
.divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--color-border, #e6eaf2);
}

/* 社交登录 */
.social-login {
  display: flex;
  gap: 12px;
}

.social-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: 1px solid var(--color-border-light, #d7dbe4);
  border-radius: 12px;
  background: #fff;
  color: var(--color-text-secondary, #374151);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.social-btn:hover:not(:disabled) {
  border-color: var(--color-primary, #2d6a4f);
  background: var(--color-primary-bg, #e8f5e9);
}

.social-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.social-btn svg {
  color: #07c160;
}

/* 底部 */
.footer {
  margin: 24px 0 0;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
  text-align: center;
}

.footer a {
  color: var(--color-primary, #2d6a4f);
  font-weight: 600;
}

.footer a:hover {
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 480px) {
  .card {
    padding: 32px 24px 24px;
    border-radius: 20px;
  }
  
  h1 {
    font-size: 24px;
  }
}
</style>
