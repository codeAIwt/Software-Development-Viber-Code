<script setup>
import { ref, computed } from "vue";
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
const showPassword = ref(false);
const showPassword2 = ref(false);

// 错误状态
const phoneError = ref("");
const passwordError = ref("");
const password2Error = ref("");
const shakePhone = ref(false);
const shakePassword = ref(false);
const shakePassword2 = ref(false);
const shakeAgreed = ref(false);

// 密码强度计算
const passwordStrength = computed(() => {
  const pwd = password.value;
  if (!pwd) return { level: 0, text: "", color: "" };
  
  let score = 0;
  if (pwd.length >= 6) score++;
  if (pwd.length >= 10) score++;
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^a-zA-Z0-9]/.test(pwd)) score++;
  
  if (score <= 2) return { level: 1, text: "弱", color: "#ef4444" };
  if (score <= 3) return { level: 2, text: "中", color: "#f59e0b" };
  return { level: 3, text: "强", color: "#22c55e" };
});

// 验证函数
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
  if (password.value.length < 6) {
    passwordError.value = "密码至少6位";
    return false;
  }
  passwordError.value = "";
  return true;
}

function validatePassword2() {
  if (!password2.value) {
    password2Error.value = "请确认密码";
    return false;
  }
  if (password.value !== password2.value) {
    password2Error.value = "两次密码不一致";
    return false;
  }
  password2Error.value = "";
  return true;
}

function triggerShake(field) {
  const shakeMap = {
    phone: shakePhone,
    password: shakePassword,
    password2: shakePassword2,
    agreed: shakeAgreed
  };
  const ref = shakeMap[field];
  if (ref) {
    ref.value = true;
    setTimeout(() => { ref.value = false; }, 500);
  }
}

async function onSubmit() {
  const phoneValid = validatePhone();
  const passwordValid = validatePassword();
  const password2Valid = validatePassword2();
  
  if (!phoneValid) {
    triggerShake("phone");
    return;
  }
  if (!passwordValid) {
    triggerShake("password");
    return;
  }
  if (!password2Valid) {
    triggerShake("password2");
    return;
  }
  if (!agreed.value) {
    triggerShake("agreed");
    ui.showToast("请先同意用户协议");
    return;
  }
  
  loading.value = true;
  try {
    const { data } = await userApi.register(phone.value.trim(), password.value);
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
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="floating-shape shape-1">
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="50" fill="#2d6a4f" opacity="0.06"/>
        </svg>
      </div>
      <div class="floating-shape shape-2">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <rect width="80" height="80" rx="20" fill="#f57c00" opacity="0.05"/>
        </svg>
      </div>
      <div class="floating-shape shape-3">
        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
          <polygon points="30,0 60,30 30,60 0,30" fill="#1976d2" opacity="0.05"/>
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

      <h1>创建账号</h1>
      <p class="subtitle">加入线上伴学，开启学习陪伴之旅</p>

      <!-- 步骤指示器 -->
      <div class="steps">
        <div class="step active">
          <div class="step-dot">1</div>
          <span>填写信息</span>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-dot">2</div>
          <span>选择标签</span>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-dot">3</div>
          <span>完成注册</span>
        </div>
      </div>

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
              autocomplete="new-password" 
              placeholder="请输入密码（至少6位）"
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
          <!-- 密码强度指示器 -->
          <div v-if="password" class="password-strength">
            <div class="strength-bars">
              <div class="strength-bar" :class="{ active: passwordStrength.level >= 1 }" :style="{ background: passwordStrength.level >= 1 ? passwordStrength.color : '' }"></div>
              <div class="strength-bar" :class="{ active: passwordStrength.level >= 2 }" :style="{ background: passwordStrength.level >= 2 ? passwordStrength.color : '' }"></div>
              <div class="strength-bar" :class="{ active: passwordStrength.level >= 3 }" :style="{ background: passwordStrength.level >= 3 ? passwordStrength.color : '' }"></div>
            </div>
            <span class="strength-text" :style="{ color: passwordStrength.color }">{{ passwordStrength.text }}</span>
          </div>
          <span v-if="passwordError" class="error-msg">{{ passwordError }}</span>
        </div>

        <div class="field" :class="{ error: password2Error, shake: shakePassword2 }">
          <label for="password2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            确认密码
          </label>
          <div class="password-wrapper">
            <input 
              id="password2"
              v-model="password2" 
              :type="showPassword2 ? 'text' : 'password'" 
              autocomplete="new-password" 
              placeholder="请再次输入密码"
              @blur="validatePassword2"
              @input="password2Error = ''"
            />
            <button 
              type="button" 
              class="toggle-password"
              @click="showPassword2 = !showPassword2"
              tabindex="-1"
            >
              <svg v-if="showPassword2" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
          <span v-if="password2Error" class="error-msg">{{ password2Error }}</span>
        </div>

        <label class="checkbox-field" :class="{ shake: shakeAgreed }">
          <input v-model="agreed" type="checkbox" />
          <span class="checkbox-custom">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </span>
          <span class="checkbox-text">我已阅读并同意<a href="#" @click.prevent>《用户协议》</a>与<a href="#" @click.prevent>《隐私政策》</a></span>
        </label>

        <button class="primary" type="submit" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? "注册中" : "注册" }}
        </button>
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
  animation: float 8s ease-in-out infinite;
}

.shape-1 {
  top: 5%;
  right: 10%;
  animation-delay: 0s;
}

.shape-2 {
  bottom: 10%;
  left: 5%;
  animation-delay: 2s;
}

.shape-3 {
  top: 40%;
  left: 10%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-25px) rotate(8deg);
  }
}

/* 卡片 */
.card {
  width: min(440px, 100%);
  background: #fff;
  border-radius: 24px;
  padding: 36px 36px 28px;
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
  margin-bottom: 20px;
}

h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  text-align: center;
  letter-spacing: -0.5px;
  color: var(--color-text, #1c2533);
}

.subtitle {
  margin: 8px 0 24px;
  color: var(--color-text-muted, #6b7280);
  font-size: 14px;
  text-align: center;
}

/* 步骤指示器 */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 28px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-border, #e6eaf2);
  color: var(--color-text-muted, #6b7280);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.step.active .step-dot {
  background: var(--color-primary, #2d6a4f);
  color: #fff;
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.3);
}

.step span {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
  font-weight: 500;
}

.step.active span {
  color: var(--color-primary, #2d6a4f);
}

.step-line {
  width: 40px;
  height: 2px;
  background: var(--color-border, #e6eaf2);
  margin-bottom: 20px;
}

/* 表单 */
.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
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

input[type="text"],
input[type="password"] {
  padding: 13px 16px;
  border-radius: 12px;
  border: 1.5px solid var(--color-border-light, #d7dbe4);
  background: var(--color-bg-input, #f9fafb);
  transition: all 0.2s ease;
  font-size: 15px;
  width: 100%;
}

input[type="text"]:focus,
input[type="password"]:focus {
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

/* 密码强度指示器 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.strength-bars {
  display: flex;
  gap: 4px;
}

.strength-bar {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background: var(--color-border, #e6eaf2);
  transition: all 0.3s ease;
}

.strength-text {
  font-size: 12px;
  font-weight: 600;
}

/* 复选框 */
.checkbox-field {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary, #374151);
}

.checkbox-field.shake {
  animation: shake 0.5s ease;
}

.checkbox-field input[type="checkbox"] {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border-light, #d7dbe4);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
  margin-top: 1px;
}

.checkbox-custom svg {
  opacity: 0;
  transform: scale(0);
  color: #fff;
  transition: all 0.2s ease;
}

.checkbox-field input:checked + .checkbox-custom {
  background: var(--color-primary, #2d6a4f);
  border-color: var(--color-primary, #2d6a4f);
}

.checkbox-field input:checked + .checkbox-custom svg {
  opacity: 1;
  transform: scale(1);
}

.checkbox-text {
  line-height: 1.5;
}

.checkbox-text a {
  color: var(--color-primary, #2d6a4f);
  font-weight: 500;
}

/* 主按钮 */
.primary {
  margin-top: 6px;
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

/* 底部 */
.footer {
  margin: 20px 0 0;
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
  text-align: center;
}

.footer a {
  color: var(--color-primary, #2d6a4f);
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 480px) {
  .card {
    padding: 28px 20px 24px;
    border-radius: 20px;
  }
  
  h1 {
    font-size: 22px;
  }
  
  .steps {
    gap: 4px;
  }
  
  .step span {
    display: none;
  }
  
  .step-line {
    width: 30px;
    margin-bottom: 0;
  }
}
</style>
