import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from config import Config


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            orig_name TEXT NOT NULL,
            uploader_ip TEXT,
            created_at TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT
        )
        """)
        conn.commit()


class MediaRepository:
    """Repository class for media operations."""
    
    @staticmethod
    def create_media(filename: str, orig_name: str, uploader_ip: str, 
                    file_size: Optional[int] = None, file_type: Optional[str] = None) -> bool:
        """Create a new media record."""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO media 
                       (filename, orig_name, uploader_ip, created_at, file_size, file_type) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (filename, orig_name, uploader_ip, datetime.utcnow().isoformat(), 
                     file_size, file_type)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    @staticmethod
    def get_all_media() -> List[Dict[str, Any]]:
        """Get all media records ordered by creation date (newest first)."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT filename, orig_name, created_at, file_size, file_type FROM media ORDER BY id DESC"
            ).fetchall()
            
            return [
                {
                    "filename": row["filename"],
                    "thumb": Path(row["filename"]).stem + ".webp",
                    "orig_name": row["orig_name"],
                    "created_at": row["created_at"].replace("T", " ")[:19],
                    "file_size": row["file_size"],
                    "file_type": row["file_type"]
                }
                for row in rows
            ]
    
    @staticmethod
    def delete_media(filename: str) -> bool:
        """Delete a media record by filename."""
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM media WHERE filename = ?", (filename,))
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    @staticmethod
    def get_media_by_filename(filename: str) -> Optional[Dict[str, Any]]:
        """Get a specific media record by filename."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM media WHERE filename = ?", (filename,)
            ).fetchone()
            
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def get_media_count() -> int:
        """Get total count of media records."""
        with get_db_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM media").fetchone()
            return result[0] if result else 0