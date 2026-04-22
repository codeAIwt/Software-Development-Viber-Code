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
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e3e7ef;
  font-size: 14px;
  color: #4b5565;
  box-shadow: 0 2px 6px rgba(28, 37, 51, 0.04);
  backdrop-filter: blur(8px);
}
</style>
