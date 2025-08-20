from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
	database_url: str = Field(default="sqlite:///./app.db")
	upload_dir: str = Field(default="uploads")
	max_upload_size_mb: int = Field(default=512)

	class Config:
		env_file = ".env"


settings = Settings() 