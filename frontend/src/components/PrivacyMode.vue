<script setup>
defineProps({
  label: { type: String, default: "隐私模式（占位）" },
});
</script>

<template>
  <div class="card">{{ label }}</div>
</template>

<style scoped>
.card {
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid #e3e7ef;
  font-size: 14px;
  color: #4b5565;
}
</style>
