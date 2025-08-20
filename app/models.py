from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.database import Base


class File(Base):
	__tablename__ = "files"

	id: Mapped[str] = mapped_column(String, primary_key=True)
	filename: Mapped[str] = mapped_column(String, nullable=False)
	content_type: Mapped[str] = mapped_column(String, nullable=True)
	status: Mapped[str] = mapped_column(String, default="uploading")
	progress: Mapped[int] = mapped_column(Integer, default=0)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
	content_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
	error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

	rows: Mapped[list["ParsedRow"]] = relationship("ParsedRow", back_populates="file", cascade="all, delete-orphan")


class ParsedRow(Base):
	__tablename__ = "parsed_rows"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	file_id: Mapped[str] = mapped_column(String, ForeignKey("files.id", ondelete="CASCADE"))
	row_index: Mapped[int] = mapped_column(Integer, nullable=False)
	# store row as JSON string for flexibility
	data_json: Mapped[str] = mapped_column(Text, nullable=False)

	file: Mapped[File] = relationship("File", back_populates="rows") 