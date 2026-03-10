from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str = "receipts"

    # Plaid
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str = "production"
    plaid_access_token: str = ""

    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # App
    admin_phone: str
    admin_email: str = ""
    reminder_interval_hours: int = 24
    max_reminders: int = 3
    days_to_look_back: int = 7
    secret_key: str = "change-me"
    google_sheets_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
