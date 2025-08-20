from __future__ import annotations
import os
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, UploadFile, File as FastAPIFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models import File as FileModel, ParsedRow
from app.schemas import FileCreateResponse, FileProgressResponse, FileListItem, ParsedContentResponse
from app.progress import progress_tracker
from app.background import process_file_in_background


app = FastAPI(title="File Parser CRUD API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency

def get_db() -> Session:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


# Ensure upload dir exists
os.makedirs(settings.upload_dir, exist_ok=True)


@app.post("/files", response_model=FileCreateResponse)
async def upload_file(
	background_tasks: BackgroundTasks,
	file: Annotated[UploadFile, FastAPIFile(...)],
	db: Session = Depends(get_db),
):
	file_id = str(uuid.uuid4())

	# basic size guard via SpooledTemporaryFile doesn't expose easily; rely on server/client for very large
	filename = file.filename or "uploaded_file"
	content_type = file.content_type

	storage_path = os.path.join(settings.upload_dir, f"{file_id}_{filename}")

	progress_tracker.set_status(file_id, "uploading")
	progress_tracker.set_progress(file_id, 0)

	# Save stream to disk with simulated progress
	bytes_written = 0
	chunk_size = 1024 * 1024
	with open(storage_path, "wb") as out:
		while True:
			chunk = await file.read(chunk_size)
			if not chunk:
				break
			out.write(chunk)
			bytes_written += len(chunk)
			# simulate progress if size unknown
			progress_tracker.set_progress(file_id, min(95, progress_tracker.get_progress(file_id) + 5))

	# persist DB record
	db_file = FileModel(
		id=file_id,
		filename=filename,
		content_type=content_type,
		status="uploading",
		progress=progress_tracker.get_progress(file_id),
		created_at=datetime.utcnow(),
		updated_at=datetime.utcnow(),
		storage_path=storage_path,
	)
	db.add(db_file)
	db.commit()

	# enqueue background parsing
	background_tasks.add_task(process_file_in_background, file_id, storage_path)

	return FileCreateResponse(file_id=file_id, status=progress_tracker.get_status(file_id) or "uploading", progress=progress_tracker.get_progress(file_id))


@app.get("/files/{file_id}/progress", response_model=FileProgressResponse)
async def get_progress(file_id: str, db: Session = Depends(get_db)):
	db_file = db.get(FileModel, file_id)
	if not db_file:
		raise HTTPException(status_code=404, detail="File not found")
	status = progress_tracker.get_status(file_id) or db_file.status
	progress = progress_tracker.get_progress(file_id) or db_file.progress
	return FileProgressResponse(file_id=file_id, status=status, progress=progress, error_message=progress_tracker.get_error(file_id))


@app.get("/files/{file_id}", response_model=ParsedContentResponse)
async def get_file_content(file_id: str, db: Session = Depends(get_db)):
	db_file = db.get(FileModel, file_id)
	if not db_file:
		raise HTTPException(status_code=404, detail="File not found")

	status = progress_tracker.get_status(file_id) or db_file.status
	if status != "ready":
		return ParsedContentResponse(file_id=file_id, status=status, content=None, message="File upload or processing in progress. Please try again later.")

	rows = (
		db.query(ParsedRow)
		.filter(ParsedRow.file_id == file_id)
		.order_by(ParsedRow.row_index.asc())
		.all()
	)
	content = [__import__("json").loads(r.data_json) for r in rows]
	return ParsedContentResponse(file_id=file_id, status="ready", content=content)


@app.get("/files", response_model=list[FileListItem])
async def list_files(db: Session = Depends(get_db)):
	files = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
	return [FileListItem.model_validate(f) for f in files]


@app.delete("/files/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
	db_file = db.get(FileModel, file_id)
	if not db_file:
		raise HTTPException(status_code=404, detail="File not found")

	# delete rows and file
	if db_file.storage_path and os.path.exists(db_file.storage_path):
		try:
			os.remove(db_file.storage_path)
		except OSError:
			pass

	db.delete(db_file)
	db.commit()
	return {"message": "File deleted"}


@app.get("/")
async def root():
	return {"status": "ok"} 