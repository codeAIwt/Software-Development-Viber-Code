<script setup>
import CommonToast from "./components/CommonToast.vue";
</script>

<template>
  <CommonToast />
  <div class="page-shell">
    <router-view />
  </div>
</template>

<style scoped>
.page-shell {
  min-height: 100vh;
  background: #f6f7fb;
  color: #1c2533;
}
</style>
