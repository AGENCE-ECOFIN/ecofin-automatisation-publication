from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ecofin_pub"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Blotato API (Plateforme de publication centralisée - 3 réseaux)
    BLOTATO_API_KEY: Optional[str] = None
    BLOTATO_LINKEDIN_ACCOUNT_ID: Optional[str] = None
    BLOTATO_X_ACCOUNT_ID: Optional[str] = None
    BLOTATO_FACEBOOK_ACCOUNT_ID: Optional[str] = None
    BLOTATO_FACEBOOK_PAGE_ID: Optional[str] = None  # ID de la page Facebook
    
    # Buffer API (Legacy - remplacé par Blotato)
    BUFFER_ACCESS_TOKEN: Optional[str] = None
    BUFFER_LINKEDIN_PROFILE_ID: Optional[str] = None
    BUFFER_TWITTER_PROFILE_ID: Optional[str] = None
    BUFFER_FACEBOOK_PROFILE_ID: Optional[str] = None
    BUFFER_INSTAGRAM_PROFILE_ID: Optional[str] = None
    
    # Legacy tokens (optionnels)
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    
    # SMTP Configuration
    SMTP_HOST: str = "sequencemedia.smtp.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "n8n_mediamania"
    SMTP_PASSWORD: str = "W44MptRw9ww63C"
    SMTP_FROM_EMAIL: str = "n8n_mediamania@sequencemedia.smtp.com"
    SMTP_FROM_NAME: str = "EcoFin Publication"
    
    # Application
    APP_NAME: str = "EcoFin Publication"
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"


settings = Settings()
