from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MySQL 连接字符串
    database_url: str = "mysql+pymysql://UserSoft:SoftP0987@127.0.0.1:3306/SoftwareProject?charset=utf8mb4"
    # 生产环境请使用 redis://...；本地无 Redis 时可设为 "fakeredis"
    redis_url: str = "fakeredis"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    default_avatar_url: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=study"

    rate_limit_register_ip_max: int = 10
    rate_limit_login_ip_max: int = 20


settings = Settings()