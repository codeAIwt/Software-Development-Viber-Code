<script setup>
import { ref, watch } from 'vue';
import * as userApi from '../api/user';
import { useUiStore } from '../store';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  currentAvatar: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue', 'avatarUpdated']);

const ui = useUiStore();
const avatarUrl = ref('');
const loading = ref(false);

watch(() => props.modelValue, (val) => {
  if (val) {
    avatarUrl.value = props.currentAvatar || '';
  }
});

function close() {
  emit('update:modelValue', false);
}

async function save() {
  if (!avatarUrl.value.trim()) {
    ui.showToast('请输入头像URL');
    return;
  }

  loading.value = true;
  try {
    const { data } = await userApi.updateAvatar(avatarUrl.value.trim());
    if (data.code === 200) {
      ui.showToast('头像更新成功');
      emit('avatarUpdated', data.data.avatar);
      close();
    } else {
      ui.showToast(data.msg || '更新失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || '更新失败');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="avatar-dialog-overlay" @click.self="close">
      <div class="avatar-dialog">
        <div class="dialog-header">
          <span>更换头像</span>
          <button class="close-btn" @click="close">&times;</button>
        </div>
        <div class="dialog-body">
          <div class="avatar-preview">
            <div
              class="preview-avatar"
              :style="{ backgroundImage: avatarUrl ? `url(${avatarUrl})` : 'none' }"
            >
              <span v-if="!avatarUrl" class="preview-placeholder">?</span>
            </div>
          </div>
          <div class="form-item">
            <label>头像URL</label>
            <input
              v-model="avatarUrl"
              type="text"
              placeholder="请输入头像图片URL"
              @keyup.enter="save"
            />
          </div>
          <p class="tip">输入图片链接地址，支持 JPG、PNG、GIF 等格式</p>
        </div>
        <div class="dialog-footer">
          <button class="cancel-btn" @click="close">取消</button>
          <button class="save-btn" :disabled="loading" @click="save">
            {{ loading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.avatar-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.avatar-dialog {
  background: #fff;
  border-radius: 16px;
  width: 320px;
  max-width: 90vw;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e6eaf2;
  font-weight: 600;
  font-size: 16px;
  color: #1c2533;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #6b7280;
}

.dialog-body {
  padding: 20px;
}

.avatar-preview {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.preview-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #f1f3f5;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #e6eaf2;
}

.preview-placeholder {
  font-size: 32px;
  color: #adb5bd;
}

.form-item {
  margin-bottom: 12px;
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #6b7280;
}

.form-item input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e6eaf2;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-item input:focus {
  border-color: #3b82f6;
}

.tip {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e6eaf2;
}

.cancel-btn,
.save-btn {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f1f3f5;
  border: none;
  color: #6b7280;
}

.cancel-btn:hover {
  background: #e9ecef;
}

.save-btn {
  background: #3b82f6;
  border: none;
  color: #fff;
}

.save-btn:hover:not(:disabled) {
  background: #2563eb;
}

.save-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
