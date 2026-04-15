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
  background: linear-gradient(180deg, #f6f7fb 0%, #eef1f7 100%);
  color: #1c2533;
}
</style>
