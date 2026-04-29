<script setup>
import { ref, onMounted, computed } from 'vue';
import * as bookmarkApi from '../api/bookmark';
import { useUiStore } from '../store';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'dialog'
  }
});

const emit = defineEmits(['update:modelValue']);

const ui = useUiStore();
const bookmarks = ref([]);
const allTags = ref([]);
const selectedTag = ref('');
const loading = ref(false);
const showAddDialog = ref(false);
const showEditTagsDialog = ref(false);
const showDeleteDialog = ref(false);
const showDeleteTagDialog = ref(false);

const newBookmark = ref({ title: '', url: '', tags: '' });
const editingBookmark = ref(null);
const editingTags = ref('');
const deletingBookmarkId = ref(null);
const deletingTag = ref('');

const filteredBookmarks = computed(() => {
  if (!selectedTag.value) return bookmarks.value;
  return bookmarks.value.filter(b => {
    if (!b.tags) return false;
    return b.tags.split(',').map(t => t.trim()).includes(selectedTag.value);
  });
});

async function loadData() {
  loading.value = true;
  try {
    const [bookmarksRes, tagsRes] = await Promise.all([
      bookmarkApi.getBookmarks(),
      bookmarkApi.getAllTags()
    ]);
    if (bookmarksRes.data.code === 200) {
      bookmarks.value = bookmarksRes.data.data;
    }
    if (tagsRes.data.code === 200) {
      allTags.value = tagsRes.data.data;
    }
  } catch (e) {
    console.error('加载收藏失败', e);
  } finally {
    loading.value = false;
  }
}

async function addBookmark() {
  if (!newBookmark.value.title.trim()) {
    ui.showToast('请输入标题');
    return;
  }
  if (!newBookmark.value.url.trim()) {
    ui.showToast('请输入网址');
    return;
  }

  try {
    const { data } = await bookmarkApi.createBookmark(newBookmark.value);
    if (data.code === 200) {
      ui.showToast('收藏成功');
      bookmarks.value.unshift(data.data);
      if (newBookmark.value.tags) {
        const newTags = newBookmark.value.tags.split(',').map(t => t.trim()).filter(t => t);
        newTags.forEach(t => {
          if (!allTags.value.includes(t)) allTags.value.push(t);
        });
      }
      closeAddDialog();
    } else {
      ui.showToast(data.msg || '收藏失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || '收藏失败');
  }
}

function confirmDelete(bookmarkId) {
  deletingBookmarkId.value = bookmarkId;
  showDeleteDialog.value = true;
}

async function executeDelete() {
  if (!deletingBookmarkId.value) return;
  const id = deletingBookmarkId.value;
  try {
    const { data } = await bookmarkApi.deleteBookmark(id);
    if (data.code === 200) {
      ui.showToast('删除成功');
      bookmarks.value = bookmarks.value.filter(b => b.id !== id);
    } else {
      ui.showToast(data.msg || '删除失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || '删除失败');
  } finally {
    closeDeleteDialog();
  }
}

function closeDeleteDialog() {
  showDeleteDialog.value = false;
  deletingBookmarkId.value = null;
}

function confirmDeleteTag(tag) {
  deletingTag.value = tag;
  showDeleteTagDialog.value = true;
}

async function executeDeleteTag() {
  if (!deletingTag.value) return;
  const tag = deletingTag.value;
  try {
    const { data } = await bookmarkApi.deleteTag(tag);
    if (data.code === 200) {
      ui.showToast(data.msg || '标签已删除');
      if (selectedTag.value === tag) {
        selectedTag.value = '';
      }
      allTags.value = (await bookmarkApi.getAllTags()).data.data || [];
      bookmarks.value = (await bookmarkApi.getBookmarks()).data.data || [];
    } else {
      ui.showToast(data.msg || '删除失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || '删除失败');
  } finally {
    closeDeleteTagDialog();
  }
}

function closeDeleteTagDialog() {
  showDeleteTagDialog.value = false;
  deletingTag.value = '';
}

async function removeTagFromBookmark(bookmark, tagToRemove) {
  const tags = bookmark.tags.split(',').map(t => t.trim()).filter(t => t);
  const newTags = tags.filter(t => t !== tagToRemove).join(',');
  try {
    const { data } = await bookmarkApi.updateBookmarkTags(bookmark.id, newTags);
    if (data.code === 200) {
      bookmark.tags = data.data.tags;
      allTags.value = (await bookmarkApi.getAllTags()).data.data || [];
    }
  } catch (e) {
    ui.showToast('删除标签失败');
  }
}

async function updateTags() {
  if (!editingBookmark.value) return;
  try {
    const { data } = await bookmarkApi.updateBookmarkTags(editingBookmark.value.id, editingTags.value);
    if (data.code === 200) {
      ui.showToast('标签更新成功');
      const idx = bookmarks.value.findIndex(b => b.id === editingBookmark.value.id);
      if (idx !== -1) bookmarks.value[idx].tags = data.data.tags;
      allTags.value = (await bookmarkApi.getAllTags()).data.data || [];
      closeEditTagsDialog();
    } else {
      ui.showToast(data.msg || '更新失败');
    }
  } catch (e) {
    ui.showToast(e.response?.data?.msg || '更新失败');
  }
}

function openEditTags(bookmark) {
  editingBookmark.value = bookmark;
  editingTags.value = bookmark.tags || '';
  showEditTagsDialog.value = true;
}

function closeAddDialog() {
  showAddDialog.value = false;
  newBookmark.value = { title: '', url: '', tags: '' };
}

function closeEditTagsDialog() {
  showEditTagsDialog.value = false;
  editingBookmark.value = null;
  editingTags.value = '';
}

function openUrl(url) {
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }
  window.open(url, '_blank');
}

function close() {
  emit('update:modelValue', false);
}

function selectTag(tag) {
  selectedTag.value = selectedTag.value === tag ? '' : tag;
}

onMounted(loadData);
</script>

<template>
  <!-- 弹窗模式 -->
  <Teleport to="body" v-if="mode === 'dialog'">
    <div v-if="modelValue" class="bookmark-overlay" @click.self="close">
      <div class="bookmark-panel">
        <div class="panel-header">
          <h3>收藏夹</h3>
          <div class="header-actions">
            <button class="add-btn" @click="showAddDialog = true">+ 添加</button>
            <button class="close-btn" @click="close">&times;</button>
          </div>
        </div>

        <div class="tag-filter" v-if="allTags.length > 0">
          <div
            v-for="tag in allTags"
            :key="tag"
            class="tag-chip-wrapper"
          >
            <button
              class="tag-chip"
              :class="{ active: selectedTag === tag }"
              @click="selectTag(tag)"
            >
              {{ tag }}
            </button>
            <button class="tag-chip-delete" @click.stop="confirmDeleteTag(tag)">×</button>
          </div>
        </div>

        <div class="bookmark-list" v-if="!loading">
          <div
            v-for="bookmark in filteredBookmarks"
            :key="bookmark.id"
            class="bookmark-item"
          >
            <div class="bookmark-content" @click="openUrl(bookmark.url)">
              <div class="bookmark-title">{{ bookmark.title }}</div>
              <div class="bookmark-url">{{ bookmark.url }}</div>
              <div class="bookmark-tags" v-if="bookmark.tags">
                <span
                  v-for="tag in bookmark.tags.split(',')"
                  :key="tag"
                  class="tag"
                >
                  {{ tag.trim() }}
                  <button class="tag-delete" @click.stop="removeTagFromBookmark(bookmark, tag.trim())">×</button>
                </span>
              </div>
            </div>
            <div class="bookmark-actions">
              <button class="action-btn" @click.stop="openEditTags(bookmark)" title="编辑标签">🏷️</button>
              <button class="action-btn" @click.stop="confirmDelete(bookmark.id)" title="删除">🗑️</button>
            </div>
          </div>
          <div v-if="filteredBookmarks.length === 0" class="empty-state">
            <p>{{ selectedTag ? '该标签下没有收藏' : '暂无收藏' }}</p>
          </div>
        </div>
        <div v-else class="loading">加载中...</div>
      </div>

      <!-- 添加收藏弹窗 -->
      <div v-if="showAddDialog" class="mini-dialog">
        <div class="mini-dialog-header">添加收藏</div>
        <div class="mini-dialog-body">
          <input v-model="newBookmark.title" placeholder="标题" class="dialog-input" />
          <input v-model="newBookmark.url" placeholder="网址 (URL)" class="dialog-input" />
          <input v-model="newBookmark.tags" placeholder="标签 (多个用英文逗号隔开)" class="dialog-input" />
        </div>
        <div class="mini-dialog-footer">
          <button class="btn-secondary" @click="closeAddDialog">取消</button>
          <button class="btn-primary" @click="addBookmark">添加</button>
        </div>
      </div>

      <!-- 编辑标签弹窗 -->
      <div v-if="showEditTagsDialog" class="mini-dialog">
        <div class="mini-dialog-header">编辑标签</div>
        <div class="mini-dialog-body">
          <input v-model="editingTags" placeholder="标签 (多个用英文逗号隔开)" class="dialog-input" />
        </div>
        <div class="mini-dialog-footer">
          <button class="btn-secondary" @click="closeEditTagsDialog">取消</button>
          <button class="btn-primary" @click="updateTags">保存</button>
        </div>
      </div>

      <!-- 删除确认弹窗 -->
      <div v-if="showDeleteDialog" class="mini-dialog">
        <div class="mini-dialog-header">确认删除</div>
        <div class="mini-dialog-body">
          <p class="delete-tip">确定要删除该收藏吗？此操作不可撤销。</p>
        </div>
        <div class="mini-dialog-footer">
          <button class="btn-secondary" @click="closeDeleteDialog">取消</button>
          <button class="btn-danger" @click="executeDelete">删除</button>
        </div>
      </div>

      <!-- 删除标签确认弹窗 -->
      <div v-if="showDeleteTagDialog" class="mini-dialog">
        <div class="mini-dialog-header">删除标签</div>
        <div class="mini-dialog-body">
          <p class="delete-tip">确定要删除标签「{{ deletingTag }}」吗？</p>
          <p class="delete-warning">所有使用此标签的收藏都将被移除该标签。</p>
        </div>
        <div class="mini-dialog-footer">
          <button class="btn-secondary" @click="closeDeleteTagDialog">取消</button>
          <button class="btn-danger" @click="executeDeleteTag">删除</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 悬浮模式 -->
  <div v-if="mode === 'float' && modelValue" class="bookmark-float-content">
    <div class="tag-filter" v-if="allTags.length > 0">
      <div
        v-for="tag in allTags"
        :key="tag"
        class="tag-chip-wrapper"
      >
        <button
          class="tag-chip"
          :class="{ active: selectedTag === tag }"
          @click="selectTag(tag)"
        >
          {{ tag }}
        </button>
        <button class="tag-chip-delete" @click.stop="confirmDeleteTag(tag)">×</button>
      </div>
    </div>

    <div class="bookmark-list" v-if="!loading">
      <div
        v-for="bookmark in filteredBookmarks"
        :key="bookmark.id"
        class="bookmark-item"
      >
        <div class="bookmark-content" @click="openUrl(bookmark.url)">
          <div class="bookmark-title">{{ bookmark.title }}</div>
          <div class="bookmark-url">{{ bookmark.url }}</div>
          <div class="bookmark-tags" v-if="bookmark.tags">
            <span
              v-for="tag in bookmark.tags.split(',')"
              :key="tag"
              class="tag"
            >
              {{ tag.trim() }}
              <button class="tag-delete" @click.stop="removeTagFromBookmark(bookmark, tag.trim())">×</button>
            </span>
          </div>
        </div>
        <div class="bookmark-actions">
          <button class="action-btn" @click.stop="openEditTags(bookmark)" title="编辑标签">🏷️</button>
          <button class="action-btn" @click.stop="confirmDelete(bookmark.id)" title="删除">🗑️</button>
        </div>
      </div>
      <div v-if="filteredBookmarks.length === 0" class="empty-state">
        <p>{{ selectedTag ? '该标签下没有收藏' : '暂无收藏' }}</p>
      </div>
    </div>
    <div v-else class="loading">加载中...</div>

    <!-- 添加收藏按钮 -->
    <button class="float-add-btn" @click="showAddDialog = true">+ 添加收藏</button>

    <!-- 添加收藏弹窗 -->
    <div v-if="showAddDialog" class="mini-dialog">
      <div class="mini-dialog-header">添加收藏</div>
      <div class="mini-dialog-body">
        <input v-model="newBookmark.title" placeholder="标题" class="dialog-input" />
        <input v-model="newBookmark.url" placeholder="网址 (URL)" class="dialog-input" />
        <input v-model="newBookmark.tags" placeholder="标签 (多个用英文逗号隔开)" class="dialog-input" />
      </div>
      <div class="mini-dialog-footer">
        <button class="btn-secondary" @click="closeAddDialog">取消</button>
        <button class="btn-primary" @click="addBookmark">添加</button>
      </div>
    </div>

    <!-- 编辑标签弹窗 -->
    <div v-if="showEditTagsDialog" class="mini-dialog">
      <div class="mini-dialog-header">编辑标签</div>
      <div class="mini-dialog-body">
        <input v-model="editingTags" placeholder="标签 (多个用英文逗号隔开)" class="dialog-input" />
      </div>
      <div class="mini-dialog-footer">
        <button class="btn-secondary" @click="closeEditTagsDialog">取消</button>
        <button class="btn-primary" @click="updateTags">保存</button>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteDialog" class="mini-dialog">
      <div class="mini-dialog-header">确认删除</div>
      <div class="mini-dialog-body">
        <p class="delete-tip">确定要删除该收藏吗？此操作不可撤销。</p>
      </div>
      <div class="mini-dialog-footer">
        <button class="btn-secondary" @click="closeDeleteDialog">取消</button>
        <button class="btn-danger" @click="executeDelete">删除</button>
      </div>
    </div>

    <!-- 删除标签确认弹窗 -->
    <div v-if="showDeleteTagDialog" class="mini-dialog">
      <div class="mini-dialog-header">删除标签</div>
      <div class="mini-dialog-body">
        <p class="delete-tip">确定要删除标签「{{ deletingTag }}」吗？</p>
        <p class="delete-warning">所有使用此标签的收藏都将被移除该标签。</p>
      </div>
      <div class="mini-dialog-footer">
        <button class="btn-secondary" @click="closeDeleteTagDialog">取消</button>
        <button class="btn-danger" @click="executeDeleteTag">删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bookmark-overlay {
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

.bookmark-panel {
  background: #fff;
  border-radius: 16px;
  width: 400px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bookmark-float-content {
  padding: 12px;
  max-height: calc(60vh - 60px);
  overflow-y: auto;
}

.float-add-btn {
  width: 100%;
  padding: 10px;
  margin-top: 8px;
  background: #f1f3f5;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #3b82f6;
  cursor: pointer;
  transition: background 0.2s;
}

.float-add-btn:hover {
  background: #e5e7eb;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e6eaf2;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1c2533;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-btn {
  background: #3b82f6;
  color: #fff;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
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

.tag-filter {
  padding: 12px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-bottom: 1px solid #f1f3f5;
}

.tag-chip-wrapper {
  display: flex;
  align-items: center;
  gap: 2px;
}

.tag-chip {
  background: #f1f3f5;
  border: none;
  padding: 4px 10px;
  border-radius: 12px 0 0 12px;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-chip.active {
  background: #3b82f6;
  color: #fff;
}

.tag-chip-wrapper:hover .tag-chip {
  background: #e5e7eb;
}

.tag-chip-wrapper:hover .tag-chip.active {
  background: #2563eb;
}

.tag-chip-delete {
  background: #f1f3f5;
  border: none;
  padding: 4px 6px;
  border-radius: 0 12px 12px 0;
  font-size: 12px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-chip-wrapper:hover .tag-chip-delete {
  background: #fee2e2;
  color: #ef4444;
}

.bookmark-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.bookmark-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f9fafb;
}

.bookmark-content {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.bookmark-title {
  font-size: 14px;
  font-weight: 500;
  color: #1c2533;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bookmark-url {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

.bookmark-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  background: #e5e7eb;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.tag-delete {
  background: none;
  border: none;
  padding: 0;
  margin-left: 2px;
  font-size: 14px;
  line-height: 1;
  color: #9ca3af;
  cursor: pointer;
}

.tag-delete:hover {
  color: #ef4444;
}

.bookmark-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  font-size: 14px;
  opacity: 0.6;
}

.action-btn:hover {
  opacity: 1;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

/* 弹窗样式 */
.mini-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  border-radius: 12px;
  width: 320px;
  max-width: 90vw;
  z-index: 1001;
}

.mini-dialog-header {
  padding: 16px 20px;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid #e6eaf2;
}

.mini-dialog-body {
  padding: 16px 20px;
}

.dialog-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e6eaf2;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.dialog-input:last-child {
  margin-bottom: 0;
}

.delete-tip {
  margin: 0 0 8px 0;
  color: #6b7280;
  font-size: 14px;
}

.delete-warning {
  margin: 0;
  color: #ef4444;
  font-size: 13px;
}

.mini-dialog-footer {
  display: flex;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid #e6eaf2;
}

.btn-secondary,
.btn-primary,
.btn-danger {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary {
  background: #f1f3f5;
  border: none;
  color: #6b7280;
}

.btn-primary {
  background: #3b82f6;
  border: none;
  color: #fff;
}

.btn-danger {
  background: #ef4444;
  border: none;
  color: #fff;
}
</style>
