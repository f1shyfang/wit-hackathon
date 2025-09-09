import os
import sqlite3
import json
from typing import Optional, Dict, Any

DB_PATH = os.environ.get("NOTREALLY_DB_PATH", os.path.join(os.path.dirname(__file__), "notreally.db"))


def get_conn() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def init_db() -> None:
	conn = get_conn()
	try:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS jobs (
				id TEXT PRIMARY KEY,
				filename TEXT,
				filepath TEXT,
				status TEXT,
				created_at TEXT,
				results_json TEXT
			)
			"""
		)
		conn.commit()
	finally:
		conn.close()


def insert_job(job_id: str, filename: str, filepath: str, status: str, created_at: str) -> None:
	conn = get_conn()
	try:
		conn.execute(
			"INSERT INTO jobs (id, filename, filepath, status, created_at, results_json) VALUES (?, ?, ?, ?, ?, ?)",
			(job_id, filename, filepath, status, created_at, None),
		)
		conn.commit()
	finally:
		conn.close()


def update_job_result(job_id: str, status: str, results: Optional[Dict[str, Any]]) -> None:
	conn = get_conn()
	try:
		results_json = json.dumps(results) if results is not None else None
		conn.execute(
			"UPDATE jobs SET status = ?, results_json = ? WHERE id = ?",
			(status, results_json, job_id),
		)
		conn.commit()
	finally:
		conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
	conn = get_conn()
	try:
		cur = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
		row = cur.fetchone()
		if not row:
			return None
		data = dict(row)
		results = json.loads(data["results_json"]) if data.get("results_json") else None
		return {
			"job_id": data["id"],
			"status": data["status"],
			"results": results,
			"created_at": data["created_at"],
			"filename": data["filename"],
		}
	finally:
		conn.close()
