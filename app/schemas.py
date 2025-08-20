from pydantic import BaseModel
from datetime import datetime
from typing import Any


class FileCreateResponse(BaseModel):
	file_id: str
	status: str
	progress: int


class FileProgressResponse(BaseModel):
	file_id: str
	status: str
	progress: int
	error_message: str | None = None


class FileListItem(BaseModel):
	id: str
	filename: str
	status: str
	created_at: datetime

	class Config:
		from_attributes = True


class ParsedContentResponse(BaseModel):
	file_id: str
	status: str
	content: list[dict[str, Any]] | None = None
	message: str | None = None 