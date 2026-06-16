"""Backup / full-export of the database and resource files."""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

from loguru import logger

from config import settings

# Resource subfolders included in a full export (logs/backups are excluded).
_RESOURCE_DIRS = ("uploads", "reports", "exports")


class BackupService:
    def _checkpoint(self):
        """Flush the SQLite WAL into the main db file so a file copy is complete."""
        try:
            from database.engine import engine
            with engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as e:  # pragma: no cover - best effort
            logger.warning(f"WAL checkpoint failed: {e}")

    def backup_db(self) -> str:
        """Copy the database to the backups folder; returns the backup path."""
        self._checkpoint()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = settings.BACKUPS_DIR / f"backup_{timestamp}.db"
        settings.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(settings.DB_FILE, dest)
        logger.info(f"Database backed up to {dest}")
        return str(dest)

    def _dispose_engine(self):
        """Release all DB connections so the .db file can be replaced (Windows lock)."""
        try:
            from database.session import db_session as scoped
            scoped.remove()
        except Exception as e:  # pragma: no cover
            logger.warning(f"scoped session remove failed: {e}")
        try:
            from database.engine import engine
            engine.dispose()
        except Exception as e:  # pragma: no cover
            logger.warning(f"engine dispose failed: {e}")

    def _clear_wal_sidecars(self):
        for suffix in ("-wal", "-shm"):
            side = Path(str(settings.DB_FILE) + suffix)
            if side.exists():
                try:
                    side.unlink()
                except OSError:
                    pass

    def restore_db(self, src_path: str):
        """Replace the live database with a backup .db file. The app must be
        restarted afterwards (the ORM session/engine state becomes stale)."""
        self._checkpoint()
        self._dispose_engine()
        self._clear_wal_sidecars()
        shutil.copy2(src_path, settings.DB_FILE)
        logger.info(f"Database restored from {src_path}")

    def restore_full(self, zip_path: str):
        """Restore a full export zip (db + uploads/reports/exports) into DATA_DIR.
        The app must be restarted afterwards."""
        self._checkpoint()
        self._dispose_engine()
        base = settings.DATA_DIR.resolve()
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                target = (settings.DATA_DIR / member).resolve()
                # Guard against path traversal outside DATA_DIR.
                if not str(target).startswith(str(base)):
                    continue
                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        self._clear_wal_sidecars()
        logger.info(f"Full restore completed from {zip_path}")

    def export_all(self, dest_zip: str) -> str:
        """Zip the database + resource files (uploads/reports/exports) into dest_zip."""
        self._checkpoint()
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            if settings.DB_FILE.exists():
                archive.write(settings.DB_FILE, "center_management.db")
            for sub in _RESOURCE_DIRS:
                base = settings.DATA_DIR / sub
                if not base.exists():
                    continue
                for file in base.rglob("*"):
                    if file.is_file():
                        archive.write(file, str(Path(sub) / file.relative_to(base)))
        logger.info(f"Full export written to {dest_zip}")
        return dest_zip
