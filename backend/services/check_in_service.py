"""打卡业务逻辑"""

from datetime import datetime, date, timezone, timedelta

from sqlalchemy.orm import Session

from models.check_in import CheckIn


def check_in(db: Session, user_id: str) -> dict:
    """用户打卡"""
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz).date()

    existing = db.query(CheckIn).filter(
        CheckIn.user_id == user_id,
        CheckIn.check_in_date == today
    ).first()

    if existing:
        return {
            "checked_in": True,
            "check_in_date": today.isoformat(),
            "msg": "今日已打卡"
        }

    check_in_record = CheckIn(
        user_id=user_id,
        check_in_date=today,
        create_time=datetime.now(beijing_tz)
    )
    db.add(check_in_record)
    db.commit()

    return {
        "checked_in": True,
        "check_in_date": today.isoformat(),
        "msg": "打卡成功"
    }


def get_check_in_status(db: Session, user_id: str) -> dict:
    """获取用户打卡状态"""
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz).date()

    existing = db.query(CheckIn).filter(
        CheckIn.user_id == user_id,
        CheckIn.check_in_date == today
    ).first()

    monday = today - timedelta(days=(today.isoweekday() - 1))
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    week_records = db.query(CheckIn).filter(
        CheckIn.user_id == user_id,
        CheckIn.check_in_date.in_(week_dates)
    ).all()
    checked_dates = set(r.check_in_date for r in week_records)

    all_records = db.query(CheckIn).filter(
        CheckIn.user_id == user_id
    ).order_by(CheckIn.check_in_date.desc()).all()

    total_days = len(all_records)

    consecutive_days = 0
    check_dates = set(r.check_in_date for r in all_records)
    current_date = today
    if current_date not in check_dates:
        current_date = today - timedelta(days=1)

    while current_date in check_dates:
        consecutive_days += 1
        current_date = current_date - timedelta(days=1)

    return {
        "checked_in_today": existing is not None,
        "check_in_date": today.isoformat() if existing else None,
        "total_days": total_days,
        "consecutive_days": consecutive_days,
        "week_calendar": [
            {
                "date": d.isoformat(),
                "checked": d in checked_dates,
                "is_today": d == today
            }
            for d in week_dates
        ]
    }
