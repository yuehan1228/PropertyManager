"""应用配置 —— 通过环境变量 / .env 文件注入"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./fund_tracker.db"

    # 定时任务
    daily_job_hour: int = 22     # 每日净值同步 & 结算任务的小时 (UTC+8)
    daily_job_minute: int = 0
    timezone: str = "Asia/Shanghai"

    # 数据源
    fund_api_timeout: int = 15   # 天天基金 / 新浪 API 超时秒数
    fund_sync_batch_size: int = 5  # 并发同步基金数量

    # 业务参数
    order_cutoff_time: str = "15:00"  # 当日下单截止时间

    # 认证
    jwt_secret: str = "change-me-in-production-please-32chars!"
    dev_mode: bool = True              # 开发模式：Web 前端可免 token 访问
    wechat_appid: str = ""             # 微信小程序 AppID
    wechat_secret: str = ""            # 微信小程序 AppSecret

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
