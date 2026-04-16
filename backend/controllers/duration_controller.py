from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from config.db import get_db
from models.user import User
from services.duration_service import (
    get_user_daily_duration,
    get_user_weekly_duration,
    get_rank_list
)
from utils import auth as auth_utils

router = APIRouter()


def _json_ok(data=None, msg: str = "OK"):
    return {"code": 200, "msg": msg, "data": data if data is not None else {}}


@router.get("/daily")
def get_daily_duration(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    study_date: date = Query(None, description="学习日期，默认为今天")
):
    """
    获取用户每日学习时长
    """
    if not study_date:
        study_date = date.today()
    
    data = get_user_daily_duration(db, user.id, study_date)
    return _json_ok(data, "获取成功")


@router.get("/weekly")
def get_weekly_duration(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户最近7天学习时长
    """
    data = get_user_weekly_duration(db, user.id)
    return _json_ok(data, "获取成功")


@router.get("/rank")
def get_rank(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    study_date: date = Query(None, description="学习日期，默认为今天"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制")
):
    """
    获取学习时长排行榜
    """
    if not study_date:
        study_date = date.today()
    
    data = get_rank_list(db, study_date, limit)
    return _json_ok(data, "获取成功")