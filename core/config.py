from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # กำหนดค่าตัวแปรและ Type
    MONGODB_URL: str
    DATABASE_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    LINE_CHANNEL_ID: str
    LINE_CHANNEL_SECRET: str
    LINE_REDIRECT_URI: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
