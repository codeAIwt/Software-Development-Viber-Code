<script setup>
import CommonToast from "./components/CommonToast.vue";
</script>

<template>
  <CommonToast />
  <div class="page-shell">
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.page-shell {
  min-height: 100vh;
  background: var(--color-bg, #f6f7fb);
  color: var(--color-text, #1c2533);
}

/* Page Transition */
.page-enter-active {
  animation: pageEnter 0.35s ease-out;
}

.page-leave-active {
  animation: pageLeave 0.25s ease-in;
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pageLeave {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-12px);
  }
}
</style>
