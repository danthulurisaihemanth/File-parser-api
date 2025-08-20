from __future__ import annotations
from threading import Lock
from typing import Dict


class ProgressTracker:
	def __init__(self) -> None:
		self._lock = Lock()
		self._progress: Dict[str, int] = {}
		self._status: Dict[str, str] = {}
		self._error: Dict[str, str] = {}

	def set_status(self, file_id: str, status: str) -> None:
		with self._lock:
			self._status[file_id] = status

	def get_status(self, file_id: str) -> str | None:
		with self._lock:
			return self._status.get(file_id)

	def set_progress(self, file_id: str, percent: int) -> None:
		percent = max(0, min(100, int(percent)))
		with self._lock:
			self._progress[file_id] = percent

	def get_progress(self, file_id: str) -> int:
		with self._lock:
			return self._progress.get(file_id, 0)

	def set_error(self, file_id: str, message: str) -> None:
		with self._lock:
			self._error[file_id] = message

	def get_error(self, file_id: str) -> str | None:
		with self._lock:
			return self._error.get(file_id)


progress_tracker = ProgressTracker() 