"""学习时长业务逻辑"""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.study_duration import StudyDuration
from utils import cache


def get_user_daily_duration(db: Session, user_id: str, study_date: date) -> dict:
    """
    获取用户某一天的学习时长
    :param db: 数据库会话
    :param user_id: 用户ID
    :param study_date: 学习日期
    :return: 学习时长信息
    """
    record = db.query(StudyDuration).filter(
        StudyDuration.user_id == user_id,
        StudyDuration.study_date == study_date
    ).first()
    
    if record:
        return {
            "user_id": user_id,
            "study_date": study_date,
            "total_minutes": record.total_minutes,
            "beat_percent": record.beat_percent
        }
    else:
        return {
            "user_id": user_id,
            "study_date": study_date,
            "total_minutes": 0,
            "beat_percent": None
        }


def get_user_weekly_duration(db: Session, user_id: str) -> list:
    """
    获取用户最近7天的学习时长
    :param db: 数据库会话
    :param user_id: 用户ID
    :return: 最近7天的学习时长列表
    """
    today = date.today()
    durations = []
    
    for i in range(7):
        study_date = today - timedelta(days=i)
        duration = get_user_daily_duration(db, user_id, study_date)
        durations.append(duration)
    
    return durations


def update_study_duration(db: Session, user_id: str, minutes: int) -> StudyDuration:
    """
    更新用户学习时长
    :param db: 数据库会话
    :param user_id: 用户ID
    :param minutes: 学习时长（分钟）
    :return: 更新后的学习时长记录
    """
    if minutes < 0:
        raise ValueError("学习时长不能为负数")
    
    today = date.today()
    
    # 查找或创建记录
    record = db.query(StudyDuration).filter(
        StudyDuration.user_id == user_id,
        StudyDuration.study_date == today
    ).first()
    
    if record:
        # 更新现有记录
        record.total_minutes += minutes
        # 截断到1440分钟（24小时）
        if record.total_minutes > 1440:
            record.total_minutes = 1440
    else:
        # 创建新记录
        record = StudyDuration(
            user_id=user_id,
            study_date=today,
            total_minutes=min(minutes, 1440),
            beat_percent=None,
            create_time=datetime.now()
        )
        db.add(record)
    
    db.commit()
    db.refresh(record)
    return record


def calculate_beat_percent(db: Session, study_date: date) -> None:
    """
    计算指定日期的击败百分比
    :param db: 数据库会话
    :param study_date: 学习日期
    """
    # 获取有效用户数（学习时长>0）
    effective_users = db.query(func.count(StudyDuration.id)).filter(
        StudyDuration.study_date == study_date,
        StudyDuration.total_minutes > 0
    ).scalar()
    
    if effective_users == 0:
        return
    
    # 获取所有用户的学习时长
    records = db.query(StudyDuration).filter(
        StudyDuration.study_date == study_date
    ).all()
    
    # 计算每个用户的击败百分比
    for record in records:
        if record.total_minutes == 0:
            record.beat_percent = None
        else:
            # 计算学习时长小于当前用户的人数
            less_count = db.query(func.count(StudyDuration.id)).filter(
                StudyDuration.study_date == study_date,
                StudyDuration.total_minutes < record.total_minutes
            ).scalar()
            
            # 计算击败百分比
            beat_percent = (less_count / effective_users) * 100
            # 四舍五入到两位小数
            record.beat_percent = round(beat_percent, 2)
    
    db.commit()
    
    # 更新Redis缓存
    update_rank_cache(db, study_date)


def update_rank_cache(db: Session, study_date: date) -> None:
    """
    更新排行榜缓存
    :param db: 数据库会话
    :param study_date: 学习日期
    """
    r = cache._redis()
    key = f"rank:beat:{study_date}"
    
    # 获取所有用户的击败百分比
    records = db.query(StudyDuration).filter(
        StudyDuration.study_date == study_date
    ).all()
    
    # 清空现有缓存
    r.delete(key)
    
    # 更新缓存
    for record in records:
        if record.beat_percent is not None:
            r.hset(key, record.user_id, str(record.beat_percent))
    
    # 设置缓存过期时间（48小时）
    r.expire(key, 48 * 60 * 60)


def get_rank_list(db: Session, study_date: date, limit: int = 10) -> list:
    """
    获取排行榜列表
    :param db: 数据库会话
    :param study_date: 学习日期
    :param limit: 返回数量限制
    :return: 排行榜列表
    """
    r = cache._redis()
    key = f"rank:beat:{study_date}"
    
    # 从缓存获取
    rank_data = r.hgetall(key)
    
    if rank_data:
        # 缓存存在，从缓存构建排行榜
        rank_items = []
        for user_id, beat_percent_str in rank_data.items():
            # 从数据库获取用户的学习时长
            record = db.query(StudyDuration).filter(
                StudyDuration.user_id == user_id,
                StudyDuration.study_date == study_date
            ).first()
            
            if record:
                rank_items.append({
                    "user_id": user_id,
                    "beat_percent": float(beat_percent_str),
                    "total_minutes": record.total_minutes
                })
        
        # 按击败百分比排序
        rank_items.sort(key=lambda x: x["beat_percent"], reverse=True)
        return rank_items[:limit]
    
    # 缓存不存在，实时计算排行榜
    return calculate_real_time_rank_list(db, study_date, limit)


def calculate_real_time_rank_list(db: Session, study_date: date, limit: int = 10) -> list:
    """
    实时计算排行榜列表（无需等待定时任务）
    :param db: 数据库会话
    :param study_date: 学习日期
    :param limit: 返回数量限制
    :return: 排行榜列表
    """
    # 获取当日所有学习记录
    records = db.query(StudyDuration).filter(
        StudyDuration.study_date == study_date
    ).all()
    
    if not records:
        return []
    
    # 计算有效用户数（学习时长>0）
    effective_users = len([r for r in records if r.total_minutes > 0])
    
    if effective_users == 0:
        return []
    
    # 实时计算每个用户的击败百分比
    rank_items = []
    for record in records:
        if record.total_minutes > 0:
            # 计算学习时长小于当前用户的人数
            less_count = len([r for r in records if r.total_minutes < record.total_minutes and r.total_minutes > 0])
            
            # 计算击败百分比
            beat_percent = (less_count / effective_users) * 100
            # 四舍五入到两位小数
            beat_percent = round(beat_percent, 2)
            
            rank_items.append({
                "user_id": record.user_id,
                "beat_percent": beat_percent,
                "total_minutes": record.total_minutes
            })
    
    # 按击败百分比排序
    rank_items.sort(key=lambda x: x["beat_percent"], reverse=True)
    
    # 更新缓存（下次查询可以直接使用）
    update_real_time_rank_cache(rank_items, study_date)
    
    return rank_items[:limit]


def update_real_time_rank_cache(rank_items: list, study_date: date) -> None:
    """
    更新实时排行榜缓存（10分钟过期）
    :param rank_items: 排行榜数据
    :param study_date: 学习日期
    """
    r = cache._redis()
    key = f"rank:beat:{study_date}"
    
    # 清空现有缓存
    r.delete(key)
    
    # 更新缓存
    for item in rank_items:
        r.hset(key, item["user_id"], str(item["beat_percent"]))
    
    # 设置缓存过期时间（10分钟）
    r.expire(key, 10 * 60)