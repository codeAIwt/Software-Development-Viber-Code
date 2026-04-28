from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from config.db import get_db
from models.user import User
from services.duration_service import (
    get_user_daily_duration,
    get_user_weekly_duration,
    get_user_period_duration,
    get_weekly_rank_list,
    get_monthly_rank_list,
    get_rank_list
)
from utils import auth as auth_utils

router = APIRouter()


def _json_ok(data=None, msg: str = "OK"):
    return {"code": 200, "msg": msg, "data": data if data is not None else {}}


def _get_week_start(d: date) -> date:
    """获取给定日期所在周的周一"""
    return d - timedelta(days=d.weekday())


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
    获取学习时长排行榜（日榜）
    """
    if not study_date:
        study_date = date.today()

    data = get_rank_list(db, study_date, limit)
    return _json_ok(data, "获取成功")


@router.get("/rank/weekly")
def get_weekly_rank(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    week_start: date = Query(None, description="周开始日期（周一），默认为本周一"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制")
):
    """
    获取学习时长周排行榜
    """
    if not week_start:
        week_start = _get_week_start(date.today())

    data = get_weekly_rank_list(db, week_start, limit)
    return _json_ok(data, "获取成功")


@router.get("/rank/monthly")
def get_monthly_rank(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    year: int = Query(None, description="年份，默认为今年"),
    month: int = Query(None, description="月份，默认为本月"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制")
):
    """
    获取学习时长月排行榜
    """
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    data = get_monthly_rank_list(db, year, month, limit)
    return _json_ok(data, "获取成功")


@router.get("/period/summary")
def get_period_summary(
    user: User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
    period: str = Query("week", description="时间段：week 或 month")
):
    """
    获取用户周或月学习时长汇总
    """
    today = date.today()

    if period == "week":
        week_start = _get_week_start(today)
        week_end = week_start + timedelta(days=6)
        data = get_user_period_duration(db, user.id, week_start, week_end)
    elif period == "month":
        if today.month == 12:
            month_start = date(today.year, 12, 1)
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_start = date(today.year, today.month, 1)
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        data = get_user_period_duration(db, user.id, month_start, month_end)
    else:
        return {"code": 400, "msg": "period 参数非法，只支持 week 或 month", "data": {}}

    return _json_ok(data, "获取成功")