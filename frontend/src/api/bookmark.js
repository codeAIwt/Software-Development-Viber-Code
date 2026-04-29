import client from "./client";

/**
 * 创建收藏
 */
export function createBookmark(data) {
  return client.post("/bookmark", data);
}

/**
 * 获取用户的收藏列表
 * @param {string} tag - 可选，筛选标签
 */
export function getBookmarks(tag) {
  return client.get("/bookmark", { params: tag ? { tag } : {} });
}

/**
 * 获取用户的所有标签
 */
export function getAllTags() {
  return client.get("/bookmark/tags");
}

/**
 * 更新收藏的标签
 */
export function updateBookmarkTags(bookmarkId, tags) {
  return client.put(`/bookmark/${bookmarkId}/tags`, { tags });
}

/**
 * 删除收藏
 */
export function deleteBookmark(bookmarkId) {
  return client.delete(`/bookmark/${bookmarkId}`);
}

/**
 * 删除标签（从所有收藏中移除）
 */
export function deleteTag(tag) {
  return client.delete(`/bookmark/tag/${encodeURIComponent(tag)}`);
}
