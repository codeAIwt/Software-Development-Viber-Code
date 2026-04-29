"""收藏夹API路由"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.db import get_db
from models.user import User
import services.bookmark_service as bookmark_service
from utils.auth import get_current_user


router = APIRouter(tags=["收藏夹"])


class CreateBookmarkBody(BaseModel):
    title: str
    url: str
    tags: Optional[str] = None


class UpdateTagsBody(BaseModel):
    tags: str


def _json_ok(data=None, msg="操作成功"):
    result = {"code": 200, "msg": msg}
    if data is not None:
        result["data"] = data
    return result


def _json_err(status_code: int, code: int, msg: str):
    return {"code": code, "msg": msg}


@router.post("")
def create_bookmark(
    body: CreateBookmarkBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建收藏"""
    try:
        bookmark = bookmark_service.create_bookmark(
            db, user.id, body.title, body.url, body.tags
        )
        return _json_ok({
            "id": bookmark.id,
            "title": bookmark.title,
            "url": bookmark.url,
            "tags": bookmark.tags,
            "created_time": bookmark.created_time.isoformat() if bookmark.created_time else None
        }, msg="收藏成功")
    except bookmark_service.BookmarkServiceError as e:
        return _json_err(400, e.code, e.msg)


@router.get("")
def get_bookmarks(
    tag: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有收藏"""
    try:
        bookmarks = bookmark_service.get_user_bookmarks(db, user.id, tag)
        return _json_ok([{
            "id": b.id,
            "title": b.title,
            "url": b.url,
            "tags": b.tags,
            "created_time": b.created_time.isoformat() if b.created_time else None
        } for b in bookmarks])
    except Exception as e:
        return _json_err(500, 500, str(e))


@router.get("/tags")
def get_all_tags(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有标签"""
    try:
        tags = bookmark_service.get_user_all_tags(db, user.id)
        return _json_ok(tags)
    except Exception as e:
        return _json_err(500, 500, str(e))


@router.put("/{bookmark_id}/tags")
def update_tags(
    bookmark_id: int,
    body: UpdateTagsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新收藏的标签"""
    try:
        bookmark = bookmark_service.update_bookmark_tags(
            db, user.id, bookmark_id, body.tags
        )
        return _json_ok({
            "id": bookmark.id,
            "tags": bookmark.tags
        }, msg="标签更新成功")
    except bookmark_service.BookmarkServiceError as e:
        return _json_err(400, e.code, e.msg)


@router.delete("/{bookmark_id}")
def delete_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除收藏"""
    try:
        bookmark_service.delete_bookmark(db, user.id, bookmark_id)
        return _json_ok(msg="删除成功")
    except bookmark_service.BookmarkServiceError as e:
        return _json_err(400, e.code, e.msg)


@router.delete("/tag/{tag}")
def delete_tag(
    tag: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除标签（从所有收藏中移除）"""
    try:
        count = bookmark_service.delete_tag_from_all(db, user.id, tag)
        return _json_ok({"count": count}, msg=f"已从{count}个收藏中删除标签「{tag}」")
    except Exception as e:
        return _json_err(500, 500, str(e))
