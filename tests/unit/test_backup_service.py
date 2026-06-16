import os
import zipfile

from application.services import backup_service as bs
from config import settings


def test_backup_db(tmp_path, monkeypatch):
    db = tmp_path / "center_management.db"
    db.write_text("dbdata", encoding="utf-8")
    monkeypatch.setattr(settings, "DB_FILE", db)
    monkeypatch.setattr(settings, "BACKUPS_DIR", tmp_path / "backups")
    svc = bs.BackupService()
    monkeypatch.setattr(svc, "_checkpoint", lambda: None)

    path = svc.backup_db()
    assert os.path.exists(path)
    assert path.endswith(".db")


def test_export_all_zip(tmp_path, monkeypatch):
    db = tmp_path / "center_management.db"
    db.write_text("dbdata", encoding="utf-8")
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DB_FILE", db)
    docs = tmp_path / "uploads" / "documents"
    docs.mkdir(parents=True)
    (docs / "f.txt").write_text("x", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "exports").mkdir()

    svc = bs.BackupService()
    monkeypatch.setattr(svc, "_checkpoint", lambda: None)
    out = tmp_path / "export.zip"
    svc.export_all(str(out))

    with zipfile.ZipFile(out) as archive:
        names = [n.replace("\\", "/") for n in archive.namelist()]
    assert "center_management.db" in names
    assert "uploads/documents/f.txt" in names


def test_restore_db(tmp_path, monkeypatch):
    target = tmp_path / "center_management.db"
    target.write_text("old", encoding="utf-8")
    src = tmp_path / "backup.db"
    src.write_text("restored", encoding="utf-8")
    monkeypatch.setattr(settings, "DB_FILE", target)
    svc = bs.BackupService()
    monkeypatch.setattr(svc, "_checkpoint", lambda: None)
    monkeypatch.setattr(svc, "_dispose_engine", lambda: None)

    svc.restore_db(str(src))
    assert target.read_text(encoding="utf-8") == "restored"


def test_restore_full(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DB_FILE", tmp_path / "center_management.db")
    archive_path = tmp_path / "exp.zip"
    with zipfile.ZipFile(archive_path, "w") as a:
        a.writestr("center_management.db", "DBDATA")
        a.writestr("uploads/documents/f.txt", "FILE")
    svc = bs.BackupService()
    monkeypatch.setattr(svc, "_checkpoint", lambda: None)
    monkeypatch.setattr(svc, "_dispose_engine", lambda: None)

    svc.restore_full(str(archive_path))
    assert (tmp_path / "center_management.db").read_text(encoding="utf-8") == "DBDATA"
    assert (tmp_path / "uploads" / "documents" / "f.txt").read_text(encoding="utf-8") == "FILE"

