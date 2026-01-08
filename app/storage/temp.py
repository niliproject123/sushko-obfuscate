import os
import time
import uuid
import threading
from pathlib import Path
from app.config import config


class TempFileStorage:
    """Temporary file storage with automatic cleanup."""

    def __init__(self, base_dir: str = "/tmp/pdf_extractor"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._start_cleanup_thread()

    def save(self, content: bytes, extension: str = ".pdf") -> str:
        """
        Save content to a temporary file.

        Returns:
            File ID for retrieval.
        """
        file_id = str(uuid.uuid4())
        file_path = self.base_dir / f"{file_id}{extension}"
        file_path.write_bytes(content)
        return file_id

    def get(self, file_id: str, extension: str = ".pdf") -> bytes | None:
        """Retrieve file content by ID."""
        file_path = self.base_dir / f"{file_id}{extension}"
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def delete(self, file_id: str, extension: str = ".pdf") -> bool:
        """Delete a file by ID."""
        file_path = self.base_dir / f"{file_id}{extension}"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def _cleanup_old_files(self):
        """Remove files older than TTL."""
        current_time = time.time()
        for file_path in self.base_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > config.FILE_TTL:
                    try:
                        file_path.unlink()
                    except OSError:
                        pass

    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup."""
        def cleanup_loop():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_old_files()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()


# Global storage instance
storage = TempFileStorage()
