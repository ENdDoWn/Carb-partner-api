from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # กำหนดค่าตัวแปรและ Type
    MONGODB_URL: str
    DATABASE_NAME: str

    # บอกให้ไปอ่านจากไฟล์ .env
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
