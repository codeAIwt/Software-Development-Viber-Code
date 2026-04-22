<script setup>
import StudyRoomList from "../components/StudyRoomList.vue";
</script>

<template>
  <div class="wrap">
    <header class="bar">
      <router-link to="/home">返回首页</router-link>
      <h2>自习室</h2>
    </header>
    <StudyRoomList />
  </div>
</template>

<style scoped>
.wrap {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 20px 40px;
}
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e6eaf2;
}
h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.3px;
}
</style>
