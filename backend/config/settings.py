from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "mysql+pymysql://UserSoft:SoftP0987@127.0.0.1:3306/SoftwareProject?charset=utf8mb4"
    #"mysql+pymysql://UserSoft:********@127.0.0.1:3306/SoftwareProject?charset=utf8mb4"
    #"sqlite:///./online_study.db"
    # 生产环境请使用 redis://...；本地无 Redis 时可设为 "fakeredis"
    redis_url: str = "fakeredis"

    jwt_secret: str = "dev-only-secret-key-not-for-production-use"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    default_avatar_url: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=study"

    rate_limit_register_ip_max: int = 10
    rate_limit_login_ip_max: int = 20

    @model_validator(mode="after")
    def validate_jwt_secret(self):
        is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
        if is_production:
            if self.jwt_secret == "dev-only-secret-key-not-for-production-use" or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be set via environment variable and be at least 32 characters long in production."
                )
        return self


settings = Settings()
