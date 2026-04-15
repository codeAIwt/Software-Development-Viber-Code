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
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  z-index: 9999;
  max-width: 90vw;
  text-align: center;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
