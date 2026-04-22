<script setup>
import { storeToRefs } from "pinia";
import { useUiStore } from "../store";

const ui = useUiStore();
const { toast } = storeToRefs(ui);
</script>

<template>
  <Transition name="fade">
    <div v-if="toast.visible" class="toast">{{ toast.message }}</div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  left: 50%;
  bottom: 88px;
  transform: translateX(-50%);
  background: rgba(28, 37, 51, 0.92);
  color: #fff;
  padding: 11px 20px;
  border-radius: 12px;
  font-size: 14px;
  z-index: 9999;
  max-width: 90vw;
  text-align: center;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
.fade-enter-active,
.fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
</style>
