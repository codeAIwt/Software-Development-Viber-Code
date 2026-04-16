"""学习时长统计与击败百分比计算定时任务"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from config.db import get_db
from services.duration_service import calculate_beat_percent
from utils import cache


def run_duration_schedule():
    """
    执行学习时长统计与击败百分比计算
    每日04:00执行，统计前一天的学习时长
    """
    # 获取前一天的日期
    study_date = date.today() - timedelta(days=1)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已经执行过
        r = cache._redis()
        lock_key = f"lock:duration_schedule:{study_date}"
        
        # 尝试获取锁
        if not r.set(lock_key, "1", ex=3600, nx=True):
            print(f"{study_date} 的时长统计任务已经执行过，跳过")
            return
        
        print(f"开始执行 {study_date} 的学习时长统计任务")
        
        # 计算击败百分比
        calculate_beat_percent(db, study_date)
        
        print(f"{study_date} 的学习时长统计任务执行完成")
    except Exception as e:
        print(f"执行学习时长统计任务失败: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    # 手动执行任务
    run_duration_schedule()
"""每日学习时长统计定时任务占位；见 database-design.md 第 11 节。"""