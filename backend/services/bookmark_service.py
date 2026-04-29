"""收藏夹业务逻辑"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.bookmark import Bookmark


class BookmarkServiceError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(msg)


def create_bookmark(db: Session, user_id: str, title: str, url: str, tags: Optional[str] = None) -> Bookmark:
    """创建收藏"""
    if not title or len(title) > 200:
        raise BookmarkServiceError(400, "标题长度不合法，最多200字符")
    if not url or len(url) > 2000:
        raise BookmarkServiceError(400, "URL长度不合法，最多2000字符")
    if tags and len(tags) > 255:
        raise BookmarkServiceError(400, "标签长度超出限制")

    bookmark = Bookmark(
        user_id=user_id,
        title=title.strip(),
        url=url.strip(),
        tags=tags.strip() if tags else "",
        created_time=datetime.now(timezone(timedelta(hours=8)))
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def get_user_bookmarks(db: Session, user_id: str, tag: Optional[str] = None) -> list:
    """获取用户的所有收藏"""
    query = db.query(Bookmark).filter(Bookmark.user_id == user_id)

    if tag:
        tags_list = [t.strip() for t in tag.split(",") if t.strip()]
        if tags_list:
            for t in tags_list:
                query = query.filter(Bookmark.tags.contains(t))

    bookmarks = query.order_by(Bookmark.created_time.desc()).all()
    return bookmarks


def get_user_all_tags(db: Session, user_id: str) -> list:
    """获取用户的所有标签（去重）"""
    bookmarks = db.query(Bookmark.tags).filter(Bookmark.user_id == user_id).all()
    all_tags = set()
    for record in bookmarks:
        if record.tags:
            for t in record.tags.split(","):
                t = t.strip()
                if t:
                    all_tags.add(t)
    return sorted(list(all_tags))


def update_bookmark_tags(db: Session, user_id: str, bookmark_id: int, tags: str) -> Bookmark:
    """更新收藏的标签"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise BookmarkServiceError(404, "收藏不存在")

    if tags and len(tags) > 255:
        raise BookmarkServiceError(400, "标签长度超出限制")

    bookmark.tags = tags.strip() if tags else ""
    db.commit()
    db.refresh(bookmark)
    return bookmark


def delete_bookmark(db: Session, user_id: str, bookmark_id: int) -> bool:
    """删除收藏"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise BookmarkServiceError(404, "收藏不存在")

    db.delete(bookmark)
    db.commit()
    return True


def delete_tag_from_all(db: Session, user_id: str, tag_to_delete: str) -> int:
    """从所有收藏中删除指定标签，返回受影响的收藏数量"""
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.tags.contains(tag_to_delete)
    ).all()

    count = 0
    for bookmark in bookmarks:
        if bookmark.tags:
            tags_list = [t.strip() for t in bookmark.tags.split(",") if t.strip()]
            if tag_to_delete in tags_list:
                tags_list.remove(tag_to_delete)
                bookmark.tags = ",".join(tags_list)
                count += 1

    if count > 0:
        db.commit()
    return count
