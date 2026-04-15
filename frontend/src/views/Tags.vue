<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import * as userApi from "../api/user";
import { useUiStore } from "../store";

const router = useRouter();
const ui = useUiStore();

// 热门标签列表
const tags = [
  "考研",
  "期末考试",
  "考公",
  "英语四级",
  "英语六级",
  "托福",
  "雅思",
  "计算机二级",
  "教师资格证",
  "注册会计师",
  "司法考试",
  "考研数学",
  "考研英语",
  "考研政治",
  "专业课"
];

// 选中的标签
const selectedTags = ref([]);
const saving = ref(false);

// 切换标签选择
function toggleTag(tag) {
  const index = selectedTags.value.indexOf(tag);
  if (index > -1) {
    selectedTags.value.splice(index, 1);
  } else {
    selectedTags.value.push(tag);
  }
}

// 保存标签
async function saveTags() {
  saving.value = true;
  try {
    const { data } = await userApi.updateTags(selectedTags.value);
    if (data.code !== 200) {
      ui.showToast(data.msg || "保存失败");
      return;
    }
    ui.showToast("标签设置成功");
    await router.replace("/home");
  } catch (e) {
    ui.showToast(e.response?.data?.msg || e.message || "网络错误");
  } finally {
    saving.value = false;
  }
}

// 跳过标签选择
async function skipTags() {
  await router.replace("/home");
}
</script>

<template>
  <div class="wrap">
    <div class="card">
      <h2>选择学习标签</h2>
      <p class="subtitle">选择你感兴趣的学习标签，我们将为你推荐相关的自习室</p>
      
      <div class="tags-container">
        <button 
          v-for="tag in tags" 
          :key="tag"
          class="tag" 
          :class="{ active: selectedTags.includes(tag) }"
          @click="toggleTag(tag)"
        >
          {{ tag }}
        </button>
      </div>
      
      <div class="actions">
        <button class="secondary" type="button" @click="skipTags">
          跳过
        </button>
        <button class="primary" type="button" :disabled="saving" @click="saveTags">
          {{ saving ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.card {
  width: min(500px, 100%);
  background: #fff;
  border-radius: 16px;
  padding: 32px 28px;
  box-shadow: 0 18px 50px rgba(28, 37, 51, 0.08);
  border: 1px solid #eceff5;
}

h2 {
  margin: 0 0 8px;
  font-size: 22px;
  text-align: center;
}

.subtitle {
  margin: 0 0 24px;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 24px;
}

.tag {
  padding: 8px 16px;
  border: 1px solid #d7dbe4;
  border-radius: 20px;
  background: #f9fafb;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tag:hover {
  border-color: #3b5bfd;
  background: #eff6ff;
}

.tag.active {
  border-color: #3b5bfd;
  background: #3b5bfd;
  color: #fff;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.primary {
  padding: 10px 24px;
  border: none;
  border-radius: 10px;
  background: #3b5bfd;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.secondary {
  padding: 10px 24px;
  border: 1px solid #d7dbe4;
  border-radius: 10px;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  font-weight: 600;
}
</style>