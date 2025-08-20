from __future__ import annotations
from sqlalchemy.orm import Session
from app.models import File, ParsedRow
from app.progress import progress_tracker
from app.parser import parse_file_to_rows
from app.database import SessionLocal
import json
import time


def process_file_in_background(file_id: str, file_path: str) -> None:
	db = SessionLocal()
	try:
		file: File | None = db.get(File, file_id)
		if file is None:
			return

		progress_tracker.set_status(file_id, "processing")
		file.status = "processing"
		db.add(file)
		db.commit()

		# parse with progress simulated per batch
		batch: list[ParsedRow] = []
		for idx, row in enumerate(parse_file_to_rows(file_path)):
			pr = ParsedRow(file_id=file_id, row_index=idx, data_json=json.dumps(row))
			batch.append(pr)
			if len(batch) >= 500:
				db.bulk_save_objects(batch)
				db.commit()
				batch.clear()
				progress_tracker.set_progress(file_id, min(99, (progress_tracker.get_progress(file_id) + 1)))
				time.sleep(0.01)

		# flush remaining
		if batch:
			db.bulk_save_objects(batch)
			db.commit()

		progress_tracker.set_progress(file_id, 100)
		progress_tracker.set_status(file_id, "ready")
		file.status = "ready"
		file.progress = 100
		db.add(file)
		db.commit()
	except Exception as exc:
		progress_tracker.set_status(file_id, "failed")
		progress_tracker.set_error(file_id, str(exc))
		file = db.get(File, file_id)
		if file:
			file.status = "failed"
			file.error_message = str(exc)
			db.add(file)
			db.commit()
	finally:
		db.close() 