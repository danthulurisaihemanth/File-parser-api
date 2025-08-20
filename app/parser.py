from __future__ import annotations
from typing import Iterable
import os
import math
import pandas as pd


def parse_file_to_rows(file_path: str) -> Iterable[dict]:
	# detect format by extension
	ext = os.path.splitext(file_path)[1].lower()
	if ext in [".csv", ".txt"]:
		df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
	elif ext in [".xls", ".xlsx"]:
		df = pd.read_excel(file_path, dtype=str)
		# replace NaN with empty strings
		df = df.fillna("")
	else:
		# fallback: try csv reading
		df = pd.read_csv(file_path, dtype=str, keep_default_na=False)

	for index, row in df.iterrows():
		yield {k: ("" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)) for k, v in row.to_dict().items()} 