<script setup>
import { storeToRefs } from "pinia";
import { useUiStore } from "../store";

const ui = useUiStore();
const { toast } = storeToRefs(ui);

// 根据消息内容自动判断类型
function getToastType() {
  const msg = toast.value.message?.toLowerCase() || '';
  if (msg.includes('成功') || msg.includes('完成') || msg.includes('已')) return 'success';
  if (msg.includes('失败') || msg.includes('错误') || msg.includes('无法')) return 'error';
  if (msg.includes('警告') || msg.includes('注意')) return 'warning';
  return 'info';
}
</script>

<template>
  <Transition name="toast">
    <div v-if="toast.visible" class="toast-container">
      <div class="toast" :class="[`toast-${getToastType()}`]">
        <!-- 图标 -->
        <div class="toast-icon">
          <!-- 成功 -->
          <svg v-if="getToastType() === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="9 12 11.5 14.5 16 10"/>
          </svg>
          <!-- 错误 -->
          <svg v-else-if="getToastType() === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <!-- 警告 -->
          <svg v-else-if="getToastType() === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <!-- 信息 -->
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
        </div>
        <!-- 消息 -->
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.toast-container {
  position: fixed;
  left: 50%;
  bottom: 88px;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 500;
  max-width: 90vw;
  text-align: left;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18), 0 4px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(12px);
  pointer-events: auto;
}

.toast-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-message {
  line-height: 1.4;
}

/* Toast 类型样式 */
.toast-success {
  background: linear-gradient(135deg, #2d6a4f 0%, #40916c 100%);
  color: #fff;
}

.toast-success .toast-icon {
  color: #a7f3d0;
}

.toast-error {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
  color: #fff;
}

.toast-error .toast-icon {
  color: #fecaca;
}

.toast-warning {
  background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
  color: #fff;
}

.toast-warning .toast-icon {
  color: #fef3c7;
}

.toast-info {
  background: rgba(28, 37, 51, 0.95);
  color: #fff;
}

.toast-info .toast-icon {
  color: #94a3b8;
}

/* 动画 */
.toast-enter-active {
  animation: toastEnter 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
}

.toast-leave-active {
  animation: toastLeave 0.25s cubic-bezier(0.06, 0.71, 0.55, 1);
}

@keyframes toastEnter {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(24px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes toastLeave {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(-12px) scale(0.95);
  }
}

/* 响应式 */
@media (max-width: 640px) {
  .toast-container {
    bottom: 100px;
    left: 16px;
    right: 16px;
    transform: none;
  }
  
  .toast {
    width: 100%;
    justify-content: center;
    text-align: center;
  }
}
</style>
